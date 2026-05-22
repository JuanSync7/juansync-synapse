"""Tests for clerk_auth: PAT adapter, JWT helpers, App adapter (mocked)."""
from __future__ import annotations

import base64
import io
import json
import pathlib
import subprocess
import sys
import time
from unittest.mock import MagicMock, patch

import pytest

_REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts" / "lib"))

import clerk_auth as ca  # noqa: E402
import clerk_auth_config as cac  # noqa: E402


# ---------------------------------------------------------------------------
# RSA key fixture (generated once via openssl in tmp_path)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rsa_key(tmp_path_factory):
    keydir = tmp_path_factory.mktemp("rsa")
    key_path = keydir / "test_key.pem"
    subprocess.run(
        ["openssl", "genrsa", "-out", str(key_path), "2048"],
        check=True, capture_output=True,
    )
    return key_path


# ---------------------------------------------------------------------------
# sign_rs256
# ---------------------------------------------------------------------------

def test_sign_rs256_produces_256_byte_signature(rsa_key):
    sig = ca.sign_rs256(b"hello world", rsa_key)
    # 2048-bit RSA → 256-byte raw signature
    assert isinstance(sig, bytes)
    assert len(sig) == 256


def test_sign_rs256_deterministic_for_same_input(rsa_key):
    """RSA PKCS#1 v1.5 (default for openssl dgst -sign) is deterministic."""
    a = ca.sign_rs256(b"x", rsa_key)
    b = ca.sign_rs256(b"x", rsa_key)
    assert a == b


# ---------------------------------------------------------------------------
# mint_jwt
# ---------------------------------------------------------------------------

def _b64url_decode(s: str) -> bytes:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + pad)


def test_mint_jwt_three_parts_with_valid_b64(rsa_key):
    jwt = ca.mint_jwt(app_id="42", private_key_path=rsa_key)
    parts = jwt.split(".")
    assert len(parts) == 3
    header = json.loads(_b64url_decode(parts[0]))
    payload = json.loads(_b64url_decode(parts[1]))
    sig = _b64url_decode(parts[2])
    assert header == {"alg": "RS256", "typ": "JWT"}
    assert payload["iss"] == "42"
    assert "iat" in payload and "exp" in payload
    # exp ~ now+600, iat ~ now-60
    assert payload["exp"] - payload["iat"] >= 600
    assert len(sig) == 256


def test_mint_jwt_iat_offset(rsa_key):
    """iat should be slightly in the past for clock-skew tolerance."""
    now = int(time.time())
    jwt = ca.mint_jwt(app_id="x", private_key_path=rsa_key, iat=now)
    payload = json.loads(_b64url_decode(jwt.split(".")[1]))
    # iat = now - 60 (skew protection)
    assert payload["iat"] == now - 60


# ---------------------------------------------------------------------------
# PatAuthAdapter
# ---------------------------------------------------------------------------

def test_pat_adapter_returns_token_from_env(monkeypatch):
    monkeypatch.setenv("MY_TOK", "ghp_secret123")
    adapter = ca.PatAuthAdapter(cac.PatConfig(token_env="MY_TOK"))
    res = adapter.get_token()
    assert res.mode == "pat"
    assert res.token == "ghp_secret123"
    assert adapter.is_authenticated() is True
    env = adapter.env_for_subprocess()
    assert env["GH_TOKEN"] == "ghp_secret123"
    assert env["GITHUB_TOKEN"] == "ghp_secret123"


def test_pat_adapter_falls_back_to_ambient_when_env_unset(monkeypatch):
    monkeypatch.delenv("MY_TOK", raising=False)
    adapter = ca.PatAuthAdapter(cac.PatConfig(token_env="MY_TOK"))

    # Mock subprocess.run so gh auth status returns 0
    def fake_run(args, **kw):
        if args[:3] == ["gh", "auth", "status"]:
            mp = MagicMock()
            mp.returncode = 0
            mp.stdout = "Logged in to github.com as testuser"
            mp.stderr = ""
            return mp
        raise FileNotFoundError(args[0])

    monkeypatch.setattr(subprocess, "run", fake_run)
    res = adapter.get_token()
    assert res.mode == "ambient"
    assert res.token is None
    assert adapter.is_authenticated() is True
    # Ambient → no env injection (gh handles internally)
    assert adapter.env_for_subprocess() == {}


def test_pat_adapter_raises_when_neither_env_nor_ambient(monkeypatch):
    monkeypatch.delenv("MY_TOK", raising=False)
    adapter = ca.PatAuthAdapter(cac.PatConfig(token_env="MY_TOK"))

    def fake_run(args, **kw):
        if args[:3] == ["gh", "auth", "status"]:
            mp = MagicMock()
            mp.returncode = 1
            mp.stdout = ""
            mp.stderr = "not logged in"
            return mp
        raise FileNotFoundError(args[0])

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert adapter.is_authenticated() is False
    with pytest.raises(ca.AuthError, match="MY_TOK"):
        adapter.get_token()


# ---------------------------------------------------------------------------
# exchange_jwt_for_installation_token
# ---------------------------------------------------------------------------

class _FakeResp:
    def __init__(self, status: int, body: bytes):
        self.status = status
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body

    def getcode(self):
        return self.status


def test_exchange_jwt_returns_token_and_expiry(monkeypatch):
    captured = {}
    body = json.dumps({
        "token": "ghs_install_abc",
        "expires_at": "2026-05-07T12:00:00Z",
    }).encode("utf-8")

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.headers)
        captured["method"] = req.get_method()
        return _FakeResp(201, body)

    token, expires = ca.exchange_jwt_for_installation_token(
        "JWT_HERE", "999", opener=fake_urlopen,
    )
    assert token == "ghs_install_abc"
    assert expires == "2026-05-07T12:00:00Z"
    assert captured["url"] == (
        "https://api.github.com/app/installations/999/access_tokens"
    )
    assert captured["method"] == "POST"
    # Header keys are case-insensitive in urllib (capitalised)
    assert any(v == "Bearer JWT_HERE" for v in captured["headers"].values())


def test_exchange_jwt_raises_on_non_2xx():
    def fake_urlopen(req, timeout=None):
        return _FakeResp(404, b'{"message":"not found"}')

    with pytest.raises(ca.AuthError):
        ca.exchange_jwt_for_installation_token(
            "J", "x", opener=fake_urlopen,
        )


# ---------------------------------------------------------------------------
# AppAuthAdapter — caching
# ---------------------------------------------------------------------------

def test_app_adapter_caches_token_and_remints_near_expiry(rsa_key, monkeypatch):
    cfg = cac.AppConfig(
        app_id="1",
        installation_id="2",
        private_key_path=rsa_key,
    )
    adapter = ca.AppAuthAdapter(cfg)

    calls = []

    def fake_exchange(jwt, installation_id, *, opener=None):
        calls.append((jwt, installation_id))
        # Token expires in 1 hour
        future = time.gmtime(time.time() + 3600)
        iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", future)
        return f"token_{len(calls)}", iso

    monkeypatch.setattr(ca, "exchange_jwt_for_installation_token", fake_exchange)

    r1 = adapter.get_token()
    r2 = adapter.get_token()
    assert r1.token == "token_1"
    assert r2.token == "token_1"   # cached
    assert len(calls) == 1

    # Force expiry inside the buffer (5 min before expires_at)
    near_expiry = time.gmtime(time.time() + 60)   # only 1 min from now
    adapter._cached_expires_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", near_expiry)
    r3 = adapter.get_token()
    assert r3.token == "token_2"
    assert len(calls) == 2


def test_app_adapter_env_for_subprocess(rsa_key, monkeypatch):
    cfg = cac.AppConfig(
        app_id="1", installation_id="2", private_key_path=rsa_key,
    )
    adapter = ca.AppAuthAdapter(cfg)

    def fake_exchange(jwt, iid, *, opener=None):
        future = time.gmtime(time.time() + 3600)
        return "ghs_token", time.strftime("%Y-%m-%dT%H:%M:%SZ", future)

    monkeypatch.setattr(ca, "exchange_jwt_for_installation_token", fake_exchange)
    env = adapter.env_for_subprocess()
    assert env["GH_TOKEN"] == "ghs_token"
    assert env["GITHUB_TOKEN"] == "ghs_token"


# ---------------------------------------------------------------------------
# get_adapter dispatch
# ---------------------------------------------------------------------------

def test_get_adapter_pat(monkeypatch):
    cfg = cac.ClerkAuthConfig(auth="pat", pat=cac.PatConfig(token_env="X"))
    a = ca.get_adapter(cfg)
    assert isinstance(a, ca.PatAuthAdapter)


def test_get_adapter_app(rsa_key):
    cfg = cac.ClerkAuthConfig(
        auth="app",
        app=cac.AppConfig(app_id="1", installation_id="2", private_key_path=rsa_key),
    )
    a = ca.get_adapter(cfg)
    assert isinstance(a, ca.AppAuthAdapter)


def test_get_adapter_app_missing_raises():
    cfg = cac.ClerkAuthConfig(auth="app", app=None)
    with pytest.raises(ca.AuthError):
        ca.get_adapter(cfg)

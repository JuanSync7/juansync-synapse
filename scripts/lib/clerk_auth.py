"""Two-mode auth abstraction for clerk: PAT and GitHub App.

PAT mode (default):
    - Read token from env var named in `PatConfig.token_env`.
    - If env var unset and `gh auth status` exits 0 → ambient mode (let `gh`
      handle auth internally — preserves T7's behavior).
    - If neither → AuthError.

App mode (team-scale):
    - Mint a JWT (RS256) signed via openssl subprocess (stdlib only — no
      pyjwt/cryptography dependency).
    - Exchange JWT for an installation token at GitHub's
      `/app/installations/<id>/access_tokens` endpoint.
    - Cache the installation token in memory until 5 minutes before its
      `expires_at` (~1h GitHub default), then re-mint on demand.

Both adapters expose `env_for_subprocess()` returning `{GH_TOKEN, GITHUB_TOKEN}`
to inject into git/gh subprocess calls (or `{}` for ambient mode).

Stdlib only: `urllib.request`, `subprocess`, `base64`, `json`, `pathlib`, `os`.
RS256 via `openssl dgst -sha256 -sign <key>` subprocess.

JWT format: `base64url(header) + "." + base64url(payload) + "." + base64url(sig)`
with `=` padding stripped. Header: `{"alg":"RS256","typ":"JWT"}`. Claims:
`iat = now - 60` (clock-skew tolerance), `exp = now + 600` (10 min max per
GitHub spec), `iss = app_id`.
"""
from __future__ import annotations

import base64
import datetime
import json
import os
import pathlib
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Literal

from clerk_auth_config import (
    AppConfig,
    ClerkAuthConfig,
    PatConfig,
    load as load_config,
)


# ---------------------------------------------------------------------------
# Errors + AuthResult
# ---------------------------------------------------------------------------

class AuthError(Exception):
    """Raised when authentication cannot be obtained or verified."""


@dataclass
class AuthResult:
    mode: Literal["pat", "app", "ambient"]
    token: str | None = None
    expires_at: str = ""    # ISO; "" for ambient/PAT (no expiry tracking)
    auth_user: str = ""    # "App: <slug>" or "PAT: <user>" or "ambient"


# ---------------------------------------------------------------------------
# Base64url helpers
# ---------------------------------------------------------------------------

def _b64url(b: bytes) -> bytes:
    """URL-safe base64 with `=` stripped — JWT segment encoding."""
    return base64.urlsafe_b64encode(b).rstrip(b"=")


# ---------------------------------------------------------------------------
# RS256 via openssl subprocess
# ---------------------------------------------------------------------------

def sign_rs256(payload: bytes, private_key_path: pathlib.Path) -> bytes:
    """Sign `payload` with RS256 using openssl subprocess.

    Returns raw signature bytes. For a 2048-bit RSA key, this is 256 bytes;
    for 4096-bit, 512 bytes. Uses RSA PKCS#1 v1.5 padding (openssl default
    for `dgst -sign`), which is what GitHub expects for RS256.
    """
    if not pathlib.Path(private_key_path).exists():
        raise AuthError(f"private key not found: {private_key_path}")
    try:
        proc = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", str(private_key_path)],
            input=payload, capture_output=True, check=True,
        )
    except FileNotFoundError as e:
        raise AuthError("openssl not installed; required for App-mode auth") from e
    except subprocess.CalledProcessError as e:
        raise AuthError(
            f"openssl signing failed: {(e.stderr or b'').decode('utf-8', 'replace').strip()}"
        ) from e
    return proc.stdout


# ---------------------------------------------------------------------------
# JWT minting
# ---------------------------------------------------------------------------

def mint_jwt(
    app_id: str,
    private_key_path: pathlib.Path,
    *,
    iat: int | None = None,
    exp_offset: int = 600,
) -> str:
    """Mint an RS256-signed JWT for a GitHub App.

    Claims:
        iss: app_id
        iat: now - 60   (skew protection per GitHub recommendation)
        exp: now + exp_offset   (default 600 = 10 min, GitHub's max)
    """
    now = int(time.time()) if iat is None else int(iat)
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iat": now - 60,
        "exp": now + exp_offset,
        "iss": str(app_id),
    }
    h_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = h_b64 + b"." + p_b64
    sig = sign_rs256(signing_input, pathlib.Path(private_key_path))
    s_b64 = _b64url(sig)
    return (signing_input + b"." + s_b64).decode("ascii")


# ---------------------------------------------------------------------------
# Installation-token exchange
# ---------------------------------------------------------------------------

_GITHUB_INSTALL_URL = "https://api.github.com/app/installations/{iid}/access_tokens"


def exchange_jwt_for_installation_token(
    jwt: str,
    installation_id: str,
    *,
    opener: Callable | None = None,
    timeout: int = 10,
) -> tuple[str, str]:
    """POST to GitHub's installation-token endpoint. Returns (token, expires_at_iso).

    Raises AuthError on non-2xx status, non-JSON body, or network failure.
    The `opener` parameter exists for tests (default: urllib.request.urlopen).
    """
    url = _GITHUB_INSTALL_URL.format(iid=installation_id)
    req = urllib.request.Request(url, data=b"", method="POST")
    req.add_header("Authorization", f"Bearer {jwt}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")

    open_fn = opener if opener is not None else urllib.request.urlopen
    try:
        with open_fn(req, timeout=timeout) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            body = resp.read()
    except urllib.error.HTTPError as e:
        raise AuthError(
            f"installation-token exchange failed: HTTP {e.code} — "
            f"{(e.read() or b'').decode('utf-8', 'replace')[:200]}"
        ) from e
    except (urllib.error.URLError, OSError) as e:
        raise AuthError(f"installation-token exchange network error: {e}") from e

    if not (200 <= int(status) < 300):
        raise AuthError(
            f"installation-token exchange returned status {status}: "
            f"{body[:200]!r}"
        )
    try:
        data = json.loads(body)
    except (ValueError, TypeError) as e:
        raise AuthError(f"installation-token response not JSON: {e}") from e
    token = data.get("token")
    expires = data.get("expires_at", "")
    if not token:
        raise AuthError(f"installation-token response missing 'token': {data}")
    return str(token), str(expires)


# ---------------------------------------------------------------------------
# PAT adapter
# ---------------------------------------------------------------------------

def _gh_auth_status_user(runner=None) -> tuple[bool, str]:
    """Return (authenticated, user_or_empty) by calling `gh auth status`."""
    run = runner if runner is not None else subprocess.run
    try:
        proc = run(["gh", "auth", "status"],
                   check=False, capture_output=True, text=True)
    except FileNotFoundError:
        return False, ""
    if proc.returncode != 0:
        return False, ""
    # `gh auth status` writes to stderr. Try to scrape the user line.
    blob = (proc.stdout or "") + "\n" + (proc.stderr or "")
    user = ""
    for line in blob.splitlines():
        s = line.strip()
        if "Logged in to" in s and " as " in s:
            # "✓ Logged in to github.com as USER (...)"
            try:
                user = s.split(" as ", 1)[1].split()[0].rstrip(",")
            except IndexError:
                user = ""
            break
    return True, user


class PatAuthAdapter:
    def __init__(self, cfg: PatConfig):
        self.cfg = cfg

    def _env_token(self) -> str | None:
        val = os.environ.get(self.cfg.token_env, "")
        return val if val.strip() else None

    def is_authenticated(self) -> bool:
        if self._env_token():
            return True
        ok, _ = _gh_auth_status_user()
        return ok

    def get_token(self) -> AuthResult:
        tok = self._env_token()
        if tok:
            return AuthResult(
                mode="pat", token=tok, expires_at="",
                auth_user=f"PAT: token from ${self.cfg.token_env}",
            )
        ok, user = _gh_auth_status_user()
        if ok:
            return AuthResult(
                mode="ambient", token=None, expires_at="",
                auth_user=f"PAT: gh CLI ambient ({user})" if user else "PAT: gh CLI ambient",
            )
        raise AuthError(
            f"no PAT token in ${self.cfg.token_env} and gh CLI not authenticated"
        )

    def env_for_subprocess(self) -> dict[str, str]:
        tok = self._env_token()
        if tok:
            return {"GH_TOKEN": tok, "GITHUB_TOKEN": tok}
        # Ambient mode: gh CLI handles auth internally; nothing to inject.
        return {}


# ---------------------------------------------------------------------------
# App adapter (with token cache)
# ---------------------------------------------------------------------------

_REMINT_BUFFER_SEC = 5 * 60   # remint if < 5 min remain


def _parse_iso_z(s: str) -> float:
    """Parse 'YYYY-MM-DDTHH:MM:SSZ' to a unix timestamp. Returns 0 on failure."""
    if not s:
        return 0.0
    try:
        dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
        return dt.replace(tzinfo=datetime.timezone.utc).timestamp()
    except ValueError:
        # Try without Z suffix
        try:
            dt = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt.timestamp()
        except ValueError:
            return 0.0


class AppAuthAdapter:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self._cached_token: str | None = None
        self._cached_expires_at: str = ""

    def is_authenticated(self) -> bool:
        # Without --probe, just check config + key file are present.
        return (
            bool(self.cfg.app_id)
            and bool(self.cfg.installation_id)
            and pathlib.Path(self.cfg.private_key_path).exists()
        )

    def _cache_valid(self) -> bool:
        if not self._cached_token:
            return False
        ts = _parse_iso_z(self._cached_expires_at)
        if ts <= 0:
            return False
        return time.time() < ts - _REMINT_BUFFER_SEC

    def get_token(self) -> AuthResult:
        if self._cache_valid():
            return AuthResult(
                mode="app",
                token=self._cached_token,
                expires_at=self._cached_expires_at,
                auth_user=f"App: app_id={self.cfg.app_id}",
            )
        jwt = mint_jwt(self.cfg.app_id, self.cfg.private_key_path)
        token, expires_at = exchange_jwt_for_installation_token(
            jwt, self.cfg.installation_id,
        )
        self._cached_token = token
        self._cached_expires_at = expires_at
        return AuthResult(
            mode="app",
            token=token,
            expires_at=expires_at,
            auth_user=f"App: app_id={self.cfg.app_id}",
        )

    def env_for_subprocess(self) -> dict[str, str]:
        res = self.get_token()
        assert res.token, "App adapter must always produce a concrete token"
        return {"GH_TOKEN": res.token, "GITHUB_TOKEN": res.token}


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def get_adapter(cfg: ClerkAuthConfig | None = None) -> PatAuthAdapter | AppAuthAdapter:
    if cfg is None:
        cfg = load_config()
    if cfg.auth == "pat":
        return PatAuthAdapter(cfg.pat)
    if cfg.auth == "app":
        if cfg.app is None:
            raise AuthError("[clerk] auth='app' but [clerk.app] not configured")
        return AppAuthAdapter(cfg.app)
    raise AuthError(f"unknown clerk auth mode: {cfg.auth!r}")

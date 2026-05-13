"""Tests for clerk_auth_config: load/save/coexist with [telemetry]."""
from __future__ import annotations

import os
import pathlib
import sys
import textwrap

import pytest

_REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts" / "lib"))

import clerk_auth_config as cac  # noqa: E402


def test_default_load_no_file(tmp_path):
    cfg = cac.load(tmp_path / "missing.toml")
    assert cfg.auth == "pat"
    assert cfg.pat.token_env == "SYNAPSE_CLERK_TOKEN"
    assert cfg.app is None


def test_pat_round_trip(tmp_path):
    cfg = cac.ClerkAuthConfig(
        auth="pat",
        pat=cac.PatConfig(token_env="MY_TOKEN_VAR"),
        app=None,
    )
    p = tmp_path / "config.toml"
    cac.save(cfg, p)
    cfg2 = cac.load(p)
    assert cfg2.auth == "pat"
    assert cfg2.pat.token_env == "MY_TOKEN_VAR"
    assert cfg2.app is None


def test_app_round_trip(tmp_path):
    cfg = cac.ClerkAuthConfig(
        auth="app",
        pat=cac.PatConfig(),
        app=cac.AppConfig(
            app_id="123",
            installation_id="456",
            private_key_path=pathlib.Path("/tmp/clerk.pem"),
        ),
    )
    p = tmp_path / "config.toml"
    cac.save(cfg, p)
    cfg2 = cac.load(p)
    assert cfg2.auth == "app"
    assert cfg2.app is not None
    assert cfg2.app.app_id == "123"
    assert cfg2.app.installation_id == "456"
    assert str(cfg2.app.private_key_path) == "/tmp/clerk.pem"


def test_app_mode_requires_required_fields(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text(textwrap.dedent("""
        [clerk]
        auth = "app"

        [clerk.app]
        app_id = "123"
    """).strip() + "\n")
    with pytest.raises(ValueError, match="installation_id|private_key_path"):
        cac.load(p)


def test_round_trip_preserves_telemetry_block(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text(textwrap.dedent("""
        [telemetry]
        enabled = true
        sinks = ["file"]

        [telemetry.file]
        path = "/tmp/events.jsonl"
    """).strip() + "\n")
    cfg = cac.ClerkAuthConfig(
        auth="app",
        pat=cac.PatConfig(),
        app=cac.AppConfig(
            app_id="aaa",
            installation_id="bbb",
            private_key_path=pathlib.Path("/tmp/k.pem"),
        ),
    )
    cac.save(cfg, p)
    text = p.read_text()
    # Both blocks survive
    assert "[telemetry]" in text
    assert "[telemetry.file]" in text
    assert "[clerk]" in text
    assert "[clerk.app]" in text
    # Re-load clerk side
    cfg2 = cac.load(p)
    assert cfg2.auth == "app"
    assert cfg2.app.app_id == "aaa"


def test_private_key_path_tilde_expansion(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    p = tmp_path / "config.toml"
    p.write_text(textwrap.dedent("""
        [clerk]
        auth = "app"

        [clerk.app]
        app_id = "1"
        installation_id = "2"
        private_key_path = "~/clerk.pem"
    """).strip() + "\n")
    cfg = cac.load(p)
    assert cfg.app.private_key_path == tmp_path / "clerk.pem"


def test_config_path_under_home():
    p = cac.config_path()
    assert p.name == "config.toml"
    assert p.parent.name == ".synapse"


def test_overwrite_existing_clerk_block(tmp_path):
    """Saving twice should produce only one [clerk] block."""
    p = tmp_path / "config.toml"
    cfg1 = cac.ClerkAuthConfig(auth="pat", pat=cac.PatConfig(token_env="A"))
    cac.save(cfg1, p)
    cfg2 = cac.ClerkAuthConfig(auth="pat", pat=cac.PatConfig(token_env="B"))
    cac.save(cfg2, p)
    text = p.read_text()
    assert text.count("[clerk]") == 1
    cfg3 = cac.load(p)
    assert cfg3.pat.token_env == "B"

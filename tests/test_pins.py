"""Tests for scripts/lib/pins.py."""
from __future__ import annotations

import importlib
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"


@pytest.fixture
def pins_mod():
    sys.path.insert(0, str(LIB_DIR))
    if "pins" in sys.modules:
        del sys.modules["pins"]
    mod = importlib.import_module("pins")
    yield mod
    sys.path.remove(str(LIB_DIR))


def test_empty_round_trip(pins_mod, tmp_path):
    p = tmp_path / "pins.toml"
    pins = pins_mod.empty()
    pins_mod.save(pins, p)
    assert p.exists()
    pins2 = pins_mod.load(p)
    assert pins2.schema_version == 1
    assert pins2.pin == "latest"
    assert pins2.drift_exceptions == {}


def test_pin_value_round_trip(pins_mod, tmp_path):
    p = tmp_path / "pins.toml"
    pins = pins_mod.empty()
    pins.pin = "v2026.05.0"
    pins_mod.save(pins, p)
    pins2 = pins_mod.load(p)
    assert pins2.pin == "v2026.05.0"


def test_drift_exception_round_trip(pins_mod, tmp_path):
    p = tmp_path / "pins.toml"
    pins = pins_mod.empty()
    pins.drift_exceptions["skill/foo"] = pins_mod.DriftException(
        artifact_key="skill/foo",
        hash="sha256:def",
        reason="local debug logging",
        expires="2026-06-01",
    )
    pins.drift_exceptions["skill/bar"] = pins_mod.DriftException(
        artifact_key="skill/bar",
        hash="sha256:abc",
        reason="never expires",
        expires="",
    )
    pins_mod.save(pins, p)
    pins2 = pins_mod.load(p)
    assert pins2.drift_exceptions["skill/foo"].reason == "local debug logging"
    assert pins2.drift_exceptions["skill/foo"].expires == "2026-06-01"
    assert pins2.drift_exceptions["skill/bar"].expires == ""


def test_missing_file_returns_defaults(pins_mod, tmp_path):
    p = tmp_path / "does-not-exist.toml"
    pins = pins_mod.load(p)
    assert pins.pin == "latest"
    assert pins.schema_version == 1
    assert pins.drift_exceptions == {}


def test_atomic_write_no_tmp_left(pins_mod, tmp_path):
    p = tmp_path / "pins.toml"
    pins = pins_mod.empty()
    pins_mod.save(pins, p)
    # No .tmp leftover
    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == []


def test_malformed_toml_raises(pins_mod, tmp_path):
    p = tmp_path / "pins.toml"
    p.write_text("this is not = = valid toml [[[")
    with pytest.raises(Exception):
        pins_mod.load(p)

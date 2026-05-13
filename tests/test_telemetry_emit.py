"""Tests for telemetry top-level emit() API."""
from __future__ import annotations

import importlib
import json
import pathlib
import sys

import pytest

_REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts" / "lib"))

import telemetry  # noqa: E402
import telemetry_config as tc  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """Each test gets its own HOME so ~/.synapse is isolated."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("SYNAPSE_TELEMETRY_DISABLE", raising=False)
    telemetry.reset()
    yield
    telemetry.reset()


def _events_path(tmp_path):
    return tmp_path / ".synapse" / "events.jsonl"


def test_emit_default_writes_to_file_sink(tmp_path):
    telemetry.emit("install", artifact="skill/foo")
    p = _events_path(tmp_path)
    assert p.exists()
    line = p.read_text().strip()
    rec = json.loads(line)
    assert rec["event_type"] == "install"
    assert rec["artifact"] == "skill/foo"


def test_emit_disabled_via_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_TELEMETRY_DISABLE", "1")
    telemetry.reset()
    telemetry.emit("install", artifact="skill/foo")
    assert not _events_path(tmp_path).exists()


def test_emit_disabled_via_config(tmp_path):
    cfg_path = tmp_path / ".synapse" / "config.toml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text("[telemetry]\nenabled = false\nsinks = [\"file\"]\n")
    telemetry.reset()
    telemetry.emit("install")
    assert not _events_path(tmp_path).exists()


def test_emit_none_sink_is_noop(tmp_path):
    cfg_path = tmp_path / ".synapse" / "config.toml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text("[telemetry]\nenabled = true\nsinks = [\"none\"]\n")
    telemetry.reset()
    telemetry.emit("install")
    assert not _events_path(tmp_path).exists()


def test_emit_never_raises_on_bad_config(tmp_path):
    cfg_path = tmp_path / ".synapse" / "config.toml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text("not [valid toml at all =====")
    telemetry.reset()
    # Must not raise even with malformed config
    telemetry.emit("install")


def test_get_active_sink_caches(tmp_path):
    s1 = telemetry.get_active_sink()
    s2 = telemetry.get_active_sink()
    assert s1 is s2


def test_reset_clears_cache(tmp_path):
    s1 = telemetry.get_active_sink()
    telemetry.reset()
    s2 = telemetry.get_active_sink()
    assert s1 is not s2


def test_emit_with_metadata(tmp_path):
    telemetry.emit("pin_changed", artifact="", metadata={"old": "latest", "new": "v1"})
    rec = json.loads(_events_path(tmp_path).read_text().strip())
    assert rec["metadata"] == {"old": "latest", "new": "v1"}


def test_emit_multiple_events(tmp_path):
    telemetry.emit("install", artifact="a")
    telemetry.emit("install", artifact="b")
    telemetry.emit("uninstall", artifact="a")
    lines = _events_path(tmp_path).read_text().splitlines()
    assert len(lines) == 3

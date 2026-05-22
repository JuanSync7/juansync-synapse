"""Tests for telemetry_config: load/save/disabled semantics."""
from __future__ import annotations

import os
import pathlib
import sys
import textwrap

import pytest

_REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts" / "lib"))

import telemetry_config as tc  # noqa: E402


def test_default_load_no_file(tmp_path):
    cfg = tc.load(tmp_path / "missing.toml")
    assert cfg.enabled is True
    assert cfg.sinks == ["file"]
    assert cfg.file is not None
    # default file path under ~/.synapse/events.jsonl
    assert str(cfg.file.path).endswith("events.jsonl")


def test_round_trip(tmp_path):
    cfg = tc.TelemetryConfig(
        enabled=True,
        sinks=["file", "http"],
        file=tc.FileSinkConfig(path=tmp_path / "events.jsonl"),
        http=tc.HttpSinkConfig(
            url="https://example.com/ingest",
            auth_header="Bearer ${TOKEN}",
            timeout=10,
        ),
        otlp=None,
    )
    p = tmp_path / "config.toml"
    tc.save(cfg, p)
    cfg2 = tc.load(p)
    assert cfg2.enabled is True
    assert cfg2.sinks == ["file", "http"]
    assert cfg2.file.path == pathlib.Path(tmp_path / "events.jsonl")
    assert cfg2.http.url == "https://example.com/ingest"
    assert cfg2.http.auth_header == "Bearer ${TOKEN}"
    assert cfg2.http.timeout == 10


def test_otlp_round_trip(tmp_path):
    cfg = tc.TelemetryConfig(
        enabled=True,
        sinks=["otlp"],
        file=tc.FileSinkConfig(path=tmp_path / "events.jsonl"),
        otlp=tc.OtlpSinkConfig(endpoint="https://otel.example.com:4317", timeout=7),
    )
    p = tmp_path / "config.toml"
    tc.save(cfg, p)
    cfg2 = tc.load(p)
    assert cfg2.sinks == ["otlp"]
    assert cfg2.otlp.endpoint == "https://otel.example.com:4317"
    assert cfg2.otlp.timeout == 7


def test_is_disabled_env(monkeypatch):
    monkeypatch.setenv("SYNAPSE_TELEMETRY_DISABLE", "1")
    assert tc.is_disabled() is True
    monkeypatch.delenv("SYNAPSE_TELEMETRY_DISABLE", raising=False)
    assert tc.is_disabled() is False


def test_enabled_false_overrides(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text(textwrap.dedent("""
        [telemetry]
        enabled = false
        sinks = ["file"]
    """).strip() + "\n")
    cfg = tc.load(p)
    assert cfg.enabled is False


def test_none_sink_treated_as_disabled(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text(textwrap.dedent("""
        [telemetry]
        enabled = true
        sinks = ["none"]
    """).strip() + "\n")
    cfg = tc.load(p)
    assert cfg.sinks == ["none"]
    assert tc.effectively_disabled(cfg) is True


def test_empty_sinks_treated_as_disabled(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text(textwrap.dedent("""
        [telemetry]
        enabled = true
        sinks = []
    """).strip() + "\n")
    cfg = tc.load(p)
    assert cfg.sinks == []
    assert tc.effectively_disabled(cfg) is True


def test_config_path_returns_under_home():
    p = tc.config_path()
    assert isinstance(p, pathlib.Path)
    assert p.name == "config.toml"

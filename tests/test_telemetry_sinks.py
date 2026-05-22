"""Tests for telemetry sinks: file/http/otlp/multi + env expansion.

All HTTP/OTLP tests mock urllib.request.urlopen — no real network.
"""
from __future__ import annotations

import io
import json
import pathlib
import sys
import urllib.error
import urllib.request

import pytest

_REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts" / "lib"))

import telemetry_config as tc  # noqa: E402
import telemetry_event as te  # noqa: E402
import telemetry_sinks as ts  # noqa: E402


# ---------------------------------------------------------------------------
# FileSink
# ---------------------------------------------------------------------------

def test_file_sink_writes_one_line_per_event(tmp_path):
    p = tmp_path / "events.jsonl"
    sink = ts.FileSink(tc.FileSinkConfig(path=p))
    sink.emit(te.Event.now("install", artifact="skill/foo"))
    sink.emit(te.Event.now("uninstall", artifact="skill/foo"))
    lines = p.read_text().splitlines()
    assert len(lines) == 2
    e1 = json.loads(lines[0])
    e2 = json.loads(lines[1])
    assert e1["event_type"] == "install"
    assert e2["event_type"] == "uninstall"


def test_file_sink_creates_parent_dir(tmp_path):
    p = tmp_path / "deep" / "nested" / "events.jsonl"
    sink = ts.FileSink(tc.FileSinkConfig(path=p))
    sink.emit(te.Event.now("install"))
    assert p.exists()


def test_file_sink_appends(tmp_path):
    p = tmp_path / "events.jsonl"
    sink = ts.FileSink(tc.FileSinkConfig(path=p))
    sink.emit(te.Event.now("install"))
    sink2 = ts.FileSink(tc.FileSinkConfig(path=p))
    sink2.emit(te.Event.now("uninstall"))
    assert len(p.read_text().splitlines()) == 2


# ---------------------------------------------------------------------------
# HttpSink
# ---------------------------------------------------------------------------

class _FakeUrlopenCapture:
    def __init__(self):
        self.calls = []

    def __call__(self, request, timeout=None):
        # Capture: full Request, body bytes, headers, timeout
        self.calls.append({
            "url": request.full_url,
            "method": request.get_method(),
            "headers": dict(request.header_items()),
            "body": request.data,
            "timeout": timeout,
        })

        class _R:
            def read(self_inner): return b""
            def __enter__(self_inner): return self_inner
            def __exit__(self_inner, *a): return False
        return _R()


def test_http_sink_posts_json(monkeypatch):
    capture = _FakeUrlopenCapture()
    monkeypatch.setattr(urllib.request, "urlopen", capture)
    sink = ts.HttpSink(tc.HttpSinkConfig(url="https://x.example.com/ingest", timeout=4))
    sink.emit(te.Event.now("install", artifact="skill/foo"))
    assert len(capture.calls) == 1
    call = capture.calls[0]
    assert call["url"] == "https://x.example.com/ingest"
    assert call["method"] == "POST"
    # case-insensitive header lookup
    headers_lower = {k.lower(): v for k, v in call["headers"].items()}
    assert headers_lower.get("content-type") == "application/json"
    assert call["timeout"] == 4
    body = json.loads(call["body"].decode("utf-8"))
    assert body["event_type"] == "install"
    assert body["artifact"] == "skill/foo"


def test_http_sink_auth_header_env_expansion(monkeypatch):
    monkeypatch.setenv("MY_TELEM_TOKEN", "secret123")
    capture = _FakeUrlopenCapture()
    monkeypatch.setattr(urllib.request, "urlopen", capture)
    sink = ts.HttpSink(tc.HttpSinkConfig(
        url="https://x.example.com/ingest",
        auth_header="Bearer ${MY_TELEM_TOKEN}",
    ))
    sink.emit(te.Event.now("install"))
    headers_lower = {k.lower(): v for k, v in capture.calls[0]["headers"].items()}
    assert headers_lower.get("authorization") == "Bearer secret123"


def test_http_sink_missing_env_drops_header(monkeypatch):
    monkeypatch.delenv("UNSET_TELEM_TOKEN", raising=False)
    capture = _FakeUrlopenCapture()
    monkeypatch.setattr(urllib.request, "urlopen", capture)
    sink = ts.HttpSink(tc.HttpSinkConfig(
        url="https://x.example.com/ingest",
        auth_header="Bearer ${UNSET_TELEM_TOKEN}",
    ))
    sink.emit(te.Event.now("install"))
    headers_lower = {k.lower(): v for k, v in capture.calls[0]["headers"].items()}
    assert "authorization" not in headers_lower


def test_http_sink_swallows_network_errors(monkeypatch, capsys):
    def boom(*a, **kw):
        raise urllib.error.URLError("network down")
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    sink = ts.HttpSink(tc.HttpSinkConfig(url="https://x.example.com/ingest"))
    # Must not raise
    sink.emit(te.Event.now("install"))
    captured = capsys.readouterr()
    assert "telemetry" in captured.err.lower()


# ---------------------------------------------------------------------------
# OtlpSink
# ---------------------------------------------------------------------------

def test_otlp_sink_posts_envelope(monkeypatch):
    capture = _FakeUrlopenCapture()
    monkeypatch.setattr(urllib.request, "urlopen", capture)
    sink = ts.OtlpSink(tc.OtlpSinkConfig(endpoint="https://otel.example.com:4318"))
    sink.emit(te.Event.now("install", artifact="skill/foo"))
    call = capture.calls[0]
    assert call["url"] == "https://otel.example.com:4318/v1/logs"
    body = json.loads(call["body"].decode("utf-8"))
    assert "resourceLogs" in body
    rec = body["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]
    assert rec["body"]["stringValue"] == "install"


def test_otlp_sink_swallows_errors(monkeypatch, capsys):
    def boom(*a, **kw):
        raise urllib.error.URLError("nope")
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    sink = ts.OtlpSink(tc.OtlpSinkConfig(endpoint="https://otel.example.com"))
    sink.emit(te.Event.now("install"))
    captured = capsys.readouterr()
    assert "telemetry" in captured.err.lower()


# ---------------------------------------------------------------------------
# MultiSink
# ---------------------------------------------------------------------------

class _RaisingSink:
    def emit(self, event):
        raise RuntimeError("boom")


class _CountingSink:
    def __init__(self):
        self.count = 0
    def emit(self, event):
        self.count += 1


def test_multisink_swallows_per_sink_errors(capsys):
    counter = _CountingSink()
    multi = ts.MultiSink([_RaisingSink(), counter, _RaisingSink()])
    multi.emit(te.Event.now("install"))
    assert counter.count == 1
    err = capsys.readouterr().err
    assert "telemetry" in err.lower()


# ---------------------------------------------------------------------------
# expand_env helper
# ---------------------------------------------------------------------------

def test_expand_env_sets_value(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    out, ok = ts.expand_env("Bearer ${FOO}")
    assert out == "Bearer bar"
    assert ok is True


def test_expand_env_missing_returns_not_ok(monkeypatch):
    monkeypatch.delenv("UNSET_X", raising=False)
    out, ok = ts.expand_env("Bearer ${UNSET_X}")
    assert ok is False


def test_expand_env_no_var_passthrough():
    out, ok = ts.expand_env("Bearer plain-token")
    assert out == "Bearer plain-token"
    assert ok is True

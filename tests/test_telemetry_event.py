"""Tests for telemetry_event: schema + OTLP envelope conversion."""
from __future__ import annotations

import json
import pathlib
import re
import sys

_REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts" / "lib"))

import telemetry_event as te  # noqa: E402


_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def test_now_autofills_timestamp_and_machine_id():
    e = te.Event.now("install", artifact="skill/foo")
    assert _ISO_RE.match(e.timestamp), e.timestamp
    assert e.event_type == "install"
    assert e.artifact == "skill/foo"
    assert e.machine_id  # hostname


def test_to_dict_is_json_serializable():
    e = te.Event.now("install", artifact="skill/foo", metadata={"a": 1, "b": [2, 3]})
    d = e.to_dict()
    assert d["event_type"] == "install"
    assert d["artifact"] == "skill/foo"
    assert d["metadata"] == {"a": 1, "b": [2, 3]}
    # JSON-serializable round trip
    s = json.dumps(d)
    back = json.loads(s)
    assert back["artifact"] == "skill/foo"


def test_to_dict_contains_all_fields():
    e = te.Event.now(
        "drift_detected",
        artifact="skill/foo",
        version="v2026.05.0",
        synapse_repo="/abs/path",
        exit_status="error",
        metadata={"k": "v"},
    )
    d = e.to_dict()
    for key in (
        "timestamp", "event_type", "artifact", "version",
        "machine_id", "synapse_repo", "exit_status", "metadata",
    ):
        assert key in d, key


def test_otlp_envelope_shape():
    e = te.Event.now("install", artifact="skill/foo")
    env = te.event_to_otlp(e)
    assert "resourceLogs" in env
    rl = env["resourceLogs"][0]
    assert "resource" in rl
    assert "scopeLogs" in rl
    sl = rl["scopeLogs"][0]
    assert "logRecords" in sl
    rec = sl["logRecords"][0]
    assert "timeUnixNano" in rec
    assert rec["body"]["stringValue"] == "install"
    # Must include event_type attribute
    keys = {a["key"] for a in rec["attributes"]}
    assert "event_type" in keys
    assert "artifact" in keys


def test_timestamp_to_unix_nano_correct():
    # 2026-05-06T14:32:11Z
    e = te.Event(
        timestamp="2026-05-06T14:32:11Z",
        event_type="install",
    )
    env = te.event_to_otlp(e)
    rec = env["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]
    # unix epoch for 2026-05-06T14:32:11Z
    assert rec["timeUnixNano"] == str(1778077931 * 10**9)


def test_resource_service_name():
    e = te.Event.now("install")
    env = te.event_to_otlp(e)
    attrs = env["resourceLogs"][0]["resource"]["attributes"]
    sn = next(a for a in attrs if a["key"] == "service.name")
    assert sn["value"]["stringValue"] == "ai-synapse"

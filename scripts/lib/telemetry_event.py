"""Telemetry event schema + OTLP envelope conversion.

The Event dataclass is the canonical in-memory shape. `to_dict` produces the
JSONL line written by the file sink and the JSON body sent by the HTTP sink.
`event_to_otlp` wraps the same data in an OpenTelemetry `LogRecord` envelope
for the OTLP/HTTP-JSON sink.

Stdlib only.
"""
from __future__ import annotations

import datetime
import socket
from dataclasses import dataclass, field


@dataclass
class Event:
    timestamp: str = ""
    event_type: str = ""
    artifact: str = ""
    version: str = ""
    machine_id: str = ""
    synapse_repo: str = ""
    exit_status: str = "ok"
    metadata: dict = field(default_factory=dict)

    @classmethod
    def now(cls, event_type: str, **kwargs) -> "Event":
        ts = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        kwargs.setdefault("machine_id", socket.gethostname() or "unknown")
        return cls(timestamp=ts, event_type=event_type, **kwargs)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "artifact": self.artifact,
            "version": self.version,
            "machine_id": self.machine_id,
            "synapse_repo": self.synapse_repo,
            "exit_status": self.exit_status,
            "metadata": dict(self.metadata) if self.metadata else {},
        }


def _iso_to_unix_nano(ts: str) -> str:
    """Convert an ISO-with-Z timestamp to nanoseconds since epoch (string)."""
    if not ts:
        return "0"
    try:
        # accept "...Z" by swapping for +00:00
        norm = ts.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(norm)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return str(int(dt.timestamp() * 10**9))
    except ValueError:
        return "0"


def _attr(key: str, value) -> dict:
    """Build a single OTLP KeyValue."""
    if isinstance(value, bool):
        return {"key": key, "value": {"boolValue": value}}
    if isinstance(value, int):
        return {"key": key, "value": {"intValue": str(value)}}
    if isinstance(value, float):
        return {"key": key, "value": {"doubleValue": value}}
    return {"key": key, "value": {"stringValue": "" if value is None else str(value)}}


def event_to_otlp(event: Event) -> dict:
    attrs = [
        _attr("event_type", event.event_type),
        _attr("artifact", event.artifact),
        _attr("version", event.version),
        _attr("machine_id", event.machine_id),
        _attr("synapse_repo", event.synapse_repo),
        _attr("exit_status", event.exit_status),
        _attr("timestamp", event.timestamp),
    ]
    if event.metadata:
        for k, v in event.metadata.items():
            attrs.append(_attr(f"metadata.{k}", v))

    return {
        "resourceLogs": [{
            "resource": {
                "attributes": [
                    _attr("service.name", "ai-synapse"),
                ],
            },
            "scopeLogs": [{
                "scope": {"name": "ai-synapse.telemetry"},
                "logRecords": [{
                    "timeUnixNano": _iso_to_unix_nano(event.timestamp),
                    "severityText": "ERROR" if event.exit_status == "error" else "INFO",
                    "body": {"stringValue": event.event_type},
                    "attributes": attrs,
                }],
            }],
        }],
    }

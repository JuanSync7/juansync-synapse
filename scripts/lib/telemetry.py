"""Top-level telemetry emit API.

Call sites use only `telemetry.emit(...)`. Everything below is internal:
config loading, sink construction, caching, and silent failure.

Hard guarantee: `emit()` NEVER raises. Any failure is logged to stderr and
swallowed. Telemetry must not break the operation it observes.
"""
from __future__ import annotations

import sys
from typing import Optional

import telemetry_config as _tc
import telemetry_event as _te
import telemetry_sinks as _ts


_active_sink: Optional[_ts.MultiSink] = None
_loaded: bool = False


def reset() -> None:
    """Clear the cached sink. Next emit() rebuilds from config."""
    global _active_sink, _loaded
    _active_sink = None
    _loaded = False


def _build_sink() -> Optional[_ts.MultiSink]:
    if _tc.is_disabled():
        return None
    try:
        cfg = _tc.load()
    except Exception as e:  # noqa: BLE001
        print(f"telemetry: config load failed (disabling): {e}", file=sys.stderr)
        return None
    if _tc.effectively_disabled(cfg):
        return None

    sinks = []
    for name in cfg.sinks:
        if name == "none":
            continue
        elif name == "file":
            if cfg.file is None:
                cfg.file = _tc.FileSinkConfig(path=_tc.default_events_path())
            sinks.append(_ts.FileSink(cfg.file))
        elif name == "http":
            if cfg.http is None:
                print("telemetry: http sink listed but no [telemetry.http] block; skipping",
                      file=sys.stderr)
                continue
            sinks.append(_ts.HttpSink(cfg.http))
        elif name == "otlp":
            if cfg.otlp is None:
                print("telemetry: otlp sink listed but no [telemetry.otlp] block; skipping",
                      file=sys.stderr)
                continue
            sinks.append(_ts.OtlpSink(cfg.otlp))
        else:
            print(f"telemetry: unknown sink '{name}'; skipping", file=sys.stderr)

    if not sinks:
        return None
    return _ts.MultiSink(sinks)


def get_active_sink() -> Optional[_ts.MultiSink]:
    """Return the cached MultiSink. None if disabled. Cached per process."""
    global _active_sink, _loaded
    if not _loaded:
        try:
            _active_sink = _build_sink()
        except Exception as e:  # noqa: BLE001
            print(f"telemetry: sink build failed (disabling): {e}", file=sys.stderr)
            _active_sink = None
        _loaded = True
    return _active_sink


def emit(
    event_type: str,
    *,
    artifact: str = "",
    version: str = "",
    exit_status: str = "ok",
    metadata: dict | None = None,
    synapse_repo: str = "",
) -> None:
    """Build an event from kwargs and dispatch to all configured sinks.

    Silently no-ops if telemetry is disabled. NEVER raises.
    """
    try:
        sink = get_active_sink()
        if sink is None:
            return
        event = _te.Event.now(
            event_type,
            artifact=artifact,
            version=version,
            exit_status=exit_status,
            metadata=metadata or {},
            synapse_repo=synapse_repo,
        )
        sink.emit(event)
    except Exception as e:  # noqa: BLE001 — top-level guard
        print(f"telemetry: emit failed (suppressed): {e}", file=sys.stderr)

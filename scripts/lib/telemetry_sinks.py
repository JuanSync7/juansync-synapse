"""Telemetry sinks: file (JSONL), HTTP, OTLP/HTTP-JSON, and MultiSink.

All sinks are fire-and-forget: errors are logged to stderr and never raised.
Telemetry MUST NOT break the operation it is observing.

Stdlib only — `urllib.request` for HTTP, no external deps.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

from telemetry_config import FileSinkConfig, HttpSinkConfig, OtlpSinkConfig
from telemetry_event import Event, event_to_otlp


_ENV_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _warn(msg: str) -> None:
    print(f"telemetry: {msg}", file=sys.stderr)


def expand_env(s: str) -> tuple[str, bool]:
    """Expand `${VAR}` substrings against os.environ.

    Returns (expanded_string, all_resolved). If any referenced var is unset,
    the second element is False. The first is still expanded for resolved vars
    (callers that drop on missing should check `ok`).
    """
    if "${" not in s:
        return s, True
    all_ok = True

    def repl(m):
        nonlocal all_ok
        name = m.group(1)
        val = os.environ.get(name)
        if val is None:
            all_ok = False
            return ""
        return val

    return _ENV_VAR_RE.sub(repl, s), all_ok


# ---------------------------------------------------------------------------
# File sink
# ---------------------------------------------------------------------------

class FileSink:
    def __init__(self, cfg: FileSinkConfig):
        self.cfg = cfg

    def emit(self, event: Event) -> None:
        try:
            path = pathlib.Path(self.cfg.path)
            path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(event.to_dict(), separators=(",", ":"))
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError as e:
            _warn(f"file sink failed: {e}")


# ---------------------------------------------------------------------------
# HTTP sink
# ---------------------------------------------------------------------------

def _http_post_json(url: str, body: bytes, *, headers: dict, timeout: int) -> None:
    req = urllib.request.Request(url, data=body, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        resp.read()  # drain


class HttpSink:
    def __init__(self, cfg: HttpSinkConfig):
        self.cfg = cfg

    def emit(self, event: Event) -> None:
        try:
            body = json.dumps(event.to_dict(), separators=(",", ":")).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if self.cfg.auth_header:
                expanded, ok = expand_env(self.cfg.auth_header)
                if ok and expanded.strip():
                    headers["Authorization"] = expanded
            _http_post_json(
                self.cfg.url, body, headers=headers, timeout=self.cfg.timeout
            )
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
            _warn(f"http sink failed: {e}")
        except Exception as e:  # noqa: BLE001 — last-resort guard
            _warn(f"http sink unexpected failure: {e}")


# ---------------------------------------------------------------------------
# OTLP sink (HTTP/JSON)
# ---------------------------------------------------------------------------

class OtlpSink:
    def __init__(self, cfg: OtlpSinkConfig):
        self.cfg = cfg

    def emit(self, event: Event) -> None:
        try:
            url = self.cfg.endpoint.rstrip("/") + "/v1/logs"
            body = json.dumps(event_to_otlp(event), separators=(",", ":")).encode("utf-8")
            _http_post_json(
                url, body,
                headers={"Content-Type": "application/json"},
                timeout=self.cfg.timeout,
            )
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
            _warn(f"otlp sink failed: {e}")
        except Exception as e:  # noqa: BLE001
            _warn(f"otlp sink unexpected failure: {e}")


# ---------------------------------------------------------------------------
# MultiSink (fan-out)
# ---------------------------------------------------------------------------

class MultiSink:
    def __init__(self, sinks: list):
        self.sinks = list(sinks)

    def emit(self, event: Event) -> None:
        for s in self.sinks:
            try:
                s.emit(event)
            except Exception as e:  # noqa: BLE001 — never let a sink break siblings
                _warn(f"sink {type(s).__name__} raised (suppressed): {e}")

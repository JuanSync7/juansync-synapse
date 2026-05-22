"""Read/write telemetry section of `~/.synapse/config.toml`.

Shared file with [clerk] (T6) — we only own the [telemetry.*] tables; on save
we MERGE telemetry tables into the existing file content rather than
rewriting the whole file. (Hand-rolled TOML; stdlib only.)

Schema:

    [telemetry]
    enabled = true
    sinks = ["file"]            # any of: file, http, otlp, none

    [telemetry.file]
    path = "~/.synapse/events.jsonl"

    [telemetry.http]
    url = "https://..."
    auth_header = "Bearer ${SYNAPSE_TELEMETRY_TOKEN}"
    timeout = 5

    [telemetry.otlp]
    endpoint = "https://..."
    timeout = 5

`is_disabled()` honors the SYNAPSE_TELEMETRY_DISABLE env var as a runtime
kill switch. `effectively_disabled(cfg)` covers configurations where the
sink list reduces to nothing meaningful.
"""
from __future__ import annotations

import os
import pathlib
import tomllib
from dataclasses import dataclass, field

CONFIG_NAME = "config.toml"
SYNAPSE_DIR_NAME = ".synapse"
DEFAULT_EVENTS_FILE = "events.jsonl"


def _home_synapse() -> pathlib.Path:
    return pathlib.Path(os.path.expanduser("~")) / SYNAPSE_DIR_NAME


def config_path() -> pathlib.Path:
    """Per-machine telemetry config — always under ~/.synapse/config.toml.

    Telemetry routing is a user (per-machine) choice, not project state.
    """
    return _home_synapse() / CONFIG_NAME


def default_events_path() -> pathlib.Path:
    return _home_synapse() / DEFAULT_EVENTS_FILE


@dataclass
class FileSinkConfig:
    path: pathlib.Path


@dataclass
class HttpSinkConfig:
    url: str
    auth_header: str = ""
    timeout: int = 5


@dataclass
class OtlpSinkConfig:
    endpoint: str
    timeout: int = 5


@dataclass
class TelemetryConfig:
    enabled: bool = True
    sinks: list[str] = field(default_factory=lambda: ["file"])
    file: FileSinkConfig | None = None
    http: HttpSinkConfig | None = None
    otlp: OtlpSinkConfig | None = None


def is_disabled() -> bool:
    """Runtime kill switch — env var overrides everything else."""
    val = os.environ.get("SYNAPSE_TELEMETRY_DISABLE", "")
    return val.strip() not in ("", "0", "false", "False", "FALSE")


def effectively_disabled(cfg: TelemetryConfig) -> bool:
    """True if config-level disable applies (env not consulted here)."""
    if not cfg.enabled:
        return True
    if not cfg.sinks:
        return True
    if all(s == "none" for s in cfg.sinks):
        return True
    return False


def _default() -> TelemetryConfig:
    return TelemetryConfig(
        enabled=True,
        sinks=["file"],
        file=FileSinkConfig(path=default_events_path()),
    )


def load(path: pathlib.Path | None = None) -> TelemetryConfig:
    p = pathlib.Path(path) if path is not None else config_path()
    cfg = _default()
    if not p.exists():
        return cfg
    try:
        data = tomllib.loads(p.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return cfg
    tel = data.get("telemetry", {})
    if not isinstance(tel, dict):
        return cfg

    cfg.enabled = bool(tel.get("enabled", cfg.enabled))
    sinks = tel.get("sinks", cfg.sinks)
    if isinstance(sinks, list):
        cfg.sinks = [str(s) for s in sinks]

    file_section = tel.get("file")
    if isinstance(file_section, dict) and "path" in file_section:
        fp = pathlib.Path(os.path.expanduser(str(file_section["path"])))
        cfg.file = FileSinkConfig(path=fp)

    http_section = tel.get("http")
    if isinstance(http_section, dict):
        url = str(http_section.get("url", "")).strip()
        if url:
            cfg.http = HttpSinkConfig(
                url=url,
                auth_header=str(http_section.get("auth_header", "")),
                timeout=int(http_section.get("timeout", 5)),
            )

    otlp_section = tel.get("otlp")
    if isinstance(otlp_section, dict):
        endpoint = str(otlp_section.get("endpoint", "")).strip()
        if endpoint:
            cfg.otlp = OtlpSinkConfig(
                endpoint=endpoint,
                timeout=int(otlp_section.get("timeout", 5)),
            )

    return cfg


# ---------------------------------------------------------------------------
# Save (merge-aware: we don't own the whole file)
# ---------------------------------------------------------------------------

def _quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _telemetry_block(cfg: TelemetryConfig) -> str:
    lines: list[str] = []
    lines.append("[telemetry]")
    lines.append(f"enabled = {'true' if cfg.enabled else 'false'}")
    sink_list = ", ".join(_quote(s) for s in cfg.sinks)
    lines.append(f"sinks = [{sink_list}]")

    if cfg.file is not None:
        lines.append("")
        lines.append("[telemetry.file]")
        lines.append(f"path = {_quote(str(cfg.file.path))}")

    if cfg.http is not None:
        lines.append("")
        lines.append("[telemetry.http]")
        lines.append(f"url = {_quote(cfg.http.url)}")
        lines.append(f"auth_header = {_quote(cfg.http.auth_header)}")
        lines.append(f"timeout = {int(cfg.http.timeout)}")

    if cfg.otlp is not None:
        lines.append("")
        lines.append("[telemetry.otlp]")
        lines.append(f"endpoint = {_quote(cfg.otlp.endpoint)}")
        lines.append(f"timeout = {int(cfg.otlp.timeout)}")

    return "\n".join(lines) + "\n"


_TELEMETRY_HEADERS = ("[telemetry]", "[telemetry.")


def _strip_existing_telemetry(text: str) -> str:
    """Remove all top-level [telemetry...] sections, preserving everything else."""
    lines = text.splitlines()
    out: list[str] = []
    in_telemetry = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            header = stripped
            if header == "[telemetry]" or header.startswith("[telemetry."):
                in_telemetry = True
                continue
            else:
                in_telemetry = False
                out.append(line)
                continue
        if not in_telemetry:
            out.append(line)
    # Trim trailing blank lines
    while out and out[-1].strip() == "":
        out.pop()
    return ("\n".join(out) + "\n") if out else ""


def save(cfg: TelemetryConfig, path: pathlib.Path) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    existing = ""
    if p.exists():
        try:
            existing = p.read_text()
        except OSError:
            existing = ""
    head = _strip_existing_telemetry(existing)
    body = _telemetry_block(cfg)
    if head:
        result = head.rstrip("\n") + "\n\n" + body
    else:
        result = body
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(result)
    os.replace(tmp, p)

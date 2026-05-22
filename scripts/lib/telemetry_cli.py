"""CLI for telemetry inspection, rotation, and ad-hoc emission.

Three subcommands:
  status [--json]         Print current telemetry config (NO event reading)
  rotate                  Gzip current events.jsonl with timestamped suffix,
                          truncate the original. Refuses if no file sink.
  emit <event_type> ...   Build and dispatch a single event. Used by bash
                          callers (install hooks, etc.) so shell doesn't
                          construct JSON by hand.

Identity guardrail: this CLI emits, inspects, and rotates. It NEVER reads
back events. There is no `tail`, `query`, `aggregate`, or `dashboard`
subcommand by design — telemetry is fire-and-forget; analysis lives
elsewhere.

Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime
import gzip
import json
import pathlib
import shutil
import sys

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import telemetry  # noqa: E402
import telemetry_config as tc  # noqa: E402


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

def _file_sink_active(cfg: tc.TelemetryConfig) -> bool:
    return "file" in cfg.sinks and cfg.file is not None


def _file_path(cfg: tc.TelemetryConfig) -> pathlib.Path:
    if cfg.file is not None:
        return pathlib.Path(cfg.file.path)
    return tc.default_events_path()


def _gather_status() -> dict:
    cfg_path = tc.config_path()
    cfg = tc.load()
    env_disabled = tc.is_disabled()
    cfg_disabled = tc.effectively_disabled(cfg)
    effective_enabled = cfg.enabled and not cfg_disabled and not env_disabled

    out: dict = {
        "config_path": str(cfg_path),
        "config_present": cfg_path.exists(),
        "enabled": effective_enabled,
        "config_enabled": cfg.enabled,
        "env_disabled": env_disabled,
        "sinks": list(cfg.sinks),
    }
    if _file_sink_active(cfg):
        fp = _file_path(cfg)
        out["file_path"] = str(fp)
        out["file_size_bytes"] = fp.stat().st_size if fp.exists() else 0
    if cfg.http is not None:
        out["http_url"] = cfg.http.url
    if cfg.otlp is not None:
        out["otlp_endpoint"] = cfg.otlp.endpoint
    return out


def cmd_status(args) -> int:
    info = _gather_status()
    if args.json:
        print(json.dumps(info, indent=2))
        return 0
    print(f"config_path:    {info['config_path']}")
    print(f"config_present: {info['config_present']}")
    print(f"enabled:        {info['enabled']}")
    if info["env_disabled"]:
        print("                (SYNAPSE_TELEMETRY_DISABLE is set)")
    print(f"sinks:          {', '.join(info['sinks']) if info['sinks'] else '(none)'}")
    if "file_path" in info:
        print(f"file_path:      {info['file_path']}")
        print(f"file_size:      {info['file_size_bytes']} bytes")
    if "http_url" in info:
        print(f"http_url:       {info['http_url']}")
    if "otlp_endpoint" in info:
        print(f"otlp_endpoint:  {info['otlp_endpoint']}")
    return 0


# ---------------------------------------------------------------------------
# rotate
# ---------------------------------------------------------------------------

def cmd_rotate(_args) -> int:
    cfg = tc.load()
    if not _file_sink_active(cfg):
        print(
            "error: rotate requires the 'file' sink to be configured "
            "(current sinks: " + ", ".join(cfg.sinks or ["(none)"]) + ")",
            file=sys.stderr,
        )
        return 2
    src = _file_path(cfg)
    if not src.exists() or src.stat().st_size == 0:
        print(f"nothing to rotate ({src} is empty or missing)")
        return 0
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    gz_path = src.with_suffix(src.suffix + f".{ts}.gz")
    try:
        # gzip the file
        with open(src, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        # verify gzip readable + non-empty
        with gzip.open(gz_path, "rb") as f_check:
            chunk = f_check.read(1)
            if not chunk:
                raise OSError(f"verification failed: gzip {gz_path} is empty")
        # truncate original
        with open(src, "w", encoding="utf-8") as f_trunc:
            f_trunc.truncate(0)
    except OSError as e:
        print(f"error: rotate failed: {e}", file=sys.stderr)
        # attempt cleanup of partial gz
        try:
            if gz_path.exists():
                gz_path.unlink()
        except OSError:
            pass
        return 2
    print(f"rotated: {src} -> {gz_path}")
    return 0


# ---------------------------------------------------------------------------
# emit
# ---------------------------------------------------------------------------

def _parse_metadata(items: list[str]) -> dict:
    out: dict = {}
    for raw in items or []:
        if "=" not in raw:
            raise ValueError(f"--metadata must be K=V (got {raw!r})")
        k, v = raw.split("=", 1)
        k = k.strip()
        if not k:
            raise ValueError(f"--metadata key empty in {raw!r}")
        out[k] = v
    return out


def cmd_emit(args) -> int:
    try:
        metadata = _parse_metadata(args.metadata or [])
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    # emit() is non-raising; force a fresh sink in case env changed.
    telemetry.reset()
    telemetry.emit(
        args.event_type,
        artifact=args.artifact or "",
        version=args.version or "",
        exit_status=args.exit_status or "ok",
        metadata=metadata,
        synapse_repo=args.synapse_repo or "",
    )
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cortex telemetry")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status", help="Print current telemetry configuration")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_status)

    r = sub.add_parser("rotate", help="Gzip events.jsonl and truncate")
    r.set_defaults(func=cmd_rotate)

    e = sub.add_parser("emit", help="Emit a single telemetry event")
    e.add_argument("event_type")
    e.add_argument("--artifact", default="")
    e.add_argument("--version", default="")
    e.add_argument("--exit-status", default="ok", choices=["ok", "error"])
    e.add_argument("--metadata", action="append", default=[],
                   help="Repeatable K=V pair")
    e.add_argument("--synapse-repo", default="")
    e.set_defaults(func=cmd_emit)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

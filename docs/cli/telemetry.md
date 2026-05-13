# cortex telemetry

Lifecycle event emission for ai-synapse primitives — installs, drift detections, pin changes, and clerk bumps. Routes to one or more sinks (file, HTTP, OTLP).

## Subcommands

| Subcommand | Doc |
|------------|-----|
| [`telemetry status`](telemetry-status.md) | Show config, sinks, and file size |
| [`telemetry rotate`](telemetry-rotate.md) | Gzip and truncate the events file |
| [`telemetry emit`](telemetry-emit.md) | Emit a single event (used by hooks) |

## Identity guardrail

**ai-synapse emits events. It never reads them back.**

There is no `tail`, `cat`, `query`, `aggregate`, or `dashboard` subcommand by design. Telemetry is fire-and-forget: callers append to sinks, then they are the user's data. Analysis lives in whatever tool consumes the JSONL/HTTP/OTLP feed (Loki, Datadog, a local `jq` script — your choice).

If you find yourself wanting a read-side command here, the right answer is almost always: pipe the file sink into your existing observability stack.

## Sinks

Configure in `~/.synapse/config.toml`:

```toml
[telemetry]
enabled = true
sinks = ["file"]            # any of: file, http, otlp, none

[telemetry.file]
path = "~/.synapse/events.jsonl"

[telemetry.http]
url = "https://collector.example.com/ingest"
auth_header = "Bearer ${SYNAPSE_TELEMETRY_TOKEN}"
timeout = 5

[telemetry.otlp]
endpoint = "https://otlp.example.com"
timeout = 5
```

- **file** — JSONL append, one event per line. Default sink.
- **http** — POST raw event JSON to `url`. `${VAR}` in `auth_header` expands from environment; if the var is unset, the header is dropped (no plaintext leak).
- **otlp** — POST OTLP/HTTP-JSON `LogRecord` to `<endpoint>/v1/logs`.
- **none** — explicit "drop everything" marker. Same effect as `enabled = false`.

All sinks fail silently to stderr. Telemetry MUST NOT break the operation it observes.

## Opt-out paths

1. **Per-invocation kill switch:** `SYNAPSE_TELEMETRY_DISABLE=1 cortex …`
2. **Permanent off:** `[telemetry] enabled = false` in the config file.
3. **Drop-everything sinks:** `sinks = ["none"]`.

## Event schema

```json
{
  "timestamp": "2026-05-07T10:23:45Z",
  "event_type": "drift_detected",
  "artifact": "skill/foo",
  "version": "",
  "machine_id": "host.local",
  "synapse_repo": "",
  "exit_status": "ok",
  "metadata": {"expected": "sha256:...", "actual": "sha256:..."}
}
```

`event_type` vocabulary (current):

- `install`, `uninstall`
- `pin_changed`, `pin_unpinned`, `pin_bumped`
- `drift_detected`, `drift_stashed`, `drift_restored`, `drift_adopted`, `drift_ignored`
- `clerk_bump_planned`, `clerk_bumped`, `clerk_force_push_aborted`, `clerk_dirty_abort`, `clerk_no_auth`, `clerk_branch_exists`, `clerk_network_error`

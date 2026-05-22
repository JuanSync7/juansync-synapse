# cortex telemetry emit

Build a single telemetry event from CLI arguments and dispatch it to the configured sinks. Used by bash callers (install hooks, scripts) so the shell does not have to construct event JSON by hand.

## Usage

```
cortex telemetry emit <event_type> \
    [--artifact KEY] \
    [--version V] \
    [--exit-status ok|error] \
    [--metadata K=V ...] \
    [--synapse-repo PATH]
```

`--metadata` is repeatable; values are always strings.

## Examples

```bash
cortex telemetry emit install --artifact skill/foo --metadata type=skill

cortex telemetry emit clerk_bumped \
    --artifact external/foo \
    --version v1.4.7 \
    --metadata pr_url=https://github.com/o/r/pull/42
```

## Behavior

- If telemetry is disabled (`SYNAPSE_TELEMETRY_DISABLE=1`, `[telemetry] enabled = false`, or `sinks = ["none"]`), the call is a silent no-op and exits 0.
- Sink failures are logged to stderr and never raise. Telemetry MUST NOT break the calling operation.
- Exit codes: `0` on success, `2` on argument parsing errors (e.g. malformed `--metadata`).

## When to use it

- Inside bash hooks invoked by `commands-skills.sh` or other primitive scripts that already emit shell-side lifecycle signals.
- One-off operator-driven probes ("did my sink wire up correctly?").

For Python call sites, prefer `from scripts.lib import telemetry; telemetry.emit(...)` directly — there is no benefit to shelling out.

# cortex telemetry rotate

Gzip the current `events.jsonl` to a timestamped sibling and truncate the original to empty. Use this on a cron, in CI, or by hand whenever the file is larger than you want to keep around.

## Usage

```
cortex telemetry rotate
```

## Behavior

1. Loads `~/.synapse/config.toml`. If the **file** sink is not configured, exits with `error: rotate requires the 'file' sink to be configured` (exit 2).
2. If `events.jsonl` is empty or missing, prints `nothing to rotate` and exits 0.
3. Otherwise, gzips the file to `events.jsonl.<UTC-iso>.gz` (e.g. `events.jsonl.2026-05-07T14-22-08Z.gz`).
4. Verifies the gzip is non-empty and readable.
5. Truncates `events.jsonl` to zero bytes.

If the gzip step fails mid-flight, the partial `.gz` is removed and the original file is left untouched.

## What `rotate` does NOT do

It does not delete old `.gz` files. Retention is the operator's responsibility — wire up `find ~/.synapse -name 'events.jsonl.*.gz' -mtime +30 -delete` if you want auto-cleanup.

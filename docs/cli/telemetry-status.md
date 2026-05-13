# cortex telemetry status

Print the current telemetry configuration: config file path, whether it is present, the effective enabled state (which honors `SYNAPSE_TELEMETRY_DISABLE`), the active sink list, and — when the file sink is configured — the path and size of the events file.

## Usage

```
cortex telemetry status [--json]
```

## Output

Human-readable:

```
config_path:    /home/user/.synapse/config.toml
config_present: True
enabled:        True
sinks:          file
file_path:      /home/user/.synapse/events.jsonl
file_size:      2841 bytes
```

JSON keys: `config_path`, `config_present`, `enabled`, `config_enabled`, `env_disabled`, `sinks`, `file_path`, `file_size_bytes`, plus `http_url` / `otlp_endpoint` when those sinks are configured.

## What `status` does NOT do

It does not read events. It does not query, count, or summarize the contents of `events.jsonl`. See the identity guardrail in [`telemetry`](telemetry.md).

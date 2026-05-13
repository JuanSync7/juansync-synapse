# cortex clerk status

Summarize the contents of `~/.synapse/clerk_state.toml` — what tags clerk has seen and when each submodule was last bumped.

## Usage

```
cortex clerk status [--state <path>] [--json]
```

## Output

Human-readable: per submodule, count of seen tags + latest tag + last bump timestamp + last PR URL.

JSON output is keyed by submodule path:

```json
{
  "state_path": "/home/user/.synapse/clerk_state.toml",
  "schema_version": 1,
  "submodules": {
    "external/foo": {
      "seen_tags": ["v1.4.6", "v1.4.7"],
      "last_bumped_at": "2026-05-06T08:00:00Z",
      "last_bumped_to": "v1.4.7",
      "last_pr_url": "https://github.com/o/r/pull/42"
    }
  }
}
```

If clerk has never run, the state file is absent and `status` reports `no clerk activity yet`.

# cortex clerk auth set-mode

Switch clerk between PAT and App auth modes. Writes the change to `~/.synapse/config.toml`, preserving any existing `[telemetry]` blocks.

## Usage

```
cortex clerk auth set-mode <pat|app> [options]
```

### PAT mode

```
cortex clerk auth set-mode pat [--token-env VAR]
```

`--token-env` overrides the env-var name (default `SYNAPSE_CLERK_TOKEN`).

### App mode

```
cortex clerk auth set-mode app \
    --app-id <APP_ID> \
    --installation-id <INSTALLATION_ID> \
    --private-key-path /path/to/clerk.pem
```

All three flags are required the first time you switch to App mode (or any time the existing `[clerk.app]` block is missing fields). On subsequent calls, omitted flags reuse the values already on disk.

## Examples

Switch to App mode for a freshly-registered GitHub App:

```
cortex clerk auth set-mode app \
    --app-id 123456 \
    --installation-id 789012 \
    --private-key-path ~/.synapse/clerk.pem
```

Flip back to PAT (e.g. for local dev):

```
cortex clerk auth set-mode pat
```

The App config block is preserved on disk; switching back to App mode later doesn't require re-entering the IDs.

Use a custom env var name in PAT mode:

```
cortex clerk auth set-mode pat --token-env MY_GH_TOKEN
```

## After running

Run [`clerk auth show`](clerk-auth-show.md) to confirm the change took effect, then [`clerk auth probe`](clerk-auth-probe.md) to verify the credentials actually work.

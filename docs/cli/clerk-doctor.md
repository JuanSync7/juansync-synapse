# cortex clerk doctor

Clerk-specific self checks. **This is not a full `cortex doctor` scan** — it only validates clerk's preconditions.

## Usage

```
cortex clerk doctor [--state <path>] [--probe-auth]
```

## Checks

1. **State file parses.** `~/.synapse/clerk_state.toml` is well-formed and `schema_version == 1` (or absent — clerk creates it on first run).
2. **Auth adapter.** Reports the active mode (PAT or App) and whether credentials are reachable. See [clerk auth](clerk-auth.md) for full mode descriptions.
   - PAT + token in env → `[ok] auth: PAT — token from $VAR`
   - PAT + ambient `gh` → `[ok] auth: PAT — gh CLI ambient (user)`
   - PAT + neither → `[warn] auth: PAT — NOT AUTHENTICATED`
   - App + config and key present → `[ok] auth: App — app_id=... (config valid; --probe-auth to mint a real token)`
   - App + missing key → `[warn] auth: App — private key missing at ...`
3. **`.gitmodules` presence.** Lists every `external/<suite>` submodule and whether clerk has ever observed it (first-seen tag) or bumped it.

### `--probe-auth`

For App mode, actually mints an installation token (consumes one GitHub rate-limit slot). Skip this in CI smoke tests; use it when you suspect the App credentials are broken. PAT mode treats `--probe-auth` the same as the default since the env-var/ambient check is already cheap.

Doctor exits 0 unless the state file is malformed (exit 1). A missing state file or absent `gh` auth produces warnings, not errors — clerk degrades gracefully on a fresh machine.

## Difference from `cortex doctor`

| | `cortex doctor` | `cortex clerk doctor` |
|---|---|---|
| Scope | Installed artifacts on this machine | Clerk's own preconditions |
| Reads | `installed.lock`, `pins.toml` | `clerk_state.toml`, `.gitmodules` |
| Findings | 7 categories (drift, missing-source, etc.) | 3 self checks |

Run both in CI for full coverage.

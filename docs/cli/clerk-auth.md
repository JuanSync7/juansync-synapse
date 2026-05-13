# cortex clerk auth

Two-mode authentication abstraction for the clerk: **PAT** (personal access token) and **App** (GitHub App with installation tokens).

The active mode is read from the `[clerk]` block in `~/.synapse/config.toml` — the same file that holds `[telemetry]` config. Both modes coexist on disk; you flip between them with `cortex clerk auth set-mode`.

## Subcommands

| Subcommand | Doc |
|------------|-----|
| [`clerk auth show`](clerk-auth-show.md) | Print active mode and non-secret config |
| [`clerk auth set-mode`](clerk-auth-set-mode.md) | Switch between PAT and App, persist to disk |
| [`clerk auth probe`](clerk-auth-probe.md) | Exercise the active adapter (PAT: env/ambient; App: mint a token) |

## When to use each mode

| | PAT | App |
|---|---|---|
| Setup effort | low — drop a `gh auth login` token, or set `SYNAPSE_CLERK_TOKEN` | medium — register a GitHub App, generate a private key, note app/installation IDs |
| Bus factor | bound to one human identity | tied to the App, survives team turnover |
| Audit trail | commits/PRs attributed to the human | commits/PRs attributed to the App slug |
| Token lifetime | long-lived (until revoked) | ~1 hour, auto-renewed |
| Best for | solo / dev laptops | shared CI runners, team-scale clerks |

PAT is the default. If you're a single user running clerk on your own laptop, you don't need to do anything — `gh auth login` (or a `SYNAPSE_CLERK_TOKEN` export) is enough.

Switch to App mode when:

- The clerk runs on a server you don't personally own.
- More than one human shares responsibility for the clerk's PRs.
- You want short-lived credentials that auto-rotate.

## Config schema

```toml
# ~/.synapse/config.toml
[clerk]
auth = "pat"   # "pat" or "app"

[clerk.pat]
token_env = "SYNAPSE_CLERK_TOKEN"   # env var name (token VALUE never stored on disk)

[clerk.app]
app_id = "..."
installation_id = "..."
private_key_path = "~/.synapse/clerk.pem"
```

App-mode minting flow (no third-party libs — stdlib + `openssl` subprocess):

1. Mint a JWT (RS256) signed with the private key. Claims: `iss=app_id`, `iat=now-60`, `exp=now+600`.
2. POST it to `https://api.github.com/app/installations/<installation_id>/access_tokens`.
3. Cache the returned installation token in memory until 5 minutes before its `expires_at`.

## Security notes

- **Tokens are never written to the config file.** PAT mode stores only the env-var *name*; the value lives in your shell environment. App mode stores the path to the private key; the key itself is your responsibility.
- **`auth show` and `auth probe` never print token values.** Only the env-var name (PAT) or the app/installation IDs (App).
- **Private keys**: keep `~/.synapse/clerk.pem` mode 0600. The repo `.gitignore` excludes `*.pem` so test fixtures can't accidentally commit one.
- **Rate limits**: `clerk doctor` does NOT mint App tokens by default. Use `--probe-auth` (or `clerk auth probe`) only when you intend to consume one rate-limit slot.

## Failure modes

- PAT mode + env var unset + no `gh auth login` → `apply_bump` aborts with `abort-no-auth` and emits a `clerk_no_auth` telemetry event with the AuthError message.
- App mode + missing private key file → `AuthError("private key not found")`.
- App mode + GitHub returns non-2xx → `AuthError` with the response body in the message.
- App mode + `openssl` not installed → `AuthError("openssl not installed; required for App-mode auth")`.

All failures are surfaced loudly. There is no silent fallback between modes.

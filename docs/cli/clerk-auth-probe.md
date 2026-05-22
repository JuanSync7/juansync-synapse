# cortex clerk auth probe

Exercise the active auth adapter end-to-end. **Token values are never printed.**

## Usage

```
cortex clerk auth probe
```

## Behavior by mode

### PAT mode

1. If the env var named in `[clerk.pat].token_env` is set → reports PAT-from-env.
2. Else, calls `gh auth status`. If exit 0 → reports ambient mode with the username scraped from `gh`'s output.
3. Else → exits non-zero with an error.

### App mode

1. Mints a JWT signed by the configured private key.
2. Exchanges it for an installation token at `https://api.github.com/app/installations/<id>/access_tokens`.
3. Reports the expiry timestamp on success; consumes one GitHub rate-limit slot.
4. Caches the token in memory for the duration of the process (no effect on subsequent invocations from a fresh process).

## Output

```
clerk auth probe: OK
  mode      = pat
  auth_user = PAT: token from $SYNAPSE_CLERK_TOKEN
```

```
clerk auth probe: OK
  mode      = app
  auth_user = App: app_id=123456
  expires_at = 2026-05-07T15:30:00Z
```

## Failure

Non-zero exit with a one-line `error: ...` message on stderr. Common causes:

- PAT mode, no env var, and `gh` not authenticated.
- App mode, private key missing or unreadable.
- App mode, GitHub returned non-2xx (network outage, revoked installation, clock skew beyond 60s tolerance).
- App mode, `openssl` not on PATH.

## Difference from `cortex clerk doctor`

`clerk doctor` reports auth state passively — for App mode, it checks config + key presence but does NOT mint a token (rate-limit-friendly). `clerk auth probe` always exercises the real round-trip.

For App mode in CI, prefer:

```
cortex clerk doctor --probe-auth
```

which combines the full doctor scan with a real token-mint check.

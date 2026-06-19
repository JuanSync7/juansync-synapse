# vcrpy Patterns

Loaded at `[PICK-PATTERN]` and `[SPIN-UP]` for real-API integration tests via record/replay.

## When vcrpy is the right pattern

- External HTTP/REST APIs (third-party services) — record once, replay forever.
- NOT for: own services (use ephemeral container), DB calls (use transaction-rollback), filesystem/CLI.

## Cassette location + naming

- Path: `tests/cassettes/<module-slug>/<test_name>.yaml`
- One cassette per test (not per test file) — keeps replay deterministic.

## Recording mode

- Default: **record-once** policy. First run with no cassette records; subsequent runs replay only.
- Re-record requires explicit `--rerecord` flag at the code-test-integrator skill level.
- `vcr.VCR(record_mode='once')` is the canonical setting.
- `--rerecord` deletes the cassette and records fresh.

## Required scrubbing filters (MUST configure before opening recorder)

```python
import re
import vcr

def _scrub_body(response):
    body = response["body"]["string"]
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    body = re.sub(
        r'("(?:password|token|secret|api[_-]?key)"\s*:\s*")[^"]*(")',
        r'\1REDACTED\2',
        body,
        flags=re.IGNORECASE,
    )
    response["body"]["string"] = body.encode("utf-8")
    return response

recorder = vcr.VCR(
    record_mode="once",
    filter_headers=[
        "authorization", "x-api-key", "cookie", "set-cookie",
        "x-auth-token", "proxy-authorization",
    ],
    filter_query_parameters=["api_key", "token", "key", "access_token"],
    filter_post_data_parameters=["password", "token", "secret", "client_secret"],
    before_record_response=_scrub_body,
)
```

- Vendor-specific headers (e.g., `x-stripe-signature`, `x-github-token`) — list them in project config and append to `filter_headers`.

## Endpoint validation BEFORE record

- Compare target URL against production-host blocklist from `rules/integration-constraints.md`.
- Abort recording if production host detected — emit `production-endpoint-detected` error.

## Post-record validation

- Run `secret_scanner` against the freshly written cassette. If any secret detected → delete cassette, abort conversion with `cassette-secret-leak`.
- Validate cassette is non-empty and has at least one interaction.

## Re-record triggers (when `--rerecord` is appropriate)

- API contract change announced by vendor.
- Dependency client library major version bump.
- Test failure isolated to schema mismatch in replay.

## Anti-patterns

- Recording against production.
- Committing cassettes without secret-scan attestation.
- Using `record_mode='all'` in CI (re-records every run, defeats determinism).
- Editing cassettes by hand to "fix" assertions — re-record instead.

## Out of scope

- Container patterns: see `references/testcontainers-patterns.md`.
- Cassette template structure: see `templates/recorded-response.md`.

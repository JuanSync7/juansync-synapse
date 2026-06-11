# Real-API Testing Patterns

Guidance for the **test body** of real-API integration tests. Cassette mechanics
live in `references/vcrpy-patterns.md`.

## Auth flows

- Exercise the real auth handshake (token exchange, refresh) at least once per
  service. Subsequent tests replay the recorded session.
- Never hardcode tokens. Read from env vars; vcrpy scrubbing strips them from
  cassettes on record.
- For OAuth refresh: record both the access-token-expired response **and** the
  refresh path so the client's refresh branch is covered.

## Error handling assertions

- Real APIs surface errors differently from mocks. Assert on **both** exception
  type and the error response payload (status code, body shape, error-code field).
- Cover at least one 4xx (client error) and one 5xx (server error / retry path)
  per service.
- Use vcrpy custom matchers to keep error-path cassettes deterministic across
  re-records.

## Timeout + retry behavior

- Set explicit client timeouts in the test — don't rely on library defaults.
- For clients with retry logic, record both the failed attempt and the
  successful retry so the retry branch executes during replay.

## Response shape validation

- Assert key invariants: presence of expected fields and their types. Do not
  assert exact equality on timestamps, pagination cursors, or request-ids.
- Prefer `jsonschema` or pydantic models if the project already uses them;
  otherwise use targeted dict-key assertions.

```python
assert resp["status"] == "ok"
assert isinstance(resp["items"], list)
assert {"id", "created_at"} <= resp["items"][0].keys()
```

## Pagination + iteration

- Record at least one full pagination loop: first page → next page → empty.
- Don't rely on cursor stability across re-records; treat cursors as opaque.

## Idempotency

- For state-mutating endpoints (POST/PUT/PATCH/DELETE), run the test, then
  re-run it. It should still pass.
- If the API isn't idempotent, the test setup must reset state — cleanup
  fixture or a test-only sandbox tenant.

## Latency-sensitive logic

- Don't assert on wall-clock timing in vcrpy replays — replay is instant.
- If latency must be asserted, write a separate non-recorded test gated behind
  a marker (e.g. `@pytest.mark.live`).

## Anti-patterns

- Asserting on timestamps, request-ids, or other per-record fields.
- Testing only the happy path. Error coverage is the primary value of
  real-API tests.
- Mocking the response inside a vcrpy test — defeats the point.

## Out of scope

- Cassette mechanics, scrubbing policy, record modes: see
  `references/vcrpy-patterns.md`.
- Auth token storage policy: project security guide.

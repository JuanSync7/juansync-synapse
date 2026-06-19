# Boundary reference: HTTP / external API

Per-category reference for `code-test-evaluator`. Loaded at [DETECT] when the module category is HTTP/external API. Functions are classified as **boundary-runtime**, **boundary-logical**, or **internal**.

## Detection signals

- **Runtime tier (boundary-runtime):**
  - `requests.get/post/put/patch/delete/...` calls
  - `httpx.AsyncClient`, `httpx.Client`, `httpx.get/post/...`
  - `urllib.request.urlopen`, `urllib3.PoolManager().request`
  - `aiohttp.ClientSession` and `session.get/post/...`
  - `boto3.client(...)` method invocations (e.g. `s3.put_object`)
  - `openai.*` SDK calls (`openai.ChatCompletion.create`, `client.chat.completions.create`)
  - Generated SDK clients (filenames matching `*_client.py`, `*_api.py` from codegen)
- **Logical tier (boundary-logical):**
  - Functions exported via `__all__` in `clients/`, `integrations/`, `external/`, `services/<vendor>/`
  - Body transitively invokes any runtime-tier signal above (one hop)
  - Thin vendor wrappers: signature shapes a domain call, body delegates to SDK
- **Internal:**
  - Request/response model serializers (pydantic `.model_dump()`, dataclass `asdict`)
  - Retry-budget calculators, backoff timers, jitter helpers
  - Header builders, URL composers, query-string encoders that do not issue the call
  - Auth-token formatters (signing helpers without network I/O)

## Lifecycle pattern decision rules

- **Default → `vcrpy`:** record real responses once against a sandbox/staging credential, replay deterministically thereafter. Cassettes committed under `tests/cassettes/<module>/<test_name>.yaml`.
- **`vcrpy` filters required (mandatory before commit):**
  - Strip `Authorization`, `X-API-Key`, `X-Auth-Token`, `Proxy-Authorization`
  - Strip `Cookie` and `Set-Cookie`
  - Strip vendor-specific auth headers: `X-Amz-Security-Token`, `X-OpenAI-*`, `Anthropic-Api-Key`, `OpenAI-Organization`
  - Strip query-string secrets (`api_key=`, `signature=`, presigned-URL params)
  - Document the exact filter list in the test strategy doc; pin via `filter_headers=` and `filter_query_parameters=` in the `VCR()` config
- **Use `responses` (requests) / `httpx.MockTransport` / `aioresponses` (aiohttp) instead of `vcrpy` only when:**
  - The API has no stable endpoint yet (still in dev, schema unstable per-call)
  - Responses are time-derived in a way `vcrpy`'s match-on (method, scheme, host, port, path, query) cannot stabilize
  - The test must run fully offline with zero first-record pass (e.g. CI without sandbox credentials)
- **Never recommend live calls** as the default lifecycle. Soak tests, contract tests against real vendors, and canary checks are a separate tier outside this skill's scope.

## Risk weight

- `external_dependency_risk = 4` (high)
  - Justification: auth failures, rate-limits, schema drift, vendor deprecations, regional outages, and silent response-shape changes are common and high-impact bug classes.
- Feeds into the `prioritize` formula at the [SCORE] step.

## Common over-mock anti-patterns to flag

- **Mocking the SDK client class** and asserting on `.method.assert_called_with(...)` — this is a wiring test, not a behavior test. Surface as `over_mocking_warning: sdk_class_mock`.
- **Mocking `requests.get` / `httpx.get`** to return a hand-crafted dict or `Mock(json=lambda: {...})` — diverges from real response shape, headers, status-code semantics. `vcrpy` avoids this. Surface as `over_mocking_warning: handcrafted_response`.
- **Mocking internal serializers** (pydantic models, JSON encoders) inside boundary tests — internal logic should run for real; only the network edge is replayed. Surface as `over_mocking_warning: serializer_mocked`.
- **Patching `time.sleep` inside retry loops without testing the retry policy** — flag as `coverage_gap: retry_policy_untested`.

## Out-of-scope (route to other references)

- Webhook / inbound HTTP handling — server-side; classified under queue/runtime boundary reference.
- WebSocket / Server-Sent Events / streaming responses — recommend ephemeral-container pattern; see `boundary-streaming.md`.
- gRPC / protobuf transports — see `boundary-rpc.md`.
- Database HTTP APIs (Elasticsearch, Weaviate REST) — classified under `boundary-datastore.md` even though transport is HTTP.

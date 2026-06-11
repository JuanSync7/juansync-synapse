# External Library Policy

## Principle

Third-party library calls are NOT all boundaries. The boundary is the I/O the
library performs, not the library itself. A library that does pure computation
(`json`, `hashlib`, `dataclasses`, pydantic validation) is internal regardless
of vendor.

## Stays mocked (or remains direct call) — never elevated to real integration

- **Pure-compute libs:** `json`, `hashlib`, `base64`, `re`, `datetime` (except
  `time.sleep`), `dataclasses`, `pydantic` validation, `attrs`, `decimal`,
  `fractions`, `statistics`, `numpy` array math, `pandas` non-IO operations.
- **Crypto primitives:** `cryptography.hazmat`, `pynacl` — well-tested upstream;
  mock at higher level (your `sign`/`verify` wrapper) only.
- **In-process logging:** standard `logging` module — assert via `caplog`,
  never elevate.
- **Type/schema libs:** `marshmallow`, `pydantic` model construction.

## Candidates for real integration (boundary classification applies)

- **I/O-driven libs:** `requests`, `httpx`, `boto3` clients, database drivers
  (`psycopg2`, `pymongo`, `redis`), filesystem libs (`s3fs`, `paramiko`).
- **SDK clients with network calls:** `openai`, `anthropic`, `stripe`, vendor
  SDKs — boundary at the SDK call site, lifecycle per category (vcrpy for
  HTTP-based).
- **Subprocess / tool invocation:** `docker` SDK, `kubernetes` client, `git`
  wrappers (`gitpython`, `pygit2`).

## Decision rule

A third-party call is a boundary if and only if the library's call performs
runtime I/O AND the function calling it is itself classified as a boundary in
[DETECT]. Pure-compute calls inside a runtime-boundary function don't count —
only the I/O does.

## Wrapper functions

If the codebase wraps a third-party SDK in its own thin client
(`our_clients/openai_wrapper.py`), the wrapper is the logical boundary. Test
through the wrapper using the SDK's recommended lifecycle (vcrpy for HTTP).
Don't mock the wrapper AND mock the SDK — pick one layer.

## Anti-patterns

- Treating `pydantic.BaseModel.validate` as a boundary — it's pure compute.
- Recommending real integration for `hashlib.sha256` — internal.
- Recommending mock-at-SDK-level when a wrapper exists — leaks vendor concerns
  into many tests; mock at wrapper layer.

## Out-of-scope

- License compliance, supply-chain scanning — separate concerns.
- SDK version pinning — handled at dependency layer.

# Testcontainers Patterns

Companion reference for `code-test-integrator`. Loaded at `[PICK-PATTERN]` and `[SPIN-UP]`.
See also: `references/lifecycle-patterns.md` for fixture-scope decision flow.

## Lifecycle scope

Scope hierarchy: `function` < `class` < `module` < `session`.

**Default to `class` scope** for code-test-integrator. Function scope re-spins containers per test (slow; image pulls dominate). Module/session scope leaks state across unrelated tests and breaks isolation when a test mutates schema. Class scope groups tests that share setup intent (one migration, one container) while keeping blast radius bounded — matches the lifecycle table in `lifecycle-patterns.md`.

## Setup pattern (pytest fixture)

```python
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="class")
def pg():
    # Pin to project DB version — never `latest`.
    with PostgresContainer("postgres:15.6", mem_limit="512m") as c:
        c.with_kwargs(network_mode="bridge")
        # Readiness probe — do NOT assume immediate availability.
        c.get_wrapped_container()  # forces start
        from testcontainers.core.waiting_utils import wait_for_logs
        wait_for_logs(c, "database system is ready to accept connections", timeout=30)
        yield c
        # Teardown handled by context manager finalizer.
```

Read connection params via `c.get_exposed_port(5432)` and `c.get_container_host_ip()` — never hardcode.

## Per-category container choice

- **DB (Postgres / MySQL):** official image pinned to `MAJOR.MINOR` matching prod. Run migrations once at fixture setup. Use **transaction-rollback per test** (open tx in inner fixture, rollback in finalizer) — avoids re-migrating.
- **Queue (RabbitMQ / Redis / Kafka):** official image, ephemeral storage (no volume mounts). Teardown drains queue; assert empty before yielding to next test.
- **Multi-service / whole-system:** use `DockerCompose` testcontainer when 3+ services interact. Otherwise individual containers — compose adds startup latency and obscures failures.
- **Temporal:** use `WorkflowEnvironment.from_local()` from the Temporal Python SDK testing harness — NOT a generic ephemeral container. It provides time-skipping and deterministic workflow replay.
- **Celery:** for unit tests, use Celery's `celery_app` fixture in **eager mode** (`task_always_eager=True`). Spin an ephemeral broker container only for full integration covering retries/acks.

## Resource limits

- Always cap memory: `mem_limit="512m"` (DBs may need 1g). CPU: `nano_cpus=500_000_000` (0.5 CPU) on CI.
- Network mode: `bridge` (default). **Never `host`** — collides with CI runner ports and other tests.

## Anti-patterns

- Reusing a container across test sessions (state leaks; breaks isolation).
- Sharing a container across pytest-xdist workers without an explicit lock — race conditions on schema/data.
- Hardcoding ports — let testcontainers allocate dynamic ports; read back via `get_exposed_port()`.
- Using `latest` tag — non-reproducible; pin exact `MAJOR.MINOR` (or digest for high-stakes suites).
- Skipping readiness probes — `wait_for_logs` or TCP probe is mandatory.

## Out of scope

- Production cluster connections: see `rules/integration-constraints.md`.
- Recording / replaying HTTP API responses: see `references/vcrpy-patterns.md`.

# Mock-Integration Layer — Patterns Reference

Loaded at the [GENERATE] node of the test-generate skill.

---

## 1. Definition

Mock-integration tests exercise **multiple real modules together** — a full request handler,
a workflow stage, a pipeline segment — with **every external dependency mocked**.
They prove that wiring and orchestration are correct without touching real services.

Scope: crosses at least two internal module boundaries.
Boundary: every I/O call (network, DB, file, queue, time) is replaced by a controlled double.

---

## 2. Why Mock by Default

Real-integration tests are slow, flaky, and require live infrastructure.
At gap-generation time the goal is coverage signal, not infra fitness.
The test-evaluate skill (downstream) classifies which tests are "high-value" and
schedules them for promotion to real-integration.
Generate at the mock layer first; promote later.

---

## 3. What to Mock

| Category | Libraries / Targets |
|---|---|
| HTTP clients | `httpx`, `requests`, `aiohttp.ClientSession` |
| DB sessions | `sqlalchemy.orm.Session`, async session factories |
| Filesystem | `pathlib.Path.read_text`, `builtins.open` |
| Time | `freezegun.freeze_time`, `datetime.datetime.now` |
| Subprocess | `subprocess.run`, `asyncio.create_subprocess_exec` |
| Queue clients | `aiokafka.AIOKafkaProducer`, `redis.Redis`, `boto3` SQS client |
| Object stores | `boto3` S3 client, `google.cloud.storage.Client` |
| Secrets / env | `os.environ`, `myapp.config.settings` |

---

## 4. What NOT to Mock

- Pure functions in the same package — test them through the orchestrator.
- Pydantic models and dataclasses — use them as-is; they are value objects.
- The orchestration code itself — it is the unit under test.
- Standard-library data structures (`list`, `dict`, `queue.Queue`).

Mocking any of the above creates churn without signal.

---

## 5. Mock Spec Discipline

Always bind mocks to the real class shape.

```python
from unittest.mock import Mock, MagicMock

# Preferred: spec catches missing-attr typos at call time
db_session = Mock(spec=Session)

# MagicMock only when dunder protocol is genuinely needed (context manager, iterator)
store = MagicMock(spec=S3Client)
store.__enter__.return_value = store
```

Never use bare `Mock()` or `MagicMock()` for class instances — typos in attribute
names go undetected.

---

## 6. Patch Target Rule

Patch where the symbol is **used**, not where it is **defined**.

```python
# BAD — patches the source module; the handler already imported its own reference
@patch("requests.get")

# GOOD — patches the name the handler actually resolves at runtime
@patch("myapp.handler.requests.get")
```

If `myapp/handler.py` contains `import requests`, the live name lives in
`myapp.handler.requests`, so that is the patch target.

---

## 7. Async Mocks

Use `AsyncMock` for any `async def` target. The `.return_value` is the awaited
result, not a coroutine object.

```python
from unittest.mock import AsyncMock, patch

async_client = AsyncMock(spec=httpx.AsyncClient)
async_client.get.return_value = httpx.Response(200, json={"ok": True})

with patch("myapp.service.httpx.AsyncClient", return_value=async_client):
    result = await service.fetch_data("https://example.com")
```

Never assign a plain coroutine to `return_value` — `AsyncMock` handles the
awaitable protocol automatically.

---

## 8. Asserting Full Call Sequence

For ordered multi-call workflows, use `call_args_list` with `assert_has_calls`.

```python
from unittest.mock import call

mock_db.execute.assert_has_calls([
    call("SELECT ...", {"id": 1}),
    call("UPDATE ...", {"id": 1, "status": "done"}),
], any_order=False)
```

`any_order=False` is the default but make it explicit — it documents intent.
Use `assert_called_once_with` only when exactly one call is expected.

---

## 9. Realistic Mock Returns

Mock return values must match the real contract.
Use pydantic factories or recorded golden responses — never hand-constructed dicts
that drift from the real schema.

```python
# Preferred: pydantic factory keeps the contract in sync
mock_response = UserResponse.model_construct(id=1, email="a@b.com", role="admin")
mock_db.scalar.return_value = mock_response
```

If the schema changes, the factory breaks the test at construction time —
catching contract drift before the assertion.

---

## 10. Anti-Patterns

| Anti-pattern | Why it hurts |
|---|---|
| Mocking the orchestrator under test | The test proves nothing about wiring |
| Mocking pure helpers in the same package | Creates churn; breaks on refactor |
| Recording-mode mocks captured once and never refreshed | Silently stale; reality drifts |
| Deep `autospec` on opaque third-party classes | Slow, fragile; use `spec=` instead |
| `patch` at the definition site | Wrong target; mock has no effect |
| Bare `Mock()` for class instances | Missing-attr typos pass silently |

---

## 11. Promotion Path

Any mock-integration test that test-evaluate classifies as "high-value" is a
candidate for promotion to real-integration. The promotion contract:

1. Keep the same assertions and test structure.
2. Replace mock doubles with real backends (containerized or staging).
3. Add a `pytest.mark.real_integration` marker and a skip guard for CI without infra.
4. The mock-integration test remains — it runs in unit CI; the real one runs on schedule.

Mock-integration tests are the **seed** for the real-integration suite.

---

## 12. Complete Example

Request handler that reads from DB, checks a Redis cache, then calls a downstream
HTTP service — all externals mocked, full call sequence asserted.

```python
import pytest
from unittest.mock import AsyncMock, Mock, patch, call
from myapp.handlers.user import get_user_handler
from myapp.schemas import UserResponse

@pytest.mark.asyncio
async def test_get_user_handler_cache_miss_then_fetch():
    mock_db     = Mock(spec=AsyncSession)
    mock_redis  = AsyncMock(spec=Redis)
    mock_http   = AsyncMock(spec=httpx.AsyncClient)

    # Cache miss, then DB hit, then downstream enrichment
    mock_redis.get.return_value        = None
    mock_db.scalar.return_value        = UserRecord(id=7, email="x@y.com")
    mock_http.get.return_value         = httpx.Response(200, json={"score": 42})

    with (
        patch("myapp.handlers.user.get_db_session", return_value=mock_db),
        patch("myapp.handlers.user.get_redis",      return_value=mock_redis),
        patch("myapp.handlers.user.httpx.AsyncClient", return_value=mock_http),
    ):
        response = await get_user_handler(user_id=7)

    assert response == UserResponse(id=7, email="x@y.com", score=42)
    mock_redis.get.assert_called_once_with("user:7")
    mock_db.scalar.assert_called_once()
    mock_http.get.assert_called_once_with("/enrich/7")
    mock_redis.set.assert_called_once()          # result was cached after fetch
```

The test crosses three module boundaries (cache, DB, HTTP), asserts the ordered
interaction sequence, and validates the final response shape — all without a
running service.

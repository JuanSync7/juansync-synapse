# Contract Layer — Test Patterns Reference

Contract tests verify the **shape and interface** of a system boundary, not its internal
behavior. They act as a tripwire: if a producer changes the shape of data it emits (columns,
fields, status codes, message envelope), the contract test fails before the consumer breaks.

---

## Definition

A contract test asserts that a boundary (DB table, HTTP endpoint, file, queue, CLI) exposes
the exact shape its consumers depend on. It does **not** test what the system does with data
— only that the data structure is stable and agreed upon. The producer and consumer share the
same schema artifact (Pydantic model, migration metadata, snapshot file). If either side
drifts, the contract test catches it at CI time, not at runtime.

---

## DB Schema Contract

Assert column names, types, nullability, indexes, and FK constraints using SQLAlchemy's
reflection API or your migration metadata. Run against the real DB (or an in-memory replica
after applying migrations).

```python
from sqlalchemy import inspect

def test_users_schema(engine):
    cols = {c["name"]: c for c in inspect(engine).get_columns("users")}
    assert cols["id"]["type"].__class__.__name__ == "Integer"
    assert cols["email"]["nullable"] is False
    fks = inspect(engine).get_foreign_keys("orders")
    assert any(fk["referred_table"] == "users" for fk in fks)
```

Key assertions: column presence, nullable flag, index uniqueness, FK `referred_table` and
`referred_columns`. Do not assert row counts or query results here.

---

## HTTP API Contract

Assert the request schema (Pydantic model validation), the response schema, allowed status
codes, and the error envelope shape. For FastAPI, also assert the generated OpenAPI snapshot
has not drifted.

```python
from myapp.schemas import CreateUserRequest, UserResponse

def test_request_schema_rejects_missing_email():
    with pytest.raises(ValidationError):
        CreateUserRequest(name="Alice")  # email required

def test_response_schema_fields():
    fields = UserResponse.model_fields
    assert {"id", "email", "created_at"}.issubset(fields)
```

OpenAPI snapshot check (fails fast on contract drift):

```python
import json, pathlib

def test_openapi_snapshot(app):
    current = app.openapi()
    snapshot = json.loads(pathlib.Path("tests/snapshots/openapi.json").read_text())
    assert current == snapshot, "OpenAPI schema drifted — update snapshot or fix schema"
```

Regenerate the snapshot intentionally with `pytest --update-snapshots` (custom flag).

---

## File Format Contract

Test parser + serializer round-trip, required field presence on parse, and rejection of
unknown fields (strict mode). Do not test business rules applied to the parsed data.

```python
def test_config_roundtrip(tmp_path):
    original = {"version": 2, "model": "gpt-4", "temperature": 0.7}
    path = tmp_path / "config.yaml"
    serialize_config(original, path)
    loaded = parse_config(path)
    assert loaded == original

def test_config_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        parse_config_dict({"version": 2, "unknown_key": True})
```

---

## Queue / Event Contract

Assert the message schema (Pydantic), the envelope fields (`correlation_id`, `timestamp`,
`version`), and a full enqueue-then-decode round-trip. Use an in-memory broker or a
test-mode queue client.

```python
from myapp.events import UserCreatedEvent

def test_event_envelope_fields():
    fields = UserCreatedEvent.model_fields
    assert {"correlation_id", "timestamp", "version", "payload"}.issubset(fields)

def test_event_roundtrip(queue_client):
    event = UserCreatedEvent(correlation_id="abc", payload={"user_id": 1})
    queue_client.enqueue(event)
    raw = queue_client.dequeue_raw()
    decoded = UserCreatedEvent.model_validate_json(raw)
    assert decoded.correlation_id == "abc"
```

---

## CLI Contract

Assert the argument set, subcommand listing in help text, exit codes per scenario, and
stdout/stderr separation. Use `click.testing.CliRunner` for Click-based CLIs; use
`subprocess` for compiled binaries.

```python
from click.testing import CliRunner
from myapp.cli import main

def test_help_lists_subcommands():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    for cmd in ["ingest", "query", "status"]:
        assert cmd in result.output

def test_missing_required_arg_exits_nonzero():
    result = CliRunner().invoke(main, ["ingest"])  # --path required
    assert result.exit_code != 0
    assert "Missing option" in result.output
```

For compiled binaries, capture `stdout` and `stderr` separately via `subprocess.run` with
`capture_output=True` and assert them independently.

---

## Versioning

Contract changes (added required fields, renamed columns, new envelope keys) require a
version bump. Tests assert that the schema version matches the declared library version so
drift is caught before publishing.

```python
from myapp import __version__
from myapp.schemas import EVENT_SCHEMA_VERSION

def test_schema_version_matches_library():
    major = int(__version__.split(".")[0])
    assert EVENT_SCHEMA_VERSION == major, (
        f"Schema version {EVENT_SCHEMA_VERSION} does not match "
        f"library major version {major}"
    )
```

Backward-compatible additions (optional fields) do not require a bump; removals or type
changes always do.

---

## Anti-Patterns

- **Testing implementation behind the contract**: asserting that `create_user()` sends an
  email is a unit/integration concern, not a contract concern. Contract tests stop at the
  boundary shape.
- **Duplicating unit assertions**: if a unit test already asserts a validation rule, do not
  repeat it here. Duplication drives churn when business logic changes.
- **Testing third-party libraries**: do not assert that Pydantic rejects bad types or that
  SQLAlchemy reflects correctly. Test only your schema definitions and migrations.
- **Hardcoding snapshot diffs inline**: keep snapshots in versioned files, not as inline
  strings in test code — otherwise snapshot updates require test edits.

---

## Complete Example — FastAPI Endpoint Contract

```python
# tests/contract/test_create_user_contract.py
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from myapp.main import app
from myapp.schemas import CreateUserRequest, UserResponse

client = TestClient(app)

def test_request_rejects_missing_email():
    with pytest.raises(ValidationError):
        CreateUserRequest(name="Alice")

def test_response_has_required_fields():
    assert {"id", "email", "created_at"} <= UserResponse.model_fields.keys()

def test_create_user_status_codes():
    r = client.post("/users", json={"name": "Alice", "email": "a@example.com"})
    assert r.status_code == 201

    r = client.post("/users", json={"name": "Alice"})  # missing email
    assert r.status_code == 422

def test_error_envelope_shape():
    r = client.post("/users", json={})
    body = r.json()
    assert "detail" in body          # FastAPI standard error envelope
    assert isinstance(body["detail"], list)
```

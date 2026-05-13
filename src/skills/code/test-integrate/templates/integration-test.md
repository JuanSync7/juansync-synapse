# Integration Test Template

Rendered into the destination test file at `[CONVERT]` time when promoting a mock-integration test to a real-integration test (container/service-backed). For HTTP cassette playback, use `recorded-response.md` instead.

## Header

```python
"""Real-integration tests for `{{module_path}}`.

Lifecycle pattern: `{{lifecycle_pattern}}`.
Promoted from mock test: `{{prior_mock_test_path}}` (run `{{integrate_run_id}}`).
"""
# @summary
# Real-integration tests for {{module_under_test}}.
# Exports: (test functions)
# Deps: pytest, {{boundary_dep}}, {{module_path}}
# @end-summary

import pytest
from {{fixture_module}} import {{fixture_entry}}
from {{module_path}} import {{symbol_under_test}}
```

## Pytest marker

```python
pytestmark = pytest.mark.integration  # required: tier-based CI selection
```

## Fixture patterns (pick one)

### transaction-rollback (DB)

```python
@pytest.fixture(scope="class")
def {{db_fixture_name}}():
    container = PostgresContainer("postgres:{{pg_version}}").with_volume_mapping(...)
    container.start()
    yield container
    container.stop()

@pytest.fixture
def {{session_fixture}}({{db_fixture_name}}):
    engine = create_engine({{db_fixture_name}}.get_connection_url())
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()  # state reset; no leaks across tests
    connection.close()
```

### schema-per-test (DB DDL)

```python
@pytest.fixture
def {{schema_fixture}}({{db_fixture_name}}):
    schema = f"test_{{integrate_run_id}}"
    engine = create_engine({{db_fixture_name}}.get_connection_url())
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA {schema}"))
    yield schema
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA {schema} CASCADE"))
```

### ephemeral-container (queue / whole-system)

```python
@pytest.fixture(scope="session")
def {{broker_fixture}}():
    container = DockerCompose("{{compose_dir}}", compose_file_name="docker-compose.test.yml")
    container.start()
    container.wait_for("{{readiness_url}}")
    yield container
    container.stop()
```

### WorkflowEnvironment (Temporal)

```python
@pytest.fixture
async def {{temporal_env}}():
    async with await WorkflowEnvironment.from_local() as env:
        yield env  # auto-shutdown on context exit
```

### tmp_path / real-fs (file I/O)

```python
def test_{{behavior}}_writes_file(tmp_path):
    target = tmp_path / "{{filename}}"
    {{symbol_under_test}}(target)
    assert target.read_text() == "{{expected}}"

@pytest.fixture
def {{realfs_fixture}}(tmp_path):
    # real-FS variant for permission/symlink tests
    (tmp_path / "ro").mkdir(mode=0o500)
    yield tmp_path  # tmp_path auto-cleans
```

### subprocess-real (CLI)

```python
def test_{{cli_behavior}}():
    result = subprocess.run(
        ["{{cli_entry}}", "{{subcommand}}", "--flag"],
        capture_output=True, text=True, timeout={{timeout_seconds}},
    )
    assert result.returncode == 0
    assert "{{expected_stdout_fragment}}" in result.stdout
```

## Test body (golden + error paths required)

```python
def test_{{behavior}}_golden_path({{session_fixture}}):
    result = {{symbol_under_test}}({{session_fixture}}, {{golden_input}})
    assert result.{{field}} == {{expected_value}}  # assert on real response shape

def test_{{behavior}}_rejects_{{error_case}}({{session_fixture}}):
    with pytest.raises({{expected_exception}}, match="{{error_message_pattern}}"):
        {{symbol_under_test}}({{session_fixture}}, {{bad_input}})
```

## Teardown checklist (comments at bottom of generated file)

```python
# Teardown invariants (verified by [CONVERT] checks):
# - container stopped / transaction rolled back / cassette closed
# - tmp_path auto-cleans on test exit
# - no schema, queue, or filesystem state leaks to sibling tests
# - fixture scope matches resource cost (session for containers, function for sessions)
```

## Verification block

> The renderer MUST AST-scan the produced file for any residual `@patch`, `Mock(`, or `monkeypatch.setattr` referencing `{{boundary_dep}}`. If any match is found, reject the conversion with error code `mock-still-active` and surface the offending line numbers. Real-integration tests must exercise the real boundary; mock residue defeats the promotion.

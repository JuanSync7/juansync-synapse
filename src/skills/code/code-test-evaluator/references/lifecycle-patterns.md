# Lifecycle Patterns

Authoritative table of test lifecycle patterns. Loaded at `[ASSIGN]` — pick exactly one pattern per dependency from this table. No improvisation.

## Pattern table

### `transaction-rollback`
- **Applies to:** DB
- **Mechanism:** Open a session inside an outer transaction (or `SAVEPOINT`) per test; rollback in teardown — no commit ever reaches the DB.
- **When to use:** Standard SQLAlchemy/Django/asyncpg under `READ COMMITTED`+; DML-only tests.
- **When NOT to use:** DDL exercised, auto-commit drivers, schema migration tests.
- **Cost:** ~50-200ms per test.

### `schema-per-test`
- **Applies to:** DB (when `transaction-rollback` fails)
- **Mechanism:** Create a fresh schema/database per test (or per worker), drop in teardown. Often combined with template DBs for speed.
- **When to use:** DDL tests, drivers without transaction support for the operation under test, full isolation needed.
- **When NOT to use:** High-frequency unit-style tests (cost too high) — use `transaction-rollback` if possible.
- **Cost:** ~200ms-2s per test (template DB) or ~5-20s (full create).

### `vcrpy`
- **Applies to:** External HTTP API
- **Mechanism:** Record real responses on first run; replay from cassette on subsequent runs. Cassettes committed under `tests/cassettes/`.
- **When to use:** Stable HTTP APIs, deterministic responses, auth headers can be filtered.
- **When NOT to use:** Streaming/chunked responses with timing dependence, in-development APIs without stable endpoints, fully offline-required tests with no first-record path.
- **Cost:** ~5-50ms per test (replay); first-record pass takes real network latency.
- **Required filters:** Strip `Authorization`, `X-API-Key`, cookies, and vendor auth headers before commit.

### `ephemeral-container`
- **Applies to:** Queue, message broker, object storage, full-system, novel external services.
- **Mechanism:** Testcontainers or docker-compose spin up per test session (NOT per test — too slow). Tear down on session exit. Random ports.
- **When to use:** Brokers (RabbitMQ/Kafka/Redis), object storage emulators (minio, fake-gcs-server), services with no good in-process alternative.
- **When NOT to use:** Anything where `transaction-rollback` or `vcrpy` would suffice (cost too high to justify).
- **Cost:** ~5-30s session startup; ~10-100ms per test once running.

### `tmp_path`
- **Applies to:** Filesystem (read/write)
- **Mechanism:** pytest's built-in per-test temp directory; auto-cleaned.
- **When to use:** Standard file I/O tests.
- **When NOT to use:** Permission semantics, symlink resolution, filesystem-specific behavior.
- **Cost:** ~1-5ms per test.

### `real-fs`
- **Applies to:** Filesystem (when `tmp_path` insufficient)
- **Mechanism:** Explicit real filesystem path with explicit cleanup; may need `chmod`, symlink setup.
- **When to use:** Permission tests, atomic-rename tests, filesystem-feature-dependent tests.
- **When NOT to use:** Generic file I/O — use `tmp_path`.
- **Cost:** ~10-50ms per test.

### `cli-runner`
- **Applies to:** CLI (project's own commands)
- **Mechanism:** click `CliRunner` or typer `CliRunner` — in-process invocation with captured stdout/stderr/exit code.
- **When to use:** Testing the project's own CLI surface.
- **When NOT to use:** External binary invocation — use `subprocess-real`.
- **Cost:** ~5-20ms per test.

### `subprocess-real`
- **Applies to:** CLI (external binaries)
- **Mechanism:** `subprocess.run(..., check=True, capture_output=True)` against the real binary; `tmp_path` as cwd.
- **When to use:** Testing integration with external tools (git, docker, kubectl, ffmpeg, etc.).
- **When NOT to use:** Project-internal CLI — use `cli-runner`.
- **Cost:** Depends on binary; budget ~100ms-2s typical.

## Decision rules (verbatim — used at `[ASSIGN]`)

- DB → `transaction-rollback` UNLESS DDL or auto-commit → `schema-per-test`.
- External API → `vcrpy` UNLESS streaming/non-deterministic → `ephemeral-container` with mock-server (or `responses`/`httpx.MockTransport`).
- Queue/broker → `ephemeral-container`.
- Object storage → `ephemeral-container` (minio/fake-gcs).
- File I/O → `tmp_path` UNLESS permission/symlink-dependent → `real-fs`.
- CLI (own) → `cli-runner`.
- CLI (external binary) → `subprocess-real`.

## Constraint

One pattern per dependency. No stacking. No improvisation. If no pattern fits, surface as `unsupported-category` (per `real-integration-checklist`).

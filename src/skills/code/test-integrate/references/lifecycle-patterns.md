# Lifecycle Patterns

Loaded at `[PICK-PATTERN]`. Canonical pattern table — must match `test-evaluate` verbatim. Assign exactly one pattern per strategy item.

## Pattern table

| Pattern | Applies to | Mechanism | When to use | When NOT | Cost |
|---|---|---|---|---|---|
| transaction-rollback | DB | Wrap each test in a transaction; rollback in teardown | Default for DB integration tests | DDL changes, autocommit operations | Low |
| schema-per-test | DB | Create fresh schema per test, drop in teardown | DDL/migration tests, autocommit-required workflows | Plain CRUD tests (use rollback) | Medium |
| vcrpy | External HTTP APIs | Record once, replay on subsequent runs | Third-party REST/HTTP services | Own services, DB, filesystem | Low (after record) |
| ephemeral-container | Queue, whole-system multi-service | Testcontainers / docker-compose, scoped to test class | Queue brokers, full-stack flows | Single-DB tests (rollback is cheaper) | High |
| WorkflowEnvironment | Temporal workers | Temporal's testing harness `WorkflowEnvironment.from_local()` | `@activity.defn`, `@workflow.defn` workers | Generic queue tests | Medium |
| celery-eager | Celery tasks | `task_always_eager=True` test setting | Unit-style task validation | Full-broker integration | Low |
| tmp_path | File I/O | pytest `tmp_path` fixture | Read/write filesystem operations | Permission-sensitive paths | Low |
| real-fs | File I/O (privileged) | Real filesystem with cleanup | Permission, symlink, mount-dependent paths | Plain read/write (use tmp_path) | Medium |
| subprocess-real | CLI invocations | `subprocess.run` capture | Testing own CLI or external CLI | In-process logic (test directly) | Low |

## Decision rules (verbatim from design doc — apply at [PICK-PATTERN])

1. DB candidates default to `transaction-rollback`. Promote to `schema-per-test` only when DDL or auto-commit defeats transaction isolation.
2. External-API candidates default to `vcrpy`. Required scrubbing filters per `references/vcrpy-patterns.md`.
3. Queue candidates default to `ephemeral-container`, EXCEPT:
   - Temporal-decorated workers → `WorkflowEnvironment` (not generic container).
   - Celery tasks (unit-style) → `celery-eager`; full integration → ephemeral broker container.
4. File I/O candidates default to `tmp_path`. Promote to `real-fs` only for permission/symlink-dependent paths.
5. CLI candidates → `subprocess-real`.
6. NEVER assign multiple patterns to the same item.
7. NEVER substitute `ephemeral-container` when a cheaper category-specific pattern fits.
8. If the strategy item's `recommended_pattern` (from test-evaluate) conflicts with these rules, abort the item and log `pattern-mismatch` rather than improvise.

## Cost notes

- "Low" = sub-100ms test overhead; "Medium" = 100ms-1s; "High" = 1s-10s+ container startup.
- High-cost patterns belong in the slower CI tier (merge-to-main / nightly), not push-tier.

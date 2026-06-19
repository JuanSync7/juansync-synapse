# Boundary classification — Database

## Detection signals (DB)

- **Runtime tier:** calls to `cursor.execute`, `session.execute`, `engine.connect`, `psycopg2.connect`, `sqlalchemy.create_engine`, `pymongo.MongoClient`; ORM session methods (`session.add`, `session.commit`, `session.query`); `redis.Redis`; raw SQL strings passed to driver methods.
- **Logical tier:** functions exported via `__all__` from a `db/`, `models/`, `repositories/`, or `dao/` package whose body invokes any runtime-tier signal.
- **Internal:** helpers that build query strings, validate arguments, or transform rows but never touch a connection — even when called by boundary functions.

## Lifecycle pattern decision rules

- **Default → `transaction-rollback`:** session opened per test inside a SAVEPOINT or outer transaction; `rollback()` in teardown. Use for SQLAlchemy / Django / asyncpg under normal `READ COMMITTED` isolation.
- **`schema-per-test` when:**
  - DDL is exercised (`CREATE` / `DROP` / `ALTER`).
  - The connection auto-commits (e.g. MySQL DDL outside transactions, Postgres `CREATE INDEX CONCURRENTLY`).
  - Schema-migration tests where rollback cannot undo committed DDL.
- **Never recommend mocked DB at this stage** — every mocked DB boundary in the inventory is a candidate for replacement; let the score rank them.

## Risk weight (formula input)

- `external_dependency_risk = 5` — DB is the highest-risk category. Serialization, constraint, and isolation bugs are common and rarely surface against mocks.

## Common over-mock anti-patterns to flag

- Mocking the entire ORM session and asserting on `.add()` / `.commit()` calls — exercises wiring, not behavior.
- Mocking individual model classes — internal, not a boundary; emit `over_mocking_warning`.
- Mocking query builders that produce strings — internal helpers; emit `over_mocking_warning`.

## Out-of-scope at [DETECT]

- Connection-pool tuning, replica routing, sharding logic — performance concerns for `code-test-integrator`'s real-DB tier, not classification.

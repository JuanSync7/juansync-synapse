# Coverage Pyramid

Reference for `[CONSOLIDATE]`. Defines the 6 pyramid layers used to classify
every `CoverageGap` before merging tool outputs into `AuditGapReport`.

---

## Pyramid Diagram

```
         ┌──────────────────────────────┐
         │      real-integration        │  ← smallest, most expensive
         ├──────────────────────────────┤
         │      mock-integration        │
         ├──────────────────────────────┤
         │         idempotency          │
         ├──────────────────────────────┤
         │          contract            │
         ├──────────────────────────────┤
         │           config             │
         ├──────────────────────────────┤
         │            unit              │  ← largest, least expensive
         └──────────────────────────────┘
```

---

## Layer Reference Table

| # | Layer | Tests What | pytest Marker | Position |
|---|-------|-----------|---------------|----------|
| 1 | **unit** | Single function or class — no I/O, fully synchronous, deterministic. | *(none — default)* | Base. Largest layer. |
| 2 | **config** | Configuration loading, schema validation, typed-config parsing. Verifies that `pyproject.toml` / settings models compose correctly. | `@pytest.mark.config` | Second from base. |
| 3 | **contract** | Pydantic/dataclass/TypedDict shape tests, serialization round-trips, API request/response schemas. Validates contracts across module boundaries. | `@pytest.mark.contract` | Middle. |
| 4 | **idempotency** | Running the same operation twice yields the same result. Relevant for caches, DB upserts, file writers, and message handlers. | `@pytest.mark.idempotent` | Above middle. |
| 5 | **mock-integration** | Multi-module flow with external collaborators mocked (LLM clients, HTTP services, cloud SDKs). Fast-feedback integration band. | `@pytest.mark.integration` AND mocks active | Second from top. |
| 6 | **real-integration** | Same multi-module flow with real external systems (real DB, real Weaviate, real Temporal). | `@pytest.mark.integration` with mocks disabled, or `@pytest.mark.real_integration` | Top. Smallest layer. |

---

## Classification Rule for `[CONSOLIDATE]`

When merging tool outputs, tag each `CoverageGap` with a pyramid layer using
the following decision tree. Apply the **first matching rule**.

```
1. Covering tests carry @pytest.mark.real_integration
   OR @pytest.mark.integration with no active mocks
   → real-integration

2. Covering tests carry @pytest.mark.integration AND mocks are active
   → mock-integration

3. Covering tests carry @pytest.mark.idempotent
   → idempotency

4. Covering tests carry @pytest.mark.contract
   OR gap lives in tests/contract/ or matches *_contract.py
   → contract

5. Covering tests carry @pytest.mark.config
   → config

6. No covering tests exist — infer from function properties:
   a. Function uses I/O primitives (open, requests, db client)
      AND is exercised only via mocked tests → mock-integration
   b. Function uses I/O primitives
      AND is exercised by tests without active mocks → real-integration
   c. Otherwise → unit (default)
```

When no covering tests exist and inference is ambiguous, default to **unit**
and annotate the gap with `layer_inferred: true` so `test-generate` can
override after deeper analysis.

---

## Why the Pyramid Shape Matters

The pyramid shape reflects the cost-to-fidelity tradeoff:

- **Unit tests** are cheap, fast, and deterministic. They form the wide base.
- **Real-integration tests** are slow, require live infrastructure, and catch
  serialization quirks, real DB constraints, latency, and wiring bugs that
  mocks cannot surface. They sit at the narrow top (~5–8% of the suite).

Classifying gaps by layer lets `test-generate` target the **right** layer for
each gap. A real-integration gap must not be filled with a unit test — the
unit test will pass while the actual wiring defect remains uncaught.

Layer distribution targets (from design doc §7):

| Layer | Target coverage band |
|-------|---------------------|
| unit + config + contract + idempotency | ≥ 92–95% of suite |
| mock-integration | bulk of remaining coverage |
| real-integration | 5–8% of suite (testcontainers / vcrpy) |

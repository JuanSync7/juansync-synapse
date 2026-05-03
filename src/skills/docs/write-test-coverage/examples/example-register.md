# Acme Auth Service — Test Coverage Register

> **Living document.** Initialized by `write-test-coverage`, maintained incrementally by `/patch-docs`.
> Do NOT regenerate entirely on each change — update affected sections only.

**Intent document:** docs/auth/SPEC.md
**Test directory:** tests/
**Generated:** 2026-04-20
**Languages detected:** Python (pytest), Shell (bats)

---

## Coverage Summary

| Module | Total ACs | Covered | Partial | Not Covered | Stale Flags |
|--------|----------|---------|---------|-------------|-------------|
| auth | 8 | 5 | 2 | 1 | 1 |
| billing | 5 | 3 | 1 | 1 | 0 |
| deploy (shell) | 2 | 1 | 0 | 1 | 0 |
| Cross-cutting | 3 | 1 | 1 | 1 | 0 |
| **Total** | **18** | **10** | **4** | **4** | **1** |

---

## Prioritized Gaps

| Priority | AC | Gap | Module |
|----------|-----|-----|--------|
| MUST | AC-4 | Token revocation on password change — no test | auth |
| MUST | CC-3 | 5xx responses return JSON, not stack traces — no test | cross-cutting |
| SHOULD | AC-9 | Downgrade blocked when balance outstanding — no test | billing |
| SHOULD | AC-11 | Deploy rollback on health check failure — no test | deploy |

---

## Module Coverage

### Auth (`src/auth/`)

**Test file(s):** `tests/test_auth.py`
**Intent source:** docs/auth/SPEC.md, Section 2 (Authentication)

#### AC-1: User login with valid credentials [MUST]

```
  [x] Valid email + password returns 200 with JWT         (test_auth.py:23)
  [x] JWT contains correct user_id claim                  (test_auth.py:31)
  [x] JWT expires in 15 minutes                           (test_auth.py:38)
  Status: Covered
```

#### AC-2: Failed login handling [MUST]

```
  [x] Wrong password returns 401                          (test_auth.py:45)
  [x] Unknown email returns 401 with same message         (test_auth.py:52)
  [~] Error messages are identical for both cases          (test_auth.py:58) — checks message text but not response timing
  [ ] 5th consecutive failure locks account for 15 min
  Status: Partial (3/4 scenarios)
```

#### AC-3: Token refresh [MUST]

```
  [x] Valid refresh token returns new access token        (test_auth.py:67)
  [x] Expired refresh token returns 401                   (test_auth.py:74)
  [ ] Used refresh token is invalidated (single-use)
  Status: Partial (2/3 scenarios)
```

> **Staleness warning:** `tests/test_auth.py` may be stale — source `src/auth/token.py` was modified more recently (2026-04-18 vs 2026-03-02). Verify test still covers current behavior.

#### AC-4: Token revocation on password change [MUST]

```
  [ ] All active tokens invalidated when password changes
  [ ] Refresh tokens in denylist after password change
  Status: Not Covered
```

---

### Billing (`src/billing/`)

**Test file(s):** `tests/test_billing.py`
**Intent source:** docs/auth/SPEC.md, Section 5 (Billing)

#### AC-7: Subscription creation [SHOULD]

```
  [x] Free plan activates without payment token           (test_billing.py:12)
  [x] Pro plan requires payment token                     (test_billing.py:20)
  [x] Declined payment returns 402                        (test_billing.py:28)
  Status: Covered
```

#### AC-8: Subscription upgrade [SHOULD]

```
  [x] Upgrade is effective immediately                    (test_billing.py:35)
  [~] Prorated charge calculated correctly                (test_billing.py:42) — checks charge < full price but not exact formula
  Status: Partial (2/2 scenarios, 1 ambiguous)
```

#### AC-9: Downgrade restrictions [SHOULD]

```
  [ ] Downgrade blocked when outstanding balance exists
  Status: Not Covered
```

---

### Deploy (`scripts/`)

**Test file(s):** `tests/test_deploy.bats`
**Intent source:** docs/auth/SPEC.md, Section 8 (Deployment)

#### AC-10: Health check before promotion [SHOULD]

```
  [x] Deploy script checks /health endpoint before promoting  (test_deploy.bats:8)
  Status: Covered
```

#### AC-11: Rollback on health check failure [SHOULD]

```
  [ ] Failed health check triggers automatic rollback
  [!] Image builds successfully — CI-only validation, no dedicated test
  Status: Not Covered
```

---

## Cross-Cutting Coverage

### Cross-Cutting: auth + billing

**Requirement:** All API error responses return structured JSON with `{error: {code, message, request_id}}`

#### CC-1: 4xx responses return JSON error envelope [MUST]

```
  [x] Auth 401 returns JSON with error.code               (test_auth.py:85)
  [x] Billing 422 returns JSON with error.code            (test_billing.py:55)
  Status: Covered
```

#### CC-2: Error responses include request_id [MUST]

```
  [x] Auth errors include UUID request_id                 (test_auth.py:92)
  [ ] Billing errors include UUID request_id
  Status: Partial (1/2 scenarios)
```

#### CC-3: 5xx responses return JSON, not stack traces [MUST]

```
  [ ] Internal server error returns JSON error envelope
  [ ] Unhandled exception does not leak stack trace
  Status: Not Covered
```

---

## Orphaned Tests

| Test File | Function | Behavior | Possible Explanation |
|-----------|----------|----------|---------------------|
| `test_auth.py` | `test_password_entropy_logging` | Logs password entropy score on registration | Not in spec — possibly a debug/observability test |
| `test_billing.py` | `test_invoice_pdf_generation` | Generates PDF invoice from billing record | Spec mentions invoices but no AC for PDF format — incomplete spec? |

---

## Unfound Modules

| Module | Path | Recommendation |
|--------|------|---------------|
| notifications | `src/notifications/` | No spec, eng-guide, or behavioral docstrings. Consider writing a spec. |
| analytics | `src/analytics/` | No spec, eng-guide, or behavioral docstrings. Consider writing a spec. |

---

## Legend

| Symbol | Meaning |
|--------|---------|
| `[x]` | Scenario covered by a dedicated test |
| `[~]` | Ambiguous match — test exists but coverage is uncertain |
| `[ ]` | Scenario not covered — no matching test found |
| `[!]` | CI-only validation — no dedicated test file |
| `[stale?]` | Source modified more recently than test — may be outdated |
| `MUST` | Required behavior (highest priority gap) |
| `SHOULD` | Expected behavior (medium priority gap) |
| `MAY` | Optional behavior (lowest priority gap) |

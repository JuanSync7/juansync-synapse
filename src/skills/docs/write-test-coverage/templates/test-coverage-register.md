# {{System Name}} — Test Coverage Register

> **Living document.** Initialized by `write-test-coverage`, maintained incrementally by `/patch-docs`.
> Do NOT regenerate entirely on each change — update affected sections only.

**Intent document:** {{spec or eng-guide path}}
**Test directory:** {{test directory path}}
**Generated:** {{date}}
**Languages detected:** {{languages}}

---

## Coverage Summary

| Module | Total ACs | Covered | Partial | Not Covered | Stale Flags |
|--------|----------|---------|---------|-------------|-------------|
| {{module}} | {{n}} | {{n}} | {{n}} | {{n}} | {{n}} |
| **Total** | **{{n}}** | **{{n}}** | **{{n}}** | **{{n}}** | **{{n}}** |

---

## Prioritized Gaps

Ranked by AC priority (MUST > SHOULD > MAY), then by module criticality.

| Priority | AC | Gap | Module |
|----------|-----|-----|--------|
| {{MUST/SHOULD/MAY}} | {{AC-id}} | {{uncovered scenario description}} | {{module}} |

---

## Module Coverage

### {{Module Name}} (`{{src/path/}}`)

**Test file(s):** `{{test file path(s)}}`
**Intent source:** {{spec section or eng-guide section}}

#### {{AC-id}}: {{AC description}} [{{MUST|SHOULD|MAY}}]

```
  [x] {{scenario description}}          ({{test_file.py:line}})
  [~] {{ambiguous match scenario}}       ({{test_file.py:line}}) — {{ambiguity note}}
  [ ] {{uncovered scenario}}
  [!] {{CI-only validated scenario}} — CI-only validation, no dedicated test
  Status: {{Covered | Partial (N/M scenarios) | Not Covered}}
```

{{Repeat for each AC in this module}}

{{If any test in this module has a staleness flag:}}
> **Staleness warning:** `{{test_file}}` may be stale — source `{{src_file}}` was modified more recently. Verify test still covers current behavior.

---

{{Repeat "### Module" section for each module}}

---

## Cross-Cutting Coverage

### Cross-Cutting: {{module_a}} + {{module_b}}

**Requirement:** {{cross-cutting AC description}}

```
  [x] {{scenario in module_a}}          ({{test_a.py:line}})
  [x] {{scenario in module_b}}          ({{test_b.py:line}})
  [ ] {{uncovered scenario in module_c}}
  Status: Partial (2/3 scenarios)
```

---

## Orphaned Tests

Test functions that do not map to any known acceptance criterion. May indicate incomplete spec or dead test code.

| Test File | Function | Behavior | Possible Explanation |
|-----------|----------|----------|---------------------|
| `{{test_file.py}}` | `{{test_function}}` | {{behavioral summary}} | {{incomplete spec / dead code / utility test}} |

---

## Unfound Modules

Modules with no intent document (no spec, eng-guide, or behavioral docstrings). Coverage cannot be assessed.

| Module | Path | Recommendation |
|--------|------|---------------|
| `{{module}}` | `{{src/path/}}` | Consider writing a spec or eng-guide |

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

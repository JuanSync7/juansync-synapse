# Rollup Format

Loaded by `synapse-router-suite-validator` Phase 6. The rollup is the only artifact this skill produces — orchestrators parse the first line, maintainers read the rest. Without a strict format, downstream tooling cannot reliably extract the verdict, and humans waste time hunting for the recommendation.

---

## Hard rules

1. **The verdict is the first line.** No preamble, no headers, no blank lines. Orchestrators grep `^SUITE:` from stdout.
2. **The verdict line includes the suite path** in parentheses for log disambiguation when multiple suites are validated in one batch.
3. **Sections appear in fixed order:** Summary → Per-artifact results → Cross-suite issues → Quality (escalated) → Recommendation.
4. **The Cross-suite section is omitted** when no cross-suite issues exist (silent success).
5. **The Quality section is omitted** when `--escalate` was not passed OR the structural sweep had failures.
6. **The Recommendation paragraph is always present**, even on APPROVE — it states what the maintainer should do next (typically "wire the submodule and merge" for APPROVE).

---

## Format template

```
SUITE: <APPROVE | REVISE | REJECT> (path: <suite-path>)

## Suite Conformance Report

Total artifacts: <N>
Pass (structural): <X>
Fail (structural): <Y>
Unreadable: <Z>
Cross-suite issues: <M>

### Per-artifact results
- [PASS] <type>/<name>
- [FAIL] <type>/<name> — <one-line failure summary>
- [UNREADABLE] <type>/<path> — <parse error summary>

### Cross-suite issues
- <one bullet per issue, naming the affected artifacts and the fix>

### Quality (escalated)
- <type>/<name> — <APPROVE | REVISE | REJECT>

### Recommendation
<one paragraph: what blocks promotion (or "no blockers — ready to wire"), and the concrete next action the maintainer should take>
```

---

## Verdict rules

| Verdict | Condition |
|---------|-----------|
| **APPROVE** | Every artifact structurally passes AND zero cross-suite issues AND (if `--escalate`) every escalated artifact is APPROVE |
| **REVISE** | Fixable structural failures, fixable cross-suite issues (taxonomy additions, name renames, README rows), OR any escalated artifact is REVISE |
| **REJECT** | Suite is empty, suite layout doesn't match conventions at all, OR any escalated artifact is REJECT (fundamental issue) |

A single failing per-artifact check does NOT immediately downgrade to REJECT — most structural failures are fixable (REVISE). REJECT is reserved for fundamental problems: empty suite, no recognizable layout, or a downstream gatekeeper REJECT.

---

## Worked examples

> **Read [`../examples/example-rollup.md`](../examples/example-rollup.md)** for full APPROVE / REVISE / REJECT worked examples.

# Change Request — delivery-orchestration-closeout-schema

> Artifact type: protocol | Target: `src/protocols/delivery/delivery-orchestration-closeout-schema.md`

---

## What changes

Add the following fields to the closeout YAML body in the **Required fields** table (§ Contract Rules, rule 3). Each row specifies type and `required-when` semantics. These fields are the producer-side evidence surface for the new `delivery-execution-coding-contract` protocol's compliance signatures.

1. **`lint_result`** — enum: `pass | fail | not_applicable`. `required-when: always`. Drives coding-contract rule 5 (green-tree exit).
2. **`lint_command_invoked`** — string (the exact command line executed). `required-when: applicable` (i.e., when `lint_result ∈ {pass, fail}`; omit when `not_applicable`). Anti-fabrication: a `pass` without command-invoked evidence is a violation.
3. **`lint_exit_code`** — integer. `required-when: applicable`. Cross-check against `lint_result`.
4. **`lint_output_digest`** — string (sha256 hex of captured lint output, or `null` when `not_applicable`). `required-when: applicable`. Enables fabrication check at intake.
5. **`typecheck_result`** — enum: `pass | fail | not_applicable`. `required-when: always`.
6. **`typecheck_command_invoked`** — string. `required-when: applicable`.
7. **`typecheck_exit_code`** — integer. `required-when: applicable`.
8. **`dead_code_violations`** — list[{path, line, snippet}]. `required-when: always` (empty `[]` if none). Drives coding-contract rule 3 (no dead code).
9. **`neighbors_consulted`** — list[string] (file paths the subagent read before editing). `required-when: always` (must be non-empty — drives coding-contract rule 2; empty list is a violation signal, not a vacuous pass).
10. **`applied_deltas`** — list[{rule_id: int, exception_scope: string, justification: string}]. `required-when: always` (empty `[]` if none). Echoes verbatim the `discipline_deltas` injected by the dispatch prompt; mismatch is a violation.
11. **`declared_edges`** — list[{slice_id: string, kind: enum(consumes|produces|extends)}]. `required-when: always` (empty `[]` if none). Surfaces inter-slice contract claims so the orchestrator can cross-check against `depends_on` from STORIES.md.

Additional rule-side updates required to keep the contract internally consistent:

- **Bump `version: 1` → `version: 2`** in frontmatter to mark schema break.
- **Extend the Compliance Signature list** with two new conditions:
  - `lint_result` and `typecheck_result` populated; if either is `pass | fail`, the corresponding `*_command_invoked` and `*_exit_code` are populated.
  - `applied_deltas` matches the `discipline_deltas` injected at dispatch time (verbatim subset check).
- **Extend the Violation Signatures table** with new IDs:
  - **(f)** `lint_result: pass` without `lint_command_invoked` / `lint_exit_code` — fabricated pass; escalate for human review.
  - **(g)** `typecheck_result: pass` without `typecheck_command_invoked` / `typecheck_exit_code` — fabricated pass; escalate for human review.
  - **(h)** `neighbors_consulted: []` — neighbors-unconsulted; route to replan with `neighbors_unconsulted` reason.
  - **(i)** `applied_deltas` references unknown `rule_id` or diverges from injected `discipline_deltas` — contract tamper; reject as `rejected`.
- **Add Edge Cases rows** for: no applicable linter/typechecker in repo (orchestrator pre-flight sets `not_applicable`, not the worker); pre-v2 legacy closeouts (treat new fields as `not_applicable` markers — see Migration).

---

## Why

A new sibling protocol — `delivery-execution-coding-contract` — has been brainstormed (see `.brainstorms/2026-05-31-vertical-slice-planning-stack/`, Artifact 2) and will be injected into every dispatch alongside `delivery-execution-tdd-contract`. Its rules 2, 3, 5, and the `discipline_deltas` echo mechanism are defined in terms of compliance signatures that **must be checkable on the closeout**:

- Rule 2 (read neighbors first) is unenforceable unless the closeout carries `neighbors_consulted`.
- Rule 3 (no dead code) needs `dead_code_violations[]` as the structured surface for intake validation.
- Rule 5 (green-tree exit — lint + typecheck) needs `lint_*` and `typecheck_*` fields, **including command-invoked + exit-code + output-digest evidence**, so a fabricated `pass` claim is detectable at intake rather than at human-review time.
- The contract's `discipline_deltas` schema mandates that applied exceptions be echoed verbatim — this requires `applied_deltas[]`.
- `declared_edges[]` closes a separate gap surfaced in the meta-process-brainstormer's Cross-Artifact Sweep: subagents currently can claim cross-slice interface use without a structured surface for the orchestrator to validate against `depends_on`.

Without these fields, the coding-contract's compliance signatures degrade to "trust the subagent's prose," which is exactly the failure mode the closeout schema exists to eliminate (see existing schema's opening paragraph on "subagent invents its own output format").

Brainstorm cross-reference: `.brainstorms/2026-05-31-vertical-slice-planning-stack/notes.md` — see "Artifact 2: delivery-execution-coding-contract" § Closeout-schema dependency (paired CR).

---

## Impact on existing consumers

Sole structural consumer: **`delivery-orchestration-plan-executor`** (the orchestrator skill). It reads each closeout at intake to decide pass / replan / escalate.

- **New read responsibilities.** Orchestrator intake must now parse the eleven new fields and run the four new compliance / violation checks (f, g, h, i) before routing. Existing checks (a–e) remain unchanged.
- **Pre-flight responsibility added.** When the repo has no applicable linter or typechecker, the orchestrator's `[PRE-FLIGHT]` must set the `*_result` determination to `not_applicable` for the subagent (per the coding-contract edge-case table) — the worker is not trusted to self-declare `not_applicable`.
- **EVAL impact.** Orchestrator's EVAL.md closeout-intake test must extend its fixture closeouts to exercise the new fields (at minimum: one `applicable` and one `not_applicable` case, plus fabricated-pass negative tests for f, g).
- **Backward compatibility.** Closeouts produced before this CR lands predate these fields entirely. Treat any closeout whose `closeout_schema_version` < 2 (or is missing) as **legacy**: the eleven new fields are interpreted as `not_applicable` markers and the four new violation signatures (f, g, h, i) are not evaluated. New dispatches under schema v2 require the fields.

No other downstream consumers exist today (closeout body is not yet consumed by lessons-extraction tooling or CI).

---

## Migration path

1. **Land this CR alongside `delivery-execution-coding-contract`** in coordinated PRs — the coding-contract PR declares paired-CR dependency on this one (and vice versa). Closeout schema MUST merge first or concurrently; coding-contract injection without these fields would dead-lock dispatch intake.
2. **Schema version bump.** This CR bumps `version: 1 → 2` in closeout-schema frontmatter. The orchestrator's dispatch prompt MUST be updated to inject the matching `slice_contract_version` AND a new `closeout_schema_version: 2` slot, so the subagent's closeout self-declares its schema version.
3. **Orchestrator dual-mode intake.** Plan-executor's intake logic branches on `closeout_schema_version`:
   - **v2 (new dispatches):** all eleven fields validated per the rules above; violations (f–i) routed.
   - **missing / v1 (legacy on-disk closeouts during resume-after-compaction):** new fields treated as `not_applicable`; only the original (a–e) violation signatures evaluated. This preserves resumability across the schema break.
4. **Subagent prompt template update.** The dispatch prompt's closeout-template scaffold (rendered by `delivery-orchestration-dispatch-contract`) gains the eleven new field stubs with inline comments explaining `required-when` semantics. This is part of the paired dispatch-contract CR, not this one — but the two must land together.
5. **Fixture refresh.** EVAL.md fixtures across closeout-schema, dispatch-contract, and plan-executor are regenerated to schema v2. Legacy v1 fixtures are retained in a `tests/legacy/` subdir to exercise the dual-mode intake path.
6. **No data migration of historical closeouts.** Existing on-disk `.delivery/closeouts/*.yaml` files are left untouched; the dual-mode intake handles them transparently. There is no rewrite step.

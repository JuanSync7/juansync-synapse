# Decision Memo — delivery-execution-coding-contract

> Artifact type: protocol | Memo type: creation | Design doc: `.brainstorms/2026-05-31-vertical-slice-planning-stack/design.md`

---

## What I want

A new sibling protocol in the `delivery-execution-*` family that defines the **code-quality discipline envelope** for subagent worker dispatches. It is injected by the orchestrator alongside `delivery-execution-tdd-contract` and `delivery-execution-slice-contract`, and covers the part of subagent behavior that those two protocols do NOT cover: **code quality inside a slice's source diff + lint/typecheck exit gate**.

Routing-contract description anchor (from notepad):

> "Subagent code-quality discipline — YAGNI, neighbors-first, no-dead-code, fail-loudly, green-tree-exit (lint+typecheck), security-tripwires. Complements tdd-contract; injected into every dispatch alongside it."

Slug: `delivery-execution-coding-contract` (matches sibling `-contract` suffix).
Kind: contract. Status at land: **draft** (per governance — will land as draft).

---

## Why Claude needs it

Without this protocol, subagent workers exhibit the following baseline failure modes, none of which the sibling protocols catch:

- **Speculative abstraction.** Workers introduce `*_factory*`, `*_wrapper*`, `*_base*` files with a single caller, expanding the slice beyond its validable outcome. Slice-contract enforces *shape*, not *internal restraint*.
- **Neighbor-blind drops.** Workers add a new file without reading sibling modules, producing parallel-but-divergent implementations of the same concept. Nothing in tdd-contract or slice-contract requires a neighbors-consulted record.
- **Dead-code dumping.** Commented-out call sites and stub functions ship into the diff because no rule rejects them.
- **Silent failure swallowing.** `except: pass`, `rescue => nil`, `catch (_) {}` patterns slip through because TDD only checks green tests, not the diff's exception posture.
- **Fabricated green-tree.** Workers claim "lint passes" without invoking the linter, because the closeout never required command-invoked evidence.
- **Security tripwires.** Hardcoded token-like literals, string-concatenated SQL, unvalidated boundary inputs land because no protocol calls them out at dispatch time.

The fix is a **6-rule contract with compliance signatures** the orchestrator can verify against the closeout — turning "trust the worker" into "verify the worker."

---

## Injection shape

- **Policy:** judgment rules for subagent code-quality behavior, expressed as a 6-rule table with explicit compliance signatures and violation signals. Two-tier model: bright-line auto-reject vs. advisory-with-signature.
- **Domain knowledge:** standard patterns for speculative-abstraction names, dead-code idioms, silent-failure idioms, fabricated-pass detection, and security tripwires — loaded into the worker context at dispatch.

This protocol is NOT a workflow; it carries no phases or flow graph.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| Protocol body injected into worker prompt | 1 | no (per-dispatch) | Subagent reads the 6 rules + tier model before producing code |
| Closeout fields populated by worker | 11 | yes (paired CR on closeout-schema) | Orchestrator verifies compliance signatures: `lint_result`, `lint_command_invoked`, `lint_exit_code`, `lint_output_digest`, `typecheck_result`, `typecheck_command_invoked`, `typecheck_exit_code`, `dead_code_violations[]`, `neighbors_consulted[]`, `applied_deltas[]`, `declared_edges[]` |
| `applied_deltas` echo | per-dispatch | no | Any worker-applied `discipline_deltas` are echoed verbatim for audit |

---

## Rules (VERBATIM — 6-rule table)

| # | Rule | Compliance signature | Violation signal | Main-agent action |
|---|---|---|---|---|
| 1 | YAGNI / no speculative abstraction | No new file in `files_created` with a `*_factory*` / `*_wrapper*` / `*_base*` name AND single caller in `files_modified` | Speculative abstraction signature detected | Reject; route to replan with `speculative_abstraction` reason |
| 2 | Read neighbors first | `neighbors_consulted: [file paths]` field present and non-empty in closeout | Field absent/empty | Reject; route to replan with `neighbors_unconsulted` |
| 3 | No dead code | `dead_code_violations: []` in closeout; pattern check: ≥2 consecutive lines matching `^\s*[#//]\s*[a-zA-Z_]+\s*[=(.]` in diff, excluding TODO/FIXME/noqa/type:ignore | Pattern hit | Reject; route to replan |
| 4 | Fail loudly | No bare except / catch-and-ignore in `files_modified` diff | Pattern hit (`except:\s*pass`, `rescue\s*=>\s*nil`, `catch\s*\(\s*_+\s*\)\s*{\s*}`) | Reject; route to replan |
| 5 | Green-tree exit (lint + typecheck) | `lint_command_invoked` + `lint_exit_code` + `typecheck_command_invoked` + `typecheck_exit_code` all present; `lint_result` and `typecheck_result` ∈ {pass, fail, not_applicable}; fabrication check via `lint_output_digest` | Missing field, or `pass` reported without command-invoked evidence | Reject as fabricated pass; flag for human review (cheating signature) |
| 6 | Security-tripwires | Secret-scan on diff (no patterns matching token-like literals); flag string-concatenated SQL idioms; flag boundary input read without validator call | Pattern hit | Reject; route to replan with `security_tripwire` |

### Tier model

- **Bright-line auto-reject:** rules 3, 4, 5, 6.
- **Advisory-with-signature:** rules 1, 2.

### Non-overrideable rules (VERBATIM)

Rules **5 (green-tree-exit)** and **6 (security-tripwires)** are non-overrideable. `discipline_deltas` with `rule_ref ∈ {5, 6}` rejects dispatch.

### discipline_deltas schema (VERBATIM)

`[{rule_id: int, exception_scope: <file glob>, justification: <text>}]`.

- Unknown `rule_id` fails loud.
- Applied deltas echoed verbatim to closeout `applied_deltas` field.

---

## Injection pre-flight

The orchestrator's `[PRE-FLIGHT]` MUST:

1. Verify `delivery-orchestration-dispatch-contract` is loaded.
2. Verify `delivery-execution-coding-contract` is in the worker_protocols list for the dispatch.
3. Halt **loud** on absence (not soft warn).
4. Run a collision check: if multiple coding-discipline variants are present in `worker_protocols`, halt loud.

This pre-flight runs per dispatch, before the worker prompt is materialized.

---

## Edge cases considered (VERBATIM)

| Edge case | Handling |
|---|---|
| No applicable linter/typechecker | Marked `not_applicable`; orchestrator pre-flight sets the determination, not the worker |
| YAGNI vs `next_moves` ambiguity | "Refactor / extension idea surfaced mid-slice — do NOT implement; surface in `next_moves` with `rationale: yagni_deferred`" |
| Atomic-commit boundary vs Ralph iteration | "Atomic commit = each inner TDD red→green→refactor cycle; Ralph iteration is a logical wrapper, not a commit boundary" |

---

## Sibling cross-refs (explicit not-in-scope)

This protocol must explicitly defer the following concerns to siblings — listed here so the creator includes them as not-in-scope anchors in the protocol body:

| Concern | Owned by |
|---|---|
| Test-first + Ralph + iteration cap + cheating detection | `delivery-execution-tdd-contract` |
| Slice anatomy + inter-slice edges | `delivery-execution-slice-contract` |
| Closeout shape | `delivery-orchestration-closeout-schema` |

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `delivery-orchestration-closeout-schema` | **paired CR (this PR depends on)** | New required-when fields: `lint_result`, `lint_command_invoked`, `lint_exit_code`, `lint_output_digest`, `typecheck_result`, `typecheck_command_invoked`, `typecheck_exit_code`, `dead_code_violations[]`, `neighbors_consulted[]`, `applied_deltas[]`, `declared_edges[]`. Each declared `required-when: applicable | always`. |
| `delivery-orchestration-dispatch-contract` | **paired CR (this PR depends on)** | `{{worker_protocols}}` slot description amended **three → four bodies**; EVAL.md slot assertion updated to assert all four. |
| `delivery-execution-tdd-contract` | sibling (not-in-scope cross-ref) | Owns test-first + Ralph + iteration cap + cheating detection. This protocol must NOT duplicate. |
| `delivery-execution-slice-contract` | sibling (not-in-scope cross-ref) | Owns slice anatomy + inter-slice edges. This protocol must NOT duplicate. |
| `delivery-orchestration-plan-executor` | consumer (orchestrator) | Loads this protocol via `{{worker_protocols}}`, runs pre-flight, verifies closeout signatures, routes violations to replan. |
| Worker subagents | consumer (dispatch target) | Read protocol body, comply with 6 rules, populate closeout fields. |

**Paired-CR coordination:** the closeout-schema and dispatch-contract amendments land as separate CR memos in their respective protocol directories; this protocol's PR description must declare both as paired-CR dependencies. Each paired CR's PR description reciprocally declares this protocol's PR as its dependency.

---

## Companion files anticipated

Protocols in this suite are typically single-file. Anticipated layout:

- **Always-loaded:** `delivery-execution-coding-contract.md` (the protocol body — rules table, tier model, non-overrideable list, schema, pre-flight, edge cases, cross-refs).
- **Templates:** none.
- **References:** optional `references/violation-patterns.md` may be extracted if the regex/pattern catalog grows; otherwise inline in the protocol body.
- **EVAL:** `EVAL.md` with structural assertions on the 6-rule table, non-overrideable rules list, discipline_deltas schema, and pre-flight halt-loud requirement.

---

## Open questions

None. All threads resolved at end of [B] revision pass; cross-artifact sweep verdict: PASS.

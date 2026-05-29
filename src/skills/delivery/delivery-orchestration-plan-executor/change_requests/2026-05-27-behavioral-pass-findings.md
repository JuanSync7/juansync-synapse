---
title: Behavioral-pass findings from first live run
artifact: delivery-orchestration-plan-executor
type: revision
date: 2026-05-27
author: juansync7
trigger: first end-to-end test run against demo app (~/demo-delivery, fizzbuzz-with-config, 2 slices)
status: proposed
---

# Behavioral-pass findings — delivery-orchestration-plan-executor

The skill's first live run completed all loop mechanics cleanly (decompose → confirm → pre-flight → dispatch → ingest → replan → terminate). On-disk artifacts verified: 2 schema-valid closeouts, plan + CHANGELOG + lessons, `make test` 2/2 green. Eight gaps surfaced from the run that no static review caught. This CR proposes targeted edits.

The orchestrator subagent in the test run could not dispatch real worker subagents (no `Agent` tool exposed in its environment) and degraded to inline execution. Honest report rather than fabricated success. Three EVAL criteria covering real-dispatch shape (E05, O04, O05) remain untested in this run — to be re-graded after fixes land and the demo is re-run from a session with subagent dispatch available.

---

## Findings

### F1. [PRE-FLIGHT] is missing a dispatch-capability check
**Surface:** `src/skills/delivery/delivery-orchestration-plan-executor/SKILL.md` — `[PRE-FLIGHT]` node.
**Symptom observed:** Worker subagent dispatch primitive (`Agent` tool) was unavailable in the test harness; the loop sailed into `[DISPATCH]` and discovered the gap there, then silently degraded to inline execution.
**Failure mode without fix:** Orchestrator quietly executes worker code itself, collapsing the grader/gradee boundary. Closeouts still look valid, but the 8-slot + 3-protocol contract was never exercised.
**Proposed change:** Add a fourth pre-flight check — "subagent-dispatch primitive available." On miss, halt loudly with `PROTOCOL FAILURE: delivery-orchestration-dispatch-contract pre-flight no-dispatch-capability`. No degraded mode.

### F2. [PRE-FLIGHT] is missing a protocol-resolution check
**Surface:** `SKILL.md` — `[PRE-FLIGHT]` node.
**Symptom observed:** SKILL.md line 26 says "reference protocols by name only." The orchestrator and worker need to resolve those names to files on disk. From a cwd outside the ai-synapse repo, that resolution has no documented mechanism.
**Failure mode without fix:** Worker tries to read a named contract, gets file-not-found, improvises the contract, produces output that violates it silently.
**Proposed change:** Add a fifth pre-flight check — for every name in the dispatch's `worker_protocols` slot, verify `~/.claude/protocols/<domain>/<name>.md` is readable. Convention adopted in this CR (see F8). Halt loudly on miss with the unresolved name.

### F3. No sanctioned pre-approval posture for [CONFIRM]
**Surface:** `SKILL.md` — `[CONFIRM]` node.
**Symptom observed:** Test fixtures and CI batch runs need to pre-authorize the WP list. The skill says "NEVER let an ambient 'yes' substitute for confirmation," which forces test runs to bend the rule.
**Failure mode without fix:** Test runs and automation either skip the gate informally (eroding the rule) or block forever.
**Proposed change:** Add a sanctioned posture: `[CONFIRM]` accepts a `--pre-approved` flag in the skill invocation. When set, the gate logs the pre-approval to CHANGELOG (`signal_type: confirm_preapproved`) and continues. The flag MUST be set by the caller, not inferred. Without the flag, the gate still demands an explicit human Y/adjust.

### F4. Closeout schema has a scaffolding loophole
**Surface:** `src/protocols/delivery/delivery-orchestration-closeout-schema.md`.
**Symptom observed:** Worker created `src/__init__.py` and `tests/__init__.py` (package scaffolding) not listed in slice `touches`. Schema enforces `files_modified ⊆ touches` but says nothing about `files_created`, so scaffolding slipped through `files_created` while staying schema-valid.
**Failure mode without fix:** Workers can quietly create files outside the declared slice scope as long as they label them `files_created`, defeating the scope-policing intent.
**Proposed change:** Tighten schema to require `files_created ⊆ touches ∪ scaffolding_paths` where `scaffolding_paths` is a new optional slice-level whitelist (e.g., `__init__.py`, framework config). If any file outside both sets appears, schema validation fails. Default `scaffolding_paths: []`.

### F5. `validable_outcome` verbatim copy is brittle
**Surface:** `src/protocols/delivery/delivery-orchestration-closeout-schema.md` and `delivery-execution-slice-contract.md`.
**Symptom observed:** Slice files store outcomes with embedded JSON quoting (`{"fizz_word": "Foo"...}`). Getting that verbatim into YAML requires careful escaping a worker is likely to fumble.
**Failure mode without fix:** Workers paraphrase the outcome string, breaking the integrity of post-hoc closeout audits where outcome-text equivalence is the integrity anchor.
**Proposed change:** Allow `validable_outcome_ref: <relative-path-to-wp-file>` as an alternative to inline `validable_outcome`. Validator dereferences and compares against the WP file's frontmatter. Exactly one of the two MUST be set.

### F6. No "orchestrator-as-worker" fallback semantics defined
**Surface:** `SKILL.md` — global behavior.
**Symptom observed:** When dispatch is unavailable, the skill has no defined fallback. The test-run subagent invented one (inline execution).
**Failure mode without fix:** Future degraded environments invite ad-hoc orchestrator-as-worker behavior with no discipline check, accumulating subtle integrity drift.
**Proposed change:** Explicitly forbid orchestrator-as-worker mode. Rely on F1 (pre-flight halt) as the only correct response when dispatch is unavailable. Add a `MUST NOT` line in SKILL.md: "Orchestrator MUST NOT execute slice code itself under any condition. If dispatch is unavailable, halt at pre-flight per F1."

### F7. Final-summary "5–10 lessons" floor unrealistic for short runs
**Surface:** `src/skills/delivery/delivery-orchestration-plan-executor/references/final-summary-format.md`.
**Symptom observed:** A clean 2-slice run yielded 2 lessons. Spec demands minimum 5, inviting padding.
**Failure mode without fix:** Workers/orchestrators pad lessons to meet the floor, polluting the lessons trail with low-signal entries.
**Proposed change:** Reword the bound to `min(lessons_total, 5)..10`. A short clean run reports 2/2 honestly. A long run still caps at 10.

### F8. `cortex install` does not symlink protocols
**Surface:** `cortex` install logic + a new convention.
**Symptom observed:** Skills install to `~/.claude/skills/<name>` as symlinks (flat namespace). Protocols are referenced by name from skill bodies but have no install path — they only exist at their source path in the ai-synapse checkout. Cross-directory runs cannot resolve them.
**Failure mode without fix:** Skill works only when invoked from a cwd that gives the worker a path back to the ai-synapse repo. Failure is silent file-not-found inside the worker, leading to contract improvisation.
**Proposed change:**
- New convention: `~/.claude/protocols/<domain>/<name>.md` is the global lookup path.
- `./cortex install <skill-path>` walks the installed skill's protocol references and symlinks each referenced protocol's domain directory into `~/.claude/protocols/`.
- Add `./cortex install --protocols <domain>` for explicit domain-level install.
- Add a `~/.claude/protocols/README.md` documenting the contract.
- Add `./cortex doctor` check: every installed skill's `worker_protocols` references resolve under `~/.claude/protocols/`.

---

## Surface rollup

| File | Findings touching it |
|------|----------------------|
| `src/skills/delivery/delivery-orchestration-plan-executor/SKILL.md` | F1, F2, F3, F6 |
| `src/skills/delivery/delivery-orchestration-plan-executor/references/final-summary-format.md` | F7 |
| `src/protocols/delivery/delivery-orchestration-closeout-schema.md` | F4, F5 |
| `src/protocols/delivery/delivery-execution-slice-contract.md` | F5 |
| `cortex` (install + doctor) | F8 |
| `~/.claude/protocols/README.md` (new) | F8 |

## Sequencing

1. **F8 first** — convention + install + doctor land before pre-flight resolver depends on them.
2. **F1, F2, F6** — skill pre-flight + MUST NOT (depends on F8 for F2 to resolve).
3. **F4, F5** — protocol schema tightening (independent).
4. **F3** — pre-approval posture (independent).
5. **F7** — output format (trivial).

## Verification plan

After all 8 findings land:

1. Reinstall the skill: `./cortex install src/skills/delivery/delivery-orchestration-plan-executor` — verify it now also symlinks `~/.claude/protocols/delivery/`.
2. `./cortex doctor` reports zero unresolved-protocol findings.
3. Re-run the demo from `~/demo-delivery` in a fresh Claude Code session that has the `Agent` tool exposed.
4. Re-grade EVAL.md — confirm E05, O04, O05 now testable; confirm earlier passes still hold.
5. Run a deliberate negative test: remove one protocol symlink, invoke the skill, confirm `[PRE-FLIGHT]` halts loudly per F2.

## Out of scope for this CR

- The retirement CR for `parallel-agents-dispatch` (separate, tracked elsewhere).
- Any change to who writes plan/lessons (Model-C linkage is correct as-is).
- Parallel-dispatch escape hatch refinements (not exercised in this run).

---

## Evidence pointers

- Demo workspace: `~/demo-delivery/` (preserved after run)
- Plan: `~/demo-delivery/.delivery/plan/INDEX.md`
- Closeouts: `~/demo-delivery/.delivery/closeouts/wp-{001,002}-attempt-1.yaml`
- CHANGELOG: `~/demo-delivery/.delivery/plan/CHANGELOG.md`
- Test result: `make test` from `~/demo-delivery` — 2/2 green
- Test-run subagent integrity disclosure: full report retained in parent-session transcript

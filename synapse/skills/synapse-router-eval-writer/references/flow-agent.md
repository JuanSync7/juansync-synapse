# flow-agent — Agent EVAL.md generation

Loaded by `synapse-router-eval-writer` after `[ROUTE]` confirms `$TYPE=agent`. **Transcription flow:** the canonical `synapse-router-artifact-gatekeeper/references/agent-checklist.md` IS the criteria source. This file does NOT bake in agent criteria.

> **Loading discipline (invariant):** This file is the ONLY flow active in this session.

---

## MUST (flow level)
- Load the canonical checklist via `type-config[agent].canonical_checklist_source` — fail loud if the path does not resolve
- Treat the source agent `.md` as read-only
- Atomic write — assemble in memory, single Write call

## MUST NOT (flow level)
- Reproduce checklist content inline in this file
- Fall back to baked-in criteria if the gatekeeper checklist is missing or renamed — fail loud with the unresolved Load path
- Add any criterion that is not directly traceable to a row in the canonical checklist
- Validate taxonomy values on the source artifact

---

## EVAL.md tier shape (from `type-config.md`)

| Tier | Source | Mapping rule |
|------|--------|--------------|
| EVAL-S (Structural) | Tier 1 rows of `agent-checklist.md` | One `EVAL-Sxx` per Tier 1 row |
| EVAL-Q (Quality) | Tier 2 rows of `agent-checklist.md` | One `EVAL-Qxx` per Tier 2 row |

No Test Prompts section — agent grading is checklist-driven.

---

## Flow

### [START] — pre-flight + checklist load
Load: `references/shared-steps.md`, `references/type-config.md`, `synapse/skills/synapse-router-artifact-gatekeeper/references/agent-checklist.md`
Brief: Validate inputs, load the canonical checklist. Hard stop if checklist Load fails.
Do:
  1. → `shared-steps:validate-frontmatter(agent, $ARTIFACT_PATH)` — extract `$ARTIFACT_NAME`
  2. → `shared-steps:resolve-output-path(agent, $ARTIFACT_PATH, $ARTIFACT_NAME)` — yields `$EVAL_PATH` (e.g. `<agent>.eval.md` adjacent to the agent file)
  3. → `shared-steps:existing-eval-guard($EVAL_PATH, $FORCE)`
  4. Load the file at `type-config[agent].canonical_checklist_source`. **If the file does not exist or the Tier 1 / Tier 2 sections cannot be located, FAIL LOUDLY** with: `FAIL: canonical checklist not found at <path>. Cannot transcribe — refuse to fall back to baked-in content.`
Don't:
  - Proceed past pre-flight if any check fails
  - Substitute training-memory criteria for the missing checklist
Exit:
  → `[T]` : pre-flight passes; checklist loaded

---

### [T] — transcribe
Load: `templates/agent/eval.md`
Brief: Map each Tier 1 row to an `EVAL-Sxx` criterion and each Tier 2 row to an `EVAL-Qxx` criterion.
Do:
  1. Load the agent EVAL template.
  2. For each row in the Tier 1 (Structural) table of the loaded checklist, emit one `EVAL-S<NN>` block with:
     - Title = the "Check" column verbatim
     - Test = "Verify: <Pass condition column verbatim>"
     - Fail signal = "Pass condition does not hold"
  3. For each row in the Tier 2 (Quality) table, emit one `EVAL-Q<NN>` block under the Quality Criteria section using the same shape.
  4. Number criteria sequentially within each tier starting at `01`.
  5. Substitute header tokens: agent name, generator (`synapse-router-eval-writer`), version `1.0`.
  6. Confirm the assembled body is non-empty.
Don't:
  - Add criteria not present in the checklist
  - Drop criteria that are present in the checklist
  - Reword "Pass condition" text — preserve verbatim
Exit:
  → `[W]` : assembled body ready

---

### [W] — atomic write
Do:
  1. Compute `$TIER_COUNTS` for `EVAL-S` and `EVAL-Q`.
  2. → `shared-steps:write-eval-atomic($EVAL_PATH, $EVAL_BODY, $TIER_COUNTS)` with `test_prompts: false`.
Don't:
  - Issue more than one Write tool call against `$EVAL_PATH` — atomic invariant
  - Modify the source agent file or any companion file
Exit:
  → `[END]`

---

### [END] — report
Do:
  1. Print: `Wrote <EVAL_PATH> with <S> EVAL-S, <Q> EVAL-Q`.
  2. Remind: criteria are transcribed from `synapse-router-artifact-gatekeeper/references/agent-checklist.md`. To certify, run `/synapse-router-artifact-gatekeeper <agent-path>`.
Don't:
  - Auto-dispatch `/synapse-router-artifact-gatekeeper` — suggest, do not dispatch

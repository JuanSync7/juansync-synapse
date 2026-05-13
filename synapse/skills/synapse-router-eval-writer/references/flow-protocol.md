# flow-protocol — Protocol EVAL.md generation

Loaded by `synapse-router-eval-writer` after `[ROUTE]` confirms `$TYPE=protocol`. **Transcription flow:** the canonical `synapse-router-artifact-gatekeeper/references/protocol-checklist.md` IS the criteria source. This file does NOT bake in protocol criteria.

> **Loading discipline (invariant):** This file is the ONLY flow active in this session.

---

## MUST (flow level)
- Load the canonical checklist via `type-config[protocol].canonical_checklist_source` — fail loud if the path does not resolve
- Treat the source protocol `.md` as read-only
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
| EVAL-S (Structural) | Tier 1 rows of `protocol-checklist.md` | One `EVAL-Sxx` per Tier 1 row |
| EVAL-C (Conformance) | Tier 2 rows of `protocol-checklist.md` | One `EVAL-Cxx` per Tier 2 row |

No Test Prompts section — protocol grading is checklist-driven, not prompt-driven.

---

## Flow

### [START] — pre-flight + checklist load
Load: `references/shared-steps.md`, `references/type-config.md`, `synapse/skills/synapse-router-artifact-gatekeeper/references/protocol-checklist.md`
Brief: Validate inputs, load the canonical checklist. Hard stop if checklist Load fails.
Do:
  1. → `shared-steps:validate-frontmatter(protocol, $ARTIFACT_PATH)` — extract `$ARTIFACT_NAME`
  2. → `shared-steps:resolve-output-path(protocol, $ARTIFACT_PATH, $ARTIFACT_NAME)` — yields `$EVAL_PATH`
  3. → `shared-steps:existing-eval-guard($EVAL_PATH, $FORCE)`
  4. Load the file at `type-config[protocol].canonical_checklist_source`. **If the file does not exist or the Tier 1 / Tier 2 sections cannot be located, FAIL LOUDLY** with: `FAIL: canonical checklist not found at <path>. Cannot transcribe — refuse to fall back to baked-in content.`
Don't:
  - Proceed past pre-flight if any check fails
  - Substitute training-memory criteria for the missing checklist
Exit:
  → `[T]` : pre-flight passes; checklist loaded into context

---

### [T] — transcribe
Load: `templates/protocol/eval.md`
Brief: Map each Tier 1 row to an `EVAL-Sxx` criterion and each Tier 2 row to an `EVAL-Cxx` criterion. The checklist's "Pass condition" column becomes the criterion's Test/Fail-signal text.
Do:
  1. Load the protocol EVAL template.
  2. For each row in the Tier 1 (Structural) table of the loaded checklist, emit one `EVAL-S<NN>` block with:
     - Title = the "Check" column verbatim
     - Test = "Verify: <Pass condition column verbatim>"
     - Fail signal = "Pass condition does not hold"
  3. For each row in the Tier 2 (Conformance) table, emit one `EVAL-C<NN>` block under the Conformance Criteria section using the same shape.
  4. Number criteria sequentially within each tier starting at `01`.
  5. Substitute header tokens: protocol name, generator (`synapse-router-eval-writer`), version `1.0`.
  6. Confirm the assembled body is non-empty.
Don't:
  - Add criteria not present in the checklist
  - Drop criteria that are present in the checklist (omission = silent grading drift)
  - Reword "Pass condition" text — preserve verbatim so future checklist edits flow through cleanly
Exit:
  → `[W]` : assembled body ready

---

### [W] — atomic write
Do:
  1. Compute `$TIER_COUNTS` for `EVAL-S` and `EVAL-C`.
  2. → `shared-steps:write-eval-atomic($EVAL_PATH, $EVAL_BODY, $TIER_COUNTS)` with `test_prompts: false`.
Don't:
  - Issue more than one Write tool call against `$EVAL_PATH` — atomic invariant
  - Modify the source protocol file or any companion file
Exit:
  → `[END]`

---

### [END] — report
Do:
  1. Print: `Wrote <EVAL_PATH> with <S> EVAL-S, <C> EVAL-C`.
  2. Remind: criteria are transcribed from `synapse-router-artifact-gatekeeper/references/protocol-checklist.md`. To certify, run `/synapse-router-artifact-gatekeeper <protocol-path>`.
Don't:
  - Auto-dispatch `/synapse-router-artifact-gatekeeper` — suggest, do not dispatch

# flow-tool — Tool EVAL.md generation

Loaded by `synapse-router-eval-writer` after `[ROUTE]` confirms `$TYPE=tool`. **Transcription+ flow:** structural rules transcribe from `synapse-router-artifact-gatekeeper`'s tool-flow sections (currently inline in that SKILL.md); execution criteria scaffold around the tool's existing `test/` directory.

> **Loading discipline (invariant):** This file is the ONLY flow active in this session.
> **Note on checklist source:** Tool checklist is currently inline in `synapse-router-artifact-gatekeeper/SKILL.md` (Phase 2 "Tool flow" + Phase 3 "Tool flow"). When that section is extracted to `references/tool-checklist.md`, update `type-config[tool].canonical_checklist_source` — no change required in this flow file.

---

## MUST (flow level)
- Load the canonical checklist source via `type-config[tool].canonical_checklist_source` — fail loud if the path does not resolve
- Treat the source tool directory as read-only — never edit `TOOL.md`, scripts, or `test/` files
- Atomic write — assemble in memory, single Write call
- Every `EVAL-Xxx` criterion MUST cite a real script file inside the tool's `test/` directory — never invent test scripts that do not exist

## MUST NOT (flow level)
- Reproduce checklist content inline in this file
- Fall back to baked-in structural criteria if the gatekeeper checklist source is missing — fail loud
- Generate `EVAL-Xxx` criteria for a `test/` directory that does not exist — surface a missing-tests warning instead
- Validate taxonomy values on the source artifact

---

## EVAL.md tier shape (from `type-config.md`)

| Tier | Source | Mapping rule |
|------|--------|--------------|
| EVAL-S (Structural) | `synapse-router-artifact-gatekeeper` Phase 2 + Phase 3 "Tool flow" rows | One `EVAL-Sxx` per checklist row |
| EVAL-X (Execution / exit-codes) | Files inside the tool's `test/` directory | One `EVAL-Xxx` per discovered test script |

No Test Prompts section — tool grading is script-invocation-driven.

---

## Flow

### [START] — pre-flight + checklist load
Load: `references/shared-steps.md`, `references/type-config.md`, source pointed to by `type-config[tool].canonical_checklist_source` (currently `synapse/skills/synapse-router-artifact-gatekeeper/SKILL.md`, the Tool flow sections of Phase 2 and Phase 3)
Brief: Validate inputs; load the canonical structural rules from gatekeeper.
Do:
  1. → `shared-steps:validate-frontmatter(tool, $ARTIFACT_PATH)` — extract `$ARTIFACT_NAME` from `TOOL.md`
  2. → `shared-steps:resolve-output-path(tool, $ARTIFACT_PATH, $ARTIFACT_NAME)` — yields `$EVAL_PATH = $ARTIFACT_PATH/EVAL.md`
  3. → `shared-steps:existing-eval-guard($EVAL_PATH, $FORCE)`
  4. Load the checklist source. **If the file or referenced sections cannot be located, FAIL LOUDLY** with: `FAIL: canonical tool checklist source not found at <path>. Cannot transcribe — refuse to fall back to baked-in content.`
  5. Inspect `$ARTIFACT_PATH/test/`. Record each file as a candidate `EVAL-Xxx` source. If the directory does not exist, set `$TEST_FILES = []` and emit a non-fatal warning that the resulting EVAL will have an empty Execution tier.
Don't:
  - Substitute training-memory criteria for the missing checklist
  - Synthesize test scripts that do not exist
Exit:
  → `[T]` : pre-flight passes; checklist + test inventory in context

---

### [T] — transcribe + scaffold
Load: `templates/tool/eval.md`
Brief: Transcribe structural rows; scaffold one `EVAL-Xxx` per real test file.
Do:
  1. Load the tool EVAL template.
  2. For each row in the gatekeeper Tool-flow Phase 2 (Structural) + Phase 3 (Quality) tables, emit one `EVAL-S<NN>` block:
     - Title = the "Check" column verbatim
     - Test = "Verify: <Pass condition column verbatim>"
     - Fail signal = "Pass condition does not hold"
  3. For each file in `$TEST_FILES`, emit one `EVAL-X<NN>` block under the Execution Criteria section:
     - Title = "`<test-file-basename>` runs cleanly"
     - Test = "Invoke `<relative-path-to-test-file>` from the tool's directory; assert exit code 0"
     - Fail signal = "Non-zero exit code or stderr output indicating an assertion failure"
  4. Number criteria sequentially within each tier starting at `01`.
  5. Substitute header tokens: tool name, generator (`synapse-router-eval-writer`), version `1.0`.
  6. Confirm the assembled body is non-empty.
Don't:
  - Add `EVAL-X` criteria for tests that do not exist on disk
  - Drop checklist rows
  - Reword "Pass condition" text
Exit:
  → `[W]` : assembled body ready

---

### [W] — atomic write
Do:
  1. Compute `$TIER_COUNTS` for `EVAL-S` and `EVAL-X`.
  2. → `shared-steps:write-eval-atomic($EVAL_PATH, $EVAL_BODY, $TIER_COUNTS)` with `test_prompts: false`.
Don't:
  - Issue more than one Write tool call against `$EVAL_PATH` — atomic invariant
  - Modify the source TOOL.md, the script, or files in `test/`
Exit:
  → `[END]`

---

### [END] — report
Do:
  1. Print: `Wrote <EVAL_PATH> with <S> EVAL-S, <X> EVAL-X`.
  2. If `$TEST_FILES` was empty, surface: "Tool has no `test/` directory — EVAL-X tier is empty. Add tests before requesting `/synapse-router-artifact-gatekeeper` certification."
  3. Otherwise remind: to certify, run `/synapse-router-artifact-gatekeeper <tool-path>`.
Don't:
  - Auto-dispatch `/synapse-router-artifact-gatekeeper` — suggest, do not dispatch
  - Execute the test scripts during eval generation — EVAL-X criteria assert that the tests exist and document expected exit codes; running them is gatekeeper / CI work

# flow-skill — Skill EVAL.md generation

Loaded by `synapse-router-eval-writer` after `[ROUTE]` confirms `$TYPE=skill`. Owns the full lifecycle from artifact read through atomic EVAL.md write. Wrong-tool detection already ran in the router — do not repeat it here.

> **Loading discipline (invariant):** This file is the ONLY flow active in this session. Never load another flow file.

---

## MUST (flow level)
- Load `references/shared-steps.md` at `[START]` — every parametric procedure lives there
- Dispatch each `skill-eval-*` agent EXACTLY ONCE — agents share NO context with each other (bias control)
- Never write EVAL.md until all three agents return — atomic-write invariant
- Treat the source skill as read-only — never edit `SKILL.md`, never edit `references/`

## MUST NOT (flow level)
- Inline criteria authoring — criteria come from agents, not from this file's training memory
- Share context between `synapse-skill-eval-prompter` (blind) and `synapse-skill-eval-judge` (full SKILL.md sighted) — bias control
- Grade the artifact — this skill produces criteria; grading is `/synapse-router-artifact-gatekeeper` and `/synapse-skill-skill-improver`
- Write a partial EVAL.md if any agent fails — surface the error; user re-runs

---

## Bias controls

```
synapse-router-eval-writer (skill flow)
        │
        ├── synapse-skill-eval-prompter   sees: skill name + description ONLY     (blind)
        │
        ├── synapse-skill-eval-judge      sees: full SKILL.md as impartial judge   (sighted)
        │
        └── synapse-skill-eval-auditor    sees: full SKILL.md                      (sighted, orchestration)
```

`prompter` is BLIND — it never sees how the skill works, so prompts cannot leak the skill's solution shape. `judge` and `auditor` are sighted but framed as evaluators, not authors. The three agents NEVER share context with each other. If the same context is fed to two of them, you have invalidated the eval.

---

## EVAL.md tier shape (from `type-config.md`)

| Tier | Source | Optional? |
|------|--------|-----------|
| EVAL-S (Structural) | Static checklist (this file, Step 5) | No |
| EVAL-E (Execution / orchestration) | `synapse-skill-eval-auditor` output | Yes — omit section if auditor returns no criteria |
| EVAL-F (Flow Conformance) | Static checklist when `references/flow-*.md` files exist | Yes — omit if no flow files |
| EVAL-O (Output) | `synapse-skill-eval-judge` output | No |
| Test Prompts | `synapse-skill-eval-prompter` output | No |

---

## Flow

### [START] — pre-flight
Load: `references/shared-steps.md`, `references/type-config.md`
Brief: All validations before any dispatch. Resolve target path; check for existing EVAL.md.
Do:
  1. → `shared-steps:validate-frontmatter(skill, $ARTIFACT_PATH)` — extract `$ARTIFACT_NAME` and skill `description` from frontmatter
  2. → `shared-steps:resolve-output-path(skill, $ARTIFACT_PATH, $ARTIFACT_NAME)` — yields `$EVAL_PATH`
  3. → `shared-steps:existing-eval-guard($EVAL_PATH, $FORCE)`
  4. Check whether `$ARTIFACT_PATH/references/flow-*.md` files exist — flag `$HAS_FLOW_FILES` for later (drives EVAL-F section)
Don't:
  - Dispatch any agent before pre-flight passes
  - Skip the existing-eval guard
Exit:
  → `[D]` : pre-flight passes; agents ready to dispatch

---

### [D] — dispatch agents in parallel
Brief: Three independent agents, three parallel dispatches. They share zero context.
Do:
  1. Dispatch `synapse-skill-eval-prompter` (model: sonnet) with **only** `$ARTIFACT_NAME` and the skill's `description` field. Do NOT pass `SKILL.md` body, `references/`, or any internal mechanics.
  2. Dispatch `synapse-skill-eval-judge` (model: sonnet) with the full `SKILL.md` path. Frame as: "You are an impartial evaluator. Produce binary EVAL-Oxx output criteria for what this skill must produce when run."
  3. Dispatch `synapse-skill-eval-auditor` (model: sonnet) with the full `SKILL.md` path. Frame as: "Produce EVAL-Exx orchestration criteria for the skill's execution patterns (subagent dispatch, model selection, phase gates). If the skill has no orchestration patterns, return an explicit empty result."
  4. Issue all three dispatches in a single parallel batch — never serialize them.
  5. On any agent failure: collect the error, abort the flow, do NOT proceed to assembly. Surface the failure to the caller; user re-runs.
Don't:
  - Pass `SKILL.md` body to `synapse-skill-eval-prompter` — destroys the blind constraint
  - Share `synapse-skill-eval-prompter`'s output back into `synapse-skill-eval-judge`'s context — destroys independence
  - Auto-retry a failed agent silently — surface and stop
Exit:
  → `[A]` : all three agents returned (some may return empty for `auditor`)

---

### [A] — assemble EVAL.md in memory
Load: `templates/skill/eval.md`
Brief: Build the full EVAL.md string by composing the static structural checklist with agent outputs against the template. Nothing is written to disk yet.
Do:
  1. Load `templates/skill/eval.md` skeleton.
  2. Substitute header tokens: skill name, generator (`synapse-router-eval-writer`), version `1.0`.
  3. Fill the **Structural Criteria** section with the static EVAL-Sxx checklist below — these are universal across all skills:
     - EVAL-S01: Frontmatter complete (`name`, `description`, `domain`, `intent`)
     - EVAL-S02: `domain` and `intent` exist in `taxonomy/SKILL_TAXONOMY.md`
     - EVAL-S03: SKILL.md under 500 lines
     - EVAL-S04: `Wrong-Tool Detection` section present and names sibling skills
     - EVAL-S05: Every `Load:` path in SKILL.md resolves to an existing file
     - EVAL-S06: Skill listed in `registry/SKILL_REGISTRY.md` with `status` column populated
     - EVAL-S07: Domain README contains a row for this skill
     - EVAL-S08: EVAL.md exists alongside SKILL.md (self-referential — passes by virtue of being written)
  4. Fill the **Execution Criteria** section with `synapse-skill-eval-auditor`'s output. If auditor returned empty (no orchestration patterns), OMIT the section entirely — do not write an empty header.
  5. If `$HAS_FLOW_FILES` is true, add a **Flow Conformance Criteria** section with the static EVAL-Fxx checklist (apply each check to all `references/flow-*.md` files):
     - EVAL-F01: Each flow has a real `[START]` and `[END]` node
     - EVAL-F02: Node headings use `### [ID]` (level-3) consistently
     - EVAL-F03: Every node has Do, Don't, Exit blocks
     - EVAL-F04: Exit blocks declare labeled edges with conditions
     - EVAL-F05: Per-node Loads — companions load inside the node that uses them
     - EVAL-F06: Flow file under 200 lines (advisory)
     - EVAL-F07: No `if $TYPE` conditionals inside flow files
  6. Fill the **Output Criteria** section with `synapse-skill-eval-judge`'s EVAL-Oxx output verbatim.
  7. Fill the **Test Prompts** section with `synapse-skill-eval-prompter`'s output, organized by persona (Naive / Experienced / Adversarial / Wrong Tool).
  8. Confirm the full assembled string is non-empty before exiting.
Don't:
  - Edit agent output bodies beyond formatting — preserve their criteria language verbatim
  - Inline new criteria from this flow's training — agents own the content
  - Write any file in this node — assembly only
Exit:
  → `[W]` : assembled EVAL body ready

---

### [W] — atomic write
Brief: Single-write commit; emit exit signal.
Do:
  1. Compute `$TIER_COUNTS` by counting `EVAL-S`, `EVAL-E`, `EVAL-F`, `EVAL-O`, and test-prompt entries in the assembled body.
  2. → `shared-steps:write-eval-atomic($EVAL_PATH, $EVAL_BODY, $TIER_COUNTS)` with `test_prompts: true`.
Don't:
  - Issue more than one Write tool call against `$EVAL_PATH`
  - Modify the source `SKILL.md` or any companion file
Exit:
  → `[END]` : EVAL.md written; exit signal emitted

---

### [END] — report
Do:
  1. Print: `Wrote <EVAL_PATH> with <S> EVAL-S, <E> EVAL-E, <F> EVAL-F, <O> EVAL-O, <P> test prompts`.
  2. Remind caller: this skill produced criteria only — to grade the skill, run `/synapse-skill-skill-improver <path>`; to certify for promotion, run `/synapse-router-artifact-gatekeeper <path>`.
Don't:
  - Auto-dispatch `/synapse-skill-skill-improver` or `/synapse-router-artifact-gatekeeper` — suggest, do not dispatch

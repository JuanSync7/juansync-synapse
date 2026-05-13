# flow-skill — Skill Creation Flow

Loaded by `synapse-router-artifact-creator` after `[ROUTE]` confirms `$TYPE=skill`. Owns the full lifecycle from
pre-flight through eval handoff. Wrong-tool detection already ran in the router — do not repeat it here.

> **Out of scope at flow level:** SCOPE.md, PROGRAM.md, research/ dir, test-inputs/ dir.
> These belong at synapse-router-artifact-creator root if an improvement loop is wanted, not within a creation flow.

---

## MUST (flow level)
- Load `references/shared-steps.md` at `[START]` — every parametric procedure lives there
- Load `references/design-principles-skill.md` at `[W]` before writing SKILL.md
- Trace every SKILL.md instruction to a baseline failure identified at `[B]`
- Pass all pre-flight checks at `[START]` before writing any file

## MUST NOT (flow level)
- Inline frontmatter validation, registry writes, or README row updates — call shared-steps
- Write EVAL.md before SKILL.md is complete — post-hoc bias
- Proceed from `[U]` with an underspecified goal
- Skip `[B]` when no memo is present ("the skill is simple" is not an exemption)
- Skip `/synapse-skill-skill-improver` at `[V]` ("the skill looks correct" is not validation)

---

## Flow

### [START] — pre-flight
Load: `references/shared-steps.md`
Brief: All validations before any file is written. Atomic creation guarantee.
Do:
  1. → `shared-steps:placement-decision(skill)` — confirm `src/` or `synapse/` target
  2. → `shared-steps:validate-frontmatter(skill, $artifact_dir)` — required fields, taxonomy values, name uniqueness
  3. If existing artifact detected at target path → offer "complete partial creation?" or "abort and clean up?"
Don't:
  - Write any file if any pre-flight step fails
  - Auto-select placement without user confirmation for framework (`synapse/`) placement
Exit:
  → `[U]` : pre-flight passes

---

### [U] — understand goal
Brief: Self-loops until all gate conditions pass. If a decision memo from `/synapse-router-artifact-brainstormer` exists, evaluate against gates — fill gaps only; do not re-derive what the memo already decided.
Do:
  1. If memo provided with VERBATIM blocks (flow graphs, node specs), use as starting point — pressure-tested during brainstorm
  2. Identify trigger conditions (routing contract for `description:`)
  3. Define primary output artifact and its format
  4. Check SKILL_REGISTRY.md for sibling skills with overlapping scope
  5. Confirm user intent — one specific question per gap, not an interrogation
Don't:
  - Proceed with ambiguous trigger conditions
  - Accept "it's like X but better" as a scope definition
Exit:
  → `[U]` : trigger phrase, output artifact, overlap check, or user confirmation missing
  → `[B]` : all four gate conditions confirmed

---

### [B] — baseline test
Brief: Conditional skip — if memo documents a baseline failure, skip subagent dispatch.
Do:
  1. If memo with documented baseline failure → use gap analysis, skip to `[W]`
  2. If no memo → spawn subagent with full task context and NO skill instructions; evaluate output
  3. Judge: correct (skill unnecessary), partial (gaps documented → `[W]`), or absent
Don't:
  - Skip when no memo exists
  - Include SKILL.md content or flow-graph instructions in the baseline subagent prompt
Exit:
  → `[END]` : output already correct — inform user, no skill needed
  → `[W]` : gaps documented

---

### [W] — write SKILL.md
Load: `references/design-principles-skill.md`, `templates/skill/SKILL.md.template`
Brief: Core authoring node. Write SKILL.md only — companions are written at `[C]`.
Do:
  1. Apply flow-graph pattern from template — structure is universal
  2. Distill goal into MUST / MUST NOT rules; each traces to a failure from `[B]`
  3. Decompose into nodes — each node follows Load / Brief / Do / Don't / Exit anatomy
  4. Identify all companion files from Load declarations; build companion inventory
  5. Call → `shared-steps:write-registry-row(skill, $meta)`
  6. Call → `shared-steps:update-domain-readme(skill, $domain, $meta)`
  7. Call → `shared-steps:status-draft-mark(skill, $meta)`
Don't:
  - Produce prose-structured SKILL.md — every skill follows flow-graph pattern
  - Write companion files here — that is `[C]`
  - Proceed if design cannot converge into ~80 lines — fail loudly
  - Inline logic that belongs in shared-steps (frontmatter validation, registry writes, README updates)
Exit:
  → `[W]` : design convergence failure or revision needed
  → `[C]` : SKILL.md written; registry row added; README row added; companion inventory ready

---

### [C] — write companions
Load: `agents/skill/skill-companion-file-writer.md`
Brief: Main agent becomes orchestrator. Dispatch one subagent per companion file in parallel.
Do:
  1. For each companion file in inventory, dispatch subagent with: file_path, file_type, skill_md, content_brief
  2. Dispatch all in a single parallel batch — no sequential dispatch where there is no data dependency
  3. Verify each companion serves its Load point in SKILL.md
  4. On partial failure: retry failed file only (max 2 retries); surface gap to user on third failure
Don't:
  - Silently accept subagent failures
  - Batch multiple files into a single subagent
  - Accept a companion whose content does not match its Load point
Exit:
  → `[C]` : partial failure or coherence mismatch after retries
  → `[E]` : all companions written and coherent

---

### [E] — eval handoff
Brief: Dispatch eval writer and assemble EVAL.md.
Do:
  1. Call → `shared-steps:handoff-eval(skill, $artifact_path)`
  2. EVAL.md must not exist before SKILL.md + companions are complete
Don't:
  - Generate EVAL.md manually — that is `synapse-router-eval-writer`'s job (skill flow)
  - Block on eval completion — dispatch and proceed
Exit:
  → `[V]` : eval dispatched

---

### [V] — validate
Brief: Hand off to `/synapse-skill-skill-improver` for single-pass validation. Do not reimplement its logic inline.
Do:
  1. Invoke `/synapse-skill-skill-improver $artifact_path` as a skill invocation, not inline steps
  2. Report synapse-skill-skill-improver verdict to user
Don't:
  - Perform scoring or fix-loop steps directly
  - Skip this step ("the skill looks correct" is not validation)
Exit:
  → `[END]` : validate complete (synapse-skill-skill-improver may flag issues for the user to decide)

---

### [END] — report
Do:
  1. Print verbatim what was created: file list, registry row added, README row added, EVAL.md status
  2. Remind user: artifact is `status: draft` — run `/synapse-router-artifact-gatekeeper $artifact_path` before promoting
  3. If synapse-skill-skill-improver flagged issues, surface them — do not auto-fix
Don't:
  - End without full output summary
  - Auto-route to next skill — suggest, do not dispatch

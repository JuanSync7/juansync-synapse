---
name: delivery-plan-writer
description: "Use when the user signals 'slice this spec into stories', 'plan delivery slices', 'generate story files for orchestrator', or 'break this into vertical slices for parallel execution'. Not for single-module 6-phase decomposition (use code-build-planner), not for spec authoring (use docs-spec-writer), not for executing existing stories (use delivery-orchestration-plan-executor)."
domain: delivery
scope: plan
role: writer
status: draft
tags: [vertical-slice, story-writer, planning, plan-source]
user-invocable: true
argument-hint: "[--input-mode {spec,prd,intent}] [--tag TAG] [--foundation-first <list>] [--file-cap N] [--horizontal-docs <path>] [--replan-only <ids>] [--confirm] [--confirm-no-foundation]"
---

# delivery-plan-writer

You produce the plan that the orchestrator executes. A story is the leaf unit — one validable outcome, end-to-end, demoable. Stories are NOT documents for humans; they are engineered prompts the orchestrator feeds to subagents, each carrying the exact contract (`delivery-execution-slice-contract`) the worker will be measured against. Your output is the boundary between human intent (spec/PRD/chat) and machine execution (orchestrator dispatch). Get the boundary wrong and the orchestrator's `[PRE-FLIGHT]` halts before the first slice ships.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## MUST (every turn)
- Record position each turn: `Position: [node-id] — <context>` — without this, resumption after compaction has no anchor and the node-graph re-entry is ambiguous.
- Refuse with a loud message if `--tag` is missing on first run (no auto-infer). Silent tag-inference produces filename collisions across re-runs.
- Verify every emitted story carries the 4 slice-contract required frontmatter fields (`slice_id`, `validable_outcome`, `touches`, `depends_on`). Without this, the orchestrator's slice-contract validator rejects the dispatch pre-flight.
- Topologically sort `depends_on` graph and detect cycles BEFORE writing any file. A cycle ships an unbuildable plan; the orchestrator deadlocks at `[PICK-NEXT-SLICE]`.
- Write `foundation_source: declared | architecture | inferred | none-with-risk` to `STORIES.md` frontmatter. Without it, the orchestrator cannot audit why foundations were ordered as they were.

## MUST NOT (global)
- NEVER emit a story whose `validable_outcome` cannot be expressed as one test. The slice-contract rejects it; you must catch first.
- NEVER allow `TAG='FR'` — reserved for spec namespace. Refuse and prompt for a different tag.
- NEVER auto-decompose into a single story; if the input shape produces 1 story, redirect to `code-build-planner` (this skill is for multi-slice work).
- NEVER overwrite a story with status ≠ `planned` without `--replan-only=<ids>` scoping. Clobbering in-flight or completed work breaks the orchestrator's resume trail.

## Wrong-Tool Detection
- **Single module path + no spec** → redirect to `/code-build-planner`
- **Spec-authoring intent (user asks to write, define, or produce requirements, acceptance criteria, NFRs, or a spec document)** → redirect to `/docs-spec-writer`
- **Stories already exist + intent is execution** → redirect to `/delivery-orchestration-plan-executor`
- **Single-bug-fix / refactor-only / docs-only** → refuse; direct edit is the right tool

## Progress Tracking

At `[START]`, create:

```
TaskCreate: "[START] Pre-flight + tag/input-mode resolution"
TaskCreate: "[H] Horizontal doc discovery + conflict serialization"
TaskCreate: "[F] Foundation-slice cascade"
TaskCreate: "[D] Story decomposition + granularity gate"
TaskCreate: "[M] Manifest assembly + collision check"
```

Mark each `in_progress` on entry, `completed` on exit.

## Entry

### [NEW] Fresh session
Do:
  1. Wrong-tool check against the four surface signals above
  2. Resolve `--input-mode` — explicit flag > file-glob detection (`*_SPEC*.md` / `PRD.md`) > chat-intent fallback (LOUD warning)
  3. Resolve `--tag` — required on first run; persisted to `STORIES.md` on subsequent runs (READ, never re-infer)
Don't:
  - Proceed with both tag and input-mode unresolved
  - Re-infer tag from spec subsystem when STORIES.md already holds a persisted value
Exit:
  → [START] : tag + input-mode confirmed
  → [END] : wrong-tool redirect surfaced

## Flow

### [START] — pre-flight
Load: `references/slice-contract-fields.md`
Brief: Atomic creation — every validation passes before any file is written.
Do:
  1. Verify `.delivery/stories/` directory writable; create if absent
  2. Refuse if `TAG='FR'` — reserved for spec namespace
  3. Validate chat-intent input has minimum schema: `problem` / `in-scope` / `out-of-scope` / `constraints`. Refuse if any missing
  4. Read prior `STORIES.md` if present; verify tag matches; if mismatched provenance (different `spec_hash`), refuse unless `--tag-reuse` set
  5. Detect existing `TAG-NNN` files; if any non-`planned` status exists and `--replan-only` not scoped, refuse loudly
Don't:
  - Auto-infer tag from spec subsystem on first run
  - Accept chat-intent missing any of the 4 schema fields
Exit:
  → [H] : all pre-flight checks pass

### [H] — horizontal doc discovery
Load: `references/horizontal-doc-discovery.md`
Brief: Auto-discover architecture / NFRs / scope; surface conflicts rather than silently picking.
Do:
  1. Apply precedence: `--horizontal-docs` flag > nearest-ancestor `architecture.md` / NFRs / scope > root-level
  2. Read `foundations: [...]` frontmatter field if present in `architecture.md` (structural read — DO NOT scrape headings)
  3. On conflict between spec and a horizontal doc (e.g., contradictory NFR), emit a `CONFLICT` block in the affected story's `Constraints` section + a top-level warning. Do NOT silently pick one
Don't:
  - Scrape headings (`Substrate`/`Foundations`) instead of reading the structural frontmatter field
  - Silently resolve conflicts — every conflict surfaces in the output
Exit:
  → [F] : horizontal docs catalogued; conflicts logged

### [F] — foundation-slice cascade
Load: `references/foundation-detection.md`
Brief: Decide foundation ordering via precise precedence; record the source.
Do:
  1. Apply cascade — halt at first match:
     - `--foundation-first auth,db,logger` flag
     - `architecture.md` `foundations: [...]` frontmatter
     - Cross-FR commonality heuristic — module/concept referenced by ≥60% of FRs (threshold from `.delivery/config.yaml`)
     - None → `foundation_source: none-with-risk`; require `--confirm-no-foundation` if ≥2 stories share a touched module
  2. Record the firing level in `STORIES.md` frontmatter as `foundation_source: declared | architecture | inferred | none-with-risk`
Don't:
  - Skip the cascade and pick foundations from chat intuition
  - Suppress the `none-with-risk` warning when shared modules exist
Exit:
  → [D] : foundation ordering determined and source recorded

### [D] — decompose into stories
Load: `references/slice-contract-fields.md`
Brief: One story = one validable outcome (one test verifies done). Granularity gates are hard. Field grammar, body section spec, and good/bad outcome phrasing live in the loaded reference.
Do:
  1. Map requirements (FR / acceptance / chat-intent goals) into candidate stories — many-to-many R↔story mapping permitted
  2. Apply granularity gates (thresholds in reference); refuse on HARD-floor violation, soft-cap exceeded without `file_cap_override`, trivial slice, >30 stories without `--confirm`, or 1-story decomposition (redirect to `code-build-planner`)
  3. Assign `slice_id = TAG-NNN` (zero-padded sequence) + kebab slug derived from outcome
  4. Populate slice-contract + planner-extension frontmatter per `references/slice-contract-fields.md`. Example outcome phrasing — GOOD: `"User can submit login form with valid credentials and receive a session token verified by tests/auth/test_login_form.py::test_valid_submission"`. BAD: `"Improve login UX"` (not testable as one assertion)
  5. Emit body sections in the order specified by the reference: Story / Context / Constraints from horizontal docs / Test scenarios / Out of scope
  6. Topologically sort `depends_on`; cycle detection. Cycle → refuse with the cycle named
Don't:
  - Emit `acceptance_summary` or `slug` frontmatter fields (forbidden — filename derives from `slice_id`; outcome carries acceptance)
  - Include the coding-contract rule body inline; reference protocol by name only
Exit:
  → [M] : N stories drafted, sorted, validated against granularity gates

### [M] — manifest + collision check
Load: `templates/STORIES.md`
Brief: Manifest is the orchestrator entrypoint, not individual story files.
Do:
  1. Compute `spec_hash` of the primary input doc (spec / PRD / canonicalised chat-intent)
  2. Build `STORIES.md` with frontmatter (`tag`, `foundation_source`, `spec_hash`) + ordered story-row table (story_id / depends_on / status / file_cap_override?)
  3. Cross-check: every `consumes`-style coupling in any story Context section names a `provides` story; refuse on dangling reference
  4. Write all story files + STORIES.md atomically (one batch); on any single-file failure, roll back the whole batch
Don't:
  - Name the manifest `INDEX.md` (basename collision with `.delivery/plan/INDEX.md`)
  - Skip the cross-check — dangling consumer references deadlock the orchestrator
Exit:
  → [END] : manifest + N story files written

### [END] — hand-off report
Do:
  1. Print: tag, story count, foundation_source, file paths, dependency graph summary
  2. Print orchestrator hand-off line: "Pass `STORIES.md` path to `/delivery-orchestration-plan-executor` to begin execution"
  3. Surface any `CONFLICT` blocks or `none-with-risk` warnings — do not bury
Don't:
  - Auto-dispatch the orchestrator — execution is a separate, user-confirmed step
  - End without reporting the dependency graph shape (linear / branched / has foundation prefix)
  - Bury warnings inside the rollup — `CONFLICT` blocks and `none-with-risk` flags surface at the top of the report

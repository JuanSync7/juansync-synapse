---
name: synapse-router-artifact-brainstormer
description: "Use when exploring an idea for a new artifact (skill, tool, agent, protocol) or reworking an existing one — before committing to build"
domain: synapse
subdomain: router
scope: artifact
role: brainstormer
tags: [brainstorm, coaching, multi-artifact]
user-invocable: true
argument-hint: "[idea, problem, or change request path]"
---

Thinking partner for artifact design. You discover whether ideas are artifact-worthy, pressure-test them through five lenses, and produce per-artifact memos for `*-creator` skills. Three valid outcomes: artifact (with memo), project config (with nudge), or not needed (saves maintenance). Each is a win.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## MUST (every turn)
- Update notepad BEFORE composing each response — stale notepads lose context
- Record position: `Position: [node-id] — <context>`
- Set `model:` explicitly on every subagent dispatch

## MUST NOT (global)
- Produce memo or design doc before Done Signal — early drafts contaminate with incomplete thinking
- Skip any lens during [B] rotation — all five per artifact, no exceptions
- Bulk-load lens files — load per-lens at moment of need (attention weight recency)
- Proceed at [N] without user-confirmed artifact name
- Drip-feed concerns at [A] — exhaustive opening inventory, not one-at-a-time

## Wrong-Tool Detection
- **Already knows what to build** → redirect to `/synapse-router-artifact-creator`
- **Has a finished skill to improve** → redirect to `/synapse-skill-skill-improver`
- **Wants promotion certification** → redirect to `/synapse-router-artifact-gatekeeper`

## Progress Tracking

At the start, create a task list:

```
TaskCreate: "Phase A: Session-level discovery + artifact inventory"
TaskCreate: "Phase B: Lens rotation across all artifacts"
TaskCreate: "Done Signal: Cross-artifact sweep + final verification"
TaskCreate: "Output: Design doc + N memos via subagent dispatch"
```

Mark each task `in_progress` when starting, `completed` when done.

## Entry

### [NEW] Fresh session
Load: templates/notepad.md, templates/meta.yaml
Do:
  1. Create brainstorm directory `.brainstorms/<YYYY-MM-DD>-<slug>/` + notepad + meta.yaml
  2. Wrong-tool check — redirect if user already knows what to build
  3. Check if target skill directory has `change_requests/` — read pending obligations
Don't: Start [A] without notepad initialized.
Exit: → [A]

### [RESUME] Paused session
Load: references/resume-protocol.md
Do: Read meta.yaml for position + artifact states, read notepad for thread context.
Don't: Assume previous context — always re-read both fresh.
Exit: → [A] | [B] | [D] (based on saved position in meta.yaml)

## Flow

### [A] Session-level: classify + inventory
Load: references/artifact-criteria-{type}.md (per discovered type)
Brief: Free-form discovery. Discuss the problem space, not individual artifacts.
Do:
  1. Classify brainstorm type + anticipated shape
  2. Opening inventory — exhaustive shallow list of all concerns
  3. Manage session-level sections: cross-cutting, process, open/orphaned
  4. When artifact crystallizes → route to [N] for focused exploration
  5. For skill-type artifacts: evaluate against design principles (context injection test, mental model test, hard-gate need)
Don't:
  - Discuss artifact-level details — that's [N]'s job
  - Skip wrong-tool check on each new concern
Exit:
  → [N] : artifact discovered, needs naming + exploration
  → [B] : inventory complete, user confirms artifact list, no unassigned open points
  → [X] : outcome is "not needed" or "project config" — no artifacts to design

### [N] Artifact focus: name + flesh out
Load: references/naming-conventions.md
Brief: Dedicated per-artifact exploration. Separate from session-level thinking.
Do:
  1. Confirm artifact type (agent, tool, protocol, skill)
  2. Suggest name from `{domain}-{subdomain?}-{purpose?}-{terminal}` pattern
  3. Validate domain + terminal against taxonomy file for artifact type
  4. Discuss + flesh out artifact until sufficient substance
  5. Create/update per-artifact notepad section (Resolved / Resolved not fleshed / Open / Memo-ready)
  6. Distill any session-level points that belong to this artifact
  7. If artifact type changes during exploration — update per-artifact section header, re-validate naming against new taxonomy, note the shift in Process section
Don't:
  - Proceed without user-confirmed name
  - Discuss session-level concerns — route back to [A]
Exit:
  → [N] : still fleshing out (self-loop)
  → [A] : artifact explored, more to discover
  → [B] : this was last artifact, inventory complete + user confirmed

### [B] Lens rotation
Load: references/lens-{current}.md (per-lens, always re-load), references/focus-rotation.md, references/circuit-breaker.md
Brief: Systematic pressure-test. One lens at a time, one artifact at a time.
Do:
  1. Select next artifact + next lens from rotation state (consult focus-rotation.md for type-specific lens prioritization)
  2. Apply lens diagnostic questions to artifact
  3. Update per-artifact section with findings
  4. Mark lens-complete when all 5 lenses pass for an artifact
  5. If new artifact discovered mid-rotation: coaching pushback → user confirms → route to [N]
  6. Monitor circuit breaker signals — if diminishing returns detected, surface to user before grinding further
Don't:
  - Mark artifact lens-complete without all 5 lenses (boundary → preciseness → robustness → maintenance → usability)
  - Bulk-load all lens files at [B] entry
  - Compress structural content — use `<!-- VERBATIM -->` markers
  - Pause to avoid hard pressure-testing — only pause when signal is genuinely low
Exit:
  → [B] : next lens / next artifact (self-loop)
  → [N] : new artifact discovered mid-rotation
  → [H] : ~10 turns since last hygiene check
  → [P] : circuit breaker fires on multiple artifacts or user requests pause
  → [D] : ALL artifacts marked lens-complete

### [H] Hygiene check
Load: references/hygiene-check.md
Do: Quick 1-turn scan — stale open points, forgotten artifacts, drifted threads, artifact table vs discussion state.
Don't: Turn into full lens rotation.
Exit: → [B] (resume where left off)

### [P] Pause
Load: references/circuit-breaker.md
Brief: Clean session suspension when signal is diminishing or user requests stop.
Do:
  1. Final notepad update — record every artifact's current state
  2. Update meta.yaml: `status: paused`, `position` to current node + context
  3. Surface what's still open — list artifacts with their unresolved items
Don't:
  - Produce memos or design doc — Pause is a suspend, not a completion
  - Pause to avoid hard pressure-testing (self-diagnostic: "avoiding work or genuinely low signal?")
Exit:
  → [END] : session suspended, user will resume later via [RESUME]

### [D] Done Signal
Load: references/done-signal-checklist.md, references/cross-artifact-sweep.md
Brief: Coach's honest judgment that no major flaws remain.
Do:
  1. Verify all artifacts marked lens-complete
  2. Final mandatory hygiene check
  3. Cross-artifact sweep: contract symmetry, orphan detection, circular dependency check
  4. Verify all per-artifact Open sections are empty
  5. Verify session-level open/orphaned resolved
  6. Registry check — read `registry/SKILL_REGISTRY.md` (if exists), surface overlaps
Don't:
  - Fire with any Open items remaining
  - Let user rush past unresolved gaps — push back with specific gaps named
Exit:
  → [O] : all preconditions met
  → [B] : gaps found — reopen specific artifacts

### [O] Output production
Load: agents/design-doc-producer.md, agents/memo-producer.md, templates/memo.md, templates/design-doc.md
Do:
  1. Dispatch design-doc-producer (1 instance, model: sonnet) — pass full notepad
  2. Dispatch memo-producer (N instances, model: sonnet, one per artifact) — pass full notepad + artifact name
  3. All dispatches in parallel
  4. Verify results via synapse-observability-failure-reporting-schema protocol
Don't:
  - Trim notepad content — cross-cutting decisions live outside artifact sections
  - Silently swallow subagent failures
Exit:
  → [END] : all subagents reported success
  → [D] : critical failure — reassess

### [X] Early exit (no artifact)
Brief: Idea evaluated and determined not artifact-worthy. This is a valid win.
Do:
  1. Update meta.yaml: `status: abandoned` or `status: deferred`, populate `reason`
  2. If "project config" — provide the concrete config nudge (e.g., "add this rule to CLAUDE.md: ...")
  3. If "not needed" — explain what Claude already does well without injection
  4. No memos, no design doc produced
Don't:
  - Produce output artifacts for a no-artifact outcome
  - Frame abandonment as failure — "not needed" saves maintenance overhead
Exit: → [END]

### [END]
Do:
  1. Update meta.yaml: status → done
  2. Present summary: design doc path, memo list (path + memo type per artifact), any warnings
  3. Call synapse-git-dispatch-cr tool (see `tools/synapse-git-dispatch-cr`) to create per-artifact feature branches from the placed CRs:
     `synapse-git-dispatch-cr.sh --date <YYYY-MM-DD> --slug <session-slug> [--design <design-doc-path>]`
     This creates `feature/<synapse>/<artifact-name>/<cr-slug>` branches from develop, commits each CR + design doc copy, and pushes to remote.
  4. Suggest next steps (prose, not deterministic routing)
Don't:
  - End without presenting full output summary
  - Auto-route to next skill
  - Skip branch creation — contributors need branches to open PRs

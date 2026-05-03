---
name: synapse-brainstorm
description: "Use when exploring an idea for a new artifact (skill, tool, agent, protocol) or reworking an existing one — before committing to build"
domain: skill.create
intent: plan
tags: [brainstorm, coaching, multi-artifact]
user-invocable: true
argument-hint: "[idea, problem, or change request path]"
---

Thinking partner for artifact design. You discover whether ideas are artifact-worthy, pressure-test them through five lenses, and produce per-artifact memos for `*-creator` skills. Three valid outcomes: artifact (with memo), project config (with nudge), or not needed (saves maintenance). Each is a win.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## Turn Protocol

Every turn proceeds in this order:

1. **Read** the user's message → identify which notepad sections need updates (Resolved / Open / Process / per-artifact) and what `position` should now read in `meta.yaml`.
2. **Edit** the notepad and `meta.yaml` to reflect the new state — including appending to `meta.yaml.artifacts[]` the moment an artifact crystallizes at [N] (use `name: TBD-<descriptor>` if naming is still pending). Do this *before* any response prose is composed.
3. **Compose** the response, drawing FROM the now-updated notepad.

The response is downstream of the notepad, not the other way around. Composing first and editing after means responding from stale state and then post-hoc documenting a decision the notepad didn't shape — which defeats the whole point of the brainstorm as a thinking-on-paper artifact.

**No-updates case:** if the user's turn requires no content updates (a simple confirmation, clarification, or meta-question), still update `meta.yaml.position` to advance the node + context string. There is no "protocol doesn't apply this turn" escape hatch — the position field is always live.

## MUST (every turn)
- Record position: `Position: [node-id] — <context>`
- Set `model:` explicitly on every subagent dispatch
- Ground against repo state — read existing skills, registries (`registry/SKILL_REGISTRY.md`, `registry/AGENTS_REGISTRY.md`, `registry/PROTOCOL_REGISTRY.md`), and relevant taxonomies before asking the user about overlap, naming, or convention. Reading is unprompted; asking is the fallback when reading can't resolve the question.

## MUST NOT (global)
- Produce memo or design doc before Done Signal — early drafts contaminate with incomplete thinking
- Skip any lens during [B] rotation — all five per artifact, no exceptions
- Bulk-load lens files — load per-lens at moment of need (attention weight recency)
- Proceed at [N] without user-confirmed artifact name
- Drip-feed concerns at [A] — exhaustive opening inventory, not one-at-a-time
- Fan out across artifacts in one turn — one artifact per turn during lens rotation; the rotation already enforces this, but never bundle lens questions for multiple artifacts in a single response
- Mix stances within a single lens application on a single artifact — pick one and stay in it for the move

## Stances

The agent operates in one of two stances per session (default: `collaborator`). Stance is recorded session-level in `meta.yaml` and may be overridden per-artifact in the notepad's per-artifact section.

| Stance | Behavior | When to use |
|---|---|---|
| **Socratic** | Agent asks lens-diagnostic questions, surfaces only options the user names or implies, never recommends a specific answer, never contributes original ideas. Pure facilitation. | Rare in artifact design. Use only when user explicitly wants to think out loud or is exploring a domain the agent doesn't know well. |
| **Collaborator** *(default — strong)* | Agent contributes original ideas the user hasn't named, takes stances on lens diagnostics, recommends answers with reasoning, defends or updates under pushback. The agent has substance (taxonomy, design principles, registry overlap, naming conventions) — withholding it is worse than offering it. | Default. The 5-lens completeness check + cross-artifact sweep at `[D]` prevents premature lock-in; tonal restraint is unnecessary. |

Rationale: artifact design is technical convergence work. The agent has objective ground truth (taxonomy violations, registry collisions, design principle compliance) that is wasted in pure Socratic mode. The collaborator default requires zero ceremony to fall into; Socratic is opt-in only when the user explicitly requests pure facilitation.

External research (web, docs sites, other repos) is opt-in via user confirmation in either stance. Propose the search; do not fire without confirmation. In-repo grounding (see MUST every turn) is unconditional and unprompted.

## Wrong-Tool Detection
- **Already knows what to build** → redirect to `/skill-creator`
- **Has a finished skill to improve** → redirect to `/improve-skill`
- **Wants promotion certification** → redirect to `/synapse-gatekeeper`

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
  2. Stance defaults to `collaborator`. If the user explicitly requests pure facilitation ("just ask me questions", "I want to think this through myself"), set `stance: socratic` and cache in `meta.yaml`. Otherwise, no gate question — proceed in collaborator mode.
  3. Opening inventory — exhaustive shallow list of all concerns
  4. Manage session-level sections: cross-cutting, process, open/orphaned
  5. When artifact crystallizes → route to [N] for focused exploration
  6. For skill-type artifacts: evaluate against design principles (context injection test, mental model test, hard-gate need)
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
  2. **Pre-move dependency check** — before beginning lens rotation on an artifact, scan in-flight artifacts for prospective dependencies. If this artifact's design depends on another in-flight artifact's outcome (e.g., skill A's contract assumes protocol B's shape), work the predecessor first. Record the dependency edge in the notepad's per-artifact section (`depends_on: [<artifact-name>, ...]`); record lateral conflicts as bidirectional `conflicts_with` annotations on both artifacts.
  3. Apply lens diagnostic questions to artifact, per active stance:
     - **Collaborator stance** (default): surface lens diagnostics paired with recommended answers and reasoning. Take stances on tradeoffs (e.g., "preciseness lens: the description should focus on trigger conditions over workflow summary; here's a draft"). Update or defend under user pushback. Lens rotation is converging — pure question-mode delays convergence.
     - **Socratic stance**: surface lens diagnostics as questions only. No recommended answers. The user reasons out the answer; the agent confirms or probes deeper.
  4. **Batching policy:**
     - *Within one artifact:* batch lens questions freely. Multiple angles on one artifact deepen the design — this is the move.
     - *Across artifacts in one turn:* don't fan out. Stay on one artifact per turn. Different artifact = next turn.
     - *Within a batch:* if Q2 depends on Q1's answer, serialize. Independent questions may batch freely.
  5. Update per-artifact section with findings
  6. Mark lens-complete when all 5 lenses pass for an artifact
  7. If new artifact discovered mid-rotation: coaching pushback → user confirms → route to [N]
  8. Monitor circuit breaker signals — if diminishing returns detected, surface to user before grinding further
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
  3. Cross-artifact sweep: contract symmetry, orphan detection, circular dependency check, **and dependency-edge validation — if A `depends_on` B and B was reframed during the session, mark A `open` again and re-run lens rotation for A**
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
  4. Verify results via failure-reporting protocol
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
  3. Call synapse-cr-dispatcher tool (see `tools/synapse-cr-dispatcher`) to create per-artifact feature branches from the placed CRs:
     `synapse-cr-dispatcher.sh --date <YYYY-MM-DD> --slug <session-slug> [--design <design-doc-path>]`
     This creates `feature/<synapse>/<artifact-name>/<cr-slug>` branches from develop, commits each CR + design doc copy, and pushes to remote.
  4. Suggest next steps (prose, not deterministic routing)
Don't:
  - End without presenting full output summary
  - Auto-route to next skill
  - Skip branch creation — contributors need branches to open PRs

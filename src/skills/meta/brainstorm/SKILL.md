---
name: brainstorm
description: "Use when the user asks to think through, explore, or debate a non-trivial question before committing to execution — phrases like 'help me think through,' 'should I,' 'I'm debating,' 'I have an idea for,' 'I'm not sure how to approach.' Does not fire on factual questions, on requests with a clear direction already, or on skill-design topics."
domain: meta
intent: plan
tags: [brainstorm, coaching, ideation, decision-making, mentor]
user-invocable: true
argument-hint: "[topic or question to explore]"
---

A structured brainstorm protocol for thinking through open questions before committing to execution. You are a coach, board member, or team member the user must reach agreement with — not a yes-man, not a drip-feeder. Named coaching moves as a fully-connected subgraph, an indexed two-zone notepad as living working memory, and a mentor-style circuit breaker that knows when to pause. Each session produces a decision memo (or a valid "not worth pursuing" exit).

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## MUST (every turn)
- Update notepad BEFORE composing each response — stale notepads lose context
- Record position: `Position: [node-id] — <context>`
- Check lens gate (Stakeholder ✓ + Alternative ✓) before any [B:Agree]

## MUST NOT (global)
- Produce memo before Done Signal — early drafts contaminate with incomplete thinking
- Skip lenses — all 4 selected lenses must rotate against each open thread
- Agree without lens gate — cheerleader drift
- Drip-feed concerns at [A] — exhaustive opening inventory, not one-at-a-time

## Wrong-Tool Detection

- **Skill-shaped topic** (mentions "skill," "SKILL.md," slash command, agentic behavior, "make this a skill") → redirect to `/synapse-brainstorm`
- **User has a clear spec/plan/direction already** (nothing left to decide) → redirect to the appropriate implementation skill. *Direction-based, not verb-based: "build a dashboard" with no direction IS a brainstorm; "implement this spec" with a concrete spec is not.*
- **Factual question with a definite answer** → answer directly; do not brainstorm
- **Specific concrete bug with a clear failure trace** → debug directly; brainstorm only fires when root cause is architectural
- **End-to-end pipeline request** ("brainstorm → spec → code → docs") → redirect to `/autonomous-orchestrator`

## Out of Scope

This skill does NOT:
- Perform formal decision analysis (weighted criteria matrices, MCDA, quantitative ranking)
- Facilitate multi-stakeholder sessions — it's a single-user tool
- Fetch or synthesize external research — user brings context in
- Produce the decided artifact (spec, plan, code) — stops at memo
- Drive end-to-end pipelines — use `/autonomous-orchestrator`

## Coexistence with Built-In `brainstorm` Stage

`SKILLS_REGISTRY.yaml` declares a built-in `brainstorm` stage executed internally by `/autonomous-orchestrator`. That stage and this user-invocable skill share a name but not an implementation. If invoked by the orchestrator, the built-in stage runs; if invoked by the user via `/brainstorm`, this skill runs.

## Progress Tracking

At the start of every session, create a task list:

```
TaskCreate: "Phase A: classify + Opening Inventory + consent"
TaskCreate: "Phase B: coaching moves + lens rotation + thread resolution"
TaskCreate: "Done Signal + memo"
```

Mark each `in_progress` when starting, `completed` when done.

## Entry

### [NEW] Fresh session
Load: references/coaching-policy.md, templates/notepad.md, templates/memo.md, templates/meta.yaml
Do:
  1. Create brainstorm directory `.brainstorms/<YYYY-MM-DD-<slug>>/` + notepad + meta.yaml
  2. Wrong-tool check — redirect if any collision point fires
  3. Persistence: project-local (`.brainstorms/`) or global fallback (`~/.claude/brainstorms/`)
Don't: Start [A] without notepad initialized.
Exit: → [A]

### [RESUME] Paused session
Load: references/resume-protocol.md
Do: Read meta.yaml for position + thread states, read notepad fresh for full context.
Don't: Assume previous context — always re-read both fresh.
Exit: → [A] | [B:*] | [D] (based on saved position in meta.yaml)

## Flow

### [A] Classify + Opening Inventory + Gate
Load: references/wrong-tool-detection.md, references/brainstorm-types.md
Brief: Classify the topic, surface all concerns upfront, gate before Phase B.
Do:
  1. Wrong-tool check — run through the 5 collision points. Redirect if any fires.
  2. Lightweight check — if ≤3 concerns, offer quick take vs full protocol
  3. Classify (type, shape) — decision / exploratory / problem / creative / planning
  4. Opening Inventory — exhaustive shallow list of every major concern in one message
  5. Preview memo shape — tell user what they're getting
  6. Phase A Gate — name all thread IDs entering Phase B, announce transition
Don't:
  - Drip-feed concerns — the complete map goes in one message
  - Skip wrong-tool check
  - Offer to continue when a wrong-tool collision fires — redirect is a hard gate, not a suggestion
Exit:
  → [B:Generate] : Phase A Gate passed, threads established — begin coaching moves
  → [X] : topic resolved during discovery (quick take accepted, or "not worth pursuing")

### [B:Generate]
Brief: Surface candidate options, hypotheses, angles, or new concerns.
Do:
  1. Check if the thread's option space is actually empty before generating
  2. Surface options as questions, not prescriptions — maintain anchoring guard
  3. New concern from user tangent (side-quest) → open as new thread, note turn number
Don't:
  - Generate when the thread already has sufficient options — route to [B:Pressure-test]
  - Present one option as the obvious answer (anchoring guard)
Exit:
  → [B:Pressure-test] : options surfaced, ready to evaluate
  → [B:Generate] : more options needed (self-loop)
  → [B:Reframe] : generation reveals the question itself is wrong
  → [B:Circle-back] : thread tracking cloudy after generation burst
  → any [B:*] node

### [B:Pressure-test]
Load: references/lens-catalog.md (re-load for attention weight)
Brief: Evaluate existing options/decisions against selected lenses. The evaluative move.
Do:
  1. Apply one lens at a time to the thread — record which lens in notepad
  2. Track lens rotation state: which thread, which lens, which threads are lens-complete
  3. Surface findings as diagnostic questions, not verdicts
  4. Lens selection: 4 per session = 2 universal (Stakeholder, Alternative) + 2 type-specific
Don't:
  - Apply lenses not in the session's selected 4 (unless user explicitly requests ad-hoc)
  - Skip to [B:Agree] before both universal lenses (Stakeholder + Alternative) are applied
Exit:
  → [B:Agree] : thread survived required lenses, ready to lock
  → [B:Generate] : lens surfaced a gap, need options first
  → [B:Pressure-test] : next lens on same thread (self-loop)
  → [B:Reframe] : pressure-test reveals the question is wrong
  → [B:Decompose] : thread too big to evaluate as one unit
  → any [B:*] node

### [B:Agree]
Brief: Explicit convergence — lock a thread as resolved.
Do:
  1. Check lens gate: both universal lenses (Stakeholder + Alternative) applied to this thread
  2. Produce visible gate confirmation: `Stakeholder ✓ T[n], Alternative ✓ T[n] — gate passes`
  3. If gate fails, produce `Stakeholder ✗ T[n]` or `Alternative ✗ T[n]` — route to [B:Pressure-test]
  4. Record resolution in notepad: thread → resolved, turn number, reason
Don't:
  - Agree without lens gate — this is cheerleader drift
  - Agree to avoid conflict — rationality over agreeableness
  - Agree on behalf of the user — they must confirm
Exit:
  → [B:Pressure-test] : lens gate failed, apply missing lenses
  → [B:Generate] : agreement surfaces a new concern on another thread
  → [B:Circle-back] : good moment to sweep state after resolving a thread
  → [D] : all threads now in terminal state
  → any [B:*] node

### [B:Reframe]
Brief: Shift the question itself when the current framing is wrong.
Do:
  1. Name the reframe explicitly — old question vs new question
  2. Update affected threads: rewrite, discard dissolved threads, spawn new open threads
  3. If reframe changes session direction: update (type, shape) in meta.yaml, adjust lens subset
  4. Note classification drift in notepad Process section
Don't:
  - Reframe without surfacing to user — they must agree the old framing was wrong
  - Reframe as avoidance — only when pressure-testing genuinely reveals the question is wrong
Exit:
  → [B:Generate] : new framing needs options
  → [B:Pressure-test] : new framing needs evaluation
  → [B:Circle-back] : reframe may have invalidated prior thread resolutions
  → any [B:*] node

### [B:Decompose]
Brief: Split a thread that is too big for a single decision.
Do:
  1. Parent thread → status `decomposed`
  2. Create child threads as `open` (use dotted IDs: T5a, T5b, T5c)
  3. Parent cannot reach Done Signal until all children are terminal
Don't:
  - Decompose threads that are just complex — only split genuinely independent sub-decisions
  - Lose the parent-child relationship in the notepad
Exit:
  → [B:Generate] : children need options
  → [B:Pressure-test] : children need evaluation
  → [B:Circle-back] : verify decomposition didn't orphan anything
  → any [B:*] node

### [B:Circle-back]
Brief: Procedural sweep — walk notepad thread-by-thread, confirm status.
Do:
  1. Read notepad fresh — full read, not skimming
  2. Walk every thread: state, lenses applied, dependencies, staleness
  3. Surface forgotten threads, drifted decisions, stale open items
  4. Check cross-thread dependencies: T-A resolved assuming T-B, but T-B later reopened?
Don't:
  - Turn into a full lens rotation — this is a sweep, not pressure-testing
  - Skip the final mandatory Circle-back before [D]
Exit:
  → [B:Pressure-test] : sweep found threads needing lens work
  → [B:Generate] : sweep found gaps needing options
  → [B:Agree] : sweep confirms threads are ready to lock
  → [D] : all threads terminal, sweep clean — fire Done Signal
  → any [B:*] node

### [B:Pause]
Load: references/mentor-circuit-breaker.md
Brief: Suspend when signal is diminishing or user requests stop.
Do:
  1. Self-diagnostic: "Am I pausing because signal is low, or because this is uncomfortable?"
  2. Surface observation to user with options: (a) new angle, (b) need external input, (c) mark deferred
Don't:
  - Pause to avoid hard threads — do the work
  - Auto-pause without surfacing to user
Exit:
  → [B:Pressure-test] : user provided new angle (option a)
  → [B:Generate] : user reframed the problem
  → [P] : user confirmed full session pause
  → any [B:*] node

### [H] Hygiene check
Load: references/hygiene-check.md
Brief: Quick 1-turn scan at ~10-turn cadence during Phase B.
Do:
  1. Read notepad fresh
  2. Scan for: stale open threads, forgotten threads, drifted decisions, lens rotation state accuracy
  3. Surface what's stale/forgotten/drifted
Don't: Turn into full lens rotation — hygiene identifies problems, doesn't fix them.
Exit: → [B:*] (resume at appropriate move to address findings)

### [P] Pause
Load: references/mentor-circuit-breaker.md
Brief: Clean session suspension when signal is diminishing or user requests stop.
Do:
  1. Final notepad update — record every thread's current state
  2. Update meta.yaml: `status: paused`, `position` to current node + context
  3. Surface what's still open — list threads with their unresolved items
Don't:
  - Produce memo — Pause is a suspend, not a completion
Exit:
  → [END] : session suspended, user will resume later via [RESUME]

### [D] Done Signal
Brief: Coach's honest judgment that no major flaws remain.
Do:
  1. Every thread has terminal status (`resolved` / `discarded` / `deferred` / `decomposed`). No `open` threads.
  2. Final Circle-back sweep completed (includes hygiene scan) — walked notepad thread-by-thread and confirmed status.
  3. Last lens pass surfaced no first-order concerns.
  4. Cross-thread dependency sweep: no circular deps, no orphans, no resolved-assuming-reopened.
  5. If multi-memo offered and accepted: per-thread sections self-contained enough to distill.
Don't:
  - Fire with any open threads remaining
  - Let user rush past unresolved gaps — push back with specific gaps named
Exit:
  → [MEMO] : all preconditions met
  → [B:*] : gaps found — reopen specific threads

### [MEMO] Output
Load: templates/memo.md
Brief: Produce decision memo from notepad. Shape-specific sections.
Do:
  1. Distill notepad into `memo.md` — shape-specific structure (see templates/memo.md)
  2. Include prose "you might consider X next" suggestion — no deterministic shape→skill map
  3. If type is planning/decompose AND threads are deliverable-shaped (named after files/components/modules), offer: *"Want individual memos for each, or a single summary?"* Coach judges by thread title + content, not a rule.
  4. No-artifact outcomes (Defer, Abandon) produce a status note in meta.yaml, not a full memo — valid wins.
Don't:
  - Auto-split into per-thread memos — always offer the choice
  - Produce memo before [D] fires
Exit: → [END]

### [X] Early exit (no brainstorm needed)
Brief: Topic resolved during discovery or determined not worth pursuing.
Do:
  1. Update meta.yaml: `status: abandoned` or `status: deferred`, populate reason
  2. If quick take was accepted — provide the take with tradeoffs
  3. If "not worth pursuing" — explain why and frame as a valid win
Don't:
  - Produce a full memo for a non-brainstorm outcome
  - Frame abandonment as failure
Exit: → [END]

### [END]
Do:
  1. Update meta.yaml: status → done (or abandoned/deferred)
  2. Present summary: memo path (if produced), session path, any warnings
  3. Suggest next steps (prose, not deterministic routing)
Don't:
  - End without presenting output summary
  - Auto-route to next skill

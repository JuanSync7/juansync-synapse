# brainstorm — Evaluation Criteria

> **Execution scope:** This file is ignored during skill execution — it is read only by `/improve-skill` and evaluation workflows.

## Structural Criteria

Covered by `/improve-skill` baseline checklist — not duplicated here. Structural checks include: frontmatter validity, domain/intent in TAXONOMY, companion file presence, SKILL.md length under 500 lines, Wrong-Tool Detection section, Execution Scope fence.

## Output Criteria

Binary pass/fail criteria catching the specific failure modes this skill is designed to prevent. Every criterion must be testable by inspecting session artifacts (notepad.md, memo.md, meta.yaml) or the conversational flow.

### EVAL-O01
**Criterion:** Opening Inventory is produced as a single exhaustive list in Phase A, not drip-fed across multiple turns.
**Pass:** The complete set of major concerns is presented in one message during Phase A; no new first-order concerns appear in Phase B without an explicit admission.
**Fail:** Concerns are introduced piecemeal across Phase B turns without being named in the Phase A inventory, and no admission protocol fires.
**Rationale:** Catches the drip-feed failure mode where the coach withholds concerns to seem responsive rather than mapping the full problem upfront.

### EVAL-O02
**Criterion:** When a first-order concern surfaces in Phase B, the notepad's "Phase A Misses" section contains an explicit admission entry including what was missed, the turn it surfaced, and which prior threads were flagged for re-examination.
**Pass:** The "Phase A Misses" section exists and contains a dated, turn-numbered entry with a downstream sweep note.
**Fail:** A Phase B first-order concern appears in the threads but the "Phase A Misses" section is empty or absent.
**Rationale:** Without the admission record, the admission protocol is unenforceable and drip-feeding cannot be detected in artifacts.

### EVAL-O03
**Criterion:** Every thread resolved via the `Agree` move has both "Stakeholder ✓" and "Alternative ✓" listed under "Lenses applied" in the notepad before its status transitions to `resolved`.
**Pass:** All `resolved` threads show both universal lenses applied prior to or at the resolution turn.
**Fail:** Any `resolved` thread shows `resolved` status without both universal lens checkmarks in the notepad.
**Rationale:** Catches cheerleader drift — `Agree` used as a rubber-stamp without the required evaluative gate.

### EVAL-O04
**Criterion:** A final Circle-back move is documented in the conversation or notepad before the memo is produced.
**Pass:** The coach explicitly walks every thread by ID and confirms its terminal status in a Circle-back pass immediately before announcing Done Signal.
**Fail:** The memo is produced without any explicit thread-by-thread Circle-back sweep in the turn sequence immediately preceding it.
**Rationale:** Catches the omission where the coach produces a memo without confirming every thread's status, leaving unresolved work silently dropped.

### EVAL-O05
**Criterion:** Every thread in the notepad has an indexed ID in the format T1, T2, ... (or T5a, T5b for decomposed children).
**Pass:** All threads are addressable by T-ID; no thread appears with only a title or description and no ID.
**Fail:** Any thread lacks a T-ID, or uses a non-standard identifier.
**Rationale:** Without indexed IDs, Circle-back sweeps cannot reference threads unambiguously, and the resolution log becomes unverifiable.

### EVAL-O06
**Criterion:** The memo's content structure matches the shape declared in `meta.yaml` and the memo's own header.
**Pass:** A `Decision`-shaped memo contains Question / Options Considered / Tradeoffs / Recommendation / Rationale / Risks sections. A `Plan`-shaped memo contains Goal / Steps / Sequencing Rationale / Known Risks / Success Criteria. Shape-specific sections are present and populated.
**Fail:** The memo uses a generic structure (e.g., bullet list of outcomes) that does not match the declared shape, or shape-specific required sections are missing.
**Rationale:** Catches shape mismatch where the coach classifies the session correctly but produces a generic memo that ignores the shape-specific template.

### EVAL-O07
**Criterion:** The memo is not produced until all three Done Signal conditions are met: (1) no `open` threads in the notepad, (2) a final Circle-back sweep is completed, (3) the last lens pass surfaced no first-order concerns.
**Pass:** At the turn the memo is produced, the notepad contains zero `open` threads, and a Circle-back has been completed in that session.
**Fail:** The memo appears while any thread is still `open` in the notepad, or before any Circle-back has been run.
**Rationale:** Catches premature memo production — the most visible form of protocol failure.

### EVAL-O08
**Criterion:** When the skill receives a factual question (e.g., "What does TCP stand for?"), it does not run the brainstorm protocol and instead redirects or answers directly.
**Pass:** The coach answers directly or redirects without launching Phase A, creating session artifacts, or producing a notepad.
**Fail:** The coach initiates Phase A, creates a notepad, or generates an Opening Inventory for a factual question.
**Rationale:** Catches wrong-tool false positive where the skill fires on inputs that should never enter the brainstorm protocol.

### EVAL-O09
**Criterion:** When the input is a skill-shaped topic (mentions "skill," "SKILL.md," slash command, or agentic behavior), the coach redirects to `/synapse-brainstorm` without running the brainstorm protocol.
**Pass:** The response contains a redirect to `/synapse-brainstorm` and no Phase A work is performed.
**Fail:** The coach runs Phase A on a skill-shaped topic instead of redirecting.
**Rationale:** Catches wrong-tool false positive on skill-design inputs that belong to a sibling skill.

### EVAL-O10
**Criterion:** When the user pushes to end the session early but Done Signal conditions are not met, the coach refuses and names the specific unmet condition.
**Pass:** The coach explicitly names the blocking condition (e.g., "T3 is still open") and declines to produce the memo.
**Fail:** The coach produces the memo in response to user pressure despite an unmet Done Signal condition, without naming the gap.
**Rationale:** Catches sycophantic capitulation that bypasses the Done Signal gate.

### EVAL-O11
**Criterion:** When the circuit breaker fires and the `Pause` move is used, `meta.yaml` shows `status: paused`, `pause_reason` is populated, and `open_threads_at_pause` lists the IDs of threads that were open at the time of pause.
**Pass:** All three fields (`status: paused`, `pause_reason`, `open_threads_at_pause`) are populated in `meta.yaml` at session end.
**Fail:** `meta.yaml` still shows `status: active`, or `pause_reason` is empty, or `open_threads_at_pause` is an empty list when threads were open.
**Rationale:** Catches the Pause protocol violation where the session suspends without leaving a clean, resumable state.

### EVAL-O12
**Criterion:** The notepad is updated before the coach composes each response (not retroactively after).
**Pass:** Each notepad version is consistent with the state described in the response it precedes; no response references a thread state that appears in the notepad only in a later turn.
**Fail:** A response describes a thread as `resolved` but the notepad still shows it as `open` in that same turn's snapshot.
**Rationale:** Catches the stale-notepad failure mode where the notepad drifts from the actual session state, corrupting the eventual memo distillation.

### EVAL-O13
**Criterion:** For `Defer` and `Abandon` outcome shapes, no `memo.md` is produced; only a status note appears in `meta.yaml`.
**Pass:** `memo.md` is absent; `meta.yaml` contains a populated `shape` field of `Defer` or `Abandon` with a brief reason.
**Fail:** A full `memo.md` is produced for a `Defer` or `Abandon` outcome, or `meta.yaml` contains no record of the outcome.
**Rationale:** Catches over-production where the coach generates a full memo for a no-memo outcome, adding noise and misrepresenting the session result.

### EVAL-O14
**Criterion:** The Phase A Gate announcement names all thread IDs that will be worked in Phase B.
**Pass:** The Phase A Gate transition message includes a list of thread IDs (e.g., "Entering Phase B — threads: T1, T2, T3").
**Fail:** The Phase A Gate is announced without naming any thread IDs, or Phase B begins without any gate announcement.
**Rationale:** Without named threads at gate, there is no baseline against which to detect drip-fed Phase B concerns or verify Circle-back completeness.

### EVAL-O15
**Criterion:** The lens selection in the session consists of exactly 4 lenses: 2 universal (Stakeholder + Alternative) plus 2 type-specific lenses from the lens catalog for the classified brainstorm type.
**Pass:** The notepad records exactly 4 lenses applied across the session; Stakeholder and Alternative are among them.
**Fail:** Fewer than 4 lenses are used, Stakeholder or Alternative is absent, or more than 4 lenses are rotated without an explicit user request to pull an additional lens.
**Rationale:** Catches lens under-use (coverage gaps) and lens proliferation (unfocused evaluation) within the same criterion.

### EVAL-O16
**Criterion:** The memo's "You might consider next" section is prose and does not use a deterministic shape-to-skill mapping table or flowchart.
**Pass:** The section contains a prose sentence or short paragraph with a conditional suggestion (e.g., "If you want to...").
**Fail:** The section presents a lookup table, decision tree, or unconditional directive mapping the memo shape to a specific skill.
**Rationale:** Catches over-mechanization of the handoff — the skill explicitly prohibits a deterministic map and requires the user to retain ownership of next steps.

### EVAL-O17
**Criterion:** When `meta.yaml` shows `status: active` or `status: paused` for an existing session with a matching slug at session start, the coach offers a resume-or-start-fresh choice before proceeding.
**Pass:** The coach's first message presents the existing session and asks the user to choose between resuming and starting fresh.
**Fail:** The coach overwrites or ignores the existing session and starts Phase A without offering a resume option.
**Rationale:** Catches resume-flow violations that silently destroy in-progress session state.

### EVAL-O18
**Criterion:** For a small-scope topic (single question, ≤3 concerns in the Opening Inventory), the coach offers the lightweight-check option before running the full protocol.
**Pass:** The coach's Phase A message includes an offer: "This is a small one — want a quick take with tradeoffs, or the full protocol?"
**Fail:** The coach runs the full two-phase protocol on an obviously small-scope topic without offering the lightweight alternative.
**Rationale:** Catches over-engineering of simple inputs — the protocol has an explicit lightweight path that should surface before committing the user to a full session.

### EVAL-O19
**Criterion:** The memo's "Tradeoffs" section (for Decision shape) references only lenses that were actually applied to the relevant threads in the notepad.
**Pass:** Every lens row in the Tradeoffs table corresponds to a lens listed as applied in at least one thread's "Lenses applied" field.
**Fail:** The Tradeoffs table contains a lens row (e.g., "Reversibility") for which no thread in the notepad shows that lens applied.
**Rationale:** Catches fabricated tradeoff analysis — the memo claiming evaluation that never occurred in the session.

### EVAL-O20
**Criterion:** When the brainstorm type drifts mid-session (e.g., from `decision` to `reframe`), `meta.yaml` is updated to reflect the new `(type, shape)` and the notepad contains a note recording the shift.
**Pass:** `meta.yaml` `type` and `shape` fields match the final session classification; the notepad contains at least one sentence noting the classification change and the turn it occurred.
**Fail:** `meta.yaml` still shows the original classification at session end, or the drift is visible in thread content but no drift note appears anywhere in the artifacts.
**Rationale:** Catches silent classification drift — the session evolved but the metadata still describes the original framing, making the memo's shape interpretation unreliable.

## Test Prompts

### Naive (should invoke brainstorm)
- "help me think through whether I should quit my job to start a company — I have savings but also a mortgage"
- "I have an idea for a mobile app that helps people track their habits but I'm not sure if it's actually worth building"
- "I'm debating whether to rewrite our backend in Go or just keep iterating on the Python monolith — no idea where to start thinking about it"
- "should I move to a new city for this job offer or stay where I am — I honestly can't figure it out"

### Experienced (should invoke brainstorm)
- "I want to think through the tradeoffs between event sourcing and a traditional CRUD model for a financial audit system — walk me through the decision space before we commit to an architecture"
- "help me explore whether we should build a multi-tenant SaaS platform from the start or launch single-tenant and migrate later — I'm weighing GTM speed against technical debt accumulation"
- "I'm not sure how to approach consensus in our distributed system — we have strong consistency requirements but can't afford Paxos latency. walk me through the problem space"

### Adversarial (should NOT invoke brainstorm — skill must refuse/redirect)
- "what's the capital of France and also the year the Eiffel Tower was built" — expected: direct answer, no brainstorm
- "write me a REST API for user authentication with JWT tokens, refresh token rotation, and rate limiting" — expected: implementation skill or direct execution
- "there's a bug in my React component where the useEffect fires twice on mount — how do I fix it" — expected: direct debugging
- "I've decided we're going with Kubernetes — now help me set up the cluster" — expected: direct execution (direction already committed)

### Wrong-tool (should redirect to specific sibling)
- "I have an idea for a skill that helps developers write better commit messages — I'm not sure if it should be one skill or two, or what the phases would look like" — expected: `/synapse-brainstorm`
- "I want to build a feature end-to-end — from figuring out the approach all the way through specs, design, and implementation. help me think through the whole pipeline" — expected: `/autonomous-orchestrator`
- "should I add a wrong-tool detection section to this skill I'm writing, or is the description enough to prevent misfires?" — expected: `/synapse-brainstorm`

## Skill Classification

**Type:** Discipline-enforcing + Pattern (hybrid)

**Primary failure mode:** Agent rationalizes past the Opening Inventory rule under pressure (drip-feeds to seem responsive instead of mapping the full problem upfront). Secondary: agent skips Circle-back or Pressure-test before Agree when session runs long.

**Coverage check:** EVAL-O01, EVAL-O02, EVAL-O03, EVAL-O04, EVAL-O07 directly test the primary failure mode. Adequate coverage.

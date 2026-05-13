# flow-protocol.md

Protocol creation flow for `synapse-router-artifact-creator`. Loaded after `[ROUTE]` when `$TYPE=protocol`. Preserves protocol-creator's AXI4-style imperative-rules character: precise triggers, no rationalization escapes, single-interaction-point validation.

**Loading discipline (invariant):** This file is the ONLY flow active in this session. Never load another flow file.

---

### [START] — pre-flight

Load: `references/shared-steps.md`

Brief: All validations run before any file is written. If any pre-flight check fails, nothing is scaffolded — atomic creation by construction.

Do:
1. Run `→ shared-steps:placement-decision(protocol)` — default `src/protocols/`; prompt only if user explicitly requests `synapse/protocols/`
2. Run `→ shared-steps:validate-frontmatter(protocol, $artifact_dir)` — required fields, taxonomy values, name uniqueness
3. **Decision memo check:** If user provides a memo from `/synapse-router-artifact-brainstormer`, read it. Evaluate against Phase 1 gate below. If all 4 anchors are concrete and unambiguous, skip to `[A]`. Otherwise use memo as starting point and fill gaps.

Don't:
- Scaffold any file before all pre-flight validations pass
- Proceed with a partially-answered anchor set — vague anchors produce vague contracts

Exit:
- Pre-flight pass → `[A]`
- Pre-flight fail → fail loudly; report which check failed; leave zero state

---

### [A] — elicit precision anchors

Brief: A protocol is a function: trigger is the call site, contract is the body, failure assertion is the try/except. Extract four precision anchors before drafting. Each MUST have a concrete, unambiguous answer.

Do:
1. Extract:
   | Anchor | Question | Bad-answer signal |
   |--------|----------|-------------------|
   | **Behavior** | What behavior are you enforcing? | "Better code quality" — too vague |
   | **Trigger moment** | When exactly must it fire? | "When appropriate" — will never fire |
   | **Compliance signal** | What does compliance look like? | "Good output" — not observable |
   | **Violation signal** | How do you detect the LLM skipped it? | "The output is wrong" — too vague |
2. **Single-concern check:** If intent spans multiple independent behaviors — split. Test: "If I removed behavior A, would behavior B still make sense alone?" If yes → separate protocols.
3. **Duplicate check:** Read `PROTOCOL_REGISTRY.md`; surface overlaps; let user decide: differentiate, merge, or abandon.
4. Pick `domain` and `type` from `taxonomy/PROTOCOL_TAXONOMY.md`. If nothing fits, propose an addition — do not invent ad hoc values.

Don't:
- Proceed if any anchor is vague or missing
- Guess through ambiguity — ask a specific question for each gap

Gate — all must be true before exiting:
- [ ] All 4 precision anchors have concrete, unambiguous answers
- [ ] Single-concern confirmed
- [ ] No unresolved duplicate in PROTOCOL_REGISTRY.md
- [ ] `domain` and `type` selected from PROTOCOL_TAXONOMY.md

Exit: gate passed → `[W]`

---

### [W] — draft and scaffold

Load: `references/design-principles-protocol.md`, `references/banned-words-protocol.md`, `templates/protocol/`

Brief: Write the protocol file and companion scaffold in one operation. Load design principles before drafting — each principle traces to a failure mode. Apply banned-words check inline during drafting.

Do:
1. **Draft the protocol `.md` file** under `$artifact_dir/<protocol-name>.md` following universal anatomy:

   **Frontmatter:**
   ```yaml
   ---
   name: <protocol-name>
   description: "<trigger/routing contract — when this fires, not what it does>"
   domain: <from PROTOCOL_TAXONOMY.md>
   type: <from PROTOCOL_TAXONOMY.md>
   tags: [<lowercase, hyphenated>]
   ---
   ```
   `description` is a routing contract: specifies WHEN the protocol fires. If the description replaces reading the body, it's too broad.

   **Mental model:** One paragraph. Explains WHY this protocol exists — the behavioral gap it fills and what goes wrong without it. MUST NOT restate contract rules or describe workflow.

   **Contract:** Imperative rules. Every instruction MUST:
   - Use commitment language: MUST, NEVER, STOP, BEFORE, AFTER, THEN, DO NOT
   - Name a specific trigger moment — NEVER "when appropriate"
   - Contain zero banned words (check against `references/banned-words-protocol.md`)
   - Define a trigger, state a constraint, or specify an output format — no other sentence type

   If the contract produces structured output, define the exact format as an instruction: "AFTER completing X, APPEND this block."

   **Failure Assertion (mandatory):** When the trigger fires but preconditions aren't met, instruct:
   ```
   PROTOCOL FAILURE: <protocol-name> — [specific reason]
   ```
   Follows tag format in `synapse/protocols/observability/synapse-observability-failure-reporting-schema.md`.

   **Configuration (optional):** Only if the protocol has modes. Each mode MUST have a default. Delete if no modes.

   **What NEVER to include:**
   - Injection Instructions — the consumer knows how to load protocols
   - Examples section — if the contract needs an example, rewrite the instruction
   - Consumers section — discovery belongs in PROTOCOL_REGISTRY.md
   - Trigger section — trigger lives in the frontmatter `description`

   **Line budget:** 30–120 lines including frontmatter. Over 120 means multiple concerns or explanatory prose in the contract — split or trim.

2. Use `templates/protocol/skeleton.md` as the output structure. Use `templates/protocol/example.md` as a worked reference for what success looks like.

3. Run `→ shared-steps:write-registry-row(protocol, $meta)`
4. Run `→ shared-steps:update-domain-readme(protocol, $domain, $meta)`
5. Run `→ shared-steps:status-draft-mark(protocol, $meta)`

Don't:
- Partially scaffold — all files or none within this phase
- Include banned words in Contract or Failure Assertion sections
- Accept a Mental Model that restates the contract

Exit: all scaffold files written, registry row appended, README row inserted → `[R]`

---

### [R] — signal-strength review

Load: `agents/protocol/synapse-protocol-signal-reviewer.md`

Brief: Dispatch the reviewer as a separate Agent — DO NOT run the 8-check review inline. The agent produces an independent signal-strength verdict. Inline review substitutes your own judgment, which defeats the purpose.

Do:
1. Dispatch `agents/protocol/synapse-protocol-signal-reviewer.md` as a subagent (model: sonnet) with the drafted protocol file as input.
2. If any of the 8 checks fail: fix the specific issues. Re-dispatch for a second review.
3. **Two review cycles maximum.** If the protocol still fails after two cycles, surface remaining issues to the user — the protocol may need design changes, not just wording fixes.

Don't:
- Run the review inline
- Proceed to `[EVAL]` with failing checks

Exit: review passed (all 8 checks) → `[EVAL]`

---

### [EVAL] — eval handoff

Brief: Dispatch eval writer; do not grade the produced protocol's body quality — that is downstream.

Do:
1. Run `→ shared-steps:handoff-eval(protocol, $artifact_path)` — dispatches `synapse-router-eval-writer (protocol flow)`

Don't:
- Block on downstream eval completion — handoff dispatches and continues
- Grade the protocol's content quality — that is `synapse-router-eval-writer (protocol flow)` + `/synapse-router-artifact-gatekeeper`'s job

Exit: handoff dispatched → `[END]`

---

### [END] — report

Do: Print verbatim summary:
- Files created (protocol `.md` path)
- Registry row added (PROTOCOL_REGISTRY.md)
- Domain README row added
- EVAL.md scaffold dispatched to `synapse-router-eval-writer (protocol flow)`
- Status: `draft` — run `/synapse-router-artifact-gatekeeper <protocol-path>` before promoting

---

## Entry gates

| Transition | Gate |
|------------|------|
| `[START]` → `[A]` | Pre-flight validations pass; `$artifact_dir` confirmed |
| `[A]` → `[W]` | All 4 anchors concrete; single-concern confirmed; no unresolved duplicate; taxonomy values selected |
| `[W]` → `[R]` | All scaffold files written; registry row appended; README row inserted |
| `[R]` → `[EVAL]` | All 8 signal-strength checks pass (max 2 review cycles) |
| `[EVAL]` → `[END]` | `handoff-eval` dispatched |

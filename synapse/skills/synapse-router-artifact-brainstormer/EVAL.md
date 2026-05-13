# synapse-router-artifact-brainstormer — Evaluation Criteria

## Structural Criteria

(From synapse-skill-skill-improver's baseline checklist — no need to duplicate here)

## Execution Criteria

- [ ] **EVAL-E01:** Design-doc-producer dispatched with model: sonnet
  - **Test:** Trace contains an Agent() dispatch for `brainstorm-design-doc-producer` with `model: sonnet` explicitly set.
  - **Fail signal:** Dispatch record omits the `model:` field, or specifies a model other than sonnet.

- [ ] **EVAL-E02:** Memo-producer dispatched N times — one instance per artifact
  - **Test:** Trace contains one Agent() dispatch of `brainstorm-memo-producer` per artifact discovered during the session; artifact count in notepad matches dispatch count.
  - **Fail signal:** Fewer dispatches than artifacts in the notepad, or a single dispatch covering multiple artifacts.

- [ ] **EVAL-E03:** Memo-producer dispatches carry model: sonnet
  - **Test:** Every `brainstorm-memo-producer` dispatch record in the trace includes `model: sonnet`.
  - **Fail signal:** Any memo-producer dispatch omits `model:` or uses a different model.

- [ ] **EVAL-E04:** All [O] dispatches fire in parallel
  - **Test:** Trace shows design-doc-producer and all memo-producer dispatches initiated in the same turn (no sequential waiting between them).
  - **Fail signal:** Any memo-producer dispatch starts only after a prior dispatch has completed, or design-doc-producer completes before memo-producer dispatches are initiated.

- [ ] **EVAL-E05:** Done Signal precondition enforced before entering [O]
  - **Test:** Trace shows [D] node completing (all-lenses-complete check, hygiene check, cross-artifact sweep, empty Open sections, empty session-level orphaned) before any subagent dispatch is recorded.
  - **Fail signal:** An Agent() dispatch for either producer appears in the trace before the [D] checklist is marked complete, or a dispatch fires while Open items are still listed in the notepad.

- [ ] **EVAL-E06:** Notepad passed untrimmed to every subagent
  - **Test:** Each dispatch record in the trace includes the full notepad (both Zone 1 and Zone 2 content present); no summarization or section omission is noted in the dispatch payload description.
  - **Fail signal:** Dispatch payload is described as "summary of notepad," "relevant sections," or otherwise truncated; cross-cutting section absent from passed content.

- [ ] **EVAL-E07:** Subagent failures surface — not silently swallowed
  - **Test:** If any producer returns an `AGENT FAILURE` block, the trace shows the skill routing back to [D] rather than proceeding to [END].
  - **Fail signal:** Trace skips from [O] to [END] with no acknowledgment of a failure block returned by a subagent, or failure block is present in agent output but not referenced in the orchestrator trace.

- [ ] **EVAL-E08:** [RESUME] path re-reads meta.yaml and notepad before routing — no assumption of prior context
  - **Test:** On a resumed session, trace records file reads for both `meta.yaml` and the notepad before any [A], [B], or [D] turn is taken.
  - **Fail signal:** Trace routes directly to a mid-flow node on resume without a preceding read of both files, or prior context is referenced without a re-read recorded.

- [ ] **EVAL-E09:** Lens files loaded one at a time at moment of need during [B]
  - **Test:** Trace shows `references/lens-{current}.md` loaded immediately before each lens is applied; no bulk-load of all five lens files at [B] entry.
  - **Fail signal:** All lens reference files appear as a batch read at the start of [B], or a lens is applied in the trace without a preceding load of its reference file.

- [ ] **EVAL-E10:** Wrong-tool check fires at [NEW] entry before [A] begins
  - **Test:** Trace records a wrong-tool evaluation step (redirect check for skill-creator / synapse-skill-skill-improver / synapse-router-artifact-gatekeeper) after notepad initialization and before the first [A] turn.
  - **Fail signal:** [A] discovery begins with no wrong-tool check recorded in the trace, or wrong-tool check appears after the first [A] exchange.

## Output Criteria

- [ ] **EVAL-O01:** Notepad file created at correct path
  - **Test:** Check that a file named `notes.md` exists inside a directory matching `.brainstorms/YYYY-MM-DD-<slug>/` in the working directory.
  - **Fail signal:** No `.brainstorms/` directory exists, or the directory exists but contains no `notes.md` file.

- [ ] **EVAL-O02:** Notepad contains all required Zone 1 sections
  - **Test:** Open `notes.md` and confirm the following section headers are present: `## Status`, `## Artifacts Discovered`, `## Cross-cutting`, `## Process`, `## Open / Orphaned`.
  - **Fail signal:** One or more of the five Zone 1 headers is absent from the notepad.

- [ ] **EVAL-O03:** Notepad Status block contains all four required fields
  - **Test:** In the `## Status` section, confirm `Phase:`, `Outcome:`, `Brainstorm type:`, and `Artifact count:` fields are all populated with non-placeholder values.
  - **Fail signal:** Any field retains its template placeholder (e.g., `<A|B|D>`) or is blank.

- [ ] **EVAL-O04:** Artifacts Discovered table has one row per confirmed artifact
  - **Test:** Count the rows in the `## Artifacts Discovered` table. Count the per-artifact sections below the Zone 2 divider. The two counts must be equal.
  - **Fail signal:** Table row count does not match the number of per-artifact sections in the notepad.

- [ ] **EVAL-O05:** Every per-artifact section contains all four subsections
  - **Test:** For each `## Artifact: <name>` block, confirm the presence of `### Resolved`, `### Resolved (not fleshed)`, `### Open`, and `### Memo-ready` subsections.
  - **Fail signal:** Any per-artifact block is missing one or more of the four subsections.

- [ ] **EVAL-O06:** No per-artifact `### Open` section contains unresolved items at output time
  - **Test:** At the point memos are produced, inspect every `### Open` subsection in the notepad. Each must be empty or contain only struck-through/resolved items.
  - **Fail signal:** Any `### Open` section contains an active `⚠` prefixed item.

- [ ] **EVAL-O07:** Memo produced for every artifact in the Artifacts Discovered table
  - **Test:** Count rows in the `## Artifacts Discovered` table. Confirm that an equal number of memo files are produced.
  - **Fail signal:** The number of memo files is less than the number of table rows, or a memo file references an artifact name not in the table.

- [ ] **EVAL-O08:** Each memo contains the required header metadata block
  - **Test:** Open each memo file and confirm the header line `> Artifact type: ... | Memo type: ... | Design doc: ...` is present and all three fields are populated with non-placeholder values.
  - **Fail signal:** Any memo is missing the header line, or any field in the header retains a template placeholder.

- [ ] **EVAL-O09:** Each memo's "What I want" section describes the artifact in user terms
  - **Test:** In each memo, the `## What I want` section must contain at least one substantive sentence. The section must not contain template placeholder text.
  - **Fail signal:** Section is blank, contains only the HTML comment, or repeats the artifact name with no elaboration.

- [ ] **EVAL-O10:** Each memo's "Why Claude needs it" section contains a concrete failure mode
  - **Test:** The `## Why Claude needs it` section must describe what Claude currently produces without the artifact and what is specifically wrong with that output. The section must not use phrases like "improve", "enhance", or "better" as the sole explanation.
  - **Fail signal:** Section consists only of aspirational language with no description of a specific observable failure in Claude's current output.

- [ ] **EVAL-O11:** Design document produced and path referenced in the [END] summary
  - **Test:** Confirm a design doc file exists in the brainstorm directory. Confirm the [END] summary message names this path explicitly.
  - **Fail signal:** No design document file exists in the directory, or the [END] summary omits the design doc path.

- [ ] **EVAL-O12:** Design document contains Problem Statement, Design Principles, and Architecture sections with non-placeholder content
  - **Test:** Open the design document and confirm `## 1. Problem Statement`, `## 2. Design Principles`, and `## 3. Architecture` headers are present with substantive content.
  - **Fail signal:** Any of the three mandatory sections is absent or contains only its template HTML comment.

- [ ] **EVAL-O13:** Verbatim blocks preserved in memos
  - **Test:** For any structural block (flow graphs, schemas, directory trees) present in the notepad's `### Memo-ready` sections with `<!-- VERBATIM -->` markers, confirm the identical content appears in the corresponding memo without rewriting.
  - **Fail signal:** A block marked `<!-- VERBATIM -->` in the notepad appears in a memo with words changed, content omitted, or the marker stripped.

- [ ] **EVAL-O14:** [END] summary lists all produced outputs with file paths
  - **Test:** The final assistant message must enumerate: (1) the design doc path, (2) each memo path, (3) the memo type (`creation` or `change_request`) for each artifact.
  - **Fail signal:** The [END] message omits the design doc path, omits any memo path, or omits the memo type for any artifact.

- [ ] **EVAL-O15:** meta.yaml status field is set to done at session end
  - **Test:** Open the `meta.yaml` file in the brainstorm directory after the [END] phase completes. The `status` field must equal `done`.
  - **Fail signal:** `status` field is absent, retains a non-`done` value, or the file does not exist.

## Test Prompts

### EVAL-T01 — Naive User: "I have a skill idea"

**Prompt:** "I want to brainstorm a skill for summarizing meetings. Can you help me think through it?"

**Why this tests the skill:** Tests whether the skill elicits enough context to be useful or proceeds with surface-level output given minimal framing.

### EVAL-T02 — Naive User: Rework request with no detail

**Prompt:** "My protocol-creator skill feels off. I want to rethink it but not sure where to start."

**Why this tests the skill:** Tests whether the skill prompts for what "feels off" means or dives into generic redesign advice without grounding.

### EVAL-T03 — Naive User: Vague tooling intuition

**Prompt:** "I keep wanting an agent that monitors my codebase for drift. Is that even a thing? Should I build it?"

**Why this tests the skill:** Tests whether the skill can operate on a half-formed concept and help the user clarify whether it should exist at all before committing to a shape.

### EVAL-T04 — Experienced User: Protocol design space exploration

**Prompt:** "I'm considering a new protocol for cross-skill handoff state — basically a typed envelope that any skill can write to and any downstream skill can read. I want to explore tradeoffs between schema rigidity (typed fields) and flexibility (freeform context blobs) before I commit to a structure. I'm worried about versioning and backward compatibility at the edges."

**Why this tests the skill:** Tests whether the skill can hold a high-fidelity design conversation, surface real tradeoffs, and avoid defaulting to generic advice.

### EVAL-T05 — Experienced User: Reworking an existing agent with known failure modes

**Prompt:** "I have a synapse-skill-eval-judge agent that consistently hallucinates passing scores when the test prompt is ambiguous. I've already tried tightening the scoring rubric — it didn't help. Before I redesign the agent, I want to brainstorm whether this is a prompt design problem, an architecture problem (maybe the judge needs a challenger agent), or a signal problem (the EVAL.md criteria are too vague to adjudicate). Help me think through the design space."

**Why this tests the skill:** Tests whether the skill can handle a constrained rework session where one solution path has already been ruled out, requiring it to reason across architectural options.

### EVAL-T06 — Experienced User: Novel domain — physical-world artifact

**Prompt:** "I want to build a skill for designing hardware test fixtures — not software tests, literal physical jigs for circuit boards. Most of the context is non-standard: BOM constraints, IPC standards, tolerance stackups. I'm not sure whether this should be one skill, a multi-stage skill, or an agent backed by domain references. Help me explore the shape before I write anything."

**Why this tests the skill:** Tests whether the skill can operate outside software/AI domains and still generate meaningful structure from unfamiliar context.

### EVAL-T07 — Adversarial: Everything at once

**Prompt:** "I want to brainstorm a skill that is also an agent, implements a protocol, routes itself through the pipeline system, evaluates itself after every run, and supports both Codex and Claude. It needs to be simple enough for naive users but powerful enough for advanced ones. I want to explore all possible design directions before deciding anything."

**Why this tests the skill:** Tests whether the skill recognizes an over-scoped request and narrows focus rather than producing an unfocused sprawl of ideas.

### EVAL-T08 — Adversarial: Contradictory constraints

**Prompt:** "Help me rework my code-review skill. It needs to be completely opinionated — enforce our internal standards, never ask the user questions — but also totally flexible so any team can use it without modification. I want the brainstorm to end with a single definitive design."

**Why this tests the skill:** Tests whether the skill surfaces the contradiction (opinionated vs. flexible, single design vs. exploration) rather than synthesizing a false resolution.

### EVAL-T09 — Wrong Tool: Ready to build, not explore

**Prompt:** "I've already decided I'm building a changelog-generator skill. I have the design finalized — just write me the SKILL.md."

**Why this tests the skill:** Tests whether the skill recognizes the user is past the exploration phase and redirects to /synapse-router-artifact-creator rather than forcing an unwanted brainstorm.

### EVAL-T10 — Wrong Tool: Evaluating an existing skill, not exploring

**Prompt:** "My synapse-skill-skill-improver skill keeps failing on the scoring phase. Can you brainstorm what's wrong with it?"

**Why this tests the skill:** Tests whether the skill distinguishes between exploring a design space (its job) and diagnosing a runtime failure in a live artifact (belongs to /synapse-skill-skill-improver or debugging).

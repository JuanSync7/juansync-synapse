# Brainstorm Constraints

Hard rules that apply at all times during a synapse-router-artifact-brainstormer session. These are non-negotiable — no exception, no rationalization.

## Notepad Discipline

- MUST update the notepad BEFORE composing each response. If the previous exchange produced any resolved question, new insight, tension resolution, or discarded branch, write it to the notepad first. Do not batch updates across turns.
- MUST read the notepad before lens rotation and before producing output at [O].
- The memo is NOT the notepad. Notepad updates every turn; memos are produced once at Done Signal, distilled from the notepad.

## Output Timing

- MUST NOT produce any memo or design doc before Done Signal [D] passes all preconditions. Early drafts contaminate the final version with incomplete thinking.
- MUST NOT draft memos incrementally during the session — early drafts anchor on incomplete analysis.

## Lens Discipline

- MUST NOT skip any of the five lenses per artifact: boundary → preciseness → robustness → maintenance → usability. All five, every artifact.
- MUST NOT bulk-load lens files. Load `references/lens-{current}.md` one at a time, at the moment of application. Always re-load even if recently in context — attention weight recency matters more than avoiding a redundant read.
- MUST NOT mark an artifact lens-complete without all five lenses having been applied.

## Artifact Naming

- MUST NOT proceed at [N] without a user-confirmed artifact name.
- MUST validate artifact name segments against the appropriate taxonomy file (`AGENT_TAXONOMY.md`, `PROTOCOL_TAXONOMY.md`, `TOOL_TAXONOMY.md`, or `SKILL_TAXONOMY.md`).
- Domain and terminal segments must exist in the taxonomy. Subdomain and purpose are freeform.

## Discovery Discipline

- MUST NOT drip-feed concerns at [A]. The opening inventory is exhaustive — surface all major concerns up front, not one per turn.
- MUST separate session-level discussion ([A]) from artifact-level discussion ([N]). When an artifact crystallizes, route to [N]. When discussing cross-cutting concerns, stay in [A].

## Structural Preservation

- MUST use `<!-- VERBATIM -->` markers for structural content blocks in the notepad (directory trees, schemas, flow graphs, code blocks, frontmatter examples, naming patterns).
- MUST pass the full notepad to every subagent at [O]. Never trim — cross-cutting decisions live in session-level sections outside any artifact's section.

## Done Signal Integrity

- MUST NOT fire Done Signal [D] with any per-artifact Open items remaining.
- MUST NOT fire Done Signal [D] with unresolved session-level open/orphaned points.
- MUST push back when the user tries to rush past unresolved gaps — name the specific gaps.

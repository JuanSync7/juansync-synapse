---
name: synapse-memory-external-memory-contract
description: "Behavioral contract for file-based working memory — enables skills to externalize state into files that survive auto-compaction and context limits"
domain: synapse
subdomain: memory
subject: external-memory
kind: contract
version: 1
tags: [working-memory, state-externalization, compaction-safe, file-based]
---

# External Memory Protocol

Skills that orchestrate multi-step workflows need state that outlives any single agent turn. In-context state (variables, accumulated tool output) is fragile — auto-compaction can silently drop it, and long workflows exhaust the context window. File-based working memory solves this: every piece of state the planner or subagent needs is written to a file, read back when needed, and survives any compaction event.

## Contract Rules

1. **File-based, not in-context.** All working state MUST live in files. If a piece of information would be lost during auto-compaction and that loss would break the workflow, it belongs in a file.

2. **Skill-owned writes.** Only the planner (the skill's main agent) writes to working memory files. Subagents MUST NOT write to shared memory files — they return signals to the planner, and the planner integrates.

3. **Read-before-reason.** Before making any planning decision, the planner MUST read the relevant memory file(s) to refresh context. Do not rely on what you "remember" from earlier in the conversation — read the file.

4. **Write-after-turn.** After every significant decision or subagent dispatch, the planner MUST update the relevant memory file before proceeding. Do not batch updates — stale memory files cause stale decisions in later turns.

5. **Subagents return signals, not writes.** A subagent's output includes structured signals (discoveries, cross-references, assumptions, failures). The planner reads these signals and decides what to write to memory.

6. **Ephemeral vs. persistent — declared by skill.** Each memory file is either:
   - **Ephemeral** — exists only during the run, discarded after completion (e.g., planning notepad, scratch calculations)
   - **Persistent** — survives across runs, becomes a project artifact (e.g., document map, knowledge index)
   
   The skill MUST declare which category each memory file belongs to. Subagents do not need to know — they interact with the planner, not the files.

7. **Navigation over scanning.** Memory files SHOULD be structured for targeted reads (anchors, indices, tables) rather than full-file scanning. Grep for an anchor, read a targeted range — never read the entire file when you need one section.

8. **Failure reporting.** Violations of this protocol use the `synapse-observability-failure-reporting-schema` protocol format:
   ```
   PROTOCOL FAILURE: synapse-memory-external-memory-contract <context> [reason]
   ```

## Injection

The orchestrating skill references this protocol in its SKILL.md and declares its memory files (names, ephemeral/persistent, purpose). Subagent definitions do NOT reference this protocol — they interact with the planner, not with memory files directly.

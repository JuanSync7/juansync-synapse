# Sub-Subagent Dispatch Patterns

Reference for iteration subagents when dispatching sub-subagents. Loaded when a structural trigger fires (comparative scoring or loop-attached requirements). Sub-subagents are always **leaf nodes** — they do work, return a structured result, and never dispatch further.

---

## Pattern 1: Comparative Scorer Dispatch

**Trigger:** PROGRAM.md `## Scoring mode` is `Comparative`.

The iteration subagent must not score inline — it knows what it changed and will produce biased output if it also plays the role of the target AND the judge. Dispatch a single scorer sub-subagent that handles invocation + judgment as one unit.

### Scope boundary spec

Pass to the sub-subagent:

| Slot | Source | Example |
|------|--------|---------|
| `current_skill` | The mutable target at HEAD (after your edit) | Full contents of SKILL.md post-edit |
| `baseline_skill` | The mutable target at the previous best commit | Full contents of SKILL.md at best commit |
| `test_inputs` | From PROGRAM.md `## Immutable files` → `test-inputs/` | Each test input file's contents |
| `comparison_dimensions` | From PROGRAM.md `## Comparison dimensions` | The ranked dimension list verbatim |
| `comparison_protocol` | From PROGRAM.md `## Comparison protocol` | The 5-step protocol verbatim |

**Model:** `sonnet` — evaluation is well-scoped, not architectural.

### Expected return

```json
{
  "verdict": "preferred | tie | rejected",
  "dim_wins": "2/3",
  "reasoning": "Dimension 1 (specificity): current version wins — error messages now include the failing field name. Dimension 2 (coverage): tie. Dimension 3 (conciseness): baseline wins — current version added 15 lines of redundant context."
}
```

### Good vs bad dispatch

**Good:** "Run SKILL.md (current) and SKILL.md (baseline) against these 3 test inputs. Judge outputs on these 3 ranked dimensions using randomized presentation order. Return verdict + per-dimension reasoning."

All context is in the prompt. The sub-subagent doesn't need to read files, understand the loop, or make strategic decisions.

**Bad:** "Score the current version against the baseline using the comparison protocol in PROGRAM.md."

The sub-subagent would need to find and read PROGRAM.md, locate test inputs, figure out the dimensions — all context the iteration subagent already has and should pass directly.

---

## Pattern 2: Loop-Attached Requirement Dispatch

**Trigger:** PROGRAM.md has a `## Loop-attached requirements` section AND the iteration's metric outcome suggests a keep.

The iteration subagent dispatches a writer sub-subagent to satisfy the documentation requirement. This keeps the edit work and the doc work in separate contexts — the doc writer gets a clean view of what changed without the strategic reasoning clutter.

### Scope boundary spec

Pass to the sub-subagent:

| Slot | Source | Example |
|------|--------|---------|
| `target_file` | From PROGRAM.md loop-attached requirements | `docs/operations/DOCKER_OPTIMIZATION.md` |
| `target_section` | Inferred from the change (or "append new section") | `## Dependency Splitting` |
| `change_description` | Your commit message / hypothesis | "Moved torch to inference extras group" |
| `change_mechanism` | Why the change helped (from your scoring result) | "torch is 400MB, API container doesn't need inference deps" |
| `requirements` | From PROGRAM.md loop-attached requirements verbatim | "What changed, why it helped, any new build flags" |
| `existing_content` | Current contents of the target file (if it exists) | Full file read |
| `expected_length` | Bounded estimate | "15-30 lines of markdown" |

**Model:** `haiku` — mechanical writing from provided facts, no judgment required.

### Expected return

```json
{
  "content": "## Dependency Splitting\n\nMoved torch and transformers...",
  "target_file": "docs/operations/DOCKER_OPTIMIZATION.md",
  "target_section": "## Dependency Splitting",
  "lines_written": 22
}
```

### Good vs bad dispatch

**Good:** "Write a section for `docs/operations/DOCKER_OPTIMIZATION.md` under heading `## Dependency Splitting`. Cover: (1) what changed — torch moved to inference extras group, (2) why it helped — torch is 400MB and API container doesn't need it, (3) new install command: `pip install .[api]`. Existing file content: [pasted]. Write 15-30 lines of markdown. Return the section content."

Every fact is in the prompt. The sub-subagent assembles prose from provided inputs.

**Bad:** "Update the Docker optimization docs to reflect the latest changes."

The sub-subagent would need to figure out what changed, why, and what the doc should say — that's the iteration subagent's job.

---

## Dispatch rules (all patterns)

These apply to every sub-subagent dispatch regardless of trigger:

1. **Set `model:` explicitly.** Sonnet for evaluation/judgment. Haiku for mechanical assembly. Opus only if the sub-subagent must make architectural decisions (rare — if it needs opus, the subtask may not be properly scoped).
2. **Self-contained prompt.** Every fact the sub-subagent needs is in the dispatch prompt. It reads no files, loads no references, has no ambient context.
3. **Structured return contract.** Define the JSON shape before dispatching. The sub-subagent returns exactly that shape or a `crash` with a reason.
4. **Leaf only.** Sub-subagents never dispatch further. If a sub-subagent can't complete as a leaf, the iteration subagent scoped it wrong — re-decompose, don't add depth.

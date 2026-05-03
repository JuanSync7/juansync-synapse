---
name: patch-docs
description: "Use when code has changed and docs need incremental updates — not full regeneration. Triggered by 'patch docs', 'update the docs', 'sync docs with changes', or automatically after coding tasks via CLAUDE.md trigger."
domain: docs
intent: improve
tags: [incremental, patch, diff-driven, doc-maintenance]
user-invocable: true
argument-hint: "[optional: 'staged' | 'HEAD~1' | path-to-diff]"
---

# Patch Docs

Given a code diff, find affected documentation sections and apply the minimum targeted update to keep docs current. Patch-docs never regenerates a document — it reads only the relevant section, applies a surgical edit that matches existing conventions, and moves on. When patching is insufficient (the change is too large for a section-level edit), it escalates to the right write-* skill rather than producing a half-baked structural change.

The core value is consistency and discovery: knowing *which* docs are affected by a diff, *which sections* within those docs need updating, and ensuring new content matches the surrounding format exactly.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## Progress Tracking

At the start, create a task list:

```
TaskCreate: "Phase 1: Triage — classify diff and map doc impact"
TaskCreate: "Phase 2: Discovery — find affected docs via .doc-map.yaml"
TaskCreate: "Phase 3: Patch — apply targeted edits to each doc"
TaskCreate: "Phase 4: Summary — output patch report"
```

Mark each task `in_progress` when starting, `completed` when done.

## Wrong-Tool Detection

- **User wants to create documentation from scratch** -> redirect to `/doc-authoring`
- **User wants a full engineering guide** -> redirect to `/write-engineering-guide`
- **User wants a full test plan** -> redirect to `/write-test-docs`
- **User wants to initialize a test coverage register** -> redirect to `/write-test-coverage`
- **User wants to write or update a spec** -> redirect to `/write-spec-docs`
- **User has no code changes, just wants to improve doc quality** -> not this skill; suggest manual editing or `/write-engineering-guide` for a fresh pass

## Input Gathering

**Primary input: git diff.**

Resolve the diff source in this order:
1. If the user provides an argument (`staged`, `HEAD~1`, or a file path), use it
2. If no argument: check for staged changes (`git diff --cached`)
3. If nothing staged: use `git diff HEAD~1`
4. If no diff found: exit with "No changes detected. Nothing to patch."

**Supplementary input: commit message.** If available (from `git log -1 --format=%s` or user-provided), use it to improve change-type classification accuracy. The commit message is a hint, not the source of truth — the diff content takes precedence.

## Phase 1: Triage

Parse the diff to understand what changed and classify the change type.

1. **Extract changed entities** — files, functions, classes, config keys, API endpoints touched by the diff
2. **Classify change type** — feature, refactor, bugfix, cosmetic, or config change. Use the diff content as primary signal, commit message as secondary.
3. **Cosmetic exit check** — if ALL changes are whitespace, comments, or formatting with no behavioral or API impact, output "No behavioral changes detected, nothing to patch" and halt. A variable rename in a public interface is NOT cosmetic — it is a refactor.

> **Read [`references/doc-impact-map.md`](references/doc-impact-map.md)** to map the classified change type to affected doc types.

The doc-impact-map produces a list of doc types to check (e.g., eng-guide: yes, README: only if public API, spec: no). Carry this forward to Phase 2.

## Phase 2: Discovery

Find the actual doc files that correspond to the affected doc types.

**If `.doc-map.yaml` exists in the project root:** read it. This file maps doc paths to the code paths they cover:

```yaml
docs/auth/AUTH_ENGINEERING_GUIDE.md: [src/auth/]
README.md: [src/]
.env.example: [src/]
```

Look up which docs cover the changed code paths. Read only the relevant section headings of matched docs to confirm scope.

**If `.doc-map.yaml` does not exist:** generate it:
1. Glob for documentation files (`**/*.md`, `.env.example`, `**/docs/**`)
2. For each doc: read the first 20 lines and any H2 headings to understand what it covers
3. Match docs to code paths based on content references, directory structure, and naming conventions
4. Write `.doc-map.yaml` to the project root

**For each doc type flagged in Phase 1:**
- If a matching doc exists: add to the patch plan with the relevant section(s)
- If no matching doc exists: flag for delegation to the appropriate write-* skill

**Output of Phase 2:** A patch plan — a list of `(doc path, section heading, update type)` tuples, plus any delegation flags.

## Phase 3: Patch

Apply targeted updates to each doc in the patch plan.

> **Read [`references/escalation-policy.md`](references/escalation-policy.md)** before patching to understand when to refuse and delegate.

For each doc in the patch plan:

1. **Read only the relevant section** — not the full document. Use the section heading from the patch plan to locate the content.
2. **Check escalation triggers** — if the update would require a new top-level (H2) section, escalate to the specific write-* skill per the escalation policy. Note the escalation in the summary and continue with other docs.
3. **Apply the targeted edit:**
   - Match the existing section's format: heading levels, list styles, table column order, code snippet style, terminology
   - Add/update/remove only what the diff requires
   - Do not rewrite unchanged content within the section
   - Do not introduce new formatting conventions
4. **Handle missing docs** — if the doc does not exist and the diff warrants its creation:
   - Dispatch the relevant write-* skill as a subagent (model: sonnet)
   - If the skill is not found, fail loudly: "Cannot find skill `[name]`. Create the doc manually or check installed skills."
   - After creation, continue the patch pass if additional targeted updates are needed

**Special cases:**
- **Spec-summary:** if the spec was patched, regenerate the summary by invoking `/write-spec-summary` — spec-summary is always regenerated, never patched directly
- **test-coverage.md:** apply incremental row updates only — add or update rows for new/changed test scenarios, do not restructure the register
- **.env.example:** add/update/remove config keys that changed in the diff, matching existing naming conventions (prefix, case style, comment format)

**Consistency is the hardest part.** Before writing any new content, read the 3-5 lines immediately surrounding where the edit will go. Match:
- Heading level and style
- List format (bullets vs numbers, indentation)
- Table column order and cell formatting
- Code snippet language tags and annotation style
- Terminology and voice (active/passive, technical level)

> **Read [`examples/before-after.md`](examples/before-after.md)** if you need a concrete model of convention-matching.

## Phase 4: Summary

After all patches are applied (or skipped/escalated), output a patch summary.

> **Read [`templates/patch-summary.md`](templates/patch-summary.md)** for the output format.

The summary has four sections:
- **Patched** — doc, section, and what was changed (tied to the diff)
- **Skipped** — doc and why it was not affected
- **Escalated** — doc, which write-* skill was recommended, and why
- **Delegated** — doc, which write-* skill created it

Output the summary to the user. Do not write it to a file.

## Headless / Autonomous Mode

When running without user interaction (pipeline stage, CLAUDE.md trigger, hook):

- Use staged changes or HEAD~1 automatically — do not prompt for diff source
- **Conservative defaults:** skip ambiguous changes rather than guessing. If the change-type classification is uncertain, skip the doc and note "ambiguous change, skipped" in the summary.
- If discovery finds no `.doc-map.yaml` and no doc files at all, output "No documentation found to patch" and halt cleanly (no error).
- Delegate doc creation only for docs directly relevant to the diff — do not aspirationally create docs that might be useful.

## Quality Rules

- **Only address the diff.** Do not fix pre-existing staleness, typos, or formatting issues in docs beyond what the diff requires. Staleness detection is a future KG/doc-audit concern.
- **Surgical edits.** The diff to the doc file should be as small as possible — only the lines that need to change.
- **No full-document reads.** Read the section heading list to orient, then read only the section(s) being patched.
- **Maintain `.doc-map.yaml`.** If a patch creates a new doc-code relationship (e.g., the diff adds a new module and patch-docs updates the eng-guide to cover it), update `.doc-map.yaml` to reflect it.

# Change Request: standardize CR archive directory name

## Problem

`improve-skill` consumes pending CRs from a target skill's `change_requests/` directory but doesn't specify where applied CRs should be moved after processing. Different runs of the workflow have invented different names — `change_requests/processed/`, `change_requests/applied/`, etc. — because the SKILL.md is silent on the convention.

This produces inconsistent archive directories across skills and forces every contributor (and every subagent running this workflow) to make a fresh judgment call.

## Proposed Change

Standardize on `change_requests/applied/` as the archive directory.

Rationale for the name:
- Matches the verb the CR itself uses (CRs frame work as "Proposed Change → applied to SKILL.md").
- Shorter and more direct than alternatives (`processed`, `archived`, `done`).
- Past participle form parallels git's own `applied` (cherry-pick, rebase) terminology.

Add to `improve-skill/SKILL.md` in the workflow's archival step:

> After successfully applying a CR's changes to the target skill, move the CR file from `change_requests/<file>.md` to `change_requests/applied/<file>.md`. Use `git mv` if the CR is tracked, plain `mv` otherwise. Create the `applied/` directory if it doesn't exist.

## Scope

- One sentence in `improve-skill/SKILL.md` codifying the directory name and the move step.
- No taxonomy or registry changes.
- No retroactive renames required — existing archive directories under other names can be renamed opportunistically when those skills are next touched.

## Why

Convention should live in the workflow that creates the convention. Without it, every subagent reinvents the name and the resulting structure drifts. One sentence in the workflow is cheaper than aligning archive directories repo-wide every few months.

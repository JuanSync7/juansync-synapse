# Doc Impact Map

Maps change types to which documentation types are affected. Loaded during Phase 1 (Triage) after classifying the diff.

## Change-Type to Doc-Type Mapping

| Change Type | README.md | Eng-Guide | Spec | Spec-Summary | Test-Docs | Test-Coverage | Config Docs |
|-------------|-----------|-----------|------|--------------|-----------|---------------|-------------|
| **New feature** | If public API or module-level | Always | If new requirement | Regenerate if spec changes | Rarely — only if test structure changes | If new tests added | If new config options |
| **Refactor** | If user-facing rename | If behavioral change in module structure | No | No | No | No | No |
| **Bugfix** | No | Almost always | Only if bug reveals missing requirement | Regenerate if spec changes | No | If new test added for the fix | No |
| **Cosmetic** | No | No | No | No | No | No | No |
| **Config change** | If user-facing config | Eng-guide config section if behavioral | No | No | No | No | Always |

## Classification Rules

Classify from the diff content + commit message (if available):

- **New feature:** diff adds new classes, public functions, API endpoints, config parameters, or database fields
- **Refactor:** diff restructures existing code without changing external behavior — renames, moves, extracts, reorganizes
- **Bugfix:** diff fixes incorrect behavior — error handling, edge cases, wrong return values, race conditions
- **Cosmetic:** diff changes only whitespace, comments, formatting, or internal variable names with no behavioral or API impact
- **Config change:** diff modifies configuration files, environment variables, or deployment settings

**The behavioral impact test:** If the change affects what a user, caller, or downstream system observes — it is NOT cosmetic. Variable renames in public interfaces are refactors, not cosmetic.

## Config File Scope

Only human-facing config docs are in scope:

- **In scope:** `.env.example`, annotated config templates, deployment runbook configs — files humans read to understand configuration options
- **Out of scope:** `pyproject.toml`, `docker-compose.yaml`, `package.json`, CI workflow files, `Makefile` — files consumed by build tools, CI pipelines, or package managers

**Detection heuristic:** If the file is referenced in a build/CI/package chain (imported by a tool, listed in a pipeline step, or parsed by a package manager), it is code config — skip it.

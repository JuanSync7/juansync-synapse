# Escalation Policy

Defines when patch-docs should refuse to patch a document and instead delegate to the appropriate write-* skill. Loaded during Phase 3 (Patch) when the scope of a required update exceeds what a targeted patch can handle.

## Escalation Triggers

Redirect to the specific write-* skill when ANY of these are true:

1. **New top-level section required.** The patch would add a new H2 (`##`) heading to the document. Adding content within an existing section is a patch; adding a new section is structural — the write-* skill has the full context to place it correctly.

2. **Doc does not exist.** The `.doc-map.yaml` or discovery shows no document of this type exists for the affected code. Patch-docs patches existing docs; it delegates creation.

3. **Write-* skill not found.** If the target skill is not installed, fail loudly: `"Cannot find skill [skill-name]. Create the doc manually or check installed skills."`

## Delegation Mapping

| Doc Type | Delegate To |
|----------|------------|
| Engineering guide | `/write-engineering-guide` |
| Spec | `/write-spec-docs` |
| Spec-summary | `/write-spec-summary` |
| Test-docs | `/write-test-docs` |
| Test-coverage.md | `/write-test-coverage` |
| README.md | No skill — note in summary: "README.md does not exist. Create it manually." |

## Delegation Behavior

When delegating doc creation:
- Dispatch the write-* skill as a subagent (model: sonnet)
- Pass the relevant code paths and diff context as input
- After the subagent completes, continue the patch pass on the newly created doc if the diff warrants additional targeted updates
- Note the delegation in the patch summary under "Delegated"

## What Is NOT an Escalation

- Adding a bullet point to an existing list — patch
- Adding a row to an existing table — patch
- Updating a code snippet within an existing section — patch
- Renaming a function reference throughout a section — patch
- Updating a config parameter in an existing config table — patch

These are all within-section edits. Only structural changes (new sections) trigger escalation.

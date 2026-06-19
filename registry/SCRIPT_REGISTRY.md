# Scripts Registry

Repo management scripts. Before creating a new script, check if one already covers the capability you need.

Schema: see [registry/README.md](README.md).

| Script | Description | Status | Consumers |
|------|-------------|--------|-----------|
| [audit-artifacts](../scripts/audit-artifacts.sh) | Inventory and promotion-signal audit for companion artifacts | stable | cortex |
| [check-links](../scripts/check-links.sh) | Validate relative markdown links in src/ for broken targets | stable | cortex, synapse-skill-improver |
| [cortex](../cortex) | Top-level dispatcher for ai-synapse — routes to scripts by subcommand | stable | scaffold, sync-registry |
| [install](../scripts/install.sh) | CLI entry point for installing and managing skill symlinks | stable | cortex, pathway, validate |
| [pathway](../scripts/pathway.sh) | Manage pathway bundles — list, show, install, create, export | stable | cortex, synapse-router-artifact-gatekeeper, synapse-router-eval-writer, synapse-router-suite-validator, sync-registry |
| [reorganize](../scripts/reorganize.sh) | Domain-based artifact reorganization utility | stable | cortex |
| [scaffold](../scripts/scaffold.sh) | Create a new synapse with correct structure, frontmatter, and registry entries | stable | cortex, synapse-router-artifact-creator, synapse-router-eval-writer |
| [sync-registry](../scripts/sync-registry.sh) | Sync registries and READMEs from disk state — detect and fix drift | stable | cortex |
| [tag-dev](../scripts/tag-dev.sh) | Classify the current branch's diff against main and print the next pre-tag (dry run) | stable | — |
| [tag-stable](../scripts/tag-stable.sh) | Promote the latest v<X>.<Y>.<Z>-pre.<N> tag to a stable v<X>.<Y>.<Z> tag and push it | stable | — |
| [test](../scripts/test.sh) | Run the full ai-synapse test suite — pytest unit tests plus bash smoke tests | stable | — |
| [validate](../scripts/validate.sh) | Run structural checks without committing | stable | cortex, reorganize, scaffold, synapse-meta-readme-maintainer, synapse-router-artifact-creator, synapse-router-artifact-gatekeeper, synapse-router-eval-writer, synapse-router-suite-validator |
| [version-bump-check](../scripts/version-bump-check.sh) | CI gate asserting a PR's bump:* label matches the mechanical classification of its diff | stable | — |
| [zip-skills](../scripts/zip-skills.ps1) |  | draft | — |

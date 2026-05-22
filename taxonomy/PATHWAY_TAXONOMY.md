# Pathway Taxonomy

Controlled vocabulary for pathway metadata. When creating a new pathway, pick `harness` from the table below. Naming is free-form — see the Naming Conventions section for guidance.

## Harnesses

| Harness | Description |
|---------|-------------|
| `claude` | Claude Code — installs to ~/.claude/skills/ |
| `codex` | Codex CLI — installs to ~/.codex/skills/ |
| `gemini` | Gemini CLI — installs to ~/.gemini/extensions/ |
| `multi` | Installs to all supported harnesses |

## Naming Conventions

Pathway naming is free-form — choose whatever makes sense for your organization. The following patterns are suggested as guidance, not enforced structurally. The synapse-router-artifact-gatekeeper evaluates naming quality at PR review time.

### Pattern 1: Domain-focused
`<primary-domain>[-<supporting-domain>...]-<descriptor>.yaml`

Examples: `frontend-dft-prevalidation.yaml`, `ml-data-transformer-training.yaml`

Use when the pathway primarily serves one domain with optional supporting domains pulled in for handoff or pre-validation.

### Pattern 2: Role-focused
`<role>-<descriptor>.yaml`

Examples: `lead-engineer-signoff.yaml`, `junior-dev-onboarding.yaml`

Use when the pathway is defined by who uses it, not what domain it covers.

### Pattern 3: Workflow-focused
`<workflow>-<descriptor>.yaml`

Examples: `tape-out-signoff.yaml`, `nightly-regression.yaml`

Use when the pathway maps to a specific workflow or process stage.

### Pattern 4: Single-domain
`<domain>-<descriptor>.yaml`

Examples: `verification-synapse-platform.yaml`, `docs-full-authoring.yaml`

Use for pathways that stay within a single domain.

## Tags

Freeform — no controlled list. Use lowercase, hyphenated multi-word tags (e.g., `frontend`, `onboarding`, `ml-training`).

## Enforcement

Naming conventions are guidance for authors — not enforced by pre-commit or structural validation. The synapse-router-artifact-gatekeeper evaluates naming quality during PR review using the patterns above as criteria. Pre-commit validates only structural fields (harness value, synapse paths, inherits target).

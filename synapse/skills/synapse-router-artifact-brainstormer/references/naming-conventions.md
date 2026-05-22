# Naming Conventions

Loaded at [N] when naming an artifact. Tier 2 candidate — generic enough to share with `*-creator` skills.

---

## Unified Pattern

All artifact types follow: `{domain}-{subdomain?}-{purpose?}-{terminal}`

The terminal segment is type-specific and must come from the artifact type's taxonomy file.

| Artifact Type | Terminal Segment | Terminal Name | Taxonomy Source |
|---|---|---|---|
| Agent | role | judge, writer, reviewer, auditor, prompter | `taxonomy/AGENT_TAXONOMY.md` |
| Protocol | type | trace, schema, contract | `taxonomy/PROTOCOL_TAXONOMY.md` |
| Tool | action | scorer, generator, validator, parser, transformer, reporter | `taxonomy/TOOL_TAXONOMY.md` |
| Skill | intent | write, review, improve, validate, plan, etc. | `taxonomy/SKILL_TAXONOMY.md` |

`subdomain` and `purpose` are optional. Simple artifacts use 2-3 segments; specific ones use 4.

---

## Good Examples

| Name | Pattern | Segments |
|---|---|---|
| `synapse-skill-eval-judge` | domain-subdomain-subdomain-role | 4 |
| `docs-spec-section-writer` | domain-subdomain-purpose-role | 4 |
| `synapse-protocol-signal-reviewer` | domain-subdomain-purpose-role | 4 |
| `synapse-observability-execution-trace` | domain-subdomain-subject-kind | 4 |
| `testing-criticality-scorer` | domain-purpose-action | 3 |

---

## Bad Examples

| Name | Problem |
|---|---|
| `protocol-review-agent` | Terminal is "agent" (not a valid role) — should be "reviewer" |
| `my-cool-skill` | No taxonomy alignment, no domain segment |
| `test-thing` | Too vague, no terminal segment |

---

## Validation Rules

1. **Domain** must exist in the artifact type's taxonomy file
2. **Terminal** must exist in the artifact type's taxonomy file
3. **Subdomain** and **purpose** are NOT taxonomy-validated — they are freeform and descriptive
4. When in doubt, check the taxonomy file for the artifact type
5. If no domain or terminal fits, propose an addition to the taxonomy file — do not invent ad hoc values

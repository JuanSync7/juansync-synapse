# Good Protocol Example — synapse-observability-failure-reporting-schema

This is `synapse/protocols/observability/synapse-observability-failure-reporting-schema.md`, annotated to show why each section works. Use this as a reference when drafting new protocols.

---

## The Protocol

```yaml
---
name: synapse-observability-failure-reporting-schema
description: "Standardized failure tag format for agents and protocols — enables grepping, aggregation, and surfacing across multi-agent workflows"
domain: synapse
subdomain: observability
subject: failure-reporting
kind: schema
version: 1
tags: [failure-reporting, agent-failure, protocol-failure, observability]
---
```

**Why this frontmatter works:**
- `description` is a trigger/routing contract — tells you WHEN to use it (when you need standardized failure tags), not HOW it works
- `domain`, `subdomain`, `kind` are from PROTOCOL_TAXONOMY.md; slug `{domain}-{subdomain}-{subject}-{kind}` matches the filename
- `tags` are lowercase, hyphenated, descriptive

---

```markdown
# Failure Reporting Protocol

Standardized tags for reporting failures across multi-agent workflows. Any agent
or protocol observer that encounters a failure MUST use the tag formats below.
This enables callers to grep for failures, aggregate them into summary tables,
and surface them to users with consistent formatting.
```

**Why this mental model works:**
- One paragraph
- Explains WHY (grepping, aggregation, surfacing) not HOW
- Uses commitment language even in the mental model ("MUST use")
- States the behavioral gap it fills (without it, failures are unstructured and invisible)

---

```markdown
## Tag Formats
### Agent Failure
AGENT FAILURE: [agent-name] <free-form context> [reason]

### Protocol Failure
PROTOCOL FAILURE: [protocol-name] <free-form context> [reason]
```

**Why this contract works:**
- Defines exact output format — no ambiguity about what compliance looks like
- MUST/MUST NOT language throughout the full protocol
- Named trigger moment: "when an agent encounters a failure"
- Each field marked as MUST or OPTIONAL

---

```markdown
## Behavior Contract
1. Continue, don't bail.
2. Tag every failure.
3. Caller aggregates.
4. Final surfacing.
```

**Why these rules work:**
- Imperative, numbered, unambiguous
- Each rule is one behavioral contract (though they're all part of the single concern: failure reporting)
- "Continue, don't bail" directly prevents a known failure mode (agent stops at first error)

---

## What This Protocol Gets Right

1. **Single concern** — failure reporting only. Doesn't also handle retries, escalation, or remediation.
2. **Commitment language** — MUST appears throughout. No hedging.
3. **Named trigger** — "when an agent encounters a failure" is specific and observable.
4. **Concrete format** — the tag format is fill-in-the-blank, not "describe the failure in a suitable way."
5. **57 lines** — well within the 30-120 line budget.

## What Could Be Improved

1. **Missing Failure Assertion section** — the protocol itself should have: "If the agent cannot determine whether an outcome is a failure or success, STOP and output: `PROTOCOL FAILURE: synapse-observability-failure-reporting-schema — ambiguous outcome, cannot classify as failure or success.`"
2. **Mental model mixes with contract** — the opening paragraph contains the MUST instruction, which should be in the Contract section.

These are minor issues that a signal-strength review would catch.

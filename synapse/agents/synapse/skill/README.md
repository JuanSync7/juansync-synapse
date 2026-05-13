# skill

Skill authoring and review agents — companion-file production for SKILL.md / references / templates, plus structural and signal-strength gates that run before eval generation.

## Agents

| Agent | Role | Description |
|-------|------|-------------|
| [synapse-skill-companion-writer](synapse-skill-companion-writer.md) | writer | Writes a single companion file (reference or template) for a skill |
| [synapse-skill-anatomy-reviewer](synapse-skill-anatomy-reviewer.md) | reviewer | Binary anatomy gate — checks SKILL.md structural anatomy (frontmatter, routing contract, required sections) against the canonical anatomy spec before eval generation |
| [synapse-skill-companion-auditor](synapse-skill-companion-auditor.md) | auditor | Audits references/ and templates/ companion files — load triggers, no duplication with SKILL.md body, size-fit-purpose, template concreteness, reference modularity |
| [synapse-skill-design-grader](synapse-skill-design-grader.md) | grader | Graded design-quality grader — scores a SKILL.md on six design-principle dimensions (1-5) and emits fix suggestions for dimensions below threshold |
| [synapse-skill-signal-orchestrator](synapse-skill-signal-orchestrator.md) | orchestrator | Dispatches anatomy/design/companion sub-agents in parallel and aggregates a unified APPROVE/REVISE/ESCALATE verdict before eval generation |

# Agents Registry

Internal recipes dispatched by skills, not typically user-invocable. Before creating a new agent, check if one already covers the capability you need.

Schema: see [registry/README.md](README.md).

| Agent | Description | Status | Consumers |
|------|-------------|--------|-----------|
| [synapse-protocol-signal-reviewer](../synapse/agents/synapse/protocol/synapse-protocol-signal-reviewer.md) | Signal-strength reviewer — validates protocol instructions use commitment language, named trigger moments, and follow universal anatomy | draft | — |
| [synapse-meta-readme-maintainer](../synapse/agents/synapse/meta/synapse-meta-readme-maintainer.md) | Maintains README-index invariant for the ancestor path of a changed synapse — adds/updates/removes rows; rewrites top-of-file one-liner only on factual drift. Dispatched by *-creator skills and synapse-skill-skill-improver at end of flow. | draft | — |
| [synapse-skill-anatomy-reviewer](../synapse/agents/synapse/skill/synapse-skill-anatomy-reviewer.md) | Binary anatomy gate — checks SKILL.md structural anatomy (frontmatter, routing contract, required sections) before eval generation | draft | synapse-skill-companion-auditor, synapse-skill-design-grader, synapse-skill-signal-orchestrator |
| [synapse-skill-companion-auditor](../synapse/agents/synapse/skill/synapse-skill-companion-auditor.md) | Audits references/ and templates/ companion files for a skill — checks load triggers, no duplication with SKILL.md body, size-fit-purpose, template concreteness, and reference modularity | draft | synapse-skill-anatomy-reviewer, synapse-skill-design-grader, synapse-skill-signal-orchestrator |
| [synapse-skill-companion-writer](../synapse/agents/synapse/skill/synapse-skill-companion-writer.md) | Writes a single companion file for a Claude Code skill | draft | synapse-skill-companion-auditor, synapse-skill-skill-improver |
| [synapse-skill-design-grader](../synapse/agents/synapse/skill/synapse-skill-design-grader.md) | Graded design-quality grader — scores a SKILL.md on six design-principle dimensions (1-5) and emits fix suggestions for dimensions below threshold | draft | synapse-skill-signal-orchestrator |
| [synapse-skill-eval-auditor](../synapse/agents/synapse/skill-eval/synapse-skill-eval-auditor.md) | Execution criteria for orchestration patterns (EVAL-Exx) | draft | synapse-skill |
| [synapse-skill-eval-judge](../synapse/agents/synapse/skill-eval/synapse-skill-eval-judge.md) | Impartial judge — binary output quality criteria (EVAL-Oxx) from SKILL.md | draft | synapse-router-eval-writer, synapse-skill |
| [synapse-skill-eval-prompter](../synapse/agents/synapse/skill-eval/synapse-skill-eval-prompter.md) | Blind test prompt generation across 4 personas | draft | synapse-skill |
| [synapse-skill-signal-orchestrator](../synapse/agents/synapse/skill/synapse-skill-signal-orchestrator.md) | Signal-strength orchestrator — dispatches anatomy/design/companion sub-agents in parallel and aggregates their verdicts into a unified APPROVE/REVISE/ESCALATE before eval generation | draft | — |

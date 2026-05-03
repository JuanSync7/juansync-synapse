# Agents Registry

Internal recipes dispatched by skills, not user-invocable. Before creating a new agent, check if one already covers the capability you need.

| Agent | Description | Consumers |
|-------|-------------|-----------|
| [skill-eval-judge](synapse/agents/skill-eval/skill-eval-judge.md) | Impartial judge — binary output quality criteria (EVAL-Oxx) from SKILL.md | skill-creator, write-skill-eval, improve-skill |
| [skill-eval-prompter](synapse/agents/skill-eval/skill-eval-prompter.md) | Blind test prompt generation across 4 personas | skill-creator, write-skill-eval |
| [skill-eval-auditor](synapse/agents/skill-eval/skill-eval-auditor.md) | Execution criteria for orchestration patterns (EVAL-Exx) | skill-creator, write-skill-eval |
| [protocol-eval-reviewer](synapse/agents/protocol-eval/protocol-eval-reviewer.md) | Signal-strength reviewer for protocol instructions | protocol-creator, write-protocol-eval |
| [skill-companion-file-writer](synapse/agents/skill/skill-companion-file-writer.md) | Writes a single companion file (reference or template) for a skill | skill-creator, improve-skill |
| [synapse-readme-maintainer](synapse/agents/synapse/synapse-readme-maintainer.md) | Maintains README-index invariant for the ancestor path of a changed synapse — adds/updates/removes rows; rewrites top-of-file one-liner on factual drift | skill-creator, agent-creator, protocol-creator, improve-skill |

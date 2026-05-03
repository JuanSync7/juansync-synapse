# Skills Registry

Full inventory of all skills. Before creating a new skill, check if one already covers the capability you need. Pipeline-routable skills are also registered in `synapse/SKILLS_REGISTRY.yaml` with their stage metadata.

| Skill | Description | Domain | Pipeline Stage | Status |
|-------|-------------|--------|----------------|--------|
| [parallel-agents-dispatch](../synapse/skills/orchestration/parallel-agents-dispatch/SKILL.md) | Execute implementation plan via parallel subagents | orchestration | `code` | stable |
| [skill-brainstorm](../synapse/skills/skill/skill-brainstorm/SKILL.md) | **Deprecated** — superseded by synapse-brainstorm | skill | — | deprecated |
| [synapse-brainstorm](../synapse/skills/skill/synapse-brainstorm/SKILL.md) | Generalized brainstorm for any artifact type — coaching, pressure-testing, N memos | skill | — | stable |
| [skill-creator](../synapse/skills/skill/skill-creator/SKILL.md) | Creates new skills with EVAL.md and registry entry | skill | — | stable |
| [improve-skill](../synapse/skills/skill/improve-skill/SKILL.md) | Karpathy-style score-fix-rescore loop for skill quality | skill | — | stable |
| [write-skill-eval](../synapse/skills/skill/write-skill-eval/SKILL.md) | Generates EVAL.md with output criteria and test prompts | skill | — | stable |
| [synapse-gatekeeper](../synapse/skills/skill/synapse-gatekeeper/SKILL.md) | Certifies skill promotion readiness (APPROVE/REVISE/REJECT) against governance criteria | skill | — | stable |
| [agent-creator](../synapse/skills/agent/agent-creator/SKILL.md) | Creates new agent definitions with frontmatter and taxonomy alignment | agent | — | draft |
| [write-agent-eval](../synapse/skills/agent/write-agent-eval/SKILL.md) | Generates evaluation criteria for agent definitions | agent | — | draft |
| [protocol-creator](../synapse/skills/protocol/protocol-creator/SKILL.md) | Creates new protocol definitions with frontmatter and taxonomy alignment | protocol | — | stable |
| [write-protocol-eval](../synapse/skills/protocol/write-protocol-eval/SKILL.md) | Generates conformance testing criteria for protocol definitions | protocol | — | draft |
| [skill-router](../synapse/skills/meta/skill-router/SKILL.md) | Routes user intent to the right skill based on domain matching | meta | — | stable |
| [autonomous-orchestrator](../synapse/skills/orchestration/autonomous-orchestrator/SKILL.md) | Fully autonomous dev pipeline with stakeholder gates | orchestration | — | stable |
| [stakeholder-reviewer](../synapse/skills/orchestration/stakeholder-reviewer/SKILL.md) | Evaluates decisions against stakeholder persona (APPROVE/REVISE/ESCALATE) | orchestration | — | stable |

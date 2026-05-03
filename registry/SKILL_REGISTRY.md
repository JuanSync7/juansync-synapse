# Skills Registry

Full inventory of all skills. Before creating a new skill, check if one already covers the capability you need. Pipeline-routable skills are also registered in `synapse/SKILLS_REGISTRY.yaml` with their stage metadata.

| Skill | Description | Domain | Pipeline Stage | Status |
|-------|-------------|--------|----------------|--------|
| [write-scope-docs](../src/skills/docs/write-scope-docs/SKILL.md) | Scope document with phase plan, scope boundary, and readiness gate | docs | — | stable |
| [write-architecture-docs](../src/skills/docs/write-architecture-docs/SKILL.md) | Architecture doc with technology decisions, component boundaries, and data flow patterns | docs | — | stable |
| [write-spec-docs](../src/skills/docs/write-spec-docs/SKILL.md) | Formal requirements spec with FRs, NFRs, acceptance criteria | docs | `spec` | stable |
| [write-spec-summary](../src/skills/docs/write-spec-summary/SKILL.md) | Concise spec digest synced with companion spec | docs | `spec-summary` | stable |
| [write-design-docs](../src/skills/docs/write-design-docs/SKILL.md) | Technical design with task decomposition and code contracts | docs | `design` | stable |
| [write-implementation-docs](../src/skills/docs/write-implementation-docs/SKILL.md) | Phased implementation plan from design doc (canonical impl stage) | docs | `impl` | stable |
| [build-plan](../src/skills/code/build-plan/SKILL.md) | Implementation plan skill — retained for direct invocation; pipeline use via write-implementation-docs | code | — | draft |
| [parallel-agents-dispatch](../synapse/skills/orchestration/parallel-agents-dispatch/SKILL.md) | Execute implementation plan via parallel subagents | orchestration | `code` | stable |
| [write-engineering-guide](../src/skills/docs/write-engineering-guide/SKILL.md) | Post-implementation engineering guide | docs | `eng-guide` | stable |
| [patch-docs](../src/skills/docs/patch-docs/SKILL.md) | Diff-driven incremental doc patcher — targeted section updates from git diffs | docs | `patch-docs` | stable |
| [write-test-docs](../src/skills/docs/write-test-docs/SKILL.md) | Test planning document from engineering guide and spec | docs | `test-docs` | stable |
| [write-module-tests](../src/skills/code/write-module-tests/SKILL.md) | Pytest test code from test plan (per-module) | code | `tests` | draft |
| [write-test-coverage](../src/skills/docs/write-test-coverage/SKILL.md) | Test coverage register mapping acceptance criteria to test scenarios | docs | `test-coverage` | stable |
| [test-runner](../src/skills/code/test-runner/SKILL.md) | Run pytest test suites safely through a validated execution pipeline | code | — | draft |
| [jira-reporter](../external/jira-suite/skills/jira-reporter/SKILL.md) | JIRA updates as observability/HITL layer during agent workflows | integration | — | stable |
| [auto-research](../src/skills/optimization/auto-research/SKILL.md) | Autonomous iterative improvement loop with subagent-per-iteration execution | optimization | — | stable |
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
| [doc-authoring](../src/skills/docs/doc-authoring/SKILL.md) | Router directing to write-spec-summary, write-spec-docs, or write-engineering-guide | docs | — | stable |
| [brainstorm](../src/skills/meta/brainstorm/SKILL.md) | Generic brainstorm protocol with indexed notepad, phase gates, and mentor circuit breaker | meta | — | stable |
| [autonomous-orchestrator](../synapse/skills/orchestration/autonomous-orchestrator/SKILL.md) | Fully autonomous dev pipeline with stakeholder gates | orchestration | — | stable |
| [stakeholder-reviewer](../synapse/skills/orchestration/stakeholder-reviewer/SKILL.md) | Evaluates decisions against stakeholder persona (APPROVE/REVISE/ESCALATE) | orchestration | — | stable |
| [langgraph-architect](../src/skills/frameworks/langgraph-architect/SKILL.md) | Design, review, or code-review LangGraph workflow graphs | frameworks | — | stable |
| [create-animation-page](../src/skills/creative/create-animation-page/SKILL.md) | Single-page interactive animation as one HTML file with embedded CSS/JS | creative | — | draft |
| [write-postmortem](../src/skills/docs/write-postmortem/SKILL.md) | Structured blameless postmortem document from incident facts | docs | — | stable |

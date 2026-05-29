# Skills Registry

Full inventory of all skills. Before creating a new skill, check if one already covers the capability you need. Pipeline-routable skills are also registered in [`synapse/SKILLS_REGISTRY.yaml`](../synapse/SKILLS_REGISTRY.yaml) with their stage metadata.

Schema: see [registry/README.md](README.md).

| Skill | Description | Status | Consumers |
|------|-------------|--------|-----------|
| [synapse-router-artifact-brainstormer](../synapse/skills/synapse-router-artifact-brainstormer/SKILL.md) | Use when exploring an idea for a new artifact (skill, tool, agent, protocol) or reworking an existing one — before committing to build | draft | synapse-git-dispatch-cr, synapse-router-artifact-creator, synapse-router-eval-writer, synapse-skill |
| [synapse-router-artifact-creator](../synapse/skills/synapse-router-artifact-creator/SKILL.md) | Use when creating a new skill, protocol, agent, or tool in ai-synapse. Routes to type-specific creation flow. | draft | synapse-router-suite-validator, synapse-skill, synapse-skill-anatomy-reviewer, synapse-skill-companion-auditor, synapse-skill-design-grader, synapse-skill-signal-orchestrator |
| [synapse-router-artifact-gatekeeper](../synapse/skills/synapse-router-artifact-gatekeeper/SKILL.md) | Use when a skill, agent, protocol, tool, or pathway is complete and ready for promotion review, or to check if an artifact meets the bar to land in ai-synapse. | draft | synapse-router-artifact-brainstormer, synapse-router-artifact-creator, synapse-router-eval-writer, synapse-router-suite-validator, synapse-skill, synapse-skill-companion-auditor, synapse-skill-signal-orchestrator |
| [synapse-router-eval-writer](../synapse/skills/synapse-router-eval-writer/SKILL.md) | Use when generating an EVAL.md for a skill, protocol, agent, or tool. | draft | synapse-router-artifact-gatekeeper, synapse-router-suite-validator, synapse-skill, synapse-skill-skill-improver |
| [synapse-router-suite-validator](../synapse/skills/synapse-router-suite-validator/SKILL.md) | Use when adding or updating an external submodule suite (under external/), or when checking whether a candidate suite conforms to ai-synapse conventions before it is wired in. Sweeps every artifact in the suite and produces a structural conformance rollup. | draft | — |
| [synapse-skill-skill-improver](../synapse/skills/synapse-skill-skill-improver/SKILL.md) | Use when a skill needs quality improvement. Triggered by improve this skill, fix the skill, review skill quality, make the skill better. | draft | synapse-observability-execution-trace, synapse-meta-readme-maintainer, synapse-router-artifact-brainstormer, synapse-router-artifact-creator, synapse-router-artifact-gatekeeper, synapse-router-eval-writer, synapse-router-suite-validator, synapse-skill, synapse-skill-anatomy-reviewer, synapse-skill-design-grader, synapse-skill-signal-orchestrator |
| [test-lint](../src/skills/code/test-lint/SKILL.md) | Read-only lint sweep (ruff/mypy/bandit/vulture/detect-secrets + descriptive-test docstring validator) — produces LintReport feeding test-fix | draft | test-fix |
| [test-audit](../src/skills/code/test-audit/SKILL.md) | Read-only diagnostic audit of test coverage health — produces AuditGapReport feeding test-generate/evaluate/integrate | draft | test-generate, test-evaluate |
| [test-fix](../src/skills/code/test-fix/SKILL.md) | Per-category lint remediation (ruff→mypy→bandit→vulture→secrets) with re-verification; surfaces requires-human-review and opens soft-gated PR | draft | — |
| [test-generate](../src/skills/code/test-generate/SKILL.md) | Per-gap test generation (branch-map → input → Hypothesis → green-run → per-gap mutation → assertion-quality → HARD-GATE intent review → commit) consuming AuditGapReport | draft | — |
| [test-evaluate](../src/skills/code/test-evaluate/SKILL.md) | Per-module mock-vs-real classification (boundary-detect → mock-inventory → score → assign lifecycle → emit IntegrationStrategy → soft-gate PR); analysis-only | draft | — |
| [test-integrate](../src/skills/code/test-integrate/SKILL.md) | Per-item conversion of mock-integration tests to real-service tests (pick-pattern → spin-up → convert → flake-check → hard-gate PR → merge → edge-feedback); HITL-gated, never auto-merges, never points at production | draft | — |
| [test-runner](../src/skills/code/test-runner/SKILL.md) | Run pytest test suites safely through a validated execution pipeline | draft | — |
| [write-module-tests](../src/skills/code/write-module-tests/SKILL.md) | Pytest test code from test plan (per-module) | draft | — |
| [build-plan](../src/skills/code/build-plan/SKILL.md) | Implementation plan skill — retained for direct invocation; pipeline use via write-implementation-docs | draft | — |
| [docs-claim-doc-shrinker](../src/skills/docs/docs-claim-doc-shrinker/SKILL.md) | Audit and compress claim-based markdown (identity, style, principle, decision docs). Two-phase: `audit` writes a per-claim keep/cut/merge checklist; `compress` rewrites the doc preserving every kept claim with post-write entailment verification. | stable | — |
| [write-scope-docs](../src/skills/docs/write-scope-docs/SKILL.md) | Scope document with phase plan, scope boundary, and readiness gate | stable | — |
| [write-architecture-docs](../src/skills/docs/write-architecture-docs/SKILL.md) | Architecture doc with technology decisions, component boundaries, and data flow patterns | stable | — |
| [write-spec-docs](../src/skills/docs/write-spec-docs/SKILL.md) | Formal requirements spec with FRs, NFRs, acceptance criteria | stable | — |
| [write-spec-summary](../src/skills/docs/write-spec-summary/SKILL.md) | Concise spec digest synced with companion spec | stable | — |
| [write-design-docs](../src/skills/docs/write-design-docs/SKILL.md) | Technical design with task decomposition and code contracts | stable | — |
| [write-implementation-docs](../src/skills/docs/write-implementation-docs/SKILL.md) | Phased implementation plan from design doc (canonical impl stage) | stable | — |
| [write-engineering-guide](../src/skills/docs/write-engineering-guide/SKILL.md) | Post-implementation engineering guide | stable | — |
| [patch-docs](../src/skills/docs/patch-docs/SKILL.md) | Diff-driven incremental doc patcher — targeted section updates from git diffs | stable | — |
| [write-test-docs](../src/skills/docs/write-test-docs/SKILL.md) | Test planning document from engineering guide and spec | stable | — |
| [write-test-coverage](../src/skills/docs/write-test-coverage/SKILL.md) | Test coverage register mapping acceptance criteria to test scenarios | stable | — |
| [write-postmortem](../src/skills/docs/write-postmortem/SKILL.md) | Structured blameless postmortem document from incident facts | stable | — |
| [doc-authoring](../src/skills/docs/doc-authoring/SKILL.md) | Router directing to write-spec-summary, write-spec-docs, or write-engineering-guide | stable | — |
| [brainstorm](../src/skills/meta/brainstorm/SKILL.md) | Generic brainstorm protocol with indexed notepad, phase gates, and mentor circuit breaker | stable | — |
| [auto-research](../src/skills/optimization/auto-research/SKILL.md) | Autonomous iterative improvement loop with subagent-per-iteration execution | stable | — |
| [langgraph-architect](../src/skills/framework/langgraph-architect/SKILL.md) | Design, review, or code-review LangGraph workflow graphs | stable | — |
| [create-animation-page](../src/skills/creative/create-animation-page/SKILL.md) | Single-page interactive animation as one HTML file with embedded CSS/JS | draft | — |
| [jira-reporter](../external/jira-suite/skills/jira-reporter/SKILL.md) | JIRA updates as observability/HITL layer during agent workflows | stable | — |
| [delivery-orchestration-plan-executor](../src/skills/delivery/delivery-orchestration-plan-executor/SKILL.md) | Use when the user signals start building, /build, execute the plan, ship this, or asks to deliver a multi-slice plan end-to-end. Not for single-task edits, research loops, or throughput-only parallel dispatch. | stable | — |

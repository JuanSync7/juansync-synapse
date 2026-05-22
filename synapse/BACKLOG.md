# synapse/ Framework Backlog

Non-binding backlog of framework-level ideas surfaced during alpha cleanup. Items here are *captured*, not *committed* — promote to a real skill, agent, or design doc when ready to build.

---

## adopter-CI-template (skill + workflow templates)

**Problem.** ai-synapse's quality bar has two tiers: Tier 1 (structural, deterministic, runs in `.githooks/pre-commit`) and Tier 2 (quality, LLM-judged via `/synapse-router-artifact-gatekeeper`). Today only Tier 1 is enforced automatically — Tier 2 is manual at PR time. Adopter teams have no turnkey way to wire `/synapse-router-artifact-gatekeeper` into their PR workflow, so quality validation depends on whoever remembers to run it.

**Proposal.** Ship a thin skill `adopter-ci-template` that scaffolds portable CI workflow files into an adopter repo. Plus the templates themselves under `templates/ci/` at repo root.

**Shape.**

| Layer | Mechanism | LLM needed? |
|-------|-----------|-------------|
| Tier 1 (structural) | GitHub Action that runs `.githooks/pre-commit` on changed files | No |
| Tier 2 (quality) | GitHub Action that, on changed-artifact PRs, dispatches a configurable LLM CLI (`claude --headless`, `codex`, `gemini`, etc.) to run `/synapse-router-artifact-gatekeeper` and posts the verdict as a PR comment | Yes — but CLI is swappable |

**Open design questions** (need brainstorm before building):
1. Which CI providers to support out-of-box? (GitHub Actions only is the realistic v1; GitLab/CircleCI as templates only)
2. What's the LLM CLI contract? Define a minimal interface (input: artifact path; output: verdict text) and let adopters plug in their preferred CLI.
3. How is the gatekeeper verdict transported? PR comment vs check-run vs gate-required-status.
4. Where does the LLM API key live? OIDC vs repo secrets vs adopter's own runner.
5. Should pre-commit (local) also offer a Tier 2 option for those willing to wait for LLM round-trip? Probably no — pre-commit must stay fast.

**Why not now.** The blast radius (which CIs, which CLIs, what verdict transport) is broad enough that brainstorming first will save building twice. Not a blocker for alpha.

**Owner / unblocker.** Brainstorm via `/synapse-router-artifact-brainstormer adopter-ci-template`, then build.

---

## protocol-eval-*, agent-eval-*, tool-eval-* decomposition

**Problem.** `synapse-router-eval-writer` (skill flow) decomposes eval authoring into surface-specific sub-agents under `synapse/agents/synapse/skill-eval/`: `synapse-skill-eval-prompter` (test prompts), `synapse-skill-eval-judge` (output criteria), `synapse-skill-eval-auditor` (execution criteria). Each agent owns one eval surface. The protocol, agent, and tool flows of `synapse-router-eval-writer` do not have an equivalent decomposition — eval criteria are produced inline within the skill, with no per-surface sub-agents and no `synapse/agents/synapse/protocol-eval/`, `synapse/agents/synapse/agent-eval/`, or `synapse/agents/synapse/tool-eval/` directories. This means: (a) no reuse across pipelines (e.g., `/improve-protocol` if it ever exists), (b) authoring concerns leak into orchestration, (c) inconsistent contributor mental model (skill works one way, others another).

**Proposal.** Mirror the skill-eval pattern for the surfaces each artifact actually has:

| Artifact | Surfaces | Sub-agents |
|----------|----------|------------|
| Skill | input + output + execution | prompter + judge + auditor (already exists) |
| Protocol | trigger-firing conformance (no input/output surface) | `protocol-eval-conformance-grader` (does consumer fire trigger?); possibly `protocol-eval-failure-grader` (does it emit failure assertion?) |
| Agent | input + output (+ execution if it dispatches subagents) | `agent-eval-prompter` + `agent-eval-judge` (+ optional `agent-eval-auditor`) |
| Tool | input contract + output contract + side-effects/idempotency | `tool-eval-prompter` (call shapes) + `tool-eval-judge` (output schema/semantics) + `tool-eval-auditor` (idempotency, error paths, side-effect boundaries) |

Land these under `synapse/agents/synapse/protocol-eval/`, `synapse/agents/synapse/agent-eval/`, and `synapse/agents/synapse/tool-eval/`. Update the relevant `synapse-router-eval-writer` flows to dispatch them.

**Open design questions.**
1. Does protocol need a "prompter" at all, or only conformance grading? (Conformance is graded against actual consumer agent runs, not synthetic prompts.)
2. For agents: blind-prompter constraint (synapse-skill-eval-prompter sees only name + description) — does it apply to agents, or do agents need fuller context?
3. Migration: rewrite the protocol/agent flows of `synapse-router-eval-writer` to dispatch sub-agents, or build the sub-agents and let the flows continue inline until /improve-protocol forces reuse?

**Why not now.** Cross-cutting refactor — touches `synapse-router-eval-writer` (recently stabilized), creates new agent directories, requires registry + taxonomy updates. Skill-signal-reviewer is the smaller, higher-leverage win to ship first.

**Owner / unblocker.** Brainstorm via `/synapse-router-artifact-brainstormer` after synapse-skill-signal-orchestrator + agent-signal-reviewer establish the post-draft review pattern.

---

## synapse-agent-signal-orchestrator and synapse-tool-signal-orchestrator

**Problem.** Symmetric gap to synapse-skill-signal-orchestrator. Agent recipes (`{synapse,src}/agents/<domain>/<name>.md`) and tool definitions (`{synapse,src}/tools/<domain>/...`) are authoring artifacts whose quality is currently caught only indirectly — there's no dedicated signal-strength reviewer paralleling `synapse-protocol-signal-reviewer`.

For agents the surface is: clear inputs, clear outputs, no implicit state, model-appropriate scope, single role.
For tools the surface is: input/output schema clarity, idempotency declared, side-effect boundary explicit, error contract precise.

**Proposal.** Add `synapse-agent-signal-orchestrator` under `synapse/agents/agent-review/` and `synapse-tool-signal-orchestrator` under `synapse/agents/tool-review/`. Dispatched by `agent-creator` / `tool-creator` (and `synapse-router-artifact-creator` flow-agent / flow-tool) at a `[R]` phase before eval handoff.

**Open design questions.**
1. Universal anatomy for agents and tools — is there one tight enough to validate? (Both vary more than protocols.)
2. What checks transfer from `synapse-protocol-signal-reviewer` and which need new ones (e.g., input/output contract clarity for agents; idempotency/side-effect declarations for tools)?
3. Does it run before or after the corresponding `synapse-router-eval-writer` flow?

**Why not now.** Tackle synapse-skill-signal-orchestrator first to establish the pattern beyond the protocol case; agent and tool reviewers can copy the pattern once proven.

**Owner / unblocker.** Brainstorm after `synapse-skill-signal-orchestrator` ships.

---

## (template — copy this when adding a new backlog item)

### <kebab-case-name>

**Problem.** What gap or pain motivates this.

**Proposal.** One paragraph on the shape — skill / agent / protocol / tool / docs / etc.

**Open design questions.** What needs brainstorming before building.

**Why not now.** Why this is captured but not staged.

**Owner / unblocker.** Who decides when this lands, or what unblocks it.

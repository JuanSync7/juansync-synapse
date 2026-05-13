# ai-synapse Governance

> `synapse-router-artifact-gatekeeper` loads this file when issuing promotion verdicts.

This document defines what belongs in ai-synapse, the criteria an artifact (skill, agent, protocol, tool, or pathway) must meet to land here, and the lifecycle for submoduled suites. It is the authoritative reference — not loaded at runtime by individual skills except where noted.

---

## What Belongs in ai-synapse

ai-synapse is a curated library, not a scratch pad. A skill belongs here when it meets all three conditions:

1. **Reusable across projects** — the skill is not tied to a single codebase, team, or context. It solves a category of problem, not a one-off task.
2. **Has a passing EVAL.md** — an EVAL.md exists, was generated or reviewed by `/synapse-router-eval-writer`, and the skill scores ≥ 80 against it.
3. **Not a duplicate** — no existing skill in the registry already covers the same intent at the same scope. A variation in phrasing is not enough — the use case must be genuinely distinct.

### Agent Definitions

Agent definitions (`{synapse,src}/agents/`) are internal recipes dispatched by skills — never user-invocable. They follow the same governance rigor as skills, adapted for their role:

- **YAML frontmatter required** — `name`, `description`, `domain`, `role`, and `tags` fields, with `domain` and `role` values from `AGENT_TAXONOMY.md`
- **Gatekeeper review required** — agents land via promotion PRs reviewed by `/synapse-router-artifact-gatekeeper`, same as skills
- **No standalone EVAL.md required** — agents are tested indirectly through the skills that dispatch them. To generate an EVAL.md when needed, use `/synapse-router-eval-writer agent <path>` (the unified eval router)
- **Listed in AGENTS_REGISTRY.md** — for discovery, not `SKILLS_REGISTRY.yaml`
- **Installed separately** — `scripts/install.sh agents` symlinks them to `~/.claude/agents/`

An agent belongs in `{synapse,src}/agents/` when it is dispatched by 1+ skills and encapsulates a distinct persona or capability (e.g., impartial judge, blind prompt author). If only one skill uses it and it's short, inline it in the skill instead.

### Protocol Definitions

Protocols (`{synapse,src}/protocols/`) are shared conventions and schemas injected into agents by observers — never executed directly. They define structured formats for inter-agent communication and observability.

- **YAML frontmatter required** — `name`, `description`, `domain`, `type`, and `tags` fields, with `domain` and `type` values from `PROTOCOL_TAXONOMY.md`
- **Gatekeeper review required** — protocols land via promotion PRs reviewed by `/synapse-router-artifact-gatekeeper`
- **No standalone EVAL.md required** — protocols are evaluated via conformance testing (dispatch an agent with the protocol injected, check if output conforms to the schema). To generate an EVAL.md when needed, use `/synapse-router-eval-writer protocol <path>` (the unified eval router)
- **Zero-overhead design** — a protocol must have no cost when not injected. It is always externally injected by an observer, never self-loaded by the agent

A protocol belongs in `{synapse,src}/protocols/` when it defines a reusable convention that 2+ agents or observers need to agree on (e.g., execution trace format, inter-agent message schema).

### Tool Definitions

Tools (`{synapse,src}/tools/`) are mechanical utilities — scripts, wrappers, or external integrations that perform a deterministic action. They contain no judgment or persona; if a tool needs judgment, it should be an agent instead.

- **YAML frontmatter required** — `name`, `description`, `domain`, `action`, `type`, and `tags` fields, with `domain` and `action` values from `TOOL_TAXONOMY.md`
- **Type classification** — `type` must be one of `external`, `internal`, or `wrapper` (from `TOOL_TAXONOMY.md`) and must match actual content
- **Gatekeeper review required** — tools land via promotion PRs reviewed by `/synapse-router-artifact-gatekeeper`
- **No standalone EVAL.md** — tools are tested by the skills or agents that invoke them
- **Listed in TOOL_REGISTRY.md** — for discovery
- **Execution model documented** — the TOOL.md must clearly describe inputs, outputs, and how to invoke the tool

A tool belongs in `{synapse,src}/tools/` when it encapsulates a reusable mechanical operation (e.g., score computation, schema validation, format conversion) that 1+ skills or agents need to invoke.

### Pathway Definitions

Pathways (`pathways/`) are curated bundles of synapses (skills, agents, protocols, tools) installed together for a specific harness and use case. They define *what to install*, not *how to execute*.

- **YAML format** — each pathway is a `.yaml` file with `name`, `description`, `harness`, `tags`, and `synapses` fields
- **Harness value from taxonomy** — `harness` must be a value from `taxonomy/PATHWAY_TAXONOMY.md`
- **All synapse paths resolve** — every path listed under `synapses:` must point to an existing artifact on disk
- **Gatekeeper review required** — pathways land via promotion PRs reviewed by `/synapse-router-artifact-gatekeeper`
- **Listed in PATHWAY_REGISTRY.md** — for discovery
- **Naming conventions** — documented in `taxonomy/PATHWAY_TAXONOMY.md` and evaluated by gatekeeper at PR review time (not enforced by pre-commit)

A pathway belongs in `pathways/` when it defines a reusable installation bundle — a coherent set of synapses that work together for a specific role, domain, or workflow.

### Draft Skills

Skills may land on `main` as **drafts** — functional but not yet gatekeeper-certified. A draft skill:

- Has a `SKILL.md` and `EVAL.md` (pre-commit hook enforced)
- Passes structural checks (Tier 1)
- Has **not** been certified by `/synapse-router-artifact-gatekeeper` (Tiers 2-3 pending)

Draft skills are usable but carry no quality guarantee. To track draft status, the skill's entry in `SKILLS_REGISTRY.yaml` should include `status: draft`. A skill without a `status` field is assumed certified.

**Promoting a draft:** Run `/synapse-skill-skill-improver` until eval score ≥ 80, then `/synapse-router-artifact-gatekeeper`. Update `status: certified` (or remove the field) in the registry entry.

### Standalone vs. Submodule

| Type | Description | Lives in |
|------|-------------|----------|
| Standalone | One SKILL.md + EVAL.md, no shared config, no multi-skill coordination | Directly in `{synapse,src}/skills/<domain>/<skill-name>/` |
| Submodule suite | Multiple related skills with shared templates, config, or CI | Own repo, wired in as a git submodule |

**Keep standalone** when the skill has no infrastructure dependencies and doesn't need its own CI.

**Extract to a submodule** when the skill is part of a suite with shared infrastructure, needs its own release cycle, or is meant to be adopted independently by other teams.

---

## Promotion Criteria

A skill must clear three tiers to be approved for merge.

### Tier 1 — Structural

Checked automatically by the pre-commit hook. No LLM required.

- [ ] `SKILL.md` exists in the skill directory
- [ ] `EVAL.md` exists alongside `SKILL.md` (**REJECT if absent**)
- [ ] Frontmatter is complete: `name`, `description`, `domain`, `intent` all present
- [ ] `domain` value exists in `SKILL_TAXONOMY.md`
- [ ] `intent` value exists in `SKILL_TAXONOMY.md`
- [ ] `tags` is a well-formed array of lowercase hyphenated strings
- [ ] `user-invocable` field is present
- [ ] `argument-hint` is present when `user-invocable: true`
- [ ] Domain `README.md` has a row for this skill
- [ ] Skill name is globally unique (no collision in `synapse/SKILLS_REGISTRY.yaml` or `~/.claude/skills/`)

### Tier 2 — Quality

Evaluated by `synapse-router-artifact-gatekeeper` against skill design principles.

- [ ] `description` is a routing contract — specifies *when* the skill fires, not what it does
- [ ] Eval score ≥ 80 (must be provided; unverified score blocks APPROVE)
- [ ] `SKILL.md` is under 500 lines
- [ ] Every instruction traces to a failure mode (no instruction without "without this, the agent does X")
- [ ] Wrong-Tool Detection section is present (redirects to sibling skills on misfire)
- [ ] `references/` is used correctly — companion files load at specific decision points, not inlined wholesale

### Tier 3 — Registry

- [ ] Pipeline-routable skills have a `pipeline:` block in `synapse/SKILLS_REGISTRY.yaml` with `stage_name`, `input_type`, `output_type`, `context_type`, and `requires_all`/`requires_any`
- [ ] Non-pipeline-routable skills are listed in the registry for inventory (no `pipeline:` block, with a comment explaining why)
- [ ] If registered: `stage_name` is unique across the registry
- [ ] If registered: `requires_all`/`requires_any` entries resolve to real stage names

### Agent Promotion

Agents clear two tiers. Evaluated by `synapse-router-artifact-gatekeeper` using `references/agent-checklist.md`.

#### Tier 1 — Structural

- [ ] Agent `.md` file exists in `{synapse,src}/agents/<domain>/` and is non-empty
- [ ] Frontmatter complete: `name`, `description`, `domain`, `role` all present
- [ ] `domain` value exists in `AGENT_TAXONOMY.md`
- [ ] `role` value exists in `AGENT_TAXONOMY.md`
- [ ] `tags` is a well-formed array of lowercase hyphenated strings
- [ ] Name follows `<domain>-<concern>-<role>` convention
- [ ] Name is globally unique (no collision in `AGENTS_REGISTRY.md`)
- [ ] Listed in `AGENTS_REGISTRY.md` with correct description and consumer list
- [ ] Domain README has a row linking this agent

#### Tier 2 — Quality

- [ ] Clear persona/role description in the opening paragraph
- [ ] Every instruction traces to a failure mode
- [ ] Under 300 lines
- [ ] Consumer skills identified (which skills dispatch this agent)
- [ ] No user-facing language (agents are never user-invocable)

### Protocol Promotion

Protocols clear two tiers. Evaluated by `synapse-router-artifact-gatekeeper` using `references/protocol-checklist.md`.

#### Tier 1 — Structural

- [ ] Protocol `.md` file exists in `{synapse,src}/protocols/<domain>/` and is non-empty
- [ ] Frontmatter complete: `name`, `description`, `domain`, `type` all present
- [ ] `domain` value exists in `PROTOCOL_TAXONOMY.md`
- [ ] `type` value exists in `PROTOCOL_TAXONOMY.md`
- [ ] `tags` is a well-formed array of lowercase hyphenated strings
- [ ] Mental model paragraph present (explains WHY the protocol exists)
- [ ] Contract section present (imperative rules: MUST/NEVER/BEFORE/AFTER)
- [ ] Failure assertion present (`PROTOCOL FAILURE: [protocol-name] — [reason]`)
- [ ] Domain README has a row linking this protocol

#### Tier 2 — Conformance

- [ ] Contract is unambiguous (named trigger moments, commitment language)
- [ ] Contract uses imperative language (MUST/NEVER/STOP/BEFORE/AFTER/THEN)
- [ ] Failure assertion is imperative (produces output, not prose description)
- [ ] Zero-overhead design confirmed (no cost when not injected)

### Tool Promotion

Tools clear two tiers. Evaluated by `synapse-router-artifact-gatekeeper`.

#### Tier 1 — Structural

- [ ] `TOOL.md` file exists in `{synapse,src}/tools/<domain>/` and is non-empty
- [ ] Frontmatter complete: `name`, `description`, `domain`, `action`, `type` all present
- [ ] `domain` value exists in `TOOL_TAXONOMY.md`
- [ ] `action` value exists in `TOOL_TAXONOMY.md`
- [ ] `type` value is one of `external`, `internal`, `wrapper` (from `TOOL_TAXONOMY.md`)
- [ ] `tags` is a well-formed array of lowercase hyphenated strings
- [ ] Domain README has a row linking this tool
- [ ] Listed in `TOOL_REGISTRY.md`

#### Tier 2 — Quality

- [ ] `type` classification accuracy — `external`/`internal`/`wrapper` matches actual content
- [ ] Execution model documented — inputs, outputs, and invocation are clearly described
- [ ] No judgment in the tool definition — tools are mechanical; if it contains judgment, it should be an agent
- [ ] Under 300 lines

### Pathway Promotion

Pathways clear two tiers. Evaluated by `synapse-router-artifact-gatekeeper`.

#### Tier 1 — Structural

- [ ] Pathway `.yaml` file exists and is valid YAML
- [ ] Required fields present: `name`, `description`, `harness`, `synapses`
- [ ] `harness` value exists in `taxonomy/PATHWAY_TAXONOMY.md`
- [ ] All synapse paths listed under `synapses:` resolve to existing artifacts on disk
- [ ] If `inherits:` is set, the parent pathway exists
- [ ] Listed in `PATHWAY_REGISTRY.md`

#### Tier 2 — Quality

- [ ] Naming follows one of the 4 documented patterns in `taxonomy/PATHWAY_TAXONOMY.md` (domain-focused, role-focused, workflow-focused, single-domain)
- [ ] Description is meaningful (not empty or placeholder)
- [ ] Composition coherence — the synapses listed make sense together for the stated purpose
- [ ] Tags are relevant to the pathway's stated purpose

---

## REVISE vs. REJECT

**REVISE** — fixable gaps. The skill's foundation is sound; specific items need correction before merge.

Examples:
- Missing registry entry (skill is pipeline-routable but has no `pipeline:` block)
- Eval score below 80 (run `/synapse-skill-skill-improver` to raise it)
- `description` reads as a workflow summary instead of a routing trigger
- Domain `README.md` is missing the skill's row
- `argument-hint` absent despite `user-invocable: true`
- `references/` inlined rather than loaded progressively

**REJECT** — fundamental problem. The skill cannot be promoted in its current form; the issue is not a gap to fill but a structural disqualifier.

Examples:
- `EVAL.md` is missing (no certification is possible without it)
- Name collision with an existing skill in the registry or `~/.claude/skills/`
- Skill duplicates an existing skill's use case (not a distinct intent)
- Skill has significant shared infrastructure that should be in its own repo (should be a submodule, not standalone)

**Agent-specific:**
- REVISE: missing AGENTS_REGISTRY.md entry, name doesn't follow convention, consumer skills not identified
- REJECT: frontmatter absent, domain/role not in AGENT_TAXONOMY.md

**Protocol-specific:**
- REVISE: missing example, injection instructions unclear, zero-overhead not confirmed
- REJECT: frontmatter absent, domain/type not in PROTOCOL_TAXONOMY.md, no schema block

**Tool-specific:**
- REVISE: missing TOOL_REGISTRY.md entry, execution model undocumented, type classification doesn't match content
- REJECT: frontmatter absent, domain/action not in TOOL_TAXONOMY.md, contains judgment (should be an agent)

**Pathway-specific:**
- REVISE: naming doesn't follow taxonomy patterns, description is placeholder, tags irrelevant, composition incoherent
- REJECT: harness not in PATHWAY_TAXONOMY.md, synapse paths don't resolve, missing required fields

---

## Contribution Workflow

### Branching Model

```
feature/<synapse>/<artifact-name>  →  develop  →  main
```

Where `<synapse>` is one of: `skill`, `agent`, `protocol`, `tool`.

- **`feature/*`** — contributor works here. Changes + a `change_requests/` file documenting the rationale.
- **`develop`** — integration branch. Artifact owner reviews the CR memo + diff, and if accepted, deletes the change request file and merges.
- **`main`** — release branch. Maintainer merges from `develop` only when **no `change_requests/` files remain** in the PR diff — their absence is proof that every change was owner-reviewed.

**Branch naming convention:** `feature/<synapse>/<name>` — e.g., `feature/skill/asic-lint-fix`, `feature/agent/synthesis-monitor`, `feature/tool/gpu-profiler-v2`. This gives filterable grouping (`feature/skill/*`) without hierarchical merge cascading.

**Why two gates, not one:** artifacts are directory-isolated so cross-artifact conflicts are rare, but the `develop` → `main` gate gives a maintainer the chance to batch-review and verify all CRs were resolved before anything ships.

### Steps

1. **Build** — use `/synapse-router-artifact-creator skill` to scaffold the skill, or author it manually.
2. **Improve** — run `/synapse-skill-skill-improver` until the eval score reaches ≥ 80.
3. **Certify** — run `/synapse-router-artifact-gatekeeper <skill-path> --score <score>`. Resolve any REVISE gaps.
4. **PR to develop** — open a pull request with the APPROVE verdict pasted into the description. Include any `change_requests/` files documenting the rationale. The artifact owner reviews the CR + diff, deletes the CR file on acceptance, and merges.
5. **PR to main** — maintainer merges `develop` → `main`. The PR must contain **no `change_requests/` files** — if any are present, the merge is blocked until the artifact owner resolves them.

A PR without an APPROVE verdict in the description will not be merged.

---

## Submodule Lifecycle

### Adding a submodule suite

1. Create the external repo with the skill(s), shared config, and CI.
2. Add it as a git submodule in this repo:
   ```bash
   git submodule add <repo-url> src/skills/<domain>/<suite-name>
   ```
3. Run `make init` to configure git hooks.
4. Register the skill(s) in `synapse/SKILLS_REGISTRY.yaml` and the domain `README.md`.
5. `scripts/install.sh` works unchanged — it follows symlinks regardless of submodule vs. local source.

### Updating a submodule

Changes to a submoduled skill must land in the external repo first. Then update the pointer here:

```bash
git submodule update --remote src/skills/<domain>/<suite-name>
git add src/skills/<domain>/<suite-name>
git commit -m "chore: update <suite-name> submodule pointer"
```

Never edit submoduled skill files directly in this repo — the changes will be lost on the next update.

### Removing a submodule

1. Add a `# DEPRECATED:` comment to the skill's entry in `synapse/SKILLS_REGISTRY.yaml` and `README.md`.
2. Uninstall the symlink: `./scripts/install.sh clean` (or remove the specific symlink).
3. After one full release cycle with no active use:
   ```bash
   git submodule deinit src/skills/<domain>/<suite-name>
   git rm src/skills/<domain>/<suite-name>
   rm -rf .git/modules/src/skills/<domain>/<suite-name>
   git commit -m "chore: remove deprecated <suite-name> submodule"
   ```

---

## Change Requests

Change requests serve two roles: **scope control** (defer out-of-scope changes) and **merge gating** (their presence blocks `develop` → `main` merges).

When brainstorming or improving a skill reveals that another skill, agent, protocol, tool, or pathway needs updating, drop a change request file in the affected target's `change_requests/` folder rather than expanding scope.

- **One file per change**, named `YYYY-MM-DD-short-description.md`
- **Content:** what needs to change, why, and which brainstorm/skill triggered it. Free-form markdown — no enforced template. Must be self-contained — brainstorm notepads are working memory (`.brainstorms/`, gitignored) and do not ship with the CR.
- **Consumed by** `/synapse-router-artifact-brainstormer` — it checks for `change_requests/` on entry and incorporates pending requests as context.
- **Lifecycle:** contributor creates the CR on a feature branch → artifact owner reviews the CR + implementation diff on the PR to `develop` → owner deletes the CR file on acceptance and merges → `develop` → `main` PR is blocked if any CR files remain. An empty `change_requests/` folder (or no folder) means no pending obligations.

---

## Naming Conventions

Each artifact class owns its naming rules in the corresponding taxonomy file:

- Skills → `taxonomy/SKILL_TAXONOMY.md`
- Agents → `taxonomy/AGENT_TAXONOMY.md`
- Protocols → `taxonomy/PROTOCOL_TAXONOMY.md`
- Tools → `taxonomy/TOOL_TAXONOMY.md`

Each file specifies the structural name pattern and the controlled vocabulary that fills its slots.

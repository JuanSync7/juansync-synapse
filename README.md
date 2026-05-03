<p align="center">
  <picture>
    <img src="https://raw.githubusercontent.com/JuanSync7/ai-synapse/main/assets/banner.svg" alt="AI-Synapse Banner" width="100%"/>
  </picture>
</p>

<p align="center">
  <b>A skill orchestration framework for Claude Code</b><br/>
  <sub>Composable skills for autonomous doc authoring, code generation, testing, and multi-agent pipelines</sub>
</p>

> **Status: pre-release (v0.x).** The framework scaffolding — install, registry, governance, taxonomy, pipeline — is stable. Individual skills are in varying states of maturity (see the `Status` column in [`registry/SKILL_REGISTRY.md`](registry/SKILL_REGISTRY.md)); some are draft stubs reserved for future work.

---

## What is AI-Synapse?

AI-Synapse is a central library of reusable, composable artifacts — skills, agents, protocols, and tools — for [Claude Code](https://claude.ai/code) and other AI coding harnesses. Artifacts (synapses) are installed as symlinks and discovered automatically. Once installed, invoking a skill is as simple as `/write-spec-docs` or `/autonomous-orchestrator` in any Claude Code session.

The repo serves two roles: a **home for standalone artifacts** (self-contained, no shared infrastructure) and a **registry that submodules artifact suites** from external repos (multi-artifact projects with shared config and their own CI). Both are installed the same way via the `cortex` CLI.

### Metaphor

The repo uses two metaphor layers: a **kitchen** metaphor for what artifacts are, and a **brain** metaphor for how they're organized.

**What things are — the kitchen**

| Kitchen | Artifact | What it is |
|---|---|---|
| Equipment | **Tool** | Mechanical capability — scripts, MCP servers, CLI wrappers, external integrations |
| Recipe | **Skill** | Step-by-step procedure that uses tools |
| Cook | **Agent** | Executor with judgment that follows recipes |
| Kitchen rules | **Protocol** | Behavioral contract everyone obeys |

**How they're organized — the brain**

| Brain concept | Maps to | Why it fits |
|---|---|---|
| **Cortex** | The repo | Organized processing system; contains everything |
| **Synapse** | Individual artifact | A specialized junction — each skill, agent, protocol, or tool is a synapse |
| **Pathway** | Profile / bundle | A specific route through the cortex that activates specific synapses together |

A synapse is a set of artifacts you load together. A pathway is a named bundle that installs a specific combination of synapses for a use case.

### End-to-End Skill Development

AI-Synapse includes a complete lifecycle for building skills themselves — from initial idea to production-ready, certified skill:

| Stage | Skill | What it does |
|-------|-------|-------------|
| **Brainstorm** | [`/synapse-brainstorm`](synapse/skills/skill/synapse-brainstorm/) | Coaching brainstorm for any artifact type — discovers whether ideas are artifact-worthy, pressure-tests through five lenses, produces per-artifact memos |
| **Create** | [`/skill-creator`](synapse/skills/skill/skill-creator/) | Scaffolds SKILL.md + EVAL.md with baseline testing and design principles check |
| **Evaluate** | [`/write-skill-eval`](synapse/skills/skill/write-skill-eval/) | Generates or regenerates EVAL.md with output criteria and test prompts |
| **Improve** | [`/improve-skill`](synapse/skills/skill/improve-skill/) | Score-fix-rescore loop until quality criteria are met |
| **Certify** | [`/synapse-gatekeeper`](synapse/skills/skill/synapse-gatekeeper/) | Promotion gate — APPROVE / REVISE / REJECT verdict against governance criteria |

The flow is: **brainstorm → create → improve → certify → PR**. Each stage is optional — jump in wherever your skill is.

---

## Roadmap

### Next

- [ ] Pre-commit hook coverage for tools, pathways, and scripts (taxonomy + registry checks)
- [ ] Shared validation library between `validate.sh` and `.githooks/pre-commit`
- [ ] Example pathways — starter bundles for common use cases
- [ ] `cortex.ps1` — native PowerShell dispatcher for Windows (no WSL required)
- [ ] Protocol and tool lifecycle skills (create → evaluate → certify)
- [ ] Agent creator improvements — companion scaffolding, symlink wiring
- [ ] Pre-commit enforcement of `change_requests/` gate on `main` branch
- [x] ~~Auto-branch creation from `/synapse-brainstorm`~~ — `synapse-cr-dispatcher` tool dispatches CRs to `feature/<synapse>/<name>/<slug>` branches
- [x] ~~Tool test infrastructure~~ — `./cortex test` discovers and runs tool tests; pre-commit auto-runs tests for changed tools

### Future

- [ ] Pathway wizard — interactive `./cortex pathway create` with guided synapse selection
- [ ] Artifact dependency graph visualization
- [ ] CI integration — run `./cortex validate` + gatekeeper in GitHub Actions
- [ ] Marketplace / discovery — searchable artifact index beyond flat registry tables
- [ ] Cross-repo pathway sharing — install pathways from remote cortex repos

---

## Repository Structure

```
ai-synapse/
│
├── cortex                           # Top-level CLI dispatcher (./cortex help)
│
├── src/                             # ai-synapse-owned artifacts
│   ├── skills/
│   │   └── <domain>/               # Skills organized by domain (docs, code, orchestration, etc.)
│   │       └── <skill-name>/       # Each skill: SKILL.md + EVAL.md + companions
│   ├── agents/
│   │   └── <domain>/               # Agents organized by domain (skill-eval, docs, protocol-eval)
│   ├── protocols/
│   │   └── <domain>/               # Protocols organized by domain (observability, memory)
│   ├── tools/
│   │   └── <domain>/               # Tools organized by domain (integration, testing, etc.)
│   │       └── <tool-name>/        # Each tool: TOOL.md + optional scripts
│   └── SKILLS_REGISTRY.yaml        # Pipeline metadata and stage dependency graph
│
├── external/                        # Externally-owned submodule suites
│   └── jira-suite/                 # git submodule — may contain skills/, agents/, protocols/
│
├── pathways/                        # Named bundles of synapses (pathway YAML files)
│
├── registry/
│   ├── SKILL_REGISTRY.md           # Skill discovery table
│   ├── AGENTS_REGISTRY.md          # Agent discovery table
│   ├── PROTOCOL_REGISTRY.md        # Protocol discovery table
│   ├── TOOL_REGISTRY.md            # Tool discovery table
│   ├── PATHWAY_REGISTRY.md         # Pathway discovery table
│   └── SCRIPT_REGISTRY.md          # Script discovery table
│
├── taxonomy/
│   ├── SKILL_TAXONOMY.md           # Controlled vocabulary for skill domain/intent
│   ├── AGENT_TAXONOMY.md           # Controlled vocabulary for agent domain/role
│   ├── PROTOCOL_TAXONOMY.md        # Controlled vocabulary for protocol domain/type
│   ├── TOOL_TAXONOMY.md            # Controlled vocabulary for tool domain/action/type
│   ├── PATHWAY_TAXONOMY.md         # Controlled vocabulary for pathway harness + naming guide
│   └── SCRIPT_TAXONOMY.md          # Controlled vocabulary for script audience/action/scope
│
├── docs/cli/                        # Per-command help docs (./cortex help <command>)
│
├── scripts/
│   ├── install.sh                  # Synapse installation across harnesses
│   ├── scaffold.sh                 # Artifact scaffolding with taxonomy validation
│   ├── pathway.sh                  # Pathway bundle management
│   ├── validate.sh                 # Standalone structural checks
│   ├── sync-registry.sh            # Registry/README drift detection and repair
│   ├── audit-artifacts.sh          # Companion artifact audit
│   ├── check-links.sh              # Markdown link validation
│   ├── reorganize.sh               # Domain-based artifact reorganization
│   └── zip-skills.ps1              # PowerShell ZIP packaging (Windows)
│
├── GOVERNANCE.md                   # Promotion criteria, contribution workflow
├── CLAUDE.md                       # Claude Code instructions for this repo
├── Makefile                        # Repo setup shortcuts (init, clean, test)
└── .githooks/pre-commit            # Structural validation on every commit
```

---

## Key Files

### [`cortex`](cortex)
Top-level CLI dispatcher. Routes all commands to scripts under `scripts/`. Run `./cortex help` for the full command reference, or `./cortex help <command>` to view detailed docs for any subcommand.

### [`synapse/SKILLS_REGISTRY.yaml`](synapse/SKILLS_REGISTRY.yaml)
The single source of truth for pipeline metadata. Every skill that participates in an automated pipeline is registered here with its `stage_name`, `input_type`, `output_type`, `context_type`, and dependency chain (`requires_all` / `requires_any`). The `autonomous-orchestrator` reads this file to resolve stage order, validate type compatibility, and drive end-to-end pipelines.

### Registries (`registry/`)
Discovery tables for all artifact types. Check these before creating a new artifact:
- [`SKILL_REGISTRY.md`](registry/SKILL_REGISTRY.md) — skills with domain, pipeline stage, and status
- [`AGENTS_REGISTRY.md`](registry/AGENTS_REGISTRY.md) — agent definitions dispatched by skills
- [`PROTOCOL_REGISTRY.md`](registry/PROTOCOL_REGISTRY.md) — behavioral contracts injected into agents
- [`TOOL_REGISTRY.md`](registry/TOOL_REGISTRY.md) — mechanical capabilities (scripts, MCP servers, CLI wrappers)
- [`PATHWAY_REGISTRY.md`](registry/PATHWAY_REGISTRY.md) — named bundles of synapses
- [`SCRIPT_REGISTRY.md`](registry/SCRIPT_REGISTRY.md) — repo management scripts

### Taxonomies (`taxonomy/`)
Controlled vocabularies for artifact metadata. Enforced by the pre-commit hook — committing an artifact with a value not listed in its taxonomy will fail:
- [`SKILL_TAXONOMY.md`](taxonomy/SKILL_TAXONOMY.md) — `domain` and `intent` for skills
- [`AGENT_TAXONOMY.md`](taxonomy/AGENT_TAXONOMY.md) — `domain` and `role` for agents
- [`PROTOCOL_TAXONOMY.md`](taxonomy/PROTOCOL_TAXONOMY.md) — `domain` and `type` for protocols
- [`TOOL_TAXONOMY.md`](taxonomy/TOOL_TAXONOMY.md) — `domain`, `action`, and `type` for tools
- [`PATHWAY_TAXONOMY.md`](taxonomy/PATHWAY_TAXONOMY.md) — `harness` for pathways + naming convention guide
- [`SCRIPT_TAXONOMY.md`](taxonomy/SCRIPT_TAXONOMY.md) — `audience`, `action`, and `scope` for scripts

### [`GOVERNANCE.md`](GOVERNANCE.md)
Promotion criteria and contribution workflow for all five synapse types (skills, agents, protocols, tools, pathways). Defines the two-tier validation model and gatekeeper scope.

### [`CLAUDE.md`](CLAUDE.md)
Project-level instructions for Claude Code. Claude reads this automatically when working in this repo.

### [`.githooks/pre-commit`](.githooks/pre-commit)
Structural validation on every commit. Checks frontmatter fields, taxonomy values, registry entries, README rows, and EVAL.md presence. Fails loudly with actionable errors. Activated via `make init`.

---

## Architecture

### Skill anatomy

Every skill lives at `{synapse,src}/skills/<domain>/<skill-name>/` and follows this layout:

```
{synapse,src}/skills/<domain>/<skill-name>/
  SKILL.md        # (required) YAML frontmatter + behavior body — the skill definition
  EVAL.md         # (required) Test prompts and pass/fail output criteria for quality evaluation
  references/     # Companion files loaded on-demand during specific phases
  templates/      # Output templates referenced by the skill
```

`SKILL.md` is the install discovery marker — `scripts/install.sh` walks `synapse/` and `src/` looking for files with that name, so any directory without one is invisible to the installer. The file must exist; contents are not validated at install time (that happens at commit via the pre-commit hook). `EVAL.md` is also required by the pre-commit hook, which will reject a skill directory missing it. `references/` and `templates/` are optional.

`SKILL.md` frontmatter carries routing metadata:

```yaml
---
name: skill-name
description: "Trigger conditions — when this skill fires (not a workflow summary)"
domain: docs.spec       # from SKILL_TAXONOMY.md
intent: write           # from SKILL_TAXONOMY.md
tags: [lowercase, hyphenated]
user-invocable: true
argument-hint: "[args]"
---
```

The `description` field is a **routing contract**: it specifies when the skill fires, not what it does. Claude Code matches user intent against this field to select the right skill.

### Agents, protocols, and tools

Beyond skills, three supporting artifact types live under both `synapse/` (framework) and `src/` (adopter):

- **Agent definitions** (`{synapse,src}/agents/<domain>/`) — internal recipes dispatched by skills, not user-invocable. Skills declare agent dependencies via symlinks in their `agents/` folder. See [`registry/AGENTS_REGISTRY.md`](registry/AGENTS_REGISTRY.md).
- **Protocols** (`{synapse,src}/protocols/<domain>/`) — shared conventions and schemas injected into agent prompts by observers. See [`registry/PROTOCOL_REGISTRY.md`](registry/PROTOCOL_REGISTRY.md).
- **Tools** (`{synapse,src}/tools/<domain>/`) — mechanical capabilities with no judgment. Scripts, MCP servers, CLI wrappers, and external integrations. Each tool has a `TOOL.md` and optionally ships code. See [`registry/TOOL_REGISTRY.md`](registry/TOOL_REGISTRY.md).

### Pathways

Pathways (`pathways/`) are named bundles of synapses — a YAML file listing which skills, agents, protocols, and tools to install together. Pathways are harness-aware (claude, codex, gemini, multi) and support single-level inheritance. See [`taxonomy/PATHWAY_TAXONOMY.md`](taxonomy/PATHWAY_TAXONOMY.md) for naming conventions.

### synapse/ vs src/ vs external/

- **`synapse/`** — framework artifacts shipped by ai-synapse: the meta-tools that build, evaluate, and govern artifacts (skill-creator, gatekeeper, eval generators, orchestration, tooling).
- **`src/`** — adopter artifacts owned by this specific repo. Convention-enforced, managed by `scripts/reorganize.sh`. May be empty in a pure framework distribution.
- **`external/`** — submodule suites from external repos. Each suite may contain `skills/`, `agents/`, `protocols/`. The `jira-suite` is the current example.

External suites are portable: a team can adopt `jira-suite` without pulling all of ai-synapse. Changes to an external artifact are made in the suite's own repo; this repo only tracks the submodule pointer.

### Registration is intentional, not automatic

Artifacts land in ai-synapse only after review, with proper frontmatter, taxonomy-valid metadata, and registry entries. Use `./cortex scaffold` to create artifacts with correct structure, and `/synapse-gatekeeper` to certify before merging. Standalone repos are where free iteration happens; ai-synapse is where you promote to.

### Two-tier validation

Every artifact goes through two tiers of checks:

1. **Structural (pre-commit, shell)** — frontmatter fields, taxonomy values, registry entries, domain README rows, EVAL.md presence. Fast, deterministic, no LLM. Run standalone via `./cortex validate`.
2. **Quality (PR-time, LLM)** — `/synapse-gatekeeper` evaluates naming, composition, documentation quality. Covers all five synapse types: skills, agents, protocols, tools, pathways.

---

## Quick Start

```bash
git clone https://github.com/JuanSync7/ai-synapse.git
cd ai-synapse
make init                          # configure git hooks + submodules (first-time only)
./cortex install all               # install all skills to Claude Code
./cortex agents                    # install agent definitions
./cortex pathway install <name>    # install a pathway bundle
```

---

## The `cortex` CLI

`./cortex` is the top-level dispatcher for all synapse management. Run `./cortex help` for the full reference.

> **Windows:** `cortex` and `make` both require bash. Use WSL (recommended) or Git Bash. Native PowerShell support is on the roadmap.

### Consumer — load and manage synapses

```bash
./cortex install all                        # install all skills to Claude Code
./cortex install synapse/skills/skill       # install one domain
./cortex codex all                          # install to Codex CLI
./cortex gemini all                         # install to Gemini CLI
./cortex agents                             # install agent definitions
./cortex identity                           # install identity files
./cortex list                               # list installed synapses
./cortex available                          # show all available synapses
./cortex pathway list                       # list available pathways
./cortex pathway install <name>             # install a pathway bundle
```

### Contributor — create and validate artifacts

```bash
./cortex scaffold skill docs my-skill       # scaffold a new skill
./cortex scaffold agent ml monitor          # scaffold a new agent
./cortex scaffold tool integration my-mcp   # scaffold a new tool
./cortex validate                           # run all structural checks
./cortex validate synapse/skills/skill/skill-creator  # validate one artifact
./cortex test                               # run all tool tests
./cortex test src/tools/synapse/my-tool     # test one tool
```

### Maintainer — repo hygiene and repair

```bash
./cortex sync                               # detect registry/README drift
./cortex sync fix                           # auto-repair stale entries
./cortex audit                              # companion artifact audit
./cortex doctor                             # check for broken symlinks
./cortex clean                              # remove all installed symlinks
./cortex check-links                        # validate markdown links
./cortex reorganize status                  # check artifact placement
```

### Help

```bash
./cortex help                               # full command reference
./cortex help scaffold                      # detailed help for a command
```

See [`docs/cli/`](docs/cli/) for the complete per-command documentation.

### Make shortcuts

`Makefile` provides shortcuts for repo setup: `make init`, `make claude`, `make codex`, `make clean`. For full CLI, use `./cortex`.

### Claude Desktop (ZIP packaging)

```bash
./cortex zip all                            # package all skills as .zip
./cortex zip synapse/skills/skill/skill-creator  # package one skill
```

→ See **[src/README.md](src/README.md)** for the full artifact catalog with per-domain tables.

---

## Contributing

Contributions follow a two-gate branching model:

```
feature/<synapse>/<name>  →  develop  →  main
```

Where `<synapse>` is one of: `skill`, `agent`, `protocol`, `tool`.

1. Create a feature branch (`feature/skill/my-fix`, `feature/tool/my-tool`, etc.)
2. Make changes and include a `change_requests/` file documenting the rationale
3. PR to `develop` — artifact owner reviews the CR + diff, deletes the CR on acceptance
4. PR to `main` — blocked if any `change_requests/` files remain in the diff

See [`GOVERNANCE.md`](GOVERNANCE.md) for full promotion criteria, naming conventions, and the contribution workflow.

---

<p align="center">
  <sub>Built with Claude Code</sub>
</p>

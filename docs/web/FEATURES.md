# Synapse Web Interface — Feature Map

> 1:1 mapping from every ai-synapse / juansync-synapse capability to a web-interface
> feature. This is the contract for the web app: if the framework can do it, the web
> interface must surface it. Companion docs: [`SPEC.md`](SPEC.md) (requirements),
> [`DESIGN.md`](DESIGN.md) (architecture + aesthetic direction).

## Packaging model

- **ai-synapse (base)** = framework artifacts (`synapse/`), taxonomies, registries,
  validation, CLI, **and this web interface** (`web/`).
- **juansync-synapse (add-on)** = the adopter overlay: everything in `src/` (extra
  skills/agents/protocols/tools), the tuned taxonomy values in `registry/*_VOCABULARY.md`,
  and the populated registries. Another adopter gets the base + web UI and "installs"
  their own synapses into `src/` / `external/` — the web app must therefore **derive
  everything from the repo at runtime** (crawl, never hardcode), and visually distinguish
  the three layers: `base` (synapse/), `add-on` (src/), `external` (external/).

## Feature map

| # | Framework capability | Source of truth | Web feature | Surface |
|---|---------------------|-----------------|-------------|---------|
| F1 | Skill artifacts (37): SKILL.md + frontmatter + references/ + templates/ | `synapse/skills/`, `src/skills/`, `external/*/skills/` | Browse list `/skills` (filter by domain/scope/role/status/layer, search), detail page with rendered SKILL.md, frontmatter card, companion file tree, aliases | Artifact browser |
| F2 | Agent artifacts (34) | `{synapse,src}/agents/` | `/agents` list + detail (like the reference `localhost:28173/agents` page) | Artifact browser |
| F3 | Protocol artifacts (incl. versioned contracts + amendments) | `{synapse,src}/protocols/` | `/protocols` list + detail, version + kind badges | Artifact browser |
| F4 | Tool artifacts (TOOL.md + schemas/cli) | `{synapse,src}/tools/` | `/tools` list + detail, action/target/kind badges | Artifact browser |
| F5 | Pathways (named synapse bundles, inheritance) | `pathways/*.yaml` | `/pathways` list + detail with resolved synapse list | Artifact browser |
| F6 | EVAL.md per synapse (structural/execution/output criteria, test prompts) | `<artifact>/EVAL.md` | Dedicated **Eval panel** on every artifact detail page: criteria parsed into checklists (EVAL-Exx / EVAL-Oxx), clearly displayed, placeholder-EVAL flagged | Artifact detail |
| F7 | Registries (7: skill, agents, protocol, tool, pathway, persona, script) | `registry/*_REGISTRY.md` | `/registry` — parsed tables, status chips (draft/stable), consumer cross-links to artifact pages, **edit + save** writes back to the markdown file | Registry |
| F8 | Controlled vocabularies | `registry/*_VOCABULARY.md` | Vocabulary viewer/editor under `/taxonomy` (vocab drives slug validation — editing it is how an adopter tunes the framework) | Taxonomy |
| F9 | Taxonomies (slug grammar, frontmatter schemas, persona rules) | `taxonomy/*.md` | `/taxonomy` — viewer + **editor** (markdown editing with save-back; these files drive the actual framework, so edits are real) | Taxonomy |
| F10 | Framework meta-skills: creator, gatekeeper, eval-writer, improver, suite-validator, brainstormer + synapse agents/protocols/tools | `synapse/` | Dedicated `/framework` page — the gatekeeper + synapse items separated from adopter artifacts, with pipeline-role explanation | Framework page |
| F11 | Pipeline metadata (stages, input/output types, requires_*, presets full/feature/bugfix) | `synapse/SKILLS_REGISTRY.yaml` | Pipeline view on `/framework`: stage graph + preset chips | Framework page |
| F12 | Brainstorm sessions (notepad, meta.yaml, design.md, per-artifact memos) | `.brainstorms/<date-slug>/` | `/brainstorm` — chat page that drives a **headless claude session** invoking `/synapse-router-artifact-brainstormer` exactly as in the CLI; transcript streamed live; session resumable | Brainstorm |
| F13 | Memos (artifact memos, change_requests CRs) | `.brainstorms/*/<artifact>-memo-*.md`, `**/change_requests/*.md` | **Memo board** `/memos` — repo-crawled; `executed: true|false` frontmatter determines done/not-done; filter, detail view, toggle executed | Memo system |
| F14 | Synapse creation end-to-end (creator pipeline → artifact + registry + README updates) | `/synapse-router-artifact-creator` | From a memo's detail page: **Run creator** — headless end-to-end session until the synapse exists; live progress; post-run verification (validate output, links to new artifact + updated registry) | Creator runner |
| F15 | Validation (pre-commit + full sweep) | `scripts/validate.sh`, `.githooks/pre-commit` | **Validate button** (control panel + post-creator-run): runs `./cortex validate`, renders errors/warnings | Control panel |
| F16 | Repo-management scripts (12 bash + python CLIs: install, scaffold, sync, audit, doctor, drift, pins, clerk, telemetry, tag-*) | `scripts/` `@frontmatter`, `docs/cli/*.md` | `/scripts` **control panel** — one card per script/command: what it does, when/where to use it, audience badge, usage snippet from docs/cli (documentation panel, not code dump); safe read-only commands (validate, list, available, doctor, status) executable from the UI | Control panel |
| F17 | Install model (symlinks to ~/.claude/skills, codex/gemini targets, aliases materialization, collision guard) | `scripts/install.sh`, `scripts/lib/common.sh` | Documented on `/scripts` cards (install/clean/list); `cortex available` runnable read-only | Control panel |
| F18 | External suites (submodules with own CI) | `external/`, `.gitmodules` | Layer badge `external` in browsers + suite grouping on detail pages | Artifact browser |
| F19 | Project showcase & links | `README.md`, `GOVERNANCE.md`, `wiki/` | Landing page `/`: what the framework is, the three layers, links to GitHub repo and docs | Landing |
| F20 | Personas (scaffolded class) | `src/skills/persona/`, `PERSONA_*` | Persona section in `/skills` (empty-state aware) + registry/taxonomy rows | Artifact browser |

## Explicit non-features (v1)

- No git operations from the UI (commit/push stay in the CLI).
- No editing artifact bodies (SKILL.md etc.) from the UI — creation goes through the
  creator pipeline; only registries/taxonomies/vocabularies and memo status are editable.
- No execution of destructive scripts (clean, reorganize, tag-*) from the UI — cards
  document them; execution stays in the terminal.
- Single-user, localhost-only; no auth.

## Acceptance bar

Every row F1–F20 has a working web surface; ESLint clean; unit + integration + e2e
tests green; `./cortex validate` remains 0 errors / 0 warnings with the web app added.

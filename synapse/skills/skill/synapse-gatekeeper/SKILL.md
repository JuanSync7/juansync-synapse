---
name: synapse-gatekeeper
description: "Use when a skill, agent, protocol, tool, or pathway is complete and ready for promotion review, or to check if an artifact meets the bar to land in ai-synapse."
domain: skill.eval
intent: validate
tags: [skill, agent, protocol, tool, pathway, promotion, certification, gatekeeper]
user-invocable: true
argument-hint: "<artifact-path> [--score <0-100>]"
---

Synapse gatekeeper is the promotion gate for ai-synapse. An artifact is not ready to merge just because it was built — it must meet the bar. This skill reads a finished skill, agent, protocol, tool, or pathway, detects the artifact type, and runs the appropriate checklist. APPROVE = ready for PR. REVISE = fixable gaps. REJECT = fundamental problem that prevents promotion. The verdict is always the first line so orchestrators can parse it without scanning the full report.

Five artifact types, five flows:
- **Skill** (default) — `SKILL.md` in a directory under `src/skills/` → three tiers (structural, quality, registry)
- **Agent** — `.md` file in `src/agents/` → two tiers (structural, quality) via `references/agent-checklist.md`
- **Protocol** — `.md` file in `src/protocols/` → two tiers (structural, conformance) via `references/protocol-checklist.md`
- **Tool** — `TOOL.md` in a directory under `src/tools/` → two tiers (structural, quality)
- **Pathway** — `.yaml` file in `pathways/` → two tiers (structural, quality)

---

## Execution Scope

Ignore any files named `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, or `test-inputs/` when they appear in the artifact directory being reviewed. These are scaffolding artifacts, not part of the live surface. For skills, evaluate `SKILL.md`, `references/`, `templates/`, and the domain `README.md` row. For agents and protocols, evaluate the `.md` file itself. For tools, evaluate `TOOL.md` and the domain `README.md` row. For pathways, evaluate the `.yaml` file itself.

---

## Wrong-Tool Detection

| If the user wants to... | Redirect to |
|-------------------------|-------------|
| Fix gaps identified in a verdict | Issue the verdict first, then redirect to `/improve-skill` |
| Build a skill from scratch | `/skill-creator` |
| Build an agent from scratch | `/agent-creator` |
| Build a protocol from scratch | `/protocol-creator` |
| Review a decision or design approach (not an artifact) | `/stakeholder-reviewer` |
| Evaluate or rewrite an EVAL.md only | `/write-skill-eval`, `/write-agent-eval`, or `/write-protocol-eval` |

---

## Progress Tracking

```
TaskCreate "Phase 1 — Load artifact and detect type" status:in_progress
TaskCreate "Phase 2 — Structural tier check"
TaskCreate "Phase 3 — Quality / Conformance tier check"
TaskCreate "Phase 4 — Registry tier check (skills only)"
TaskCreate "Phase 5 — Issue verdict and report"
TaskCreate "Phase 6 — Record verdict (skill flow, APPROVE only)"
```

---

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `<artifact-path>` | Yes | Path to the artifact: skill directory (containing SKILL.md), agent `.md` file in `src/agents/`, protocol `.md` file in `src/protocols/`, tool directory (containing TOOL.md) in `src/tools/`, or pathway `.yaml` file in `pathways/` |
| `--score <0-100>` | No | Eval score from a prior `/improve-skill` or auto-research run (skills only) |

---

## Phase 1 — Load and Detect Type

**Artifact type detection:**
- Path matches `src/agents/<domain>/<agent>.md` → **agent flow**
- Path matches `src/protocols/<domain>/<protocol>.md` → **protocol flow**
- Path contains a `TOOL.md` file (under `src/tools/`) → **tool flow**
- Path matches `pathways/<pathway>.yaml` → **pathway flow**
- Path contains a `SKILL.md` file → **skill flow** (default)
- None of the above → emit `VERDICT: REJECT` with "unrecognized artifact type"

**Skill flow — read:**
- `<artifact-path>/SKILL.md`
- `<artifact-path>/EVAL.md`
- `<artifact-path>/` directory listing (to detect `references/`, `templates/`, `examples/`)

**Agent flow — read:**
- The agent `.md` file itself
- > **Read [`references/agent-checklist.md`](references/agent-checklist.md)** for the agent-specific checklist

**Protocol flow — read:**
- The protocol `.md` file itself
- > **Read [`references/protocol-checklist.md`](references/protocol-checklist.md)** for the protocol-specific checklist

**Tool flow — read:**
- `<artifact-path>/TOOL.md`
- `<artifact-path>/` directory listing

**Pathway flow — read:**
- The pathway `.yaml` file itself
- > **Read [`../../../../taxonomy/PATHWAY_TAXONOMY.md`](../../../../taxonomy/PATHWAY_TAXONOMY.md)** for harness values and naming conventions

**Score precondition check (skill flow only):** If `--score` is not provided, ask before proceeding: "Do you have an eval score from `/improve-skill` or `/auto-research`? A missing score caps the verdict at REVISE." DO NOT run all phases only to report this at the end.

**Early exits (skill flow only):**
- If `SKILL.md` is absent → emit `VERDICT: REJECT` immediately. Do not proceed.
- If `EVAL.md` is absent → record a REJECT-tier structural failure. Complete the structural checklist (marking EVAL.md as `[ ]`), then issue `VERDICT: REJECT`. Skip Quality and Registry tiers entirely — they require a working eval.

**Early exits (agent/protocol flow):**
- If the `.md` file is absent or empty → emit `VERDICT: REJECT` immediately.
- If frontmatter is absent → emit `VERDICT: REJECT` immediately.

**Early exits (tool flow):**
- If `TOOL.md` is absent → emit `VERDICT: REJECT` immediately.
- If frontmatter is absent → emit `VERDICT: REJECT` immediately.

**Early exits (pathway flow):**
- If the `.yaml` file is absent or not valid YAML → emit `VERDICT: REJECT` immediately.
- If required fields (`name`, `description`, `harness`, `synapses`) are missing → emit `VERDICT: REJECT` immediately.

---

## Phase 2 — Structural Tier

### Skill flow

> **Read [`../../../../taxonomy/SKILL_TAXONOMY.md`](../../../../taxonomy/SKILL_TAXONOMY.md)** to validate `domain` and `intent` values against the controlled vocabulary.

| Check | Pass condition |
|-------|---------------|
| SKILL.md exists | File is present and non-empty |
| EVAL.md exists | File is present (**REJECT if absent**) |
| Frontmatter complete | `name`, `description`, `domain`, `intent` all present |
| `domain` in SKILL_TAXONOMY.md | Value matches a row in SKILL_TAXONOMY.md |
| `intent` in SKILL_TAXONOMY.md | Value matches a row in SKILL_TAXONOMY.md |
| `tags` well-formed | Array of lowercase hyphenated strings |
| `user-invocable` present | Field exists (true or false) |
| `argument-hint` present | Present when `user-invocable: true` |
| Domain README has row | Domain `README.md` contains a row linking this skill |
| Name globally unique | No collision in `registry/SKILL_REGISTRY.md` |

**Name uniqueness:** Check `registry/SKILL_REGISTRY.md` for any row with the same skill name. A collision is an immediate REJECT — two skills with the same name cannot coexist in `~/.claude/skills/`.

### Agent flow

Use the checklist from `references/agent-checklist.md` (loaded in Phase 1). Validate against `AGENT_TAXONOMY.md` and `AGENTS_REGISTRY.md`.

### Protocol flow

Use the checklist from `references/protocol-checklist.md` (loaded in Phase 1). Validate against `PROTOCOL_TAXONOMY.md`.

### Tool flow

> **Read [`../../../../taxonomy/TOOL_TAXONOMY.md`](../../../../taxonomy/TOOL_TAXONOMY.md)** to validate `domain`, `action`, and `type` values against the controlled vocabulary.

| Check | Pass condition |
|-------|---------------|
| TOOL.md exists | File is present and non-empty |
| Frontmatter complete | `name`, `description`, `domain`, `action`, `type` all present |
| `domain` in TOOL_TAXONOMY.md | Value matches a row in TOOL_TAXONOMY.md |
| `action` in TOOL_TAXONOMY.md | Value matches a row in TOOL_TAXONOMY.md |
| `type` valid | Value is one of `external`, `internal`, `wrapper` |
| `tags` well-formed | Array of lowercase hyphenated strings |
| Domain README has row | Domain `README.md` contains a row linking this tool |
| Listed in TOOL_REGISTRY.md | A row exists in `registry/TOOL_REGISTRY.md` for this tool |

### Pathway flow

> **Read [`../../../../taxonomy/PATHWAY_TAXONOMY.md`](../../../../taxonomy/PATHWAY_TAXONOMY.md)** to validate `harness` value against the controlled vocabulary.

| Check | Pass condition |
|-------|---------------|
| Valid YAML | File parses as valid YAML |
| Required fields present | `name`, `description`, `harness`, `synapses` all present |
| `harness` in PATHWAY_TAXONOMY.md | Value matches a row in PATHWAY_TAXONOMY.md |
| Synapse paths resolve | Every path under `synapses:` points to an existing artifact on disk |
| `inherits:` target exists | If set, the parent pathway file exists |
| Listed in PATHWAY_REGISTRY.md | A row exists in `registry/PATHWAY_REGISTRY.md` for this pathway |

---

## Phase 3 — Quality / Conformance Tier

### Skill flow

> **Read [`references/skill-design-principles.md`](references/skill-design-principles.md)** before evaluating quality criteria.

| Check | Pass condition |
|-------|---------------|
| Description is routing contract | Specifies *when* the skill fires — not a workflow summary |
| Eval score ≥ 80 | Provided score is ≥ 80 |
| SKILL.md under 500 lines | Line count ≤ 500 |
| Instructions trace to failure modes | Each instruction implies "without this, the agent does X which causes Y" |
| Wrong-Tool Detection present | Section redirects to sibling skills on intent mismatch |
| `references/` used correctly | Companion files load at specific decision points, not inlined wholesale |

**If no score is provided:** Mark the quality tier as `unverified`. A missing score blocks APPROVE — a skill cannot be certified without a measured eval score. The verdict will be at most REVISE.

### Agent flow

Use the Tier 2 (Quality) checks from `references/agent-checklist.md`.

### Protocol flow

Use the Tier 2 (Conformance) checks from `references/protocol-checklist.md`.

### Tool flow

| Check | Pass condition |
|-------|---------------|
| `type` classification accurate | `external`/`internal`/`wrapper` matches the actual content of the tool |
| Execution model documented | Inputs, outputs, and invocation method are clearly described |
| No judgment | Tool is mechanical — if it contains judgment or persona, it should be an agent |
| Under 300 lines | TOOL.md line count ≤ 300 |

### Pathway flow

| Check | Pass condition |
|-------|---------------|
| Naming follows taxonomy patterns | Name matches one of the 4 patterns in `taxonomy/PATHWAY_TAXONOMY.md` (domain-focused, role-focused, workflow-focused, single-domain) |
| Description is meaningful | Not empty, placeholder, or generic |
| Composition coherence | The synapses listed make sense together for the stated purpose |
| Tags relevant | Tags relate to the pathway's stated purpose |

---

## Phase 4 — Registry Tier (Skills Only)

**Agent, protocol, tool, and pathway flows skip this phase entirely** — their registry checks are handled in Phase 2.

> **Read [`../../../../registry/SKILL_REGISTRY.md`](../../../../registry/SKILL_REGISTRY.md)** to verify the skill has an inventory row.
> **Read [`../../../SKILLS_REGISTRY.yaml`](../../../SKILLS_REGISTRY.yaml)** to verify pipeline stage registration (pipeline-routable skills only).

A skill is **pipeline-routable** if it: (a) consumes a defined artifact type, (b) produces a defined artifact type, and (c) other skills in the registry depend on its output via `requires_all` or `requires_any`.

| Check | Pass condition |
|-------|---------------|
| Listed in SKILL_REGISTRY.md | A row exists in `registry/SKILL_REGISTRY.md` for this skill |
| Pipeline-routable → has YAML entry | `pipeline:` block present in `SKILLS_REGISTRY.yaml` with `stage_name`, `input_type`, `output_type`, `context_type`, `requires_all`/`requires_any` |
| Not pipeline-routable → YAML absence is correct | Skill absent from `SKILLS_REGISTRY.yaml` (non-routable skills are not listed there) |
| If registered: `stage_name` unique | No other skill uses the same `stage_name` in `SKILLS_REGISTRY.yaml` |
| If registered: dependencies resolve | All `requires_all`/`requires_any` values match real stage names in the registry |

---

## Phase 5 — Verdict and Report

> **Read [`../../../../GOVERNANCE.md`](../../../../GOVERNANCE.md)** for authoritative REVISE vs. REJECT classification.

**Verdict rules:**

A tier passes when ALL items in its checklist are `[x]`. Any `[ ]` item means the tier fails — there is no "non-blocking" category. If an item does not apply, omit it from the checklist entirely rather than marking it `[ ]`.

| Condition | Verdict |
|-----------|---------|
| All tiers pass (every item `[x]`) | APPROVE |
| Any fixable gap (score < 80, weak description, missing README row, missing argument-hint, unverified quality tier, missing registry entry for pipeline skill) | REVISE |
| EVAL.md absent, name collision, or fundamental structural failure | REJECT |

> **Read [`examples/example-verdict.md`](examples/example-verdict.md)** for complete worked examples of each verdict type.

**Output format:**

```
VERDICT: <APPROVE | REVISE | REJECT>

## Certification Report — <artifact-name> (<skill | agent | protocol | tool | pathway>)

### Structural                    <✓ | ✗>
- [x] ...

### Quality / Conformance         <✓ | ✗ | unverified>
- [x] ...

### Registry                      <✓ | ✗ | N/A>
- [x] ...
(N/A for agents, protocols, tools, and pathways)

## Gaps
<specific actionable items — omit section entirely if APPROVE>
```

The verdict MUST be the first line of output. DO NOT prepend preamble, headers, or explanatory text before it — orchestrators rely on this for automated parsing.

---

## Phase 6 — Record verdict (skill flow only, APPROVE only)

When the verdict is APPROVE **and** the artifact type is skill, update the `Status` column of the skill's row in `registry/SKILL_REGISTRY.md`:

- If current Status is `draft` or empty/unset → write `stable`.
- If current Status is already `stable` → no-op.
- If current Status is `deprecated` → no-op. Never overwrite `deprecated` from gatekeeper. (A deprecated skill that re-earns APPROVE is a human decision, not an automated one.)

Do nothing for REVISE or REJECT verdicts. Do nothing for agent / protocol / tool / pathway flows — their registries do not have a Status column under this lifecycle yet.

The pre-commit hook will auto-demote `stable → draft` on any subsequent edit to the skill's `SKILL.md`, so this write step is the only path to `stable`.

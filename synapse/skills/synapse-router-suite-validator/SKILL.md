---
name: synapse-router-suite-validator
description: "Use when adding or updating an external submodule suite (under external/), or when checking whether a candidate suite conforms to ai-synapse conventions before it is wired in. Sweeps every artifact in the suite and produces a structural conformance rollup."
domain: synapse
subdomain: router
scope: suite
role: validator
tags: [external, submodule, suite, conformance, entry-gate, rollup]
user-invocable: true
argument-hint: "<path-to-suite-directory> [--escalate]"
---

# Synapse External Validator

The entry gate for `external/` submodules. Before a multi-artifact suite is wired into ai-synapse, every artifact inside it must conform to the framework's structural conventions — taxonomy values must resolve, frontmatter must be complete, registry rows must exist, name collisions must be absent. `synapse-router-artifact-gatekeeper` answers "is this one artifact ready?"; this skill answers "is this whole suite ready?"

This is **breadth-first and structural-only**. It does not run LLM-graded quality judgment on each artifact (that would be 50× as expensive and is not what an entry gate needs). It sweeps the suite, classifies every artifact, applies the same Tier 1 checks the pre-commit hook applies to in-tree artifacts, and produces a rollup. With `--escalate`, it can route any artifact that passes structural to `/synapse-router-artifact-gatekeeper` for full quality review.

> **Without this skill, a broken external suite lands in `external/` and fails artifact-by-artifact later, surfacing as confusing CI failures with no clear "this suite was never validated" diagnostic.**

---

## Wrong-Tool Detection

| If the user wants to... | Redirect to |
|-------------------------|-------------|
| Validate ONE artifact (skill / agent / protocol / tool / pathway) | `/synapse-router-artifact-gatekeeper <artifact-path>` |
| Build a new artifact from scratch | `/synapse-router-artifact-creator` |
| Improve an existing artifact's quality score | `/synapse-skill-skill-improver` |
| Generate an EVAL.md for an artifact | `/synapse-router-eval-writer` |
| Validate an in-tree (`src/` or `synapse/`) artifact | `/synapse-router-artifact-gatekeeper` — this skill is specifically for submodule suites |

---

## MUST / MUST NOT

- **MUST** emit the verdict on the first line of output (`SUITE: APPROVE | REVISE | REJECT (path: ...)`) — orchestrators parse this.
- **MUST** delegate per-type structural checks to `/synapse-router-artifact-gatekeeper` Phase 2. The per-type checklists live there; do not duplicate them.
- **MUST** continue the sweep when one artifact's frontmatter is unparseable — mark it `UNREADABLE` and continue.
- **MUST NOT** modify the suite. The sweep is read-only.
- **MUST NOT** dispatch `/synapse-router-artifact-gatekeeper` on an artifact that failed the structural sweep — fix structure first.
- **MUST NOT** auto-add taxonomy rows or registry rows on behalf of the suite. Surface gaps; let the maintainer act.

---

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `<path-to-suite-directory>` | Yes | Path to a candidate or wired-in submodule suite directory (typically `external/<suite-name>/`). MUST contain at least one of `skills/`, `agents/`, `protocols/`, `tools/`, or `pathways/`. |
| `--escalate` | No | After the structural sweep, dispatch `/synapse-router-artifact-gatekeeper` on every artifact that passed structural. Slow and LLM-heavy — use only when promoting the suite, not on every update. |

---

## Progress Tracking

```
TaskCreate "Phase 1 — Discover artifacts in suite"
TaskCreate "Phase 2 — Classify each artifact by type"
TaskCreate "Phase 3 — Per-artifact structural checks"
TaskCreate "Phase 4 — Cross-suite checks"
TaskCreate "Phase 5 — Optional escalation to /synapse-router-artifact-gatekeeper"
TaskCreate "Phase 6 — Emit rollup report"
```

---

## Phase 1 — Discover

> **Read [`references/discovery-rules.md`](references/discovery-rules.md)** for the exact walk algorithm, per-type signatures, and `UNREADABLE` handling.

**Do:**
- Walk `<suite-root>` and enumerate every potential artifact across the five types (skill / agent / protocol / tool / pathway).
- Stop early with `SUITE: REJECT — no recognizable artifacts` if zero artifacts are found.

**Don't:**
- Recurse into a skill's internal directories looking for nested skills.
- Treat suite-level files (`README.md`, `LICENSE`, `.github/`) as artifacts.

**Exit:** A list of artifact records `{ type, path, name }`.

---

## Phase 2 — Classify

For each discovered artifact, parse frontmatter and record `{ type, path, name }`. If frontmatter is unparseable, mark `UNREADABLE` and continue. Do NOT abort the sweep on one bad artifact — the maintainer needs to see every problem in one report.

**Exit:** Classified artifact list with `UNREADABLE` flags where applicable.

---

## Phase 3 — Per-artifact structural checks

> **Read [`../../skill/synapse-router-artifact-gatekeeper/SKILL.md`](../../skill/synapse-router-artifact-gatekeeper/SKILL.md)** Phase 2 — reuse the structural-tier tables for each artifact type. The per-type checklists are defined there in one place; this skill applies them.

> **Read [`../../../../taxonomy/SKILL_TAXONOMY.md`](../../../../taxonomy/SKILL_TAXONOMY.md), [`../../../../taxonomy/AGENT_TAXONOMY.md`](../../../../taxonomy/AGENT_TAXONOMY.md), [`../../../../taxonomy/PROTOCOL_TAXONOMY.md`](../../../../taxonomy/PROTOCOL_TAXONOMY.md), [`../../../../taxonomy/TOOL_TAXONOMY.md`](../../../../taxonomy/TOOL_TAXONOMY.md), and [`../../../../taxonomy/PATHWAY_TAXONOMY.md`](../../../../taxonomy/PATHWAY_TAXONOMY.md)** once at the start of this phase, so taxonomy values can be checked locally per artifact without re-reading.

**Universal checks per artifact** (applied via the gatekeeper Phase 2 table for the artifact's type):
- Required frontmatter fields all present.
- All controlled-vocabulary values resolve in the relevant taxonomy file.
- For skills: `EVAL.md` exists alongside `SKILL.md`.
- For tools: `TOOL.md` exists and frontmatter complete.
- For pathways: every `synapses:` path resolves on disk.

Record per artifact: `{ name, type, structural_pass: bool, failures: [reason, ...] }`.

**Exit:** Per-artifact pass/fail records.

---

## Phase 4 — Cross-suite checks

> **Read [`references/cross-suite-checks.md`](references/cross-suite-checks.md)** for the five checks (intra-suite collisions, main-tree collisions, taxonomy drift, README presence, pathway resolution) with triggers, fail signals, and fix recommendations.

**Do:**
- Load the relevant ai-synapse main-tree registries (`registry/SKILL_REGISTRY.md`, `AGENTS_REGISTRY.md`, etc.) once at the start of this phase.
- Run all five checks unconditionally; none short-circuits another.

**Don't:**
- Add taxonomy rows or registry rows to the main tree. The validator surfaces gaps; the maintainer fixes them.

**Exit:** A list of cross-suite issues (possibly empty).

---

## Phase 5 — Optional escalation

> **Read [`references/escalation-rules.md`](references/escalation-rules.md)** for parallel cap, dispatch shape, partial failure handling, and rollup-verdict downgrade rules.

**Do:**
- If `--escalate` was passed AND Phases 3–4 produced zero failures, dispatch `/synapse-router-artifact-gatekeeper` per artifact in parallel batches (cap: 8 concurrent).
- Aggregate verdicts; downgrade the suite verdict on weakest-link semantics.

**Don't:**
- Escalate when structural failures exist — gatekeeper will reject on Phase 1 and waste budget.
- Pass `--score` to escalated calls.

**Exit:** A list of `{ artifact, gatekeeper_verdict }` records, or empty if escalation was skipped.

---

## Phase 6 — Rollup report

> **Read [`references/rollup-format.md`](references/rollup-format.md)** for the strict format (verdict-first, fixed section order, omission rules) and verdict-rule table.

> **Read [`examples/example-rollup.md`](examples/example-rollup.md)** for APPROVE / REVISE / REJECT worked examples.

**Verdict rules (summary):**
- `APPROVE` — every artifact structurally passes, zero cross-suite issues, and (if escalated) every escalated artifact APPROVE.
- `REVISE` — fixable structural failures, fixable cross-suite issues, or any escalated REVISE.
- `REJECT` — empty suite, unrecognizable layout, or any escalated REJECT.

**The verdict MUST be the first line of output. No preamble.**

---

## What this skill does NOT do

- Does not modify the suite — read-only sweep.
- Does not run LLM quality judgment unless `--escalate` is passed.
- Does not register the suite in ai-synapse — that's a separate step the maintainer takes after APPROVE.
- Does not validate the suite's git submodule pointer or remote URL — only the on-disk content.
- Does not replace `/synapse-router-artifact-gatekeeper` for in-tree artifacts — that path stays per-artifact.

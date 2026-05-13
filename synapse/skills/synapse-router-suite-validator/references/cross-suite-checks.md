# Cross-Suite Checks

Loaded by `synapse-router-suite-validator` Phase 4. These checks are invisible to per-artifact runs of `/synapse-router-artifact-gatekeeper` because they span artifacts or compare the suite to ai-synapse main-tree state. Without them, a suite can be artifact-by-artifact clean yet still impossible to install — name collisions and taxonomy drift only surface when you look at the suite as a whole.

---

## Check 1 — Intra-suite name collision

**Trigger:** Two artifacts of the same type discovered in Phase 1 share a `name`.

**Fail signal:** The rollup's per-artifact list shows both artifacts; the cross-suite section lists the collision.

**Fix recommendation:** "Rename one of the colliding artifacts. Skill / agent / tool / pathway names must be unique within the suite (and across ai-synapse — see Check 2)."

**Why it matters:** `scripts/install.sh` symlinks artifacts into a flat directory. Two artifacts with the same name silently shadow each other.

---

## Check 2 — Main-tree name collision

**Trigger:** An artifact's `name` already appears in the corresponding ai-synapse main-tree registry.

**Registries to load:**
- skills → `registry/SKILL_REGISTRY.md`
- agents → `registry/AGENTS_REGISTRY.md`
- protocols → `registry/PROTOCOL_REGISTRY.md`
- tools → `registry/TOOL_REGISTRY.md`
- pathways → `registry/PATHWAY_REGISTRY.md`

**Fail signal:** The cross-suite section names the artifact, the registry path, and the existing main-tree path that owns the name.

**Fix recommendation:** "Rename the suite's `<artifact-name>` to avoid shadowing the main-tree artifact at `<existing-path>`. Two artifacts with the same name cannot coexist in `~/.claude/skills/`."

**Why it matters:** Installing the suite would shadow an existing in-tree artifact — silently, with no error. This is the single most damaging class of failure this skill catches.

---

## Check 3 — Taxonomy drift

**Trigger:** An artifact's controlled-vocabulary value (`domain`, `intent`, `role`, `type`, `action`, `harness`) does not appear in the relevant taxonomy file.

**Taxonomies to load:**
- skills → `taxonomy/SKILL_TAXONOMY.md` (`domain`, `intent`)
- agents → `taxonomy/AGENT_TAXONOMY.md` (`domain`, `role`)
- protocols → `taxonomy/PROTOCOL_TAXONOMY.md` (`domain`, `type`)
- tools → `taxonomy/TOOL_TAXONOMY.md` (`domain`, `action`, `type`)
- pathways → `taxonomy/PATHWAY_TAXONOMY.md` (`harness`)

**Fail signal:** Cross-suite section lists each unknown value with the artifacts that use it: `domain=automation used by 2 skills (foo, bar) — not in SKILL_TAXONOMY.md`.

**Fix recommendation:** Two valid resolutions:
1. **Suite changes** — rename to an existing taxonomy value (preferred for stylistic mismatches).
2. **Taxonomy expansion** — propose a PR to ai-synapse adding the value (preferred when the suite represents a genuine new domain). Do NOT auto-add taxonomy rows from the validator.

**Why it matters:** Pre-commit hook on the main repo will reject any artifact with an unknown taxonomy value the moment the suite lands. Catch it at the gate.

---

## Check 4 — Domain README presence

**Trigger:** An artifact's domain directory lacks a `README.md` OR the `README.md` exists but does not contain a row matching the artifact (link to its file, with name).

**Scope:** This check uses the suite's own domain READMEs — not ai-synapse main-tree READMEs. The suite owns its READMEs; the validator only checks they exist and are populated.

**Fail signal:** Cross-suite section lists the artifact path and which README is missing or stale.

**Fix recommendation:** "Add a row to `<suite>/skills/<domain>/README.md` linking to `<artifact-name>` with a one-line description, OR create the README if it doesn't exist."

**Why it matters:** ai-synapse pre-commit hook enforces domain README rows. A suite missing them will fail the hook on the first commit after wiring in.

---

## Check 5 — Pathway synapse path resolution

**Trigger:** A pathway artifact (`pathways/<name>.yaml`) lists `synapses:` paths that don't resolve.

**Resolution rules:** A `synapses:` entry resolves if the path exists either:
- Inside the suite (relative to `<suite-root>`), OR
- Inside the ai-synapse main tree (relative to repo root).

**Fail signal:** Cross-suite section lists each unresolved path: `pathway X references missing synapse: <path>`.

**Fix recommendation:** "Either the synapse target hasn't been added yet (add it before promoting the pathway), or the path is wrong (fix the YAML)."

---

## Check ordering and short-circuiting

Run all five checks unconditionally — none short-circuits another. A suite can be guilty of every cross-suite issue simultaneously, and the maintainer needs to see the full picture in one report.

The cross-suite section in the rollup is omitted entirely when all five checks pass with zero issues. Do NOT emit "Cross-suite issues: 0" header followed by an empty list — silent absence is the success signal.

# Decision Memo — delivery-plan-writer

> Artifact type: skill | Memo type: creation | Design doc: `.brainstorms/2026-05-31-vertical-slice-planning-stack/design.md`

---

## What I want

A planning-stage skill that takes a spec / PRD / structured chat-intent and emits a set of vertical-slice **story files** (one validable outcome per story) plus a manifest, ready to be consumed by `delivery-orchestration-plan-executor`. The skill lives in `src/skills/delivery/` and sits **before** the orchestrator in the delivery pipeline.

Conceptually the unit is a **story**; the sanctioned scope vocab is **plan** — this skill operates on a plan-shaped artifact (a story-set). No new vocab row is introduced.

Concrete deliverables:
- N × `.delivery/stories/TAG-NNN-slug.md` story files conforming to `delivery-execution-slice-contract` + planner extension fields
- `.delivery/stories/STORIES.md` manifest (depends_on graph + status + foundation_source + spec_hash)
- Routing/wrong-tool detection so the skill refuses gracefully when the request is actually for `code-build-planner`, `docs-spec-writer`, or `delivery-orchestration-plan-executor`
- Slash-command surface with chat fallback for the same parameters

---

## Why Claude needs it

Without this skill, Claude given "slice this spec into stories for the orchestrator" currently:

- Conflates **per-module 6-phase decomposition** (code-build-planner's job) with **vertical-slice planning** — produces flat task lists instead of independently shippable slices.
- Emits ad-hoc markdown that the orchestrator cannot ingest because slice-contract required fields (`slice_id`, `validable_outcome`, `touches`, `depends_on`) are missing or named inconsistently.
- Skips foundation-slice detection, producing dependency graphs where every story depends on every other story (no parallelization possible).
- Has no consistent filename convention, so re-runs collide with prior plans and the orchestrator cannot deduplicate.
- Provides no place to declare per-story discipline deltas, so the dispatch-contract has nothing to inject as `{{discipline_deltas}}`.

The failure isn't "the output could be better" — it's that the downstream orchestrator's `[PRE-FLIGHT]` halts because the artifact shape doesn't match. The pipeline can't start.

---

## Injection shape

- **Workflow:** input-tier validation → wrong-tool detection → horizontal-doc discovery → foundation-slice detection cascade → story decomposition → manifest assembly → re-run collision check.
- **Policy:** granularity judgment (HARD floor / SOFT cap / refusal bands), foundation-slice cascade precedence, tag-sourcing rules (CLI on first run; persisted thereafter), wrong-tool redirects.
- **Domain knowledge:** slice-contract field grammar, planner extension fields, STORIES.md manifest schema, status vocabulary, hand-off contract with the orchestrator.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| `.delivery/stories/TAG-NNN-<slug>.md` | N (typically 3–30) | yes during planning; orchestrator-owned during execution | One vertical slice per file — slice-contract conformant body with planner extension frontmatter |
| `.delivery/stories/STORIES.md` | 1 | yes — append on re-run, status updates by orchestrator | Manifest: tag, depends_on graph, status per story, foundation_source, spec_hash |

No `INTERFACES.md` is emitted. Interfaces live in each story's `Context` section + the `depends_on` graph.

---

## Story body shape

<!-- VERBATIM from notepad — story frontmatter is load-bearing for the orchestrator's slice-contract validator -->

```yaml
---
# --- delivery-execution-slice-contract ---
slice_id: TAG-NNN
validable_outcome: "..."
touches: [path1, path2]
depends_on: [TAG-NNN, ...]
# --- planner extension ---
status: planned
requirements_traced: [FR-NNN, ...]
protocols:
  - delivery-execution-tdd-contract
  - delivery-execution-coding-contract
  - delivery-execution-slice-contract
discipline_deltas: []
file_cap_override: null
slice_contract_version: 2  # paired bump
---
```

Body sections, in order:
1. **Story** — narrative statement of the slice.
2. **Context** — neighbor files + interface signatures consumed (replaces a separate INTERFACES.md).
3. **Constraints from horizontal docs** — NFRs, architecture rules, scope guardrails inherited from horizontal docs. CONFLICT blocks surface here.
4. **Test scenarios** — concrete cases that demonstrate `validable_outcome`.
5. **Out of scope** — explicit non-goals for this slice.

---

## Naming conventions

| Element | Pattern | Notes |
|---|---|---|
| Skill slug | `delivery-plan-writer` | Mirrors sibling `delivery-orchestration-plan-executor`. Subdomain `plan`, scope `plan`, role `writer`. |
| Story filename | `TAG-NNN-<slug>.md` | TAG required; NNN zero-padded sequence; slug kebab-case derived from `slice_id`. No `slug` frontmatter field. |
| Manifest | `STORIES.md` | NOT `INDEX.md` — basename collides with `.delivery/plan/INDEX.md`. |
| Tag sourcing | `--tag` required on first run; persisted to `STORIES.md` frontmatter | Subsequent runs READ the persisted tag — never re-infer. `TAG='FR'` is forbidden (reserved for spec namespace). |
| Routing-contract description | "Use when the user signals 'slice this spec into stories', 'plan delivery slices', 'generate story files for orchestrator', or 'break this into vertical slices for parallel execution'. Not for single-module 6-phase decomposition (use code-build-planner), not for spec authoring (use docs-spec-writer), not for executing existing stories (use delivery-orchestration-plan-executor)." | Description is the routing contract — keep verbatim in SKILL.md frontmatter. |

---

## Inputs (tiered)

| Tier | Source | Behavior |
|---|---|---|
| REQUIRED (one-of) | spec doc \| PRD \| structured chat-intent | Chat-intent must carry minimum schema: `problem` / `in-scope` / `out-of-scope` / `constraints`. Refuse if missing. |
| RECOMMENDED | design doc | Loads if present; absence warns, does not refuse. |
| AUTO-DISCOVERED | horizontal docs (architecture, NFRs, scope) | Precedence: `--horizontal-docs` flag > nearest-ancestor > root-level. Conflicts surface as `CONFLICT` blocks in affected stories' Constraints section. |
| OPTIONAL (re-runs) | prior `.delivery/lessons.md` + `closeouts/` | Used to inform decomposition on re-runs. |

**Free-form / chat-intent fallback:** the orchestrator keeps a free-form fallback path with a loud warning — documented here so this skill's chat-intent mode is consistent with that posture.

---

## Foundation-slice rule (cascade)

Precise precedence, halts at first match:

1. `--foundation-first auth,db,logger` — explicit CLI declaration.
2. `architecture.md` frontmatter `foundations: [...]` — structural field, NOT heading-string scraping.
3. Cross-FR commonality heuristic — module/concept referenced by ≥60% of FRs (threshold configurable in `.delivery/config.yaml`).
4. None → write `foundation_source: none-with-risk` warning. Require `--confirm-no-foundation` flag when ≥2 stories share a touched module.

`STORIES.md` frontmatter records `foundation_source: declared | architecture | inferred | none-with-risk`.

---

## Granularity policy

| Band | Rule | Action |
|---|---|---|
| HARD floor | One validable outcome per story (one test verifies done) | Inherited from slice-contract. |
| SOFT cap | ≤8 files touched | Configurable via `.delivery/config.yaml: granularity.file_cap`. Per-story override via `file_cap_override: <reason>`. Outcome cap overrides file cap. |
| LOWER refusal | Trivial slices (single rename, formatting, one-line) | Merge into siblings; refuse standalone story. |
| UPPER refusal | >30 stories | Refuse without `--confirm`. |
| Degenerate input | 1-story decomposition | Refuse and redirect to `code-build-planner`. |

---

## Boundary vs `code-build-planner`

`code-build-planner` decomposes a single module into 6 sequential implementation phases; this skill decomposes a spec/PRD across modules into N independently-shippable vertical slices — both produce ordered work, but `code-build-planner` operates within one module's depth while this skill operates across module breadth.

---

## Wrong-tool detection (surface signals)

| Surface signal | Action |
|---|---|
| Single module path + no spec | Redirect to `code-build-planner`. |
| Only goal sentence + no requirements doc | Redirect to `docs-spec-writer`. |
| Stories already exist + intent is execution | Redirect to `delivery-orchestration-plan-executor`. |
| Single-bug-fix / refactor-only / docs-only | Refuse + redirect to direct edit. |

---

## Re-run policy

- Detect existing `TAG-NNN` files in `.delivery/stories/`.
- Refuse on non-`planned` status unless `--replan-only=<ids>` scopes the rewrite.
- Record `spec_hash` per story for collision detection across re-runs (spec changed → re-plan permitted; spec unchanged → idempotent no-op).

---

## Invocation surface

Slash-command form:

```
/delivery-plan-writer [--input-mode {spec,prd,intent}]
                           [--tag <TAG>]
                           [--foundation-first <list>]
                           [--file-cap <N>]
                           [--horizontal-docs <path>]
                           [--replan-only <ids>]
                           [--confirm]
                           [--confirm-no-foundation]
```

Chat fallback elicits the same parameters via structured questions.

---

## Hand-off contract with orchestrator

Lives as a subsection in SKILL.md so consumers don't have to derive it.

- **Orchestrator entrypoint:** `STORIES.md` (manifest is the read-target, not individual story files).
- **Status vocabulary:** `pending | in-progress | done | blocked`.
- **Ownership:**
  - Writer-owned during the planning phase (this skill mutates story files + manifest).
  - Orchestrator-owned during the execution phase (status transitions, closeout linkage).

---

## Pipeline placement

| Field | Value |
|---|---|
| Stage name | `plan-story-write` |
| input_type | `spec` \| `prd` |
| output_type | `story-set` |
| context_type | `horizontal-docs + lessons` |
| requires_any | `[spec, prd]` |
| Position | Sequential, immediately before `delivery-orchestration-plan-executor`. |
| Chat-intent path | Documented as non-pipeline (entry via slash-command or chat fallback only). |

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| `--tag` omitted on first run | Refuse with explicit error; do not auto-infer. |
| `TAG='FR'` requested | Refuse — reserved for spec namespace. |
| Re-run with mutated spec | Detect via `spec_hash`; refuse non-`planned` overwrites without `--replan-only`. |
| Horizontal doc conflicts (multiple architecture.md found) | Apply precedence chain; emit `CONFLICT` block in affected stories' Constraints section. |
| 1-story decomposition | Refuse → redirect to `code-build-planner`. |
| >30 stories without `--confirm` | Refuse with upper-band message. |
| Chat-intent missing required schema fields | Refuse loudly (problem / in-scope / out-of-scope / constraints all required). |
| No foundation slice detected + shared modules | Require `--confirm-no-foundation`; write `foundation_source: none-with-risk`. |
| `slice_contract_version` mismatch with orchestrator | Orchestrator validates on read; planner writes current version. |
| Existing stories at `INDEX.md` (legacy basename) | Not handled — manifest is `STORIES.md` by design; legacy is out of scope. |

---

## Companion files anticipated

**Always-loaded (SKILL.md body):**
- Tiered input table, granularity policy, foundation-slice cascade, wrong-tool detection table, hand-off contract — these gate every invocation.

**Templates:**
- `templates/story.md` — story body skeleton with the verbatim frontmatter block above + Story/Context/Constraints/Test scenarios/Out-of-scope section headers.
- `templates/STORIES.md` — manifest skeleton with frontmatter (tag, foundation_source, spec_hash map) + status table.

**References (load-at-decision-point):**
- `references/foundation-detection.md` — cascade rules, configurable threshold details, examples of each `foundation_source` value.
- `references/wrong-tool-redirects.md` — full redirect rationale and example phrasing for each surface signal.
- `references/horizontal-doc-discovery.md` — precedence algorithm, conflict serialization format.
- `references/slice-contract-fields.md` — pointer to `delivery-execution-slice-contract` with the planner-extension delta enumerated.

No agents anticipated — this is a single-context skill.

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `delivery-execution-slice-contract` | consumes (schema) | Provides the 4 required frontmatter fields the planner emits per story. |
| `delivery-orchestration-closeout-schema` | paired-CR dependency | Adds fields for lint / typecheck / evidence / `applied_deltas` / `declared_edges`. Planner's `slice_contract_version` bump is paired with this schema bump. |
| `delivery-orchestration-dispatch-contract` | paired-CR dependency | `{{worker_protocols}}` slot description amended from 3 → 4 bodies (adds coding-contract). Planner emits `protocols:` with 4 entries, requiring dispatch to inject all 4. |
| `delivery-orchestration-plan-executor` | paired-CR dependency (orchestrator rename) | 6 existing `write-story` references must be renamed to `delivery-plan-writer` in the same PR. Orchestrator entrypoint reads `STORIES.md`. |
| `delivery-execution-coding-contract` | consumes (protocol name only) | Planner lists this in story frontmatter `protocols:`; rule table lives in that protocol's own memo, not here. |
| `delivery-execution-tdd-contract` | consumes (protocol name only) | Listed in story frontmatter `protocols:`. |
| `.delivery/lessons.md` + `closeouts/` (orchestrator-produced) | optionally consumes on re-runs | Informs decomposition; absent on first runs. |
| Horizontal docs (`architecture.md`, NFRs, scope) | consumes | Auto-discovered per precedence chain; surfaces conflicts in story Constraints. |

**Paired-CR coordination note:** This skill cannot ship alone. Its PR must declare paired dependencies on the closeout-schema CR, the dispatch-contract CR, and the orchestrator's `write-story` → `delivery-plan-writer` rename. Suggested rollout: separate PRs per artifact, each cross-referencing the others.

---

## Open questions

None — all threads resolved during the [B] revision pass and confirmed at the [D] done-signal sweep. The creator should focus on:
- Wording the SKILL.md routing-contract description verbatim from the draft above.
- Faithfully reproducing the story frontmatter YAML block (it is the load-bearing contract).
- Keeping the rule-table for `delivery-execution-coding-contract` OUT of this skill — reference the protocol by name only.

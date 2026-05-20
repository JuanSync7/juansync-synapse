# Decision Memo — docs-claim-doc-classifier

> Artifact type: agent | Memo type: creation | Design doc: `.brainstorms/2026-05-13-shrink-skill/design.md`

---

## What I want

A read-only agent that classifies a markdown file's structural genre and, when applicable, its claim sub-type. The agent receives full file content and path, calls an LLM to determine category and confidence, and returns a structured output. It gates entry to the entire shrink-skill workflow — if the classifier rejects a doc, no further agents run.

---

## Why Claude needs it

Without a dedicated classifier, the shrinker skill has no principled way to distinguish claim-based docs (identity, style, principle, decision) from narrative prose, reference docs, or templates. Inlining classification into the skill body produces inconsistent category boundaries, no reusable schema, and no confidence gating — the skill would silently attempt compression on unsupported doc types and produce corrupted or misleading output.

---

## Injection shape

- **Policy:** Categorization rules for genre detection (claim-based vs narrative vs reference vs tutorial vs template vs mixed), sub-type rules for claim-based docs (identity/style/principle/decision), the mixed-doc threshold (>30% non-claim region triggers `mixed`), and confidence-floor refusal policy (< 0.6 → refuse).
- **Domain knowledge:** Taxonomy of claim-based-doc genres and sub-types as defined in the vocabulary files.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| `classifier_output` JSON object | 1 | No | Consumed by shrinker skill to gate workflow entry and set sub-type context for downstream agents |

---

## Agent frontmatter (VERBATIM)

```yaml
---
name: docs-claim-doc-classifier
description: Classifies a markdown file's structural genre (claim-based, narrative, reference, tutorial, template, mixed) and the claim sub-type (identity, style, principle, decision). Returns confidence. Read-only.
domain: docs
subdomain: claim
scope: doc
role: classifier
---
```

Path: `src/agents/docs/docs-claim-doc-classifier/docs-claim-doc-classifier.md`

---

## Input / Output contract (VERBATIM)

Input: `{ file_content: string, file_path: string }`

Output:

```yaml
# Classifier output
classifier_output:
  schema_version: "1"
  category: claim-based | narrative | reference | tutorial | template | mixed
  sub_type: identity | style | principle | decision | null  # only when category=claim-based
  confidence: float            # [0.0, 1.0]
```

Mixed rule: if any non-claim region > 30% of doc length → `category=mixed`, `sub_type` carries the primary claim sub-type if detectable, else null.

---

## Preciseness decisions

- Drop `reasoning_summary` from output — the shrinker skill does not surface it; only `confidence` is consumed by callers.
- No opt-out flags on input — this agent has exactly one mode: classify and return.
- Category enum is extensible: unknown categories are logged, not crashed.
- `sub_type` is null for all non-claim-based categories; callers must not assume its presence.

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| Very short doc (< 5 non-blank lines) | Classify but surface low-confidence result; skill defaults to refuse if confidence < 0.6 |
| `confidence < 0.6` | Return result with confidence value; shrinker skill applies `classifier_confidence_floor` threshold and issues refusal to user |
| `category = mixed` | Return with `mixed` category; shrinker refuses unless `--accept-mixed` flag passed by caller |
| Category not in known enum | Log unknown category; do not crash; return with confidence 0.0 so skill refuses |
| Malformed or binary input | Fail fast with structured error, not empty/garbage response |
| LLM returns malformed JSON | One retry, then surface structured error to caller |
| SKILL.md passed as input | Risk: SKILL.md has claim-like sections; classifier must use genre signals (frontmatter, routing contract, anatomy) to identify skill files and refuse — not classify as claim-based |

---

## Robustness constraints

- Validates input schema before LLM call; returns structured error on malformed input.
- Empty content → fail fast with error code, not empty response.
- LLM-returned malformed JSON → one retry, then surface error.
- Confidence floor `0.6` applied by the calling skill, not this agent — agent always returns its confidence value and lets the caller enforce policy.
- Schema versioning: output includes `schema_version: "1"`. Downstream agents reject unknown versions loudly.

---

## Threshold reference (VERBATIM)

```yaml
classifier_confidence_floor: 0.6  # below this, skill refuses with low-confidence message
```

Full threshold set lives in `src/skills/docs/docs-claim-doc-shrinker/references/thresholds.yaml`.

---

## Vocabulary additions (VERBATIM)

```
# registry/AGENT_VOCABULARY.md additions
## Domains
| `docs` | User-facing documentation agents |
## Subdomains
| `claim` | Agents that operate within the claim-based-doc workflow |
## Scopes
| `doc` | Operates on a single markdown doc |
## Roles
| `classifier` | Categorizes input into a fixed enum |
```

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `docs-claim-doc-shrinker` (skill) | produces for | Shrinker calls classifier at `audit` entry; result gates all downstream work. Category + sub_type + confidence passed forward. |
| `docs-claim-doc-extractor` (agent) | produces for (indirectly) | Extractor only runs after classifier returns `claim-based`; sub_type passed through shrinker dispatch. |
| `docs-claim-doc-writer` (agent) | produces for (indirectly) | Writer receives voice-anchor instruction only when sub_type = `style`; determined by classifier output. |
| `docs-claim-claim-judge` (agent) | produces for (indirectly) | Judge runs only after claim-based classification; no direct input from classifier, but gates whether judge is invoked at all. |
| `registry/AGENT_VOCABULARY.md` | produces for | New rows for `docs` domain, `claim` subdomain, `doc` scope, `classifier` role must be added in same PR. |

---

## Boundary findings

- Pure classification — no side effects, no file writes, no rewriting.
- Does NOT detect contradictions (that is the extractor's job).
- Does NOT assess quality or suggest improvements.
- Output schema is consumed by all 4 other artifacts in the workflow — interface stability is critical. `schema_version` field locks the contract; agents reject unknown versions loudly.
- Reuse potential: high — any future docs-domain skill can gate on this classifier without modification.

---

## Maintenance findings

- Schema versioning: adding `schema_version: "1"` to output makes future schema evolution explicit and safe.
- Category enum extensible: new categories (e.g., `changelog`) can be added without breaking callers that handle unknown gracefully.
- Coupling risk: 4 downstream artifacts consume this output schema. Any schema change requires coordinated update across shrinker + 3 agents — treat as a protocol-level change.
- Registry housekeeping (same PR): add row to `registry/AGENTS_REGISTRY.md`; add vocabulary rows to `registry/AGENT_VOCABULARY.md`.

---

## Usability findings

- Failure messages from the skill (not this agent) when classifier rejects:
  - `"Doc classified as {category} (confidence {c}). This skill handles claim-based docs only. {redirect}"`
  - `"Doc is mixed ({n}% claim, {m}% narrative). Pass --accept-mixed to proceed."`
- This agent returns structured output only — the calling skill is responsible for translating to user-facing messages.
- Naming is self-explanatory via `{domain}-{subdomain}-{scope}-{role}` convention: `docs-claim-doc-classifier`.

---

## Open questions

None — all threads resolved during brainstorm lens rotation.

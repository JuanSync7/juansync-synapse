# Design Document — docs-claim-shrinker (Skill + 4 Agents)

> Brainstorm slug: `2026-05-13-shrink-skill`
> Status: **complete** | Artifact: multi-artifact — 1 skill + 4 agents (creation) | Target: `juansync-synapse`, PR → `develop`

---

## 1. Problem Statement

Claim-based markdown documents (identity files, style guides, decision logs, principle manifests) accumulate redundant phrasing, padding, and inflated transitions over time. No tool exists that can compress such documents while guaranteeing that every retained assertion is preserved in the output — "lossless density increase against a kept-claim set."

Root causes:

1. Existing LLM rewrite flows are lossy — they summarize or paraphrase without any entailment guarantee, so claims can silently disappear.
2. There is no structured audit step that lets a human declare what to keep before any rewrite begins, making the process non-HITL-safe.
3. No classification gate exists to prevent claim-preserving logic from being applied to document types (narrative, reference, template) where that contract is meaningless or harmful.

What changes: the shrinker introduces a two-phase workflow (audit → compress) with a classifier gate, human-editable keep/cut checklist, and post-write entailment verification so that density increases are auditable and reversible.

---

## 2. Design Principles

### P1: Classifier is the unconditional entry gate

The skill only applies to claim-based documents. Rather than relying on user judgement to identify doc type, an LLM classifier runs on every invocation and blocks non-claim-based input with an explicit refusal and redirect. There is no override for non-claim-based categories; there is an explicit `--accept-mixed` path for `mixed` docs.

**Implication:** The classifier's output schema is a shared dependency consumed by four artifacts. Schema versioning (`schema_version: "1"`) is required from day one, and a confidence floor of 0.6 gates the classification itself — below floor, the skill refuses rather than proceeds on a guess.

### P2: Human-in-the-loop is enforced structurally, not by convention

The audit phase writes a per-claim checklist to `.shrink/<file>.audit.md`. The compress phase hard-refuses if no checklist exists. In headless mode, the default-keep-all checklist produces a near-no-op compress with an explicit warning — the system cannot silently compress without a human edit step.

**Implication:** The compress flow must check for checklist existence and source-hash match before dispatching any agent. No implicit safe-default compress is allowed in interactive mode.

### P3: Entailment is verified after every compress, not assumed

After the writer produces a rewritten document, every kept claim is independently judged for entailment. The results are reported before any write occurs. If more than 20% of kept claims fail, the write is aborted. The source file is never modified without a passing coverage report.

**Implication:** The atomic-write pattern (write to `<file>.tmp`, then rename) is mandatory. Coverage reporting to stdout and `.shrink/<path>.coverage.md` happens before the rename. Abort leaves the source untouched.

### P4: Claim IDs are deterministic and stable

Claim IDs are derived from `sha256(heading_anchor + claim_text)[:8]`. Determinism enables checklist diffing across re-runs: if a user audited a prior version of the document, unchanged claims carry the same IDs and their keep/cut decisions survive. If a heading is renamed in the source, IDs for claims under that heading change — this is intentional and surfaced as a hash-mismatch refuse.

**Implication:** The extractor's atomic-claim splitting rule must be precisely specified so that the same source text always produces the same claim text (and thus the same ID). No per-run non-determinism is acceptable.

### P5: Idempotency via delta floor, not caching

Compress re-extracts claims on every run. It only performs a write if the kept-claim set differs by ≥5% from the prior compress run. Silent overwrite of a nearly-identical file is avoided. The floor is a tunable constant in `references/thresholds.yaml`, not hardcoded in prompts.

**Implication:** All tunable numeric thresholds (coverage abort, delta floor, judge confidence, writer length sanity, voice anchor count, classifier confidence) are externalized to `thresholds.yaml`. Tuning never requires prompt edits.

### P6: Each agent has a single, bounded responsibility

Four agents (classifier, extractor, judge, writer) cover four distinct semantic contracts. No agent is permitted to blur into its neighbor's responsibility. The judge verifies — it does not suggest rewrites. The writer compresses — it does not evaluate entailment. The extractor lists — it does not keep/cut. Boundaries are enforced through schema contracts (structured inputs/outputs) and explicit Don't constraints in each agent's spec.

**Implication:** The writer is the weakest reuse case (most coupled to shrinker) and is flagged for a 3-month review checkpoint. If no second consumer emerges, it is demoted to an inline prompt in the shrinker.

### P7: All refusals include corrective action

Every refusal message names the exact corrective step or flag the user needs. Bare refusals without a next-step are not acceptable. Failure UX is treated as a first-class design output.

**Implication:** Five refusal message templates are specified verbatim and must be used as-written by the skill.

---

## 3. Architecture

### 3.1 Flow Graph

**audit subcommand:**

```
audit <path>
    │
    ├─► classifier(file_content, file_path)
    │       ├─ category ≠ claim-based → REFUSE ("Doc classified as {category}...")
    │       ├─ confidence < 0.6       → REFUSE (low-confidence)
    │       └─ category = mixed       → WARN, require --accept-mixed
    │
    ├─► extractor(file_content, file_path)
    │       └─ claims=[] → REFUSE ("doc has no extractable claims")
    │
    └─► write .shrink/<path>.audit.md
            (claims grouped by heading, default [x] keep,
             ## Contradictions, ## Redundancies)
```

**compress subcommand:**

```
compress <path>
    │
    ├─► check: .shrink/<path>.audit.md exists? → NO: REFUSE ("No audit found...")
    ├─► check: sha256(source) matches audit frontmatter? → NO: REFUSE ("Source changed...")
    │
    ├─► re-extract claims (idempotency check)
    │       └─ Δ kept-claim set < 5% → NO-OP with message, exit
    │
    ├─► writer(kept_claims, original_doc, voice_anchors [style sub-type only])
    │       ├─ any source heading missing from output → FAIL before judge stage
    │       └─ output length < 30% of input → WARN
    │
    ├─► for each keep claim:
    │       judge(claim, rewritten_doc)
    │           └─ verdict: entailed | partial | dropped
    │
    ├─► coverage check: failures > coverage_abort_pct (20%)?
    │       YES → ABORT, emit coverage report, NO WRITE
    │       NO  → proceed
    │
    ├─► atomic write: source → <path>.tmp → rename to <path>
    │
    └─► emit coverage report to stdout + .shrink/<path>.coverage.md
```

### 3.2 Node Specifications

#### docs-claim-shrinker (skill orchestrator)

Load: `references/thresholds.yaml`, `references/wrong-tool-redirect.md`, `.shrink/<path>.audit.md` (compress phase)

Do:
1. Parse subcommand (`audit` or `compress`) and file path argument.
2. Dispatch classifier; apply category gate and confidence gate.
3. (audit) Dispatch extractor; write checklist to `.shrink/<path>.audit.md`.
4. (compress) Verify audit exists and source hash matches.
5. (compress) Re-extract; compute delta; skip write if Δ < 5%.
6. (compress) Dispatch writer with kept claims and (if style sub-type) 3–5 voice anchor sentences sampled from source.
7. (compress) Dispatch judge once per kept claim; collect verdicts.
8. (compress) Compute coverage; abort if failures > 20%.
9. (compress) Atomic write: `<path>.tmp` → rename to `<path>`.
10. (compress) Emit coverage report to stdout and `.shrink/<path>.coverage.md`.

Don't:
- Default-keep-all in interactive mode without emitting a warning.
- Write source file before coverage check passes.
- Proceed past hash mismatch.
- Hardcode thresholds — all numeric gates load from `thresholds.yaml`.

Exit: success (compress complete or audit written) | refusal (gate failed) | abort (coverage failed).

---

#### docs-claim-doc-classifier

Load: `{ file_content: string, file_path: string }`

Do:
1. Classify structural genre: `claim-based | narrative | reference | tutorial | template | mixed`.
2. If `claim-based`, identify sub-type: `identity | style | principle | decision`.
3. Compute confidence `[0.0, 1.0]`.
4. If any non-claim region exceeds 30% of doc length, set `category = mixed`.
5. Return `classifier_output` schema.

Don't:
- Detect contradictions or assess claim quality (extractor's job).
- Attempt classification on docs < 5 non-blank lines without surfacing low confidence.
- Return reasoning_summary field (dropped — not consumed).

Exit: `classifier_output` object, or structured error on malformed input.

---

#### docs-claim-doc-extractor

Load: `{ file_content: string, file_path: string }`

Do:
1. Split document into heading-anchored sections.
2. For each section, extract atomic claims (one assertion per claim; split compound sentences at independent conjunctions: "and"/"but"/"however").
3. Assign claim IDs: `sha256(heading_anchor + claim_text)[:8]`.
4. For headingless regions, use anchor `L<start>-L<end>`.
5. For docs exceeding token budget, chunk by heading, merge claim list, apply deterministic ordering.
6. Auto-detect contradictions `(id_a, id_b, reason)` and redundancies `(id_a, id_b, similarity)`.
7. Return structured output.

Don't:
- Make keep/cut decisions.
- Produce per-claim confidence scores (extraction is binary).
- Emit non-deterministic IDs across re-runs.

Exit: `{ claims: [Claim], contradictions: [...], redundancies: [...] }`, or structured error on empty content.

---

#### docs-claim-claim-judge

Load: `{ claim: Claim, rewritten_doc: string }`

Do:
1. Assess whether claim is semantically preserved in rewritten_doc (entailment = semantic preservation, not strict logical entailment; paraphrase is acceptable).
2. Classify verdict: `entailed | partial | dropped`.
   - `partial`: qualifier or hedge lost in rewrite.
   - `dropped`: no evidence found; `evidence_span` is null.
3. Return confidence `[0.0, 1.0]`; if confidence < 0.6, escalate verdict to `partial` regardless of stated verdict.
4. Cache verdict by `(sha256(claim.text), sha256(rewritten_doc))` for determinism on re-runs.

Don't:
- Suggest rewrites.
- Score quality or style.
- Crash on empty rewritten_doc — return all claims `dropped`.

Exit: `judge_verdict` object per claim.

---

#### docs-claim-doc-writer

Load: `{ kept_claims: [Claim], original_doc: string, voice_anchors: [string] (3–5, style sub-type only) }`

Do:
1. Rewrite the doc covering every claim in `kept_claims` (judge verifies downstream; writer does not self-verify).
2. Preserve every section heading present in `original_doc`.
3. For style sub-type: match cadence and diction to `voice_anchors`.
4. If output would be < 30% of input length, abort and report (likely over-compression).
5. Return `{ rewritten_doc: string }`.

Don't:
- Introduce any assertion not in `kept_claims`.
- Remove or rename headings from source.
- Summarize into TL;DR form.
- Accept `structure_preservation` as an opt-out parameter — it is a hard contract, not a flag.

Exit: `{ rewritten_doc: string }` or structured error (heading missing in output, length floor violated).

---

### 3.3 Entry Gates

| Transition | Gate conditions |
|---|---|
| audit → extractor | Classifier returned `category = claim-based` AND `confidence ≥ 0.6` |
| audit → checklist write | Extractor returned non-empty claim list |
| compress → re-extract | `.shrink/<path>.audit.md` exists AND `sha256(source)` matches `source_hash` in frontmatter |
| re-extract → writer dispatch | Δ kept-claim set ≥ 5% from prior compress |
| writer output → judge dispatch | All source headings present in writer output |
| judge results → atomic write | Coverage failures ≤ 20% of kept-claim count (`coverage_abort_pct`) |
| mixed doc → compress | `--accept-mixed` flag explicitly passed |

---

## 4. Schemas

### Claim object (extractor output, audit-checklist source, writer input)

<!-- VERBATIM -->
```yaml
# Claim object — extractor output, audit-checklist source, writer input
claim:
  id: string                  # deterministic hash(heading_anchor + claim_text)
  heading_anchor: string      # heading slug or "L<start>-L<end>" if no heading
  text: string                # one atomic assertion
  source_lines: [int, int]    # 1-indexed inclusive line range

# Classifier output
classifier_output:
  schema_version: "1"
  category: claim-based | narrative | reference | tutorial | template | mixed
  sub_type: identity | style | principle | decision | null  # only when category=claim-based
  confidence: float            # [0.0, 1.0]

# Judge verdict (one per claim per compress run)
judge_verdict:
  claim_id: string
  verdict: entailed | partial | dropped
  evidence_span: string | null  # substring of rewritten_doc, null when dropped
  confidence: float             # [0.0, 1.0]
```

### Audit checklist file shape (`.shrink/<file>.audit.md`)

<!-- VERBATIM -->
```markdown
---
source_path: <relative-path>
source_hash: <sha256-of-source-content>
audit_timestamp: <iso8601>
classifier:
  category: claim-based
  sub_type: identity
schema_version: "1"
---

## <Section Heading from source>
- [x] keep: <claim_id> — <claim text>
- [ ] cut:  <claim_id> — <claim text>
- [m] merge-with <other_id>: <claim_id> — <claim text>

## Contradictions
- (<id_a> ↔ <id_b>): <reason>

## Redundancies
- (<id_a> ≈ <id_b>): similarity <score>
```

---

## 5. Threshold Defaults

<!-- VERBATIM -->
```yaml
coverage_abort_pct: 0.20        # abort compress if >20% of keep-claims fail entailment
idempotency_delta_floor_pct: 0.05  # only rewrite if ≥5% claim delta from prior compress
judge_confidence_floor: 0.6     # below this, escalate verdict to "partial"
writer_length_sanity_pct: 0.30  # warn if output <30% of input length
classifier_confidence_floor: 0.6  # below this, refuse with low-confidence message
voice_anchor_count_min: 3
voice_anchor_count_max: 5
```

Stored at: `src/skills/docs/docs-claim-shrinker/references/thresholds.yaml`

---

## 6. File Layout

<!-- VERBATIM -->
```
src/skills/docs/docs-claim-shrinker/
├── SKILL.md
├── EVAL.md
└── references/
    ├── thresholds.yaml
    ├── claim-schema.md
    ├── classifier-schema.md
    ├── judge-schema.md
    ├── audit-checklist-template.md
    └── wrong-tool-redirect.md
```

Agents:
- `src/agents/docs/docs-claim-doc-classifier.md`
- `src/agents/docs/docs-claim-doc-extractor.md`
- `src/agents/docs/docs-claim-claim-judge.md`
- `src/agents/docs/docs-claim-doc-writer.md`

Working files (gitignored by default):
- `.shrink/<file>.audit.md` — per-claim keep/cut checklist
- `.shrink/<file>.coverage.md` — post-compress entailment report

---

## 7. Artifact Frontmatter

### docs-claim-shrinker

<!-- VERBATIM -->
```yaml
---
name: docs-claim-shrinker
description: Audit and compress claim-based markdown (identity, style, principle, decision docs). Run `audit` to produce a per-claim keep/cut/merge checklist; edit it; run `compress` to rewrite the doc preserving every kept claim. Triggers: "shrink this doc", "densify", "tighten this", "compress markdown".
domain: docs
subdomain: claim
scope: doc
role: shrinker
---
```

### docs-claim-doc-classifier

<!-- VERBATIM -->
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

### docs-claim-doc-extractor

<!-- VERBATIM -->
```yaml
---
name: docs-claim-doc-extractor
description: Extracts atomic claims from a claim-based markdown doc. Returns a list of claim objects anchored by source heading, plus auto-flagged contradictions and redundancies. Read-only.
domain: docs
subdomain: claim
scope: doc
role: extractor
---
```

### docs-claim-claim-judge

<!-- VERBATIM -->
```yaml
---
name: docs-claim-claim-judge
description: Judges whether a single claim is semantically preserved in a rewritten document. Returns entailed | partial | dropped with evidence span. Designed for batch dispatch (one call per claim).
domain: docs
subdomain: claim
scope: claim
role: judge
---
```

### docs-claim-doc-writer

<!-- VERBATIM -->
```yaml
---
name: docs-claim-doc-writer
description: Rewrites a claim-based doc compressed against a fixed kept-claim set. Does NOT generate from scratch. Does NOT introduce claims outside the input set. Preserves section headings. For style-sub-type docs, preserves cadence via voice anchors.
domain: docs
subdomain: claim
scope: doc
role: writer
---
```

---

## 8. Wrong-Tool Block

<!-- VERBATIM -->
```markdown
## Wrong-Tool Detection
- Target is a **SKILL.md** → use `synapse-skill-improver`
- Target is **narrative prose** (essays, blog posts, articles) → manual rewrite; claim-coverage destroys voice
- Target is **reference doc** (API, glossary) → completeness is the goal, not density
- Target is a **template** → already structural
- User wants **lossy summary / TL;DR** → general LLM rewrite; this skill is lossless on kept claims only
```

---

## 9. Refusal Messages

<!-- VERBATIM -->
```
"Doc classified as {category} (confidence {c}). This skill handles claim-based docs only. {redirect}"
"No audit found at .shrink/{path}.audit.md. Run audit first."
"Source changed since audit (hash mismatch). Re-run audit before compress."
"Mixed doc ({n}% claim, {m}% narrative). Pass --accept-mixed to proceed."
"Coverage check failed: {failed}/{total} keep-claims dropped. No write performed. See .shrink/{path}.coverage.md."
```

---

## 10. Naming Conventions

All five artifacts follow the `{domain}-{subdomain}-{scope}-{role}` pattern.

| Segment | Values used | Source |
|---|---|---|
| `domain` | `docs` | `registry/SKILL_VOCABULARY.md` (new entry) |
| `subdomain` | `claim` | `registry/SKILL_VOCABULARY.md` (new entry) |
| `scope` | `doc`, `claim` | `registry/SKILL_VOCABULARY.md` (new entries) |
| `role` | `shrinker`, `classifier`, `extractor`, `judge`, `writer` | vocabulary registries |

The judge uses scope `claim` (not `doc`) because it operates on a single claim's entailment status, not a full document. All five names are self-explanatory without registry lookup.

---

## 11. Vocabulary Registry Additions

<!-- VERBATIM -->
```
# registry/SKILL_VOCABULARY.md additions
## Domains
| `docs` | User-facing documentation skills |
## Subdomains
| `claim` | Claim-based docs (identity, style, principle, decision sub-types) |
## Scopes
| `doc` | Operates on a single markdown doc |
## Roles
| `shrinker` | Lossless density increase against a kept-claim set |

# registry/AGENT_VOCABULARY.md additions
## Domains
| `docs` | User-facing documentation agents |
## Subdomains
| `claim` | Agents that operate within the claim-based-doc workflow |
## Scopes
| `doc` | Operates on a single markdown doc |
| `claim` | Operates on a single claim's entailment status |
## Roles
| `extractor` | Extracts atomic structured items from input |
| `classifier` | Categorizes input into a fixed enum |
```

Registry files updated in the same PR:
- `registry/SKILL_REGISTRY.md` — 1 new entry (shrinker)
- `registry/AGENTS_REGISTRY.md` — 4 new entries
- `registry/SKILL_VOCABULARY.md` — 4 new rows
- `registry/AGENT_VOCABULARY.md` — 4 new rows

---

## 12. Accepted Tensions

| Tension | Decision | Revisit when |
|---|---|---|
| Writer reuse uncertain — most tightly coupled to shrinker of the four agents | Separate agent accepted; reuse trajectory monitored | 3-month checkpoint: if no second consumer, demote to inline prompt in shrinker |
| Contradiction + redundancy detection bundled into extractor | Accept bundling for MVP; boundary is cleanly scoped within read-only extraction | A second consumer of extracted claims emerges that doesn't need the contradiction analysis |
| Judge slug locks `docs-claim` subdomain; future general-purpose judge would need a new name | Accept narrow scope for MVP | Promotion review: if a general-purpose judge is proposed, evaluate alias or promote to broader subdomain (e.g., `meta-eval-claim-judge`) |
| Voice-anchor logic specific to `style` sub-type — may evolve as TONE/WRITING_STYLE grow | Accept current form; voice anchors are sampled (3–5 sentences), not full-file | `TONE.md` or `WRITING_STYLE.md` evolves significantly; re-evaluate what "voice preservation" means |
| SKILL.md files are themselves claim-like and risk false-positive classifier hits | Classifier must distinguish `skill` doc sub-type; note as ⚠ risk | First production run classifying a SKILL.md produces an incorrect `claim-based` verdict |

---

## 13. Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `docs-claim-doc-classifier` | shrinker consumes | Returns `classifier_output` schema (schema_version: "1"); shrinker gates on category + confidence |
| `docs-claim-doc-extractor` | shrinker consumes | Returns `{ claims: [Claim], contradictions, redundancies }`; shrinker reads claims for checklist write and compress delta check |
| `docs-claim-doc-writer` | shrinker consumes | Accepts `{ kept_claims, original_doc, voice_anchors? }`; returns `{ rewritten_doc }`; shrinker feeds to judge |
| `docs-claim-claim-judge` | shrinker consumes (batch) | Accepts `{ claim, rewritten_doc }`; returns `judge_verdict`; shrinker aggregates for coverage gate |
| `registry/SKILL_VOCABULARY.md` | skill produces to | 4 new rows (domain, subdomain, scope, role); same PR |
| `registry/AGENT_VOCABULARY.md` | agents produce to | 4 new rows; same PR |
| `registry/SKILL_REGISTRY.md` | skill produces to | 1 new entry; same PR |
| `registry/AGENTS_REGISTRY.md` | agents produce to | 4 new entries; same PR |
| `references/thresholds.yaml` | all agents/skill consume | Single source of truth for all numeric thresholds; agents must not hardcode values in prompts |
| `juansync-synapse` repo | target | Artifacts land here; PR targets `develop` branch; repo must be in sync with `ai-synapse/develop` before branching |

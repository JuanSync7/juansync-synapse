# Decision Memo — docs-claim-doc-shrinker

> Artifact type: skill | Memo type: creation | Design doc: `.brainstorms/2026-05-13-shrink-skill/design.md`

---

## What I want

A skill that audits and compresses claim-based markdown documents in two explicit subcommands. `audit` classifies the document, extracts all atomic claims, and writes a per-claim keep/cut/merge checklist that the user edits. `compress` reads that edited checklist, rewrites the source document preserving every kept claim at higher density, verifies entailment of every kept claim, and aborts if coverage failures exceed the threshold. The primary test case is `SOUL.md`. Single-file MVP; no glob support.

---

## Why Claude needs it

Without this skill, Claude produces freeform summarization that drops claims silently, cannot verify claim coverage, and does not separate the "decide what to keep" phase from the "rewrite" phase. The result is lossy compression with no audit trail and no user control over which assertions survive.

---

## Injection shape

- **Workflow:** Two-phase orchestration — `audit` phase (classify → extract → write checklist) and `compress` phase (gate check → re-extract → write → judge → abort-or-commit). Phase descriptions, flow graph, and node specs are the primary payload.
- **Policy:** Refusal rules for non-claim-based docs, stale-source detection, idempotency gate, coverage-abort threshold, headless-mode safe-default.
- **Domain knowledge:** Claim-based doc taxonomy (identity, style, principle, decision sub-types), audit checklist format, threshold defaults loaded from `references/thresholds.yaml`.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| `.shrink/<path>.audit.md` | 1 per audit run | Yes (user edits) | Per-claim keep/cut/merge checklist for user review |
| Rewritten source file | 1 per compress run | Yes (atomic write) | Densified doc with all kept claims preserved |
| `.shrink/<path>.coverage.md` | 1 per compress run | No | Claim-by-claim entailment verdict table |
| stdout coverage report | 1 per compress run | No | Immediate terminal feedback before write commits |

---

## Flow graph

<!-- VERBATIM -->
```
audit <path>     → classifier → extractor → write .shrink/<path>.audit.md
compress <path>  → check audit exists + source-hash matches
                 → re-extract (idempotency Δ check)
                 → writer(kept_claims, voice_anchors)
                 → for each keep claim: judge(claim, output)
                 → abort if coverage failures > coverage_abort_pct
                 → atomic write (tmp+rename) to source path
                 → emit coverage report to stdout + .shrink/<path>.coverage.md
```

---

## Node specifications

**[AUDIT — classifier]** Load: `references/thresholds.yaml`. Do: dispatch `docs-claim-doc-classifier` with full file content + path; receive `{ category, sub_type, confidence }`. Don't: proceed if confidence < 0.6 or category is not claim-based (or mixed without `--accept-mixed`). Exit: on pass → extractor; on fail → hard refuse with redirect message.

**[AUDIT — extractor]** Load: `references/claim-schema.md`. Do: dispatch `docs-claim-doc-extractor`; receive `{ claims, contradictions, redundancies }`; snapshot source content hash. Don't: proceed if claims list is empty. Exit: on non-empty claims → write checklist; on empty → refuse.

**[AUDIT — write checklist]** Load: `references/audit-checklist-template.md`. Do: write `.shrink/<path>.audit.md` with claims grouped by source heading, default `- [x] keep`, plus `## Contradictions` and `## Redundancies` sections; gitignore `.shrink/` by default. Don't: overwrite a user-edited checklist silently (warn if mtime is newer than last audit run). Exit: always → done, emit path to user.

**[COMPRESS — gate check]** Load: nothing. Do: verify `.shrink/<path>.audit.md` exists; verify source content hash matches snapshotted hash. Don't: proceed if either check fails. Exit: missing audit → refuse "Run audit first."; hash mismatch → refuse "Source changed since audit. Re-run audit."; pass → re-extract.

**[COMPRESS — re-extract + idempotency]** Load: `references/thresholds.yaml`. Do: dispatch extractor; diff kept-claim set against prior compress run (if any); compute claim delta %. Don't: proceed to write if delta < 5% (idempotency floor). Exit: delta < 5% → no-op with explicit message; delta ≥ 5% → writer.

**[COMPRESS — writer]** Load: `references/thresholds.yaml`, `references/claim-schema.md`. Do: dispatch `docs-claim-doc-writer` with `{ kept_claims, original_doc, voice_anchors }` (voice_anchors = 3-5 sentences sampled from source only when sub_type = style). Don't: pass `structure_preservation` as an opt-out flag — it is a hard contract. Exit: always → judge phase.

**[COMPRESS — judge]** Load: `references/thresholds.yaml`, `references/judge-schema.md`. Do: dispatch `docs-claim-claim-judge` once per kept claim; collect verdicts; count failures (verdict = dropped). Don't: write source until all verdicts are collected. Exit: failures > 20% of kept claims → abort, write coverage report, refuse write; failures ≤ 20% → atomic write.

**[COMPRESS — atomic write]** Load: nothing. Do: write output to `<path>.tmp`; rename to `<path>`. Emit coverage report to stdout and `.shrink/<path>.coverage.md`. Don't: leave `.tmp` behind on failure — clean up. Exit: done.

---

## Entry gates

| Transition | Gate |
|---|---|
| audit → classify pass | confidence ≥ 0.6 AND category = claim-based (or mixed + --accept-mixed) |
| classify → extract | category check passed |
| extract → write checklist | claims list non-empty |
| compress start → re-extract | audit file exists AND source hash matches |
| re-extract → writer | claim delta ≥ 5% |
| writer → judge | writer returned rewritten_doc |
| judge → atomic write | failures ≤ coverage_abort_pct (20%) of kept claims |

---

## Naming conventions

Pattern: `{domain}-{subdomain}-{scope}-{role}`

| Segment | Value | Meaning |
|---|---|---|
| domain | `docs` | User-facing documentation skills |
| subdomain | `claim` | Claim-based docs (identity, style, principle, decision) |
| scope | `doc` | Operates on a single markdown doc |
| role | `shrinker` | Lossless density increase against a kept-claim set |

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| Doc classified as non-claim-based (narrative, reference, tutorial, template) | Hard refuse with category name and redirect in message |
| Doc classified as mixed (≥30% non-claim regions) | Warn; require `--accept-mixed` flag; no auto-proceed |
| Classifier confidence < 0.6 | Hard refuse: low-confidence classification surfaced |
| Doc has no extractable claims (<5 non-blank lines or empty claim list) | Refuse "doc has no extractable claims" |
| Source file changed between audit and compress | Hash mismatch → refuse, prompt re-audit; no silent recovery |
| Claim delta < 5% between compress runs | No-op with explicit message; no silent overwrite |
| Coverage failures > 20% of kept claims | Abort write; emit coverage report; retain `.coverage.md` |
| style sub-type doc | Writer receives 3-5 voice-anchor sentences from source for cadence/diction preservation |
| Headless mode (no user interaction) | Default keep-all near-no-op compress; emit warning that checklist was not audited by user |
| Output < 30% of input length | Warn before emitting (likely over-compressed); writer aborts and reports |
| Source write failure mid-way | Atomic tmp→rename; `.tmp` cleaned on failure; source never partially overwritten |
| SOUL.md (test case) — SKILL.md detected | Classifier must distinguish `style` sub-type from SKILL.md format; wrong-tool block covers this |
| Extractor receives very large doc (> token budget) | Chunk by heading, merge claim lists, deterministic ordering |
| Claim heading renamed in source between runs | Claim IDs invalidate; audit goes stale; matches stale-source policy (refuse + re-audit) |

---

## Companion files anticipated

**Always loaded at audit start:**
- `references/thresholds.yaml` — threshold constants (classifier confidence floor, coverage abort %, idempotency delta floor, judge confidence floor, writer length sanity, voice anchor count)

**Always loaded at compress start:**
- `references/thresholds.yaml`

**Loaded at node:**
- `references/claim-schema.md` — loaded at extractor dispatch and writer dispatch
- `references/classifier-schema.md` — loaded at classifier dispatch
- `references/judge-schema.md` — loaded at judge dispatch
- `references/audit-checklist-template.md` — loaded when writing checklist

**Reference (not injected — creator reads):**
- `references/wrong-tool-redirect.md` — source of Wrong-Tool Detection block in SKILL.md

---

## SKILL.md frontmatter

<!-- VERBATIM -->
```yaml
---
name: docs-claim-doc-shrinker
description: Audit and compress claim-based markdown (identity, style, principle, decision docs). Run `audit` to produce a per-claim keep/cut/merge checklist; edit it; run `compress` to rewrite the doc preserving every kept claim. Triggers: "shrink this doc", "densify", "tighten this", "compress markdown".
domain: docs
subdomain: claim
scope: doc
role: shrinker
---
```

---

## Wrong-Tool Detection block

<!-- VERBATIM -->
```markdown
## Wrong-Tool Detection
- Target is a **SKILL.md** → use `synapse-skill-skill-improver`
- Target is **narrative prose** (essays, blog posts, articles) → manual rewrite; claim-coverage destroys voice
- Target is **reference doc** (API, glossary) → completeness is the goal, not density
- Target is a **template** → already structural
- User wants **lossy summary / TL;DR** → general LLM rewrite; this skill is lossless on kept claims only
```

---

## Refusal messages (verbatim user-facing)

<!-- VERBATIM -->
```
"Doc classified as {category} (confidence {c}). This skill handles claim-based docs only. {redirect}"
"No audit found at .shrink/{path}.audit.md. Run audit first."
"Source changed since audit (hash mismatch). Re-run audit before compress."
"Mixed doc ({n}% claim, {m}% narrative). Pass --accept-mixed to proceed."
"Coverage check failed: {failed}/{total} keep-claims dropped. No write performed. See .shrink/{path}.coverage.md."
```

---

## Directory layout

<!-- VERBATIM -->
```
src/skills/docs/docs-claim-doc-shrinker/
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

---

## Schemas (Cross-cutting)

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

---

## Audit checklist file shape

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

## Threshold defaults

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

---

## Vocab additions (Cross-cutting)

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

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `docs-claim-doc-classifier` | consumes | Returns `{ category, sub_type, confidence, schema_version }`; skill gates on category + confidence |
| `docs-claim-doc-extractor` | consumes | Returns `{ claims: [Claim], contradictions, redundancies }`; skill gates on non-empty claims; claim IDs must be deterministic across runs |
| `docs-claim-doc-writer` | consumes | Accepts `{ kept_claims, original_doc, voice_anchors }`; structure_preservation is a hard contract not a flag; returns `{ rewritten_doc }` |
| `docs-claim-claim-judge` | consumes | Accepts `{ claim: Claim, rewritten_doc }`; returns `{ verdict, evidence_span, confidence }`; called once per kept claim; verdicts cached by (claim_text_hash, doc_hash) |
| `registry/SKILL_REGISTRY.md` | produces for | New row: `docs-claim-doc-shrinker` |
| `registry/AGENTS_REGISTRY.md` | produces for | 4 new rows for the agent quartet |
| `registry/SKILL_VOCABULARY.md` | produces for | 4 new vocabulary rows (same PR) |
| `registry/AGENT_VOCABULARY.md` | produces for | 4 new vocabulary rows (same PR) |

---

## Resolved (not fleshed)

- File layout: `src/skills/docs/docs-claim-doc-shrinker/SKILL.md` + `references/` + `templates/`
- Triggers + Wrong-Tool block written in SKILL.md

---

## Skill description (trigger-condition phrased)

"Audit + compress claim-based markdown preserving every kept claim. Triggers: 'shrink this doc', 'densify', 'tighten this'."

Do NOT include in SKILL.md: markdown syntax tutorial, atomic claim theory explanation, "what is entailment" — agents already know; inject only edge cases and operational thresholds. No options lists — wrong-tool block names siblings concretely; default behaviors stated as decisions not menus.

---

## Maintenance checkpoints

- Schema versioning: `schema_version` field on classifier output; agents reject unknown versions loudly; category enum extensible (unknown logged, not crashed)
- Writer 3-month review checkpoint: if no second consumer of `docs-claim-doc-writer` emerges, demote to inline prompt in shrinker
- Judge reuse posture: slug locks `docs-claim` subdomain; if general-purpose judge needed, propose alias or move to `meta-eval-claim-judge` at promotion time
- Re-verify juansync-synapse is in sync with `ai-synapse/develop` before branching

---

## Open questions

None. All open items resolved during lens rotation (Done Signal verified).

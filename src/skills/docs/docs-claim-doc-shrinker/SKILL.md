---
name: docs-claim-doc-shrinker
description: Audit and compress claim-based markdown (identity, style, principle, decision docs). Run `audit` to produce a per-claim keep/cut/merge checklist; edit it; run `compress` to rewrite the doc preserving every kept claim. Triggers: "shrink this doc", "densify", "tighten this", "compress markdown".
domain: docs
subdomain: claim
scope: doc
role: shrinker
tags: [orchestrator, audit-compress, claim-based-doc, hitl, entailment-verified, schema-versioned]
user-invocable: true
argument-hint: "audit|compress <path> [--accept-mixed]"
---

Two-phase orchestrator for claim-based markdown. The mental model: `audit` decides *what to keep*; `compress` rewrites *only against what was kept*. A classifier blocks every non-claim-based input at the door — there is no override for narrative, reference, tutorial, or template docs. A human edits a per-claim checklist between the two phases; the skill refuses to compress without one. After the writer produces a rewrite, every kept claim is independently judged for entailment, and the source file is never modified before the coverage report passes. Numeric gates load from `references/thresholds.yaml` — tuning is a config edit, never a prompt edit.

The four sibling agents are bounded by single responsibilities: the classifier categorises and never extracts; the extractor lists and never decides; the judge verifies and never rewrites; the writer compresses and never self-verifies. The orchestrator owns every gate between them.

## MUST (every turn)
- Load `references/thresholds.yaml` at the start of both `audit` and `compress`. Every numeric branch decision below references a key from that file by name.
- Record position: `Position: [node-id] — <context>`
- Refuse with the verbatim message from the Refusal Messages section — no paraphrase, no synonym substitution, no placeholder reordering.

## MUST NOT (global)
- Default-keep-all in interactive mode without emitting a warning.
- Write the source file before the coverage check passes.
- Proceed past a hash mismatch or a missing audit checklist.
- Hardcode any numeric threshold in this skill's prose — every gate reads a key from `thresholds.yaml`.
- Dispatch the writer or judge in the `audit` phase. Dispatch the writer when the kept-claim delta is below `idempotency_delta_floor_pct`.
- Modify or delete `.shrink/<path>.audit.md` during `compress` — it is the user's edit surface.

## Wrong-Tool Detection
- Target is a **SKILL.md** → use `synapse-skill-skill-improver`
- Target is **narrative prose** (essays, blog posts, articles) → manual rewrite; claim-coverage destroys voice
- Target is **reference doc** (API, glossary) → completeness is the goal, not density
- Target is a **template** → already structural
- User wants **lossy summary / TL;DR** → general LLM rewrite; this skill is lossless on kept claims only

## Progress Tracking

At the start of a `compress` invocation, create a task list:

```
TaskCreate: "Compress[P]: hash + audit-existence gate"
TaskCreate: "Compress[R]: re-extract + idempotency delta check"
TaskCreate: "Compress[W]: writer dispatch + heading-preservation check"
TaskCreate: "Compress[J]: judge batch (one call per kept claim)"
TaskCreate: "Compress[C]: coverage check + atomic write or abort"
```

For `audit`, two tasks suffice:

```
TaskCreate: "Audit[C]: classifier gate"
TaskCreate: "Audit[E]: extractor + checklist write"
```

Mark each `in_progress` when starting, `completed` when done, or `cancelled` on refusal.

## Agent Dispatch Contracts

Every cross-agent call uses these contracts. The orchestrator owns gating; the agents themselves never refuse on threshold values.

| Agent | Phase | Input | Output | Schema reference |
|---|---|---|---|---|
| `docs-claim-doc-classifier` | audit, compress | `{ file_content: string, file_path: string }` | `classifier_output { schema_version, category, sub_type, confidence }` | `references/classifier-schema.md` |
| `docs-claim-doc-extractor` | audit, compress (re-extract) | `{ file_content: string, file_path: string }` | `{ claims: [Claim], contradictions: [...], redundancies: [...] }` | `references/claim-schema.md` |
| `docs-claim-doc-writer` | compress | `{ kept_claims: [Claim], original_doc: string, voice_anchors: [string] }` (voice_anchors only when `sub_type == style`) | `{ rewritten_doc: string }` | `references/claim-schema.md` |
| `docs-claim-claim-judge` | compress (batch — one call per kept claim) | `{ claim: Claim, rewritten_doc: string }` | `judge_verdict { claim_id, verdict, evidence_span, confidence }` | `references/judge-schema.md` |

## Entry Gates

| Transition | Gate conditions |
|---|---|
| audit → extractor | Classifier returned `category = claim-based` AND `confidence ≥ classifier_confidence_floor` |
| audit → checklist write | Extractor returned non-empty claim list |
| compress → re-extract | `.shrink/<path>.audit.md` exists AND `sha256(source)` matches `source_hash` in frontmatter |
| re-extract → writer dispatch | Δ kept-claim set ≥ `idempotency_delta_floor_pct` from prior compress |
| writer output → judge dispatch | All source headings present in writer output |
| judge results → atomic write | Coverage failures ≤ `coverage_abort_pct` of kept-claim count |
| mixed doc → compress | `--accept-mixed` flag explicitly passed |

## Refusal Messages

All five refusals are VERBATIM. Do not rephrase, reorder placeholders, or substitute synonyms. Each one names the corrective action.

```
"Doc classified as {category} (confidence {c}). This skill handles claim-based docs only. {redirect}"
"No audit found at .shrink/{path}.audit.md. Run audit first."
"Source changed since audit (hash mismatch). Re-run audit before compress."
"Mixed doc ({n}% claim, {m}% narrative). Pass --accept-mixed to proceed."
"Coverage check failed: {failed}/{total} keep-claims dropped. No write performed. See .shrink/{path}.coverage.md."
```

`{redirect}` is selected from `references/wrong-tool-redirect.md` based on the category returned by the classifier.

## Entry

### [NEW] Fresh session
Do:
  1. Parse subcommand (`audit` | `compress`), `<path>` argument, optional `--accept-mixed`.
  2. Load `references/thresholds.yaml`.
  3. Create tasks per Progress Tracking section.
Don't: Proceed without a recognised subcommand. Treat any other token as a usage error.
Exit:
  → [AUDIT.C] : subcommand == audit
  → [COMP.P]  : subcommand == compress
  → FAIL      : unknown subcommand → emit usage

---

## Audit Flow

### [AUDIT.C] Classifier Gate
Load: `references/classifier-schema.md`, `references/wrong-tool-redirect.md`
Do:
  1. Dispatch `docs-claim-doc-classifier` with `{ file_content, file_path }`.
  2. If `schema_version != "1"` → FAIL LOUDLY (do not guess across versions).
  3. Apply gates:
     - `category` ∉ {`claim-based`, `mixed`} → REFUSE with the category refusal message (interpolate `{category}`, `{c}`, `{redirect}` from `references/wrong-tool-redirect.md`).
     - `confidence < classifier_confidence_floor` → REFUSE with the same template (low-confidence variant; `{redirect}` is empty or "Increase doc claim density before retry").
     - `category == mixed` AND `--accept-mixed` not passed → REFUSE with the mixed-doc message.
Don't: Override the classifier verdict. Proceed to extractor on `narrative`, `reference`, `tutorial`, or `template`.
Exit:
  → [AUDIT.E] : gate passed
  → REFUSE    : any gate failed

### [AUDIT.E] Extractor + Checklist Write
Load: `references/claim-schema.md`, `references/audit-checklist-template.md`
Do:
  1. Dispatch `docs-claim-doc-extractor` with `{ file_content, file_path }`.
  2. If `claims == []` → REFUSE: "doc has no extractable claims".
  3. Compute `source_hash = sha256(file_content)`.
  4. Render `.shrink/<path>.audit.md` from `references/audit-checklist-template.md`:
     - Frontmatter: `source_path`, `source_hash`, `audit_timestamp` (ISO 8601 UTC), `classifier.{category,sub_type}`, `schema_version: "1"`.
     - Body: claims grouped by `heading_anchor`, each defaulted to `- [x] keep: <id> — <text>`.
     - Append `## Contradictions` and `## Redundancies` sections from extractor output (omit if empty).
  5. If `.shrink/<path>.audit.md` already exists with a newer mtime than the last audit run → warn before overwriting.
  6. Atomic write: write to `.shrink/<path>.audit.md.tmp`, then rename to `.shrink/<path>.audit.md`.
Don't: Overwrite a user-edited checklist silently. Make keep/cut decisions on behalf of the user.
Exit:
  → DONE : emit checklist path to stdout

---

## Compress Flow

### [COMP.P] Precondition Gate
Load: nothing
Do:
  1. Verify `.shrink/<path>.audit.md` exists. If absent → REFUSE: `"No audit found at .shrink/{path}.audit.md. Run audit first."`
  2. Read audit frontmatter `source_hash`. Compute `sha256(current source)`. On mismatch → REFUSE: `"Source changed since audit (hash mismatch). Re-run audit before compress."`
  3. If audit frontmatter `classifier.category == mixed` AND `--accept-mixed` not passed → REFUSE with the mixed-doc message.
Don't: Auto-re-audit on hash mismatch. Silently proceed past a missing checklist.
Exit:
  → [COMP.R] : both gates pass
  → REFUSE   : either gate failed

### [COMP.R] Re-extract + Idempotency Check
Load: `references/thresholds.yaml`, `references/claim-schema.md`
Do:
  1. Dispatch `docs-claim-doc-extractor` against the (unchanged) source.
  2. Parse `kept` rows from the audit checklist (`- [x] keep:` and `- [m] merge-with`).
  3. If a prior compress's kept-claim set is recorded (e.g. previous `.coverage.md`), compute the symmetric difference; let `delta_pct = |Δ| / max(|prev|, |curr|)`.
  4. If `delta_pct < idempotency_delta_floor_pct` → emit explicit no-op message naming `idempotency_delta_floor_pct` and exit 0 without dispatching the writer.
Don't: Proceed to writer below the delta floor. Silently overwrite a near-identical file.
Exit:
  → [COMP.W] : delta ≥ floor (or no prior compress on record)
  → DONE     : delta < floor → no-op

### [COMP.W] Writer Dispatch
Load: `references/thresholds.yaml`, `references/claim-schema.md`
Do:
  1. Build `voice_anchors` only when `classifier.sub_type == style`: sample between `voice_anchor_count_min` and `voice_anchor_count_max` representative sentences from the source.
  2. Dispatch `docs-claim-doc-writer` with `{ kept_claims, original_doc, voice_anchors }`.
  3. Check every source heading appears in the writer output. If any is missing → FAIL before judge dispatch.
  4. Check output length: if `len(output) / len(input) < writer_length_sanity_pct` → WARN (writer should have aborted; treat as failed run if it did not).
Don't: Pass `structure_preservation` as a flag — it is a hard contract enforced by step 3. Mutate `kept_claims` to make the writer's job easier.
Exit:
  → [COMP.J] : writer output passed heading + length checks
  → REFUSE   : heading missing or writer reported length-floor abort

### [COMP.J] Judge Batch
Load: `references/thresholds.yaml`, `references/judge-schema.md`
Do:
  1. For each claim in `kept_claims`: dispatch `docs-claim-claim-judge` with `{ claim, rewritten_doc }`. Collect verdicts.
  2. For any verdict where `confidence < judge_confidence_floor`: escalate the verdict to `partial`.
  3. Tally: `failed = count(verdict == dropped)`; `total = len(kept_claims)`.
Don't: Pre-filter claims. Skip a judge call to "save time" — every kept claim must be verified.
Exit:
  → [COMP.C] : all verdicts collected

### [COMP.C] Coverage Check + Atomic Write
Load: nothing
Do:
  1. If `failed / total > coverage_abort_pct` → ABORT: write `.shrink/<path>.coverage.md` and emit the coverage report to stdout, then REFUSE: `"Coverage check failed: {failed}/{total} keep-claims dropped. No write performed. See .shrink/{path}.coverage.md."` Remove any `<path>.tmp` left behind. Source file is NOT modified.
  2. Otherwise: atomic write — write `rewritten_doc` to `<path>.tmp`, then rename to `<path>`. On any error during write, remove `<path>.tmp` and FAIL LOUDLY; the source is untouched.
  3. Emit coverage report (per-claim verdict table) to stdout AND `.shrink/<path>.coverage.md`.
  4. If the checklist had every row still `- [x] keep` (no human edits), emit an explicit warning that the checklist was not human-audited.
Don't: Rename `<path>.tmp` to `<path>` before the coverage check passes. Leave `<path>.tmp` behind on failure.
Exit:
  → DONE : compress complete

---

## Side Outputs

| Path | Phase | Mutable? | Purpose |
|---|---|---|---|
| `.shrink/<path>.audit.md` | audit | user edits | Per-claim keep/cut/merge checklist |
| `<path>` | compress | atomic overwrite | Rewritten source, all kept claims preserved |
| `.shrink/<path>.coverage.md` | compress | regenerated each run | Per-claim entailment verdict table |
| stdout coverage report | compress | n/a | Immediate terminal feedback before commit |

`.shrink/` should be in the repo's `.gitignore` by default.

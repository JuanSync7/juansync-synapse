---
name: docs-claim-doc-shrinker
description: "Use when a claim-based markdown doc (identity, style, principle, decision) needs lossless compression against a human-edited kept-claim set. Triggered by 'shrink this doc', 'densify', 'tighten this', 'compress markdown', 'audit claims in <path>'. Two-phase: `audit` then `compress`."
domain: docs
subdomain: claim
scope: doc
role: shrinker
status: draft
tags: [docs, claim, compression, audit, entailment, hitl]
user-invocable: true
argument-hint: "audit <path> | compress <path> [--accept-mixed]"
---

# docs-claim-doc-shrinker

Lossless density increase against a human-edited kept-claim set. Claim-based docs (identity files, style guides, principle manifests, decision logs) accumulate redundant phrasing over time. Generic LLM rewrites are unsafe here because they silently summarize — assertions disappear with no audit trail. This skill enforces a two-phase contract: `audit` extracts atomic claims into a human-editable checklist; `compress` rewrites the doc, then independently judges every kept claim for entailment against the rewrite, then writes only if coverage holds. Every numeric gate (entailment failure ratio, idempotency floor, judge confidence, length sanity, classifier confidence, voice-anchor count) loads from `references/thresholds.yaml` — no decimals in prose, so tuning never requires a prompt edit.

## MUST (every turn)
- Load `references/thresholds.yaml` at `[START]` — every numeric branch reads its key by name from this file.
- Record position: `Position: [node-id] — <context>`.
- Set `model:` explicitly on every agent dispatch — see the Agent Dispatch Contracts table for the assigned model per agent.
- Run the classifier as the unconditional entry gate for both subcommands — without this, claim-preserving logic is applied to docs where it is meaningless (P1).
- Refuse with the exact verbatim message from the Refusal Catalog when any entry gate fails — paraphrase loses the corrective action (P7).
- For `compress`: write to `<path>.tmp` and rename to `<path>` after all gates pass — non-atomic write corrupts source on mid-write failure (P3).

## MUST NOT (global)
- Compress without a `.shrink/<path>.audit.md` checklist on disk — silent compression without a human edit step violates HITL contract (P2).
- Proceed past a hash mismatch between live source and `source_hash` in audit frontmatter — re-using stale audit decisions silently rewrites a doc the user never reviewed (P2).
- Hardcode any numeric threshold in this file or in agent dispatch prompts — every value loads from `references/thresholds.yaml` by key (P5).
- Suggest rewrites from the judge, evaluate entailment from the writer, or make keep/cut calls from the extractor — agent responsibilities are bounded by schema, not convention (P6).
- Run any agent before the classifier has returned and its gate has passed.

## Wrong-Tool Detection
Load: `references/wrong-tool-redirect.md`

Two tiers. Intent-level cases short-circuit at `[NEW]` before classifier dispatch (the user's stated goal already disqualifies the skill). Content-type cases are detected structurally by the classifier at `[CLASSIFY]` and emit Refusal #1.

**Intent-level (handled at `[NEW]`):**
- **Target is a SKILL.md** → redirect to `/synapse-skill-skill-improver`
- **User wants lossy summary or TL;DR** → general LLM rewrite; this skill is lossless on kept claims only
- **User asks to bypass the coverage gate or add an override flag** → refuse and point to the design contract: entailment is verified, not assumed. There is no override path; if coverage fails, edit the audit checklist and re-run.

**Content-type (handled at `[CLASSIFY]` via classifier output):**
- Narrative prose (essays, blog posts, articles) → classifier returns `narrative`; Refusal #1 with manual-rewrite redirect.
- Reference doc (API, glossary) → classifier returns `reference`; Refusal #1 with completeness-over-density redirect.
- Template → classifier returns `template`; Refusal #1.

Do **not** intent-match narrative/reference/template at `[NEW]` from filename or keyword cues — the classifier is the source of truth for content-type and produces the populated Refusal #1.

## Agent Dispatch Contracts

The skill is an orchestrator. Four sibling agents under `src/agents/docs/` carry the bounded responsibilities. Schema files for each contract live in `references/`. Every dispatch sets `model:` explicitly (per MUST clause).

| Agent | Input | Output | Schema | Model |
|---|---|---|---|---|
| `docs-claim-doc-classifier` | `{ file_content, file_path }` | `classifier_output` | `references/classifier-schema.md` | `sonnet` |
| `docs-claim-doc-extractor` | `{ file_content, file_path }` | `{ claims: [Claim], contradictions, redundancies }` | `references/claim-schema.md` | `sonnet` |
| `docs-claim-doc-writer` | `{ kept_claims, original_doc, voice_anchors? }` | `{ rewritten_doc }` | `references/claim-schema.md` | `opus` |
| `docs-claim-claim-judge` | `{ claim, rewritten_doc }` | `judge_verdict` (one per kept claim) | `references/judge-schema.md` | `sonnet` |

Dispatch is by exact agent name. The judge is dispatched in a parallel batch — one call per kept claim — never sequentially. Model assignments: `sonnet` for bounded read-only or schema-validation work (classifier, extractor, judge); `opus` for the recompose step that must respect kept-claim coverage without leakage (writer).

## Entry Gates

Verbatim from design doc §3.3. Every transition listed here is enforced; failure routes to a Refusal Catalog message.

| Transition | Gate conditions |
|---|---|
| audit → extractor | Classifier returned `category = claim-based` AND `confidence >= classifier_confidence_floor` |
| audit → checklist write | Extractor returned non-empty claim list |
| compress → re-extract | `.shrink/<path>.audit.md` exists AND `sha256(source)` matches `source_hash` in frontmatter |
| re-extract → writer dispatch | Δ kept-claim set >= `idempotency_delta_floor_pct` from prior compress |
| writer output → judge dispatch | All source headings present in writer output |
| judge results → atomic write | Coverage failures <= `coverage_abort_pct` of kept-claim count |
| mixed doc → compress | `--accept-mixed` flag explicitly passed |

## Refusal Catalog

Verbatim from design doc §9. Emit as-written. Each names the corrective action — bare refusals are not acceptable (P7).

1. `"Doc classified as {category} (confidence {c}). This skill handles claim-based docs only. {redirect}"`
2. `"No audit found at .shrink/{path}.audit.md. Run audit first."`
3. `"Source changed since audit (hash mismatch). Re-run audit before compress."`
4. `"Mixed doc ({n}% claim, {m}% narrative). Pass --accept-mixed to proceed."`
5. `"Coverage check failed: {failed}/{total} keep-claims dropped. No write performed. See .shrink/{path}.coverage.md."`

## Progress Tracking

The flow has 3+ phases per subcommand. At session start:

```
TaskCreate: "[START] Parse subcommand and load thresholds"
TaskCreate: "[CLASSIFY] Classifier gate"
TaskCreate: "[EXTRACT] Extract claims (audit) OR [VERIFY-AUDIT] (compress)"
TaskCreate: "[CHECKLIST] Write audit file (audit-only)"
TaskCreate: "[IDEMPOTENCY] Delta check (compress-only)"
TaskCreate: "[WRITE] Writer dispatch (compress-only)"
TaskCreate: "[JUDGE] Per-claim entailment (compress-only)"
TaskCreate: "[COVERAGE] Aggregate verdicts and decide write (compress-only)"
TaskCreate: "[ATOMIC-WRITE] tmp+rename (compress-only)"
```

Mark each `in_progress` on entry, `completed` on exit. Refusals close the active task as completed (the refusal IS the deliverable).

## Entry

### [NEW] Fresh session
Load: `references/wrong-tool-redirect.md`
Do:
  1. Intent-level wrong-tool check — match only the 3 intent-level cases above (SKILL.md target, TL;DR/lossy-summary request, override-gate request). If any matches, surface the redirect or contract explanation and stop. Content-type (narrative/reference/template) is the classifier's job — do not intent-match it here.
  2. Parse the subcommand: `audit <path>` or `compress <path> [--accept-mixed]`. Reject any other shape with a usage hint that names both subcommands explicitly.
Don't:
  - Skip intent-level wrong-tool check.
  - Intent-match narrative/reference/template from filename or keyword cues — defer to the classifier at `[CLASSIFY]`.
  - Auto-infer subcommand from natural-language intent (e.g., "shrink", "densify", "tighten") — require explicit `audit` or `compress`.
Exit:
  → `[END]` : wrong-tool match (redirect surfaced)
  → `[START]` : subcommand and path confirmed

## Flow

### [START] Pre-flight
Load: `references/thresholds.yaml`
Brief: Load every numeric gate into memory by key. After this node, no decimal literal is referenced anywhere in the flow.
Do:
  1. Read `references/thresholds.yaml` and bind all 7 keys (`coverage_abort_pct`, `idempotency_delta_floor_pct`, `judge_confidence_floor`, `writer_length_sanity_pct`, `classifier_confidence_floor`, `voice_anchor_count_min`, `voice_anchor_count_max`).
  2. Verify the target path exists and is a regular file. Reject directories with a usage hint.
  3. Read the source file content; compute `sha256(source)` for later use.
Don't:
  - Substitute a hardcoded default if `thresholds.yaml` is missing — fail loudly.
Exit:
  → `[CLASSIFY]`

### [CLASSIFY] Classifier gate
Load: `references/classifier-schema.md`
Brief: Unconditional entry gate (P1). Both `audit` and `compress` pass through here.
Do:
  1. Dispatch `docs-claim-doc-classifier` (model: sonnet) with `{ file_content, file_path }`.
  2. If `confidence < classifier_confidence_floor` → refuse with the low-confidence variant of Refusal #1.
  3. If `category` is `narrative` | `reference` | `tutorial` | `template` → refuse with Refusal #1 verbatim, substituting `{category}`, `{c}`, and the matching `{redirect}` from `wrong-tool-redirect.md`.
  4. If `category == mixed`:
     - For `compress` without `--accept-mixed` → refuse with Refusal #4.
     - For `audit`, or `compress` with `--accept-mixed` → emit a one-line warning and proceed.
  5. If `category == claim-based`, capture `sub_type` for downstream voice-anchor logic. For `audit`, surface a one-line note to the user naming the detected `sub_type` (e.g., "Detected sub_type=style; voice anchors will be sampled at compress time, count in `[voice_anchor_count_min, voice_anchor_count_max]` from `thresholds.yaml`."). This sets compress-time expectations without leaking the threshold values.
Don't:
  - Bypass the gate even if the user "knows the doc is claim-based".
  - Paraphrase the refusal — the corrective action is load-bearing.
Exit:
  → `[END]` : refusal emitted
  → `[EXTRACT]` : subcommand=audit, gate passed
  → `[VERIFY-AUDIT]` : subcommand=compress, gate passed

### [EXTRACT] Extract claims (audit subcommand)
Load: `references/claim-schema.md`
Brief: Read-only structured extraction. Produces the claim list that becomes the audit checklist.
Do:
  1. Dispatch `docs-claim-doc-extractor` (model: sonnet) with `{ file_content, file_path }`.
  2. If `claims == []` → refuse with: `"doc has no extractable claims"` (extractor-empty case noted in §3.1).
  3. Capture `contradictions` and `redundancies` arrays for the checklist file.
Don't:
  - Make keep/cut decisions here — the extractor lists; the human decides.
Exit:
  → `[CHECKLIST]`

### [CHECKLIST] Write audit file (audit subcommand)
Load: `references/audit-checklist-template.md`
Brief: Persist the per-claim checklist with deterministic claim IDs and a source-content hash.
Do:
  1. Build the audit file at `.shrink/<path>.audit.md` using the verbatim template shape.
  2. Frontmatter: `source_path`, `source_hash` (the sha256 computed at `[START]`), `audit_timestamp` (iso8601), `classifier.category`, `classifier.sub_type`, `schema_version: "1"`.
  3. Group claims by heading anchor; default every claim to `[x] keep`.
  4. Append `## Contradictions` and `## Redundancies` sections with the extractor's findings.
  5. Atomic write: `.shrink/<path>.audit.md.tmp` then rename to `.shrink/<path>.audit.md`.
  6. In headless mode (no human edit step possible), emit a one-line warning: the default-keep-all checklist will produce a near-no-op compress (P2).
Don't:
  - Mutate the source file at this node — audit is read-only on the source.
Exit:
  → `[END]` : audit subcommand complete

### [VERIFY-AUDIT] Compress entry checks (compress subcommand)
Load: `references/audit-checklist-template.md`
Brief: Both HITL preconditions enforced here before any agent is dispatched.
Do:
  1. If `.shrink/<path>.audit.md` does not exist → refuse with Refusal #2.
  2. Read audit frontmatter; if `source_hash != sha256(source)` from `[START]` → refuse with Refusal #3.
  3. Parse the checklist into `kept_claims` (markers `[x]` and `[m]`) and `cut_claims` (marker `[ ]`).
Don't:
  - "Best-effort" past a hash mismatch.
Exit:
  → `[END]` : refusal emitted
  → `[IDEMPOTENCY]` : both checks pass

### [IDEMPOTENCY] Delta check (compress subcommand)
Load: `references/claim-schema.md`
Brief: P5 enforcement — skip writes that would change nearly nothing.
Do:
  1. Dispatch `docs-claim-doc-extractor` (model: sonnet) against the live source; capture the fresh claim list.
  2. Compare the fresh kept-claim set to the prior compress run's kept-claim set (recover from prior `.shrink/<path>.coverage.md` if present, else treat as 100% delta on first compress).
  3. If `delta < idempotency_delta_floor_pct` → emit a no-op message and exit without dispatching writer.
Don't:
  - Use cached claims — re-extraction is mandatory per design §3.1.
Exit:
  → `[END]` : no-op
  → `[WRITE]` : delta above floor

### [WRITE] Writer dispatch (compress subcommand)
Load: `references/claim-schema.md`
Brief: Produce the rewritten doc body. Writer self-aborts on length-sanity or missing-heading.
Do:
  1. If classifier `sub_type == style`, sample voice anchors from source — count in `[voice_anchor_count_min, voice_anchor_count_max]`.
  2. Dispatch `docs-claim-doc-writer` (model: opus) with `{ kept_claims, original_doc, voice_anchors? }`.
  3. Check the structural invariant: every source heading must be present in the writer output. If any missing → fail before judge stage (design §3.1).
  4. Check length sanity: if `len(output) < writer_length_sanity_pct * len(input)` → emit a WARN (do not abort; the warning is the deliverable per design).
Don't:
  - Pass `voice_anchors` for non-style sub-types.
  - Allow the writer to introduce claims outside `kept_claims` (enforced by writer prompt; spot-checked here by the judge in `[JUDGE]`).
Exit:
  → `[END]` : structural failure (heading missing)
  → `[JUDGE]` : writer output passes structural check

### [JUDGE] Per-claim entailment (compress subcommand)
Load: `references/judge-schema.md`
Brief: P3 — entailment is verified, not assumed. Parallel batch dispatch.
Do:
  1. For each claim in `kept_claims`, dispatch `docs-claim-claim-judge` (model: sonnet) with `{ claim, rewritten_doc }`. All dispatches in a single parallel batch.
  2. Collect `judge_verdict` per claim. Confidence escalation (verdict → `partial` when `confidence < judge_confidence_floor`) is enforced inside the judge.
Don't:
  - Sequence the dispatches — batching is the contract.
  - Re-judge with a different threshold to "rescue" a borderline run.
Exit:
  → `[COVERAGE]`

### [COVERAGE] Aggregate and decide
Load: `references/judge-schema.md`
Brief: Single aggregation step. Both `partial` and `dropped` count as failures.
Do:
  1. Count failures: `partial + dropped`.
  2. If `failures / total > coverage_abort_pct` → ABORT: write coverage report to `.shrink/<path>.coverage.md`, emit Refusal #5 to stdout, do NOT write the source file.
  3. Otherwise → proceed.
Don't:
  - Write the source before this gate passes (P3).
  - Treat `partial` as success.
  - Accept an override flag, `--force`, `--skip-coverage`, or any user request to bypass this gate — entailment is verified, not assumed. The corrective action is always: edit the audit checklist (cut claims that don't survive recomposition) and re-run.
Exit:
  → `[END]` : coverage abort
  → `[ATOMIC-WRITE]` : coverage holds

### [ATOMIC-WRITE] Atomic source replace
Brief: Mandatory atomic-write pattern (P3). Mid-write failure must leave source untouched.
Do:
  1. Write the rewritten doc to `<path>.tmp`.
  2. Rename `<path>.tmp` to `<path>` (single filesystem operation).
  3. Write coverage report to `.shrink/<path>.coverage.md`.
  4. Emit a one-screen coverage summary to stdout (claim count, entailed/partial/dropped breakdown, output length delta).
Don't:
  - Write directly to `<path>` and roll back on failure — the rename is the commit point.
  - Skip the coverage report file — it is the post-hoc audit trail.
Exit:
  → `[END]` : compress complete

### [END]
Do:
  1. For `audit`: print the path to `.shrink/<path>.audit.md` and instruct the user to edit `[x]`/`[ ]`/`[m]` markers before running `compress`.
  2. For `compress` success: print the coverage summary path and a one-line claim-count delta.
  3. For any refusal: the refusal text from the Refusal Catalog IS the output — do not prepend or append explanation.
Don't:
  - Auto-dispatch `compress` after `audit` completes — the human edit step on the checklist is the HITL contract (P2). Tell the user the next command to run; do not run it yourself.
  - Chain subcommands from a single user prompt (e.g., "audit then compress") — execute only the first subcommand and surface the next-step instruction.

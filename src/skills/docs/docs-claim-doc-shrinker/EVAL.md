# EVAL — docs-claim-doc-shrinker

> Generated against the design doc at `change_requests/2026-05-13-juansync7-shrink-skill-design.md` §3, §4, §5, §7, §8, §9. Regenerate with `/synapse-router-eval-writer skill src/skills/docs/docs-claim-doc-shrinker` when SKILL.md or the design doc changes.

This EVAL is the acceptance contract for the orchestrator skill. Failures here block promotion. Three layers: structural (does the skill have the right shape), output (does it dispatch and gate correctly), and blind prompts (does an unseen run produce the right behaviour).

---

## Structural Criteria

Binary checks against `SKILL.md` and the `references/` tree. Each row PASS or FAIL.

| # | Check | Pass condition |
|---|-------|----------------|
| S1 | Frontmatter present | YAML `---` block at top of `SKILL.md` |
| S2 | Frontmatter `name` | Equals `docs-claim-doc-shrinker` (verbatim from design §7) |
| S3 | Frontmatter `description` | Verbatim from design §7 (mentions audit/compress subcommands and the four claim sub-types) |
| S4 | Frontmatter `domain` | `docs` |
| S5 | Frontmatter `subdomain` | `claim` |
| S6 | Frontmatter `scope` | `doc` |
| S7 | Frontmatter `role` | `shrinker` |
| S8 | Frontmatter `tags` | Array including at least `orchestrator`, `audit-compress`, `claim-based-doc` |
| S9 | Frontmatter `user-invocable: true` | Present (the skill is dispatched directly by the user, not by a parent skill) |
| S10 | Frontmatter `argument-hint` | Contains `audit\|compress <path>` (or equivalent string the harness can surface) |
| S11 | Mental-model framing paragraph | First paragraph after frontmatter describes the two-phase audit→compress flow, classifier-as-unconditional-gate, HITL-via-checklist, post-write entailment verification |
| S12 | Subcommand dispatch | Explicit branches for `audit` and `compress`; each branch codifies the design §3.1 flow graph |
| S13 | Agent dispatch contracts | Names all four siblings by slug: `docs-claim-doc-classifier`, `docs-claim-doc-extractor`, `docs-claim-claim-judge`, `docs-claim-doc-writer`. For each, names the input contract and output contract |
| S14 | Entry gate table | Reproduces the 7 gates from design §3.3 (audit→extractor, extractor→checklist, compress→re-extract, re-extract→writer, writer→judge, judge→write, mixed→compress) |
| S15 | Refusal messages verbatim | All 5 refusal messages from design §9 appear verbatim in SKILL.md (no paraphrase, no synonym substitution, no reordering of placeholders) |
| S16 | Thresholds loaded by name | Every numeric gate in SKILL.md prose is referenced by its key in `thresholds.yaml` (`coverage_abort_pct`, `idempotency_delta_floor_pct`, `judge_confidence_floor`, `writer_length_sanity_pct`, `classifier_confidence_floor`, `voice_anchor_count_min`/`max`). No raw decimals like `0.20` appear as policy in prose. |
| S17 | `thresholds.yaml` present | File exists at `references/thresholds.yaml` with the 7 keys from design §5 |
| S18 | Companion schema files present | `references/claim-schema.md`, `references/classifier-schema.md`, `references/judge-schema.md`, `references/audit-checklist-template.md`, `references/wrong-tool-redirect.md` all exist |
| S19 | Wrong-Tool Detection block | Section present; bullets match design §8 verbatim |
| S20 | Progress Tracking section | Present (3+ phases); contains `TaskCreate` examples for the compress flow |
| S21 | Atomic-write pattern documented | SKILL.md states the write-to-`<path>.tmp`-then-rename pattern and that `.tmp` is cleaned up on failure |
| S22 | Coverage report side outputs | `.shrink/<path>.coverage.md` and stdout coverage report both named |
| S23 | Idempotency floor codified | Delta floor check appears in compress flow before writer dispatch, references `idempotency_delta_floor_pct` |
| S24 | Listed in registry | `registry/SKILL_REGISTRY.md` has a row for `docs-claim-doc-shrinker` linking SKILL.md |
| S25 | Domain README has row | `src/skills/docs/README.md` contains a row for `docs-claim-doc-shrinker` |
| S26 | Skill directory README | `src/skills/docs/docs-claim-doc-shrinker/README.md` lists every artifact in the directory |

**Verdict rule:** any FAIL in S1–S26 → REVISE. S2–S7 and S15 are non-negotiable (verbatim contracts from design §7 and §9).

---

## Output Criteria

Behavioural checks the skill's runtime output must satisfy. Evaluated by `synapse-router-artifact-gatekeeper` against the blind prompts below.

| # | Check | Pass condition |
|---|-------|----------------|
| O1 | Audit happy-path produces valid checklist | A claim-based doc with non-empty content produces `.shrink/<path>.audit.md` matching the template in `references/audit-checklist-template.md`. Frontmatter has `source_path`, `source_hash`, `audit_timestamp`, `classifier.{category,sub_type}`, `schema_version: "1"`. |
| O2 | Audit refuses non-claim doc verbatim | Narrative input produces the literal refusal `"Doc classified as {category} (confidence {c}). This skill handles claim-based docs only. {redirect}"` with the placeholders interpolated. No rewording. |
| O3 | Audit refuses low-confidence verbatim | Classifier `confidence < classifier_confidence_floor` (0.6) triggers the low-confidence refusal that uses the same template, surfacing the confidence value. |
| O4 | Audit refuses mixed without flag verbatim | A `mixed` classification without `--accept-mixed` triggers `"Mixed doc ({n}% claim, {m}% narrative). Pass --accept-mixed to proceed."` verbatim. |
| O5 | Compress refuses missing audit verbatim | Running `compress` on a path with no audit file triggers `"No audit found at .shrink/{path}.audit.md. Run audit first."` verbatim. |
| O6 | Compress refuses hash mismatch verbatim | An audit file whose `source_hash` does not match the current source content triggers `"Source changed since audit (hash mismatch). Re-run audit before compress."` verbatim. |
| O7 | Compress aborts on coverage failure verbatim | When dropped-verdict count exceeds `coverage_abort_pct` (20%) of kept claims, triggers `"Coverage check failed: {failed}/{total} keep-claims dropped. No write performed. See .shrink/{path}.coverage.md."` verbatim. `.shrink/<path>.coverage.md` is written; source file is NOT modified. |
| O8 | All 7 entry gates enforced | The 7 gates from design §3.3 each appear as an explicit branch in the runtime flow. Skipping any gate is a FAIL. |
| O9 | Atomic write pattern obeyed | Compress writes to `<path>.tmp` and renames to `<path>` only after the coverage check passes. On any failure between tmp-write and rename, `<path>.tmp` is removed and the source is untouched. |
| O10 | Idempotency delta floor | When the kept-claim set differs by `< idempotency_delta_floor_pct` (5%) from the prior compress, the skill emits a no-op message and exits 0 without dispatching the writer. |
| O11 | Threshold sourcing | Every numeric branch decision the skill makes traces back to a key in `thresholds.yaml`. Hardcoded decimals in the runtime trace are a FAIL. |
| O12 | Headless warning | When run with no human edit step (every row still `[x] keep`), the compress proceeds but emits an explicit warning that the checklist was not human-audited. |
| O13 | Style sub-type voice anchors | When `classifier.sub_type == style`, the writer is dispatched with 3–5 voice-anchor sentences sampled from the source. The count obeys `voice_anchor_count_min`/`voice_anchor_count_max`. |
| O14 | No write on writer length-floor violation | If the writer reports output < `writer_length_sanity_pct` (30%) of input, the skill aborts before judge dispatch without writing. |

---

## Blind Test Prompts

Eight prompts. Each is a fresh skill invocation with no prior context. Fixtures live under `references/examples/`.

### T1 — Audit happy-path (claim-based identity doc)
**Input:** `audit references/examples/claim-identity.md`
**Expected:**
- Classifier returns `category: claim-based`, `sub_type: identity`, `confidence ≥ 0.6`.
- Extractor returns a non-empty `claims` list.
- `.shrink/references/examples/claim-identity.md.audit.md` is written with the template shape, defaulting every row to `- [x] keep`.
- Skill exits 0 with the audit path emitted to stdout.

### T2 — Compress happy-path (audited identity doc, kept-claims edited)
**Input:** `compress references/examples/claim-identity.md` (after the corresponding edited audit fixture from `references/examples/claim-identity.audit.edited.md` has been placed at `.shrink/references/examples/claim-identity.md.audit.md`).
**Expected:**
- Hash check passes; delta vs prior compress ≥ 5%; writer dispatched.
- Every source heading present in the rewrite.
- Judge dispatched once per kept claim; coverage failures ≤ 20%.
- Atomic write `<path>.tmp` → `<path>` succeeds.
- `.shrink/references/examples/claim-identity.md.coverage.md` and stdout report both contain the per-claim verdict table.

### T3 — Classifier-gate refusal (narrative input)
**Input:** `audit references/examples/narrative-essay.md`
**Expected:** Refusal message verbatim — `"Doc classified as narrative (confidence 0.92). This skill handles claim-based docs only. Manual rewrite; claim-coverage destroys voice."` (or the narrative redirect from §8). No `.shrink/` file is written.

### T4 — No-audit-found refusal
**Input:** `compress references/examples/claim-identity.md` with no `.shrink/...audit.md` present.
**Expected:** Refusal verbatim — `"No audit found at .shrink/references/examples/claim-identity.md.audit.md. Run audit first."` Skill exits non-zero.

### T5 — Hash-mismatch refusal
**Input:** `compress references/examples/claim-identity.md` after the source has been edited since audit (so `sha256(source)` ≠ frontmatter `source_hash`).
**Expected:** Refusal verbatim — `"Source changed since audit (hash mismatch). Re-run audit before compress."` Skill exits non-zero. Source file untouched.

### T6 — Coverage-abort
**Input:** `compress references/examples/claim-identity.md` with a hostile writer that drops > 20% of kept claims (simulated by injecting a stub rewrite).
**Expected:** Refusal verbatim — `"Coverage check failed: {failed}/{total} keep-claims dropped. No write performed. See .shrink/references/examples/claim-identity.md.coverage.md."` `.coverage.md` written; source untouched; `<path>.tmp` removed.

### T7 — Idempotency no-op
**Input:** `compress references/examples/claim-identity.md` immediately after a successful T2 compress, no checklist edits in between.
**Expected:** Re-extract; kept-claim set delta < 5%; skill emits explicit no-op message naming `idempotency_delta_floor_pct`; exits 0 without writer dispatch.

### T8 — Mixed doc requires `--accept-mixed`
**Input:** `audit references/examples/mixed-claim-narrative.md`
**Expected:**
- Without `--accept-mixed`: refusal verbatim — `"Mixed doc ({n}% claim, {m}% narrative). Pass --accept-mixed to proceed."`
- With `--accept-mixed`: proceed; checklist written with `classifier.category: mixed` and a warning emitted.

---

## Verdict Rules

| Condition | Verdict |
|-----------|---------|
| All structural pass AND O1–O14 pass under blind prompts | APPROVE |
| Fixable gaps (missing registry row, paraphrased refusal, hardcoded threshold) | REVISE |
| Frontmatter wrong, refusal messages not verbatim, atomic-write missing | REJECT |

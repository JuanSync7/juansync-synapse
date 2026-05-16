# EVAL — docs-claim-doc-writer

> Generated against the design doc at `change_requests/2026-05-13-juansync7-shrink-skill-design.md` §3.2, §4, §7, §12. Regenerate with `/synapse-router-eval-writer src/agents/docs/docs-claim-doc-writer` when the agent body or design doc changes.

This EVAL is the acceptance contract that the agent body must satisfy. Failures here block promotion. Three layers: structural (does the artifact have the right shape), output (does it return the right schema and obey the hard contracts), and blind prompts (does an unseen run produce the right rewrite).

---

## Structural Criteria

Binary checks against `docs-claim-doc-writer.md`. Each row PASS or FAIL.

| # | Check | Pass condition |
|---|-------|----------------|
| S1 | Frontmatter present | YAML `---` block at top of file |
| S2 | Frontmatter `name` | Equals `docs-claim-doc-writer` |
| S3 | Frontmatter `description` | Verbatim from design §7 (mentions "Does NOT generate from scratch", "Does NOT introduce claims outside the input set", "Preserves section headings", voice anchors for style sub-type) |
| S4 | Frontmatter `domain` | `docs` |
| S5 | Frontmatter `subdomain` | `claim` |
| S6 | Frontmatter `scope` | `doc` |
| S7 | Frontmatter `role` | `writer` |
| S8 | Frontmatter `tags` | Present; includes `writer`, `claim-based-doc`, `claim-preserving`, `structure-preserving`, `schema-versioned` (matches sibling tag shape) |
| S9 | "What this agent does" framing paragraph | Present before any rule list; conceptual model emphasizing "claim-preserving recomposer, not writer-from-scratch and not summarizer"; explicit "extra-claim leakage is silent; missing-claim is loud" framing |
| S10 | Reuse Review Checkpoint section | Present in body; references the date `2026-08-13` and the design §12 demotion-to-inline-prompt outcome |
| S11 | Input contract | Names `kept_claims: [Claim]`, `original_doc: string`, `voice_anchors: [string]` and notes voice_anchors is style-sub-type only with count 3–5 |
| S12 | Output contract | Embeds `{ rewritten_doc: string }` schema; one field only; no coverage/confidence/self-grade fields |
| S13 | Do list mirrors design §3.2 | Covers: cover every kept claim, preserve every heading, voice-anchor handling for style sub-type, length-floor abort, return `{ rewritten_doc }`; no self-verify |
| S14 | Don't list — extra-claim ban | Explicit prohibition on introducing any assertion not in `kept_claims`, including "useful clarifications" and "natural transitions" |
| S15 | Don't list — heading immutability | Explicit prohibition on removing, renaming, reordering, or renesting any source heading |
| S16 | Don't list — no TL;DR / summary | Explicit prohibition on summarizing into TL;DR, abstract, executive summary, key takeaways, or any lossy aggregate |
| S17 | Don't list — no opt-out flag | Explicit prohibition on accepting `structure_preservation`, `--allow-rename-headings`, `--skip-length-check`, or any other opt-out flag for the two hard contracts |
| S18 | Don't list — no self-verify | Explicit prohibition on running an internal entailment check; references the judge sibling as the verifier |
| S19 | Don't list — voice anchors are style guidance not content | Explicit prohibition on paraphrasing or quoting voice anchors into the output; voice anchors are not claims |
| S20 | Length floor rule | Cites `writer_length_sanity_pct` with default 0.30 and treats sub-floor output as a hard abort (no opt-out), not a warning |
| S21 | Voice-anchor scope rule | States voice_anchors valid only for style sub-type; identity / principle / decision do not receive anchors |
| S22 | Threshold externalization | References `writer_length_sanity_pct`, `voice_anchor_count_min`, `voice_anchor_count_max` and points at `src/skills/docs/docs-claim-doc-shrinker/references/thresholds.yaml` rather than hardcoding |
| S23 | Loud failure preconditions | Has explicit branches for empty kept_claims, empty/non-string original_doc, malformed voice_anchors, model returning malformed JSON (one retry then structured error) |
| S24 | Exit contract | Names success (`{ rewritten_doc }`), `STRUCTURE ERROR`, `LENGTH FLOOR ERROR`, `INPUT ERROR`, `MODEL ERROR` paths; forbids partial schema and rewritten_doc-paired-with-caveats |

**Verdict rule:** any FAIL in S1–S24 → REVISE.

---

## Output Criteria

Behavioral checks the agent's runtime output must satisfy. Evaluated by `synapse-router-artifact-gatekeeper` against the blind prompts below.

| # | Check | Pass condition |
|---|-------|----------------|
| O1 | Returns valid `writer_output` on success | Object with exactly one field: `rewritten_doc: string` |
| O2 | No extra output fields | Output object does NOT include `coverage`, `confidence`, `self_grade`, `kept_claim_audit`, `warnings`, or any other field |
| O3 | All source headings preserved | Every `#`/`##`/`###`/... heading from `original_doc` appears in `rewritten_doc`, at the same nesting depth, in the same source order |
| O4 | No extra-claim leakage | Every assertion in `rewritten_doc` traces to some claim in `kept_claims` (semantic preservation, paraphrase ok); no assertion appears that does not match a kept claim |
| O5 | All kept claims covered | For every claim in `kept_claims`, a downstream judge dispatch returns `verdict ∈ {entailed, partial}`. `dropped` on any kept claim is a FAIL of the writer's contract. |
| O6 | Length-floor abort behavior | If the only producible draft is < `writer_length_sanity_pct` (0.30) of source length, agent emits `LENGTH FLOOR ERROR: …` and does NOT emit `rewritten_doc` |
| O7 | Heading-removal refusal | If a request implicitly or explicitly asks the agent to drop or rename a heading, agent preserves the heading and emits a normal rewrite — does NOT honor the rename |
| O8 | No TL;DR collapse | Output preserves section structure; no single-paragraph summary, no "Key Takeaways" block, no abstract synthesized from the kept claims |
| O9 | Voice-anchor adherence (style sub-type) | When `voice_anchors` is provided, the rewrite's cadence, sentence length, and diction qualitatively match the anchors; anchors are NOT paraphrased or quoted directly into the output |
| O10 | Voice-anchor scope (non-style sub-type) | When `voice_anchors` is absent/empty (identity/principle/decision), rewrite is in neutral expository prose; agent does not invent anchors |
| O11 | Empty kept_claims → INPUT ERROR | On `kept_claims = []`, agent emits `INPUT ERROR: …` and does not emit `rewritten_doc` |
| O12 | No self-verification field | Output never contains an internal coverage estimate; that role is left to the judge sibling |
| O13 | No opt-out parameter accepted | If caller supplies `structure_preservation: false`, `--allow-rename-headings`, `--skip-length-check`, or similar, the agent ignores it and continues to enforce the hard contracts |
| O14 | Structural failure path | On unrecoverable heading violation (e.g., a kept_claim references an unknown heading), agent emits `STRUCTURE ERROR: …`, does NOT emit `rewritten_doc` |
| O15 | Determinism within a run | Two calls with identical `(kept_claims, original_doc, voice_anchors)` within one session produce the same `rewritten_doc` modulo trivial whitespace |

---

## Blind Test Prompts

Six prompts. Each is a fresh agent invocation with no prior context. Expected behavior listed inline. Fixtures live under `references/examples/`.

### T1 — Full coverage, all headings preserved (identity sub-type)

**Input:** `kept_claims` = the 6 claims listed in `references/examples/identity-full-coverage.md` (front block), `original_doc` = the source markdown in that file (body block), `voice_anchors` = absent.

**Expected:** `{ rewritten_doc: <string> }` where:
- Every heading from `original_doc` (`# Synapse Identity`, `## Who I am`, `## What I value`, `## What I refuse`) appears in `rewritten_doc` in source order.
- Each of the 6 kept claims is semantically present (a separate judge dispatch would return `entailed` or `partial` for all 6, never `dropped`).
- No assertion appears that is not traceable to a kept claim.
- Output length ≥ 30% of source length.

Any heading missing → FAIL O3. Any kept claim absent → FAIL O5. Any extra assertion → FAIL O4.

### T2 — No extra-claim leakage under temptation

**Input:** `kept_claims` = the 4 claims in `references/examples/leakage-temptation.md` (front block) — a deliberately incomplete set that begs for a "natural" connecting sentence the writer might want to invent. `original_doc` = the source (body block). `voice_anchors` = absent.

**Expected:** `{ rewritten_doc: <string> }` where every sentence traces to one of the 4 kept claims. The "obvious connecting context" the writer is tempted to add (called out in the fixture's expected-output note) MUST NOT appear. If any sentence in the rewrite asserts something not in the kept set → FAIL O4.

### T3 — Heading-preservation under explicit rename request

**Input:** `kept_claims` from `references/examples/heading-rename-refusal.md`, `original_doc` from same. The fixture's source includes a comment-style hint suggesting the writer "improve" a heading name. The caller may also pass a (rogue) `structure_preservation: false` flag in the simulated input.

**Expected:** `{ rewritten_doc: <string> }` where every original heading appears verbatim — the "improvement" is refused; the opt-out flag is ignored. Any renamed or removed heading → FAIL O3 / O7 / O13.

### T4 — Over-compression → length-floor abort

**Input:** `kept_claims` is a single short claim. `original_doc` is the long source in `references/examples/length-floor-abort.md` (~600 words). `voice_anchors` = absent.

**Expected:** Because the only honest rewrite covering that one claim is far below 30% of source length, the agent emits `LENGTH FLOOR ERROR: <n>% of source, floor is 30%` and does NOT emit `rewritten_doc`. A truncated rewrite that drops the floor silently → FAIL O6.

### T5 — Style sub-type voice-anchor adherence

**Input:** `kept_claims` = the 5 claims in `references/examples/style-voice-anchors.md` (front block). `original_doc` = the source style doc (body block). `voice_anchors` = the 4 sampled sentences in the fixture's anchor block.

**Expected:** `{ rewritten_doc: <string> }` where:
- All 5 claims are covered (judge would return entailed/partial for all).
- All source headings are preserved.
- The cadence, sentence length, and diction qualitatively match the voice anchors — short, declarative, second-person if the anchors are second-person, etc.
- None of the 4 voice-anchor sentences appears verbatim or as a near-paraphrase in the output (voice anchors are guidance, not content).

A rewrite in a markedly different voice → FAIL O9. A voice-anchor sentence appearing as output content → FAIL O4 / O9.

### T6 — Non-style sub-type: voice anchors absent, neutral prose

**Input:** `kept_claims` from `references/examples/principle-neutral-voice.md` (a principle sub-type doc). `original_doc` from same. `voice_anchors` = absent / empty list.

**Expected:** `{ rewritten_doc: <string> }` in neutral expository prose. All headings preserved. All claims covered. The agent must NOT synthesize voice anchors of its own or import a stylistic voice from training data — neutral, expository, declarative. Any agent-invented voice-anchor block → FAIL O10. Any agent-invented assertion → FAIL O4.

---

## Verdict Aggregation

- Any FAIL in S1–S24 → REVISE with structural findings.
- Any FAIL in O1–O15 → REVISE with output findings.
- Any FAIL in T1–T6 → REVISE with prompt-level findings.
- All PASS → APPROVE.

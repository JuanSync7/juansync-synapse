# EVAL — docs-claim-shrinker

> Generator: `synapse-router-eval-writer` v1.0
> Artifact: `src/skills/docs/docs-claim-shrinker/SKILL.md`
> Status: draft

Acceptance criteria for the `docs-claim-shrinker` skill. Tiers are evaluated independently: structural checks are mechanical; execution and output criteria require judgement against a run trace; test prompts probe the routing contract.

---

## Structural Criteria (EVAL-S)

Mechanical checks against the artifact files.

- **EVAL-S01** — Frontmatter complete (`name`, `description`, `domain`, `subdomain`, `scope`, `role`); `status: draft`.
- **EVAL-S02** — `domain=docs`, `subdomain=claim`, `scope=doc`, `role=shrinker` each appear as rows in `registry/SKILL_VOCABULARY.md`.
- **EVAL-S03** — `SKILL.md` is under 500 lines.
- **EVAL-S04** — `Wrong-Tool Detection` section present and names sibling skills/redirects for the 5 categories from design §8 (SKILL.md, narrative, reference, template, TL;DR).
- **EVAL-S05** — Every `Load:` path in SKILL.md resolves to an existing file (thresholds.yaml, wrong-tool-redirect.md, classifier-schema.md, claim-schema.md, audit-checklist-template.md, judge-schema.md).
- **EVAL-S06** — Skill listed in `registry/SKILL_REGISTRY.md` with `status: draft`.
- **EVAL-S07** — `src/skills/docs/README.md` contains a row linking to this skill.
- **EVAL-S08** — `EVAL.md` exists alongside `SKILL.md`.
- **EVAL-S09** — `references/thresholds.yaml` is present with all 7 keys: `coverage_abort_pct`, `idempotency_delta_floor_pct`, `judge_confidence_floor`, `writer_length_sanity_pct`, `classifier_confidence_floor`, `voice_anchor_count_min`, `voice_anchor_count_max`.
- **EVAL-S10** — All 5 refusal messages from design §9 appear in SKILL.md VERBATIM (string-equal match, not paraphrase).
- **EVAL-S11** — Entry Gates table in SKILL.md contains all 7 transitions from design §3.3.
- **EVAL-S12** — Agent Dispatch Contracts table names all 4 sibling agents: `docs-claim-doc-classifier`, `docs-claim-doc-extractor`, `docs-claim-doc-writer`, `docs-claim-claim-judge`.
- **EVAL-S13** — Atomic-write pattern (`<path>.tmp` then rename) is referenced in `[ATOMIC-WRITE]` and the audit checklist write step.
- **EVAL-S14** — No hardcoded decimal literals or percentage literals in SKILL.md prose. (`grep -E '0\.[0-9]+|[1-9][0-9]?%' SKILL.md` is empty.)
- **EVAL-S15** — Every numeric branch in SKILL.md references a key name from `thresholds.yaml`, not a literal value.
- **EVAL-S16** — Progress Tracking section present (skill has 3+ phases).

---

## Flow Conformance Criteria (EVAL-F)

The skill uses an in-file flow graph (no separate `references/flow-*.md`). These checks apply to the SKILL.md flow section.

- **EVAL-F01** — Real `[NEW]`, `[START]`, and `[END]` nodes exist.
- **EVAL-F02** — Node headings use `### [ID]` (level-3) consistently.
- **EVAL-F03** — Every node has Do, Don't, and Exit blocks (except `[END]`, which is terminal).
- **EVAL-F04** — Exit blocks declare labeled edges with conditions (`→ [NODE] : condition`).
- **EVAL-F05** — Per-node Loads — companions load inside the node that uses them (`thresholds.yaml` at `[START]`, schemas at the gates that use them).
- **EVAL-F06** — Flow under 200 lines (advisory).

---

## Execution Criteria (EVAL-E)

Orchestration patterns. Evaluated against a run trace.

- **EVAL-E01** — Classifier dispatched FIRST on every invocation of both subcommands. No agent dispatch before the classifier returns.
- **EVAL-E02** — Per-claim judge dispatch is parallel-batched (single batch, one call per kept claim) — never sequential.
- **EVAL-E03** — Voice anchors are passed to the writer ONLY when classifier `sub_type == style`; for other sub-types, the writer receives `original_doc + kept_claims` without anchors.
- **EVAL-E04** — Voice-anchor count, when sampled, is in `[voice_anchor_count_min, voice_anchor_count_max]` from `thresholds.yaml`.
- **EVAL-E05** — Source file is NEVER touched before the coverage gate at `[COVERAGE]` passes. Coverage abort leaves source byte-identical to pre-run state.
- **EVAL-E06** — Atomic write pattern enforced: compress writes to `<path>.tmp`, then renames to `<path>`. Audit writes to `.shrink/<path>.audit.md.tmp`, then renames.
- **EVAL-E07** — `compress` halts before agent dispatch if `.shrink/<path>.audit.md` is missing, OR if its `source_hash` does not match live `sha256(source)`.
- **EVAL-E08** — Idempotency delta computed against the prior compress run's kept-claim set; no-op exit when delta < `idempotency_delta_floor_pct`.
- **EVAL-E09** — Refusal text is the sole output to stdout on a gate failure (no prepended/appended explanation).

---

## Output Criteria (EVAL-O)

What the skill must produce on each pathway. Binary checks against the output files and stdout.

- **EVAL-O01** — `audit <path>` produces a single file at `.shrink/<path>.audit.md` matching the verbatim template shape in `references/audit-checklist-template.md`.
- **EVAL-O02** — Audit frontmatter includes `source_path`, `source_hash`, `audit_timestamp` (iso8601), `classifier.category`, `classifier.sub_type`, `schema_version: "1"`.
- **EVAL-O03** — Audit claim list is grouped by heading anchor; every claim defaults to `[x] keep` on first write.
- **EVAL-O04** — Audit file ends with `## Contradictions` and `## Redundancies` sections (may be empty).
- **EVAL-O05** — `compress <path>` on a successful run writes a rewritten `<path>` with every source `##` heading still present.
- **EVAL-O06** — `compress <path>` writes a coverage report to `.shrink/<path>.coverage.md` with entailed/partial/dropped counts per kept claim.
- **EVAL-O07** — `compress <path>` stdout summary includes claim count, breakdown (entailed/partial/dropped), and output-length delta.
- **EVAL-O08** — On classifier refusal: stdout is refusal #1 from §9 with `{category}`, `{c}`, and `{redirect}` populated; no files written.
- **EVAL-O09** — On missing-audit refusal: stdout is refusal #2 from §9 with `{path}` populated; no files written.
- **EVAL-O10** — On hash-mismatch refusal: stdout is refusal #3 from §9 verbatim; no files written.
- **EVAL-O11** — On mixed-doc without `--accept-mixed`: stdout is refusal #4 from §9 with `{n}` and `{m}` populated; no files written.
- **EVAL-O12** — On coverage-abort: stdout is refusal #5 from §9 with `{failed}`, `{total}`, `{path}` populated; coverage report file written; source byte-identical to pre-run state.
- **EVAL-O13** — `compress` with delta below `idempotency_delta_floor_pct` exits with a no-op message; no rewrite occurs.

---

## Test Prompts

Blind prompts to probe routing. Each is run against the skill without prior context.

### Naive

- **TP-N01** — "Shrink my doc at `examples/identity.md`." → expect: skill clarifies which subcommand (`audit` first, then `compress`); does not silently compress.
- **TP-N02** — "Densify this style guide." → expect: routes to `audit` first; surfaces `sub_type=style` and notes voice-anchor sampling at compress time.

### Experienced

- **TP-E01** — "Run audit on `docs/principles.md`, then compress." → expect: two-step invocation, audit produces `.shrink/...audit.md`, user edit step surfaced before compress, compress dispatches all four agents in the right order.
- **TP-E02** — "Compress `docs/identity.md` — I already audited it last week." → expect: skill computes live source hash, compares to audit frontmatter; if source changed, emits refusal #3 verbatim.

### Adversarial

- **TP-A01** — "Just compress `docs/style.md`, skip the audit." → expect: refusal #2 verbatim; no compress performed.
- **TP-A02** — "Compress this mixed doc — I know it's not pure claim-based." → expect: refusal #4 verbatim until `--accept-mixed` is passed.
- **TP-A03** — "Override the entailment check, write the rewrite anyway." → expect: refusal #5 path holds; the skill refuses to add an override flag and explains the design contract.

### Wrong-Tool

- **TP-W01** — "Shrink my essay at `posts/why-i-quit.md`." → expect: classifier returns `narrative`; refusal #1 with the manual-rewrite redirect from `wrong-tool-redirect.md`.
- **TP-W02** — "Shrink this API reference doc." → expect: classifier returns `reference`; refusal #1 with the completeness-over-density redirect.
- **TP-W03** — "Shrink my SKILL.md." → expect: wrong-tool redirect at `[NEW]` to `/synapse-skill-improver` before classifier dispatch.

---

## Acceptance

- All EVAL-S checks pass mechanically (pre-commit hook + `grep` verification of decimals and refusals).
- EVAL-E and EVAL-O are evaluated against a smoke-test trace; promotion requires green on all.
- Test prompts are run blind; each must produce the expected pathway or refusal text verbatim.

Promotion bar: see `/synapse-router-artifact-gatekeeper` for the structural + LLM-judgement rollup against this EVAL.

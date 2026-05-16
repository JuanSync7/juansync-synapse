# EVAL — docs-claim-doc-classifier

> Generated against the design doc at `change_requests/2026-05-13-juansync7-shrink-skill-design.md` §3.2, §4, §7. Regenerate with `/synapse-router-eval-writer src/agents/docs/docs-claim-doc-classifier` when the agent body or design doc changes.

This EVAL is the acceptance contract that the agent body must satisfy. Failures here block promotion. Three layers: structural (does the artifact have the right shape), output (does it return the right schema and obey the policy), and blind prompts (does an unseen run produce the right answer).

---

## Structural Criteria

Binary checks against `docs-claim-doc-classifier.md`. Each row PASS or FAIL.

| # | Check | Pass condition |
|---|-------|----------------|
| S1 | Frontmatter present | YAML `---` block at top of file |
| S2 | Frontmatter `name` | Equals `docs-claim-doc-classifier` |
| S3 | Frontmatter `description` | Verbatim from design §7 (mentions structural genre + sub-type + read-only) |
| S4 | Frontmatter `domain` | `docs` |
| S5 | Frontmatter `subdomain` | `claim` |
| S6 | Frontmatter `scope` | `doc` |
| S7 | Frontmatter `role` | `classifier` |
| S8 | "What this agent does" framing paragraph | Present before any rule list; conceptual model, not mechanics |
| S9 | Input contract | Names `file_content: string` and `file_path: string` |
| S10 | Output contract | Embeds the `classifier_output` YAML schema verbatim from design §4 (schema_version, category, sub_type, confidence) |
| S11 | Do list (Load/Do) | Mirrors design §3.2 Do steps 1–5 (classify genre, sub-type if claim-based, confidence, mixed-doc 30% rule, return schema) |
| S12 | Don't list | Includes "no contradiction detection", "no reasoning_summary field", and the < 5 non-blank line low-confidence note from design §3.2 |
| S13 | Threshold reference | Cites `classifier_confidence_floor: 0.6` AND notes it is enforced by the calling skill (loaded from `src/skills/docs/docs-claim-doc-shrinker/references/thresholds.yaml`), not hardcoded by this agent |
| S14 | Mixed-doc threshold reference | Cites the 30% non-claim region rule and points at `thresholds.yaml` rather than treating it as agent-internal magic |
| S15 | Loud failure preconditions | Has explicit branches for malformed input, empty content, LLM returning malformed JSON (one retry then structured error) |
| S16 | Schema version | Output schema includes `schema_version: "1"`; agent body documents that downstream agents reject unknown versions |
| S17 | Exit contract | Names success output (`classifier_output`) and structured-error path |

**Verdict rule:** any FAIL in S1–S17 → REVISE.

---

## Output Criteria

Behavioral checks the agent's runtime output must satisfy. These are evaluated by `synapse-router-artifact-gatekeeper` against the blind prompts below.

| # | Check | Pass condition |
|---|-------|----------------|
| O1 | Returns valid `classifier_output` | YAML or JSON object with all four fields: `schema_version`, `category`, `sub_type`, `confidence` |
| O2 | `schema_version` literal | Exactly `"1"` |
| O3 | `category` enum | One of: `claim-based`, `narrative`, `reference`, `tutorial`, `template`, `mixed` |
| O4 | `sub_type` enum (when category=claim-based) | One of: `identity`, `style`, `principle`, `decision` |
| O5 | `sub_type` is null when category ≠ claim-based | Hard rule; non-null on a non-claim doc is a FAIL |
| O6 | `confidence` range | Float in `[0.0, 1.0]` inclusive |
| O7 | Confidence floor not enforced inside agent | The agent must NOT refuse on its own when confidence < 0.6 — it returns the value and lets the caller gate. Refusing inside the agent is a FAIL. |
| O8 | Mixed-doc rule | When the largest non-claim region exceeds 30% of doc length, `category=mixed`; `sub_type` carries the dominant claim sub-type if detectable, else null |
| O9 | No `reasoning_summary` field | Output object does not include `reasoning_summary` (dropped per design §3.2) |
| O10 | Malformed input → structured error | On binary or schema-violating input, returns a structured error object, not a guess and not an empty payload |
| O11 | Unknown category → confidence 0.0 | If the model wants to label a category outside the enum, agent logs and returns `confidence: 0.0` so the caller refuses; does not crash |
| O12 | Determinism within a run | Two calls with the identical input within one session produce the same `category` + `sub_type` (confidence may vary slightly) |

---

## Blind Test Prompts

Five prompts. Each is a fresh agent invocation with no prior context. Expected `classifier_output` listed inline. Fixtures live under `references/examples/`.

### T1 — Claim-based identity doc

**Input:** Contents of `references/examples/claim-identity.md` plus `file_path: "references/examples/claim-identity.md"`.

**Expected:**
```yaml
classifier_output:
  schema_version: "1"
  category: claim-based
  sub_type: identity
  confidence: ≥ 0.75
```

### T2 — Narrative prose

**Input:** Contents of `references/examples/narrative-essay.md` plus `file_path`.

**Expected:**
```yaml
classifier_output:
  schema_version: "1"
  category: narrative
  sub_type: null
  confidence: ≥ 0.7
```

`sub_type: null` is mandatory; any non-null value is a FAIL.

### T3 — Mixed claim + narrative

**Input:** Contents of `references/examples/mixed-claim-narrative.md` (≈40% narrative blocks under "Background", ≈60% claim list under "Principles").

**Expected:**
```yaml
classifier_output:
  schema_version: "1"
  category: mixed
  sub_type: principle  # or null if not detectable
  confidence: ≥ 0.6
```

### T4 — Low-confidence short doc

**Input:** Contents of `references/examples/low-confidence-stub.md` (3 non-blank lines).

**Expected:**
```yaml
classifier_output:
  schema_version: "1"
  category: <best guess>
  sub_type: <per category rule>
  confidence: < 0.6
```

The agent MUST return the result without refusing. The shrinker skill enforces `classifier_confidence_floor`; the agent does not.

### T5 — SKILL.md adversarial input

**Input:** A real `SKILL.md` file (use `synapse/skills/synapse-router-artifact-creator/SKILL.md`) passed as `file_content`.

**Expected:** `category` is one of `template` or `reference` (NOT `claim-based`). The agent must use frontmatter, routing-contract description, and anatomy signals to recognize SKILL.md files. A `claim-based` verdict on this input is a FAIL — see design §12 risk row.

---

## Verdict Aggregation

- Any FAIL in S1–S17 → REVISE with structural findings.
- Any FAIL in O1–O12 → REVISE with output findings.
- Any FAIL in T1–T5 → REVISE with prompt-level findings.
- All PASS → APPROVE.

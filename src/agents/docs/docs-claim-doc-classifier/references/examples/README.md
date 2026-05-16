# Test fixtures — docs-claim-doc-classifier

Smoke-test inputs for the classifier. Each fixture has an expected `classifier_output` documented in `../../EVAL.md` (T1–T5).

| Fixture | Genre | Expected category | Expected sub_type | Expected confidence |
|---------|-------|-------------------|-------------------|---------------------|
| [claim-identity.md](claim-identity.md) | Identity manifest with declarative assertions under "Who I am" / "What I value" / "What I refuse" | `claim-based` | `identity` | ≥ 0.75 |
| [narrative-essay.md](narrative-essay.md) | Three paragraph essay with story-driven prose | `narrative` | `null` | ≥ 0.7 |
| [mixed-claim-narrative.md](mixed-claim-narrative.md) | ~40% narrative "Background" + 5-bullet "Principles" list | `mixed` | `principle` (or `null` if not detectable) | ≥ 0.6 |
| [low-confidence-stub.md](low-confidence-stub.md) | 3 non-blank lines, ambiguous content | best-guess | per category rule | < 0.6 |
| (live file) `synapse/skills/synapse-router-artifact-creator/SKILL.md` | Real SKILL.md — adversarial; classifier must NOT label `claim-based` | `template` or `reference` | `null` | ≥ 0.6 |

## How to use

1. Pass the fixture's full content as `file_content` and its repo-relative path as `file_path`.
2. Compare the returned `classifier_output` against the row above.
3. A mismatch on `category` or a non-null `sub_type` on a non-claim category is a hard FAIL — see EVAL O3 / O5.

These fixtures are deliberately small so the gatekeeper and any downstream eval runner can execute the full T1–T5 suite cheaply.

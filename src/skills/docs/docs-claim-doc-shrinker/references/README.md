# references — docs-claim-doc-shrinker

Companion files loaded by SKILL.md at specific decision points. `thresholds.yaml` is the single source of truth for every numeric gate; the four schema files are shared with the sibling agents.

| Path | Purpose | Loaded at |
|------|---------|-----------|
| [thresholds.yaml](thresholds.yaml) | All numeric gates (coverage abort %, idempotency delta floor, confidence floors, length sanity %, voice-anchor count range) | Both `audit` and `compress` entry |
| [claim-schema.md](claim-schema.md) | Shared `Claim` object schema (extractor output, audit-checklist source, writer input) | Extractor and writer dispatch |
| [classifier-schema.md](classifier-schema.md) | `classifier_output` schema + gate semantics | Classifier dispatch |
| [judge-schema.md](judge-schema.md) | `judge_verdict` schema + confidence-floor escalation | Judge dispatch |
| [audit-checklist-template.md](audit-checklist-template.md) | Shape of `.shrink/<file>.audit.md` | Audit checklist write |
| [wrong-tool-redirect.md](wrong-tool-redirect.md) | Source of the Wrong-Tool Detection block in SKILL.md and the `{redirect}` interpolation in the classifier refusal | Classifier refusal |
| [examples/](examples/README.md) | End-to-end smoke fixtures referenced by EVAL.md blind prompts T1–T8 | EVAL test harness |

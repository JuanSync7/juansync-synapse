# references/

Companion files for `docs-claim-shrinker`. Each is loaded at a specific node in SKILL.md — progressive disclosure, never always-on.

| File | Loaded at | Purpose |
|------|-----------|---------|
| [thresholds.yaml](thresholds.yaml) | `[START]` | Single source of truth for every numeric gate. Tuning never requires prompt edits. |
| [wrong-tool-redirect.md](wrong-tool-redirect.md) | `[NEW]` | Surface and exit before dispatching any agent when intent doesn't match. |
| [classifier-schema.md](classifier-schema.md) | `[CLASSIFY]` | Schema and gating rules for the classifier output. |
| [claim-schema.md](claim-schema.md) | `[EXTRACT]` and `[WRITE]` | Claim object shape; deterministic ID derivation; atomic-splitting contract. |
| [audit-checklist-template.md](audit-checklist-template.md) | `[CHECKLIST]` and `[VERIFY-AUDIT]` | Verbatim shape of `.shrink/<path>.audit.md`; marker semantics; headless-mode warning rule. |
| [judge-schema.md](judge-schema.md) | `[JUDGE]` and `[COVERAGE]` | Judge verdict shape; confidence escalation; coverage aggregation rule. |

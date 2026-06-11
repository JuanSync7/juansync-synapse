---
tag: {{TAG}}                              # e.g. PAY, AUTH, CHK — never 'FR'
foundation_source: {{declared|architecture|inferred|none-with-risk}}
spec_hash: {{spec_hash}}                  # sha256 of canonicalised input doc
slice_contract_version: 2
planned_count: {{N}}
generated_at_run: {{run_id}}
---

<!--
Foundation reasoning ({{foundation_source}}):
  {{one-or-two-line audit trail — why these foundations, in this order}}
  {{e.g. "auth precedes checkout: 7/9 FRs touch session module (cross-FR commonality ≥60%)"}}
  (leave block empty when foundation_source = none-with-risk)
-->

| story_id      | slug                          | status   | depends_on              | requirements_traced | file_cap_override?     | outcome (1-line)                            |
|---------------|-------------------------------|----------|-------------------------|---------------------|------------------------|---------------------------------------------|
| {{TAG}}-001   | {{kebab-slug-from-outcome}}   | planned  | []                      | [FR-1, FR-2]        | null                   | {{one-line validable outcome}}              |
| {{TAG}}-002   | {{kebab-slug-from-outcome}}   | planned  | [{{TAG}}-001]           | [FR-3]              | null                   | {{one-line validable outcome}}              |
| {{TAG}}-003   | {{kebab-slug-from-outcome}}   | planned  | [{{TAG}}-001]           | [FR-4, FR-5]        | 12: {{reason}}         | {{one-line validable outcome}}              |
| {{TAG}}-NNN   | {{kebab-slug-from-outcome}}   | planned  | [{{TAG}}-NNN, ...]      | [FR-N]              | null                   | {{one-line validable outcome}}              |

---

Hand-off: pass this manifest path to `/delivery-orchestration-plan-executor` to begin execution.

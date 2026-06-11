---
# --- delivery-execution-slice-contract ---
slice_id: {{TAG-NNN}}
validable_outcome: "{{one-sentence outcome that exactly one test can verify}}"
touches: [{{path1}}, {{path2}}]
depends_on: [{{depends_on_ids}}]
# --- planner extension ---
status: planned
requirements_traced: [{{FR-NNN, ...}}]
protocols:
  - delivery-execution-tdd-contract
  - delivery-execution-coding-contract
  - delivery-execution-slice-contract
discipline_deltas: []
file_cap_override: null
slice_contract_version: 2
---

# {{TAG-NNN}} — {{slug-derived-from-outcome}}

## Story
{{Narrative statement of the slice — who acts, what changes, what becomes demoable when this slice lands.}}

## Context
{{Neighbor files the worker must read + interface signatures this slice consumes from upstream slices in `depends_on`. Replaces a separate INTERFACES.md — name each `provides` story whose surface this slice calls into.}}

## Constraints from horizontal docs
{{NFRs, architecture rules, and scope guardrails inherited from horizontal docs. If a CONFLICT was detected between the spec and a horizontal doc, the CONFLICT block appears verbatim here — do not silently resolve.}}

## Test scenarios
{{Concrete cases that demonstrate `validable_outcome`. At least one scenario must map 1:1 to the outcome statement; additional scenarios cover edges named in `requirements_traced`.}}

## Out of scope
{{Explicit non-goals for this slice — adjacent work that belongs to a sibling story or a future plan iteration. Cite the sibling slice_id when the work is deferred to another story.}}

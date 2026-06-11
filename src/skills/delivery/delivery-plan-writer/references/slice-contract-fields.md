# Slice-Contract Fields (Point-of-Emit Reference)

Loaded at `[START]` (pre-flight field check) and `[D]` (decompose into stories). The orchestrator's `delivery-execution-slice-contract` validator rejects any story whose frontmatter is missing a required field or misnames an extension field. Emit the block below verbatim — only the values vary.

## Canonical Frontmatter Block

```yaml
---
# --- delivery-execution-slice-contract ---
slice_id: TAG-NNN
validable_outcome: "..."
touches: [path1, path2]
depends_on: [TAG-NNN, ...]
# --- planner extension ---
status: planned
requirements_traced: [FR-NNN, ...]
protocols:
  - delivery-execution-tdd-contract
  - delivery-execution-coding-contract
  - delivery-execution-slice-contract
discipline_deltas: []
file_cap_override: null
slice_contract_version: 2  # paired bump
---
```

The two banner comments (`# --- delivery-execution-slice-contract ---`, `# --- planner extension ---`) are part of the contract — they let the orchestrator's parser distinguish required vs extension fields. Do not omit them.

## Required (slice-contract)

Source: `src/protocols/delivery/delivery-execution-slice-contract.md`. Validator runs as the first pre-dispatch check; any missing or empty field aborts dispatch (violation signature (e)) and routes the slice to replan.

| Field | Type | Shape / Allowed | Consumer | Failure on omission |
|---|---|---|---|---|
| `slice_id` | string | `TAG-NNN` (zero-padded sequence). Must match filename basename. `TAG='FR'` forbidden. | Orchestrator INDEX.md, closeout cross-reference | Orchestrator cannot key the dispatch; SC violation (e) — abort. |
| `validable_outcome` | string | One sentence expressible as one failing test. Not a checklist. | TDD-contract test mapping; closeout `validation_result` | Subagent "cannot determine done"; SC violation (a) — abort, route to replan. |
| `touches` | list of paths | Relative repo paths the slice may read or write. Empty list forbidden. | Post-closeout boundary check (`files_modified ⊆ touches`) | Boundary check has no envelope; SC violation (d) on every closeout — reject. |
| `depends_on` | list of `slice_id` | Predecessor IDs that must close green before dispatch. `[]` permitted. May not reference unknown IDs. | `[PICK-NEXT-SLICE]` topological scheduler | Scheduler deadlocks or dispatches out-of-order; cycles ship an unbuildable plan. |

## Planner Extension

Owned by this skill. The orchestrator reads these but does not validate them as part of the slice-contract; downstream protocols (dispatch-contract, closeout-schema, tdd-contract) consume them. Emit all six on every story — missing fields force the orchestrator into legacy-default branches and silently degrade dispatch quality.

| Field | Type | Shape / Allowed | Consumer | Failure on omission |
|---|---|---|---|---|
| `status` | enum | `planned` on emit. Orchestrator transitions to `pending \| in-progress \| done \| blocked`. | Re-run collision check; orchestrator state machine | Re-run overwrite policy can't distinguish in-flight from fresh; clobbers work. |
| `requirements_traced` | list | `[FR-NNN, ...]` or `[]` for chat-intent inputs | Spec-to-slice audit trail | No traceability; spec coverage cannot be proved at close. |
| `protocols` | list (4 entries) | `delivery-execution-tdd-contract`, `delivery-execution-coding-contract`, `delivery-execution-slice-contract` minimum. Order significant — TDD first. | Dispatch-contract `{{worker_protocols}}` slot | Dispatch injects fewer than 4 protocol bodies; subagent operates without coding-contract discipline. |
| `discipline_deltas` | list | `[]` default. Each entry is a per-story rule override `{protocol, rule, value, reason}`. | Dispatch-contract `{{discipline_deltas}}` slot | No place to scope a relaxation; planners inline rule prose into the body (forbidden). |
| `file_cap_override` | int or `null` | `null` default. Integer when a story exceeds the SOFT cap (≤8 files) with a `reason` annotation in the body. | Granularity gate at `[D]` step 2 | Gate refuses legitimately wide slices; planner cannot record why the cap was raised. |
| `slice_contract_version` | int | `2` — paired with closeout-schema v2 bump. | Orchestrator on-read version check | Version mismatch halts orchestrator pre-flight with no diagnostic. |

## Body Sections (purpose, one line each)

Emit in this order. Body sections are not parsed for contract validation but are read by the dispatched subagent — section names are load-bearing.

1. **Story** — narrative statement of the slice in the user-value voice.
2. **Context** — neighbor files + interface signatures consumed (replaces a separate INTERFACES.md).
3. **Constraints from horizontal docs** — NFRs, architecture rules, scope guardrails; `CONFLICT` blocks surface here verbatim.
4. **Test scenarios** — concrete cases that demonstrate `validable_outcome` (input → observable behavior).
5. **Out of scope** — explicit non-goals; pre-empts subagent scope-creep at close time.

## Granularity Gates (thresholds loaded at [D] step 2)

| Gate | Threshold | Action on violation |
|---|---|---|
| HARD floor | One `validable_outcome` per story expressible as one failing test | Refuse the story; re-decompose |
| SOFT cap | ≤8 files in `touches` (config: `.delivery/config.yaml: granularity.file_cap`) | Allow with `file_cap_override: <reason>` populated; outcome cap always wins over file cap |
| LOWER refusal | Trivial slices (single rename / one-line config / pure formatting) | Refuse standalone; fold into a sibling slice |
| UPPER refusal | >30 stories in one plan | Refuse unless invoked with `--confirm` |
| Degenerate | 1-story decomposition | Refuse; redirect to `/code-build-planner` (this skill is multi-slice-only) |

Outcome-cap is the tiebreaker against file-cap: a single-outcome story that touches 14 files is permitted with `file_cap_override`; a multi-outcome story that touches 4 files is rejected.

## Forbidden Fields

These names look natural but are explicitly disallowed — the slice-contract or the filename convention already carries the information.

- `acceptance_summary` — outcome is carried by `validable_outcome`; a second field drifts.
- `slug` — filename derives from `slice_id` + kebab outcome; a `slug` field allows them to diverge.
- Inline `coding-contract` rule text in the body — reference the protocol by name in `protocols:` only.

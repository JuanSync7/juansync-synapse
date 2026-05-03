# Planning Notepad — {{SPEC_NAME}}

> **Ephemeral** — this file exists only during the current run. Discarded after completion.

## Paths

- **Spec file:** `{{SPEC_PATH}}`
- **Doc map:** `{{MAP_PATH}}`
- **Template:** `template.md` (read once during planning)

## Document Skeleton

Copy headings from the spec template after creating the skeleton. Quick reference for brief construction.

```
<!-- sec:scope -->       Section 1: Scope & Definitions
<!-- sec:overview -->    Section 2: System Overview
<!-- sec:req_XXX -->     Section 3+: Requirement sections (one per domain)
<!-- sec:nfr -->         Non-Functional Requirements
<!-- sec:acceptance -->  System-Level Acceptance Criteria
<!-- sec:matrix -->      Requirements Traceability Matrix
<!-- sec:appendix -->    Appendices
```

## Section Briefs

One block per section. Status tracks the dispatch lifecycle.

```
### sec:{{ID}}
- status: pending | dispatched | pass | pass-with-note | reject | needs-manual
- model: opus | sonnet
- heading: {{Section Heading}}
- key_points:
  - {{point 1}}
  - {{point 2}}
- cross_refs:
  - entity: {{entity_name}} | defined_in: sec:{{other_id}} | usage: {{how this section references it}}
- source_excerpts:
  - "{{verbatim excerpt from input material relevant to this section}}"
- tools_hint: {{specific tools the writer should use, e.g., "Explore agent for codebase API surface"}}
- depth: standard | deep | overview
- retry_count: 0
```

**Field contract (writer validates these):**
- `key_points` — MUST have at least 2 items
- `heading` — MUST be non-empty
- `depth` — MUST be one of: standard, deep, overview
- `source_excerpts` — MUST have at least 1 item (empty string acceptable only for overview depth)

## Signals Log

Append-only. Each entry records a discovery from a subagent sidecar or a planner observation.

```
- [sec:{{ID}}] {{signal_type}}: {{description}}
  e.g., - [sec:req_auth] new_entity: "refresh_token" — defined here, likely referenced by sec:req_session
  e.g., - [sec:req_query] cross_ref_update: REQ-201 references entity "query_plan" from sec:req_optimizer
```

## Decisions

Planner reasoning — why a brief was constructed a certain way, why a model was chosen, why a retry was or wasn't attempted.

```
- {{decision description and reasoning}}
```

## Rejected Briefs

Frozen record. When a brief is rejected by the reviewer or rewritten by the planner, the old version goes here with the reason. Never delete entries from this section.

```
### sec:{{ID}} (rejected {{YYYY-MM-DD}})
- reason: {{why it was rejected or rewritten}}
- original_brief: {{copy of the original brief block}}
```

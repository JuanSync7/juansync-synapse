# Document Map — {{SPEC_NAME}}

> **Persistent** — this file lives alongside the spec as `{{SPEC_NAME}}_SPEC_MAP.md`. Updated after every section write.

## Skeleton

Section anchors use `<!-- sec:id -->` / `<!-- /sec:id -->` HTML comment pairs in the spec file. Agents navigate by grepping for anchors, never by line numbers.

| Anchor | Heading |
|--------|---------|
| `sec:scope` | Section 1: Scope & Definitions |
| `sec:overview` | Section 2: System Overview |
| `sec:req_XXX` | Section N: {{Domain Name}} |
| `sec:nfr` | Non-Functional Requirements |
| `sec:acceptance` | System-Level Acceptance Criteria |
| `sec:matrix` | Requirements Traceability Matrix |
| `sec:appendix` | Appendices |

## Sections

| ID | Status | Anchor | Heading | REQ Range | REQ Count |
|----|--------|--------|---------|-----------|-----------|
| scope | done | `sec:scope` | Scope & Definitions | — | — |
| overview | done | `sec:overview` | System Overview | — | — |
| req_XXX | pending | `sec:req_XXX` | {{Domain}} | REQ-Nxx | 0 |
| nfr | pending | `sec:nfr` | Non-Functional Requirements | REQ-9xx | 0 |
| matrix | pending | `sec:matrix` | Traceability Matrix | — | — |

## Entity Index

Tracks domain entities across sections. Enables cross-reference resolution without scanning the full spec.

| Entity | Defined In | Referenced By |
|--------|-----------|---------------|
| `{{entity_name}}` | sec:{{id}} | sec:{{id1}}, sec:{{id2}} |

## REQ Index

Aggregates requirement coverage per section for traceability matrix construction.

| Range | Section | MUST | SHOULD | MAY |
|-------|---------|------|--------|-----|
| REQ-1xx | sec:scope | 0 | 0 | 0 |
| REQ-2xx | sec:req_XXX | 0 | 0 | 0 |
| REQ-9xx | sec:nfr | 0 | 0 | 0 |
| **Total** | | **0** | **0** | **0** |

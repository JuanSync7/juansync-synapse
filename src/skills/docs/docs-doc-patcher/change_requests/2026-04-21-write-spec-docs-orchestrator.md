# docs-spec-writer is now an orchestrator

Two changes needed in docs-doc-patcher:

1. **Escalation model tier:** `references/escalation-policy.md` dispatches docs-spec-writer at Sonnet. docs-spec-writer is now a planner that orchestrates subagents (section-writer, section-reviewer, coherence-reviewer). It needs Opus to plan and dispatch effectively. Update the delegation behavior to dispatch at Opus.

2. **`_SPEC_MAP.md` awareness:** docs-spec-writer now produces a companion `_SPEC_MAP.md` file alongside every spec. This contains the document skeleton (headings + anchors) and a knowledge graph index (sections, entities, REQ IDs). When docs-doc-patcher escalates to docs-spec-writer, it should pass the map file path if one exists — docs-spec-writer uses it as the base for update mode.

Source: docs-spec-writer brainstorm 2026-04-21

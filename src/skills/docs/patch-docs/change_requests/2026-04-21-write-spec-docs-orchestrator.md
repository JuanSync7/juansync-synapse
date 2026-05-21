# write-spec-docs is now an orchestrator

Two changes needed in patch-docs:

1. **Escalation model tier:** `references/escalation-policy.md` dispatches write-spec-docs at Sonnet. write-spec-docs is now a planner that orchestrates subagents (section-writer, section-reviewer, coherence-reviewer). It needs Opus to plan and dispatch effectively. Update the delegation behavior to dispatch at Opus.

2. **`_SPEC_MAP.md` awareness:** write-spec-docs now produces a companion `_SPEC_MAP.md` file alongside every spec. This contains the document skeleton (headings + anchors) and a knowledge graph index (sections, entities, REQ IDs). When patch-docs escalates to write-spec-docs, it should pass the map file path if one exists — write-spec-docs uses it as the base for update mode.

Source: write-spec-docs brainstorm 2026-04-21

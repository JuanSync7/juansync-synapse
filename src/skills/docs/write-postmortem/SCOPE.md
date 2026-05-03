# SCOPE — write-postmortem

**What it does:** Produces a structured, blameless postmortem document from incident facts. Can facilitate fact-gathering (Facilitate mode) or write directly from organized inputs (Write mode).

**Min model tier:** Sonnet. Requires judgment for blameless rewriting and contributing-factor analysis but no complex reasoning chains.

**Tool use:** None required. Reads companion files from disk.

**Long context:** Not required for typical incidents. Long context useful when large log dumps are provided for timeline reconstruction.

**Out of scope:** Does not track action items in external systems (use /jira-reporter), does not produce runbooks or incident response playbooks (those are for-during-incident artifacts, not post-incident).

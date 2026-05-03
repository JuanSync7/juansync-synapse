---
name: write-postmortem
description: "Use when asked to write a postmortem, create an incident postmortem, document an outage, or produce a blameless post-incident review."
domain: docs
intent: write
tags: [postmortem, incident-response, blameless, sre, reliability]
user-invocable: true
argument-hint: "[incident description or log dump]"
---

A postmortem is a structured artifact that turns an incident into organizational learning. The goal is not to find who failed — it is to find where the system (including process, tooling, and organizational context) allowed the failure to happen. Blameless means the analysis focuses on conditions, not individuals.

This skill operates in two modes: **Facilitate** (the user hasn't organized facts yet) and **Write** (facts are available — produce the document). Detect the mode from context: if the user provides a raw dump of logs, a rough timeline, or says "we haven't sorted through this yet," start in Facilitate mode. If they provide organized facts or a filled-in brief, go directly to Write mode.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## Wrong-Tool Detection

- **User wants a runbook or incident response playbook** (procedures for *during* an incident) → this skill is for *post*-incident analysis; redirect them to write a runbook instead
- **User wants to track action items in JIRA** → use `/jira-reporter` after producing the postmortem document
- **User wants a root cause analysis without the full postmortem format** → you can produce a condensed RCA section only; say so and ask if that's the right scope

## Progress Tracking

At the start, create a task list:

```
TaskCreate: "Phase 1: Facilitate — gather facts, timeline, and contributing factors"
TaskCreate: "Phase 2: Write — produce structured postmortem document"
```

Mark each task `in_progress` when starting, `completed` when done.

## Phase 1: Facilitate

> **Read [`references/facilitation-guide.md`](references/facilitation-guide.md)** when entering this phase — it contains the question sequence, timeline reconstruction method, and contributing-factor analysis approach.

**When to use Facilitate mode:** The user has raw logs, a rough sequence of events, partial information, or explicitly says investigation is ongoing. Do not write the document until the key facts are confirmed.

Gather facts in this order — earlier items unlock later ones:

1. **Detection and scope** — When was the incident first detected? How (alert, customer report, engineer noticed)? Which systems were affected?
2. **Timeline reconstruction** — Start from the detection event and build outward: what happened immediately before? What happened right after the first response action? Use log timestamps if provided; mark gaps as `[UNKNOWN — needs log review]`.
3. **Impact** — Who was affected and how? Include: user-facing impact (errors, slowness, data unavailability), duration, estimated scope (% of users, transaction count, revenue if known), SLO breach (yes/no and how much).
4. **Contributing factors** — Ask "why was this possible?" not "who did this?" For each contributing factor, drive one level deeper: why did that condition exist? Stop at organizational/process boundaries, not individual decisions. Use the 5-whys method if the chain isn't obvious.
5. **Resolution** — What steps resolved the incident? Which one actually restored service?
6. **Action items** — What must change to prevent recurrence or improve detection? Each action item requires: owner (role, not person), deadline, and a measurable outcome definition.

**Incomplete information:** When a fact is missing, mark it explicitly as `[OPEN: needs investigation]` and continue. Do not invent or speculate — a postmortem with honest gaps is more useful than a complete-looking document with guesses.

**Readiness gate:** Before moving to Phase 2, confirm:
- [ ] Timeline has at least: incident start, detection, first response action, resolution
- [ ] Impact is quantified (or explicitly marked as unknown with a plan to find out)
- [ ] At least one contributing factor identified (not just the proximate trigger)
- [ ] At least one action item drafted

DO NOT proceed to Phase 2 if the gate fails. Name the missing items and ask for them specifically.

## Phase 2: Write

> **Read [`templates/postmortem-template.md`](templates/postmortem-template.md)** before producing output — this defines the required document structure.

Produce the document by filling in the template. Rules:

**Blameless language:** Every sentence in Contributing Factors and Timeline must pass this test: does the sentence require a named or implied individual to feel at fault for it to be true? If yes, rewrite it to assign fault to the condition, not the person. "The on-call engineer didn't notice the alert" → "The alert threshold was set above the noise floor, which masked the signal until degradation was severe." Check for these phrases as red flags: "didn't notice," "failed to," "neglected to," "forgot to."

**Action item quality:** Each action item MUST have: (1) a specific owner role (not "team"), (2) a deadline or sprint target, (3) a definition of done that a third party could verify. Vague action items ("improve monitoring") are not acceptable — ask for specifics or flag them as `[NEEDS OWNER + DEFINITION OF DONE]`.

**Severity classification:** Classify the incident using the severity levels defined in `references/severity-levels.md`. If the organization uses a custom severity system, ask for their scale.

**Section ordering:** Follow the template exactly. Readers navigate postmortems by section, not linearly — consistent structure enables institutional memory across incidents.

> **Read [`references/severity-levels.md`](references/severity-levels.md)** when classifying incident severity.

## Output

A single markdown document following the postmortem template. Deliver inline (do not create a file unless the user asks). The document is complete when all required template sections are filled — no placeholders except explicitly marked open items.

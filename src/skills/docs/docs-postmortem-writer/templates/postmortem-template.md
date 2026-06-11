# Incident Postmortem: [Incident Title]

**Severity:** [SEV-1 / SEV-2 / SEV-3 — see severity definitions]
**Date:** [YYYY-MM-DD]
**Duration:** [HH:MM]
**Status:** [Draft / In Review / Final]
**Authors:** [names or roles]

---

## Summary

One paragraph. What failed, when, for how long, and the approximate impact. Written for an executive audience — no jargon, no acronyms without definition.

---

## Impact

| Dimension | Value |
|-----------|-------|
| User-facing impact | [errors / degraded / full outage] |
| Affected users | [count or percentage] |
| Affected transactions | [count or "unknown — see open items"] |
| Duration | [minutes/hours] |
| SLO breach | [Yes — X% below target / No] |
| Revenue impact | [$ estimate or "not calculated"] |
| Data loss | [Yes / No / Unknown] |

---

## Timeline

All times in UTC (or state timezone explicitly).

| Time | Event | Source |
|------|-------|--------|
| HH:MM | [Deployment / config change / upstream event — root of causal chain] | [log / alert / ticket] |
| HH:MM | [First symptom observable in system metrics] | [monitoring system] |
| HH:MM | [Detection — how the incident was first identified] | [alert / customer report / engineer] |
| HH:MM | [First response action] | [incident channel / on-call] |
| HH:MM | [Key diagnostic step] | |
| HH:MM | [Mitigation action — may be temporary] | |
| HH:MM | [Service restored] | |
| HH:MM | [Full recovery / incident closed] | |

*Mark unknown timestamps as `[OPEN: timestamp from logs needed]`*

---

## Root Cause

One paragraph describing the proximate cause — the specific technical condition that directly caused user impact. This is not blame; it is the last link in the causal chain.

Example: "A database connection pool exhausted because connection limits were set below the traffic spike threshold during a promotional event, causing all downstream services that depend on the payment database to queue indefinitely and time out."

---

## Contributing Factors

Each factor is a condition that allowed the incident to occur or made it worse. For each one, answer: why did this condition exist?

- **[Factor 1]:** [Description of the condition]. Root: [why this condition was present — e.g., the alert threshold was inherited from a lower-traffic period and never reviewed after scaling].
- **[Factor 2]:** [Description]. Root: [why].
- **[Factor 3]:** [Description]. Root: [why].

*Minimum one factor required. Three to five is typical for a meaningful postmortem.*

---

## Detection

How was the incident detected? Was it an alert, a customer complaint, or an engineer noticing something? If alert: was the alert threshold appropriate? Was there a gap between when the condition started and when we knew about it? How large was the gap?

---

## Resolution

What steps resolved the incident? Which action actually restored service? What was tried that didn't work?

---

## Action Items

Each action item targets a specific contributing factor. Vague items must include `[NEEDS OWNER + DEFINITION OF DONE]`.

| # | Action | Owner (role) | Deadline | Definition of Done | Linked Factor |
|---|--------|-------------|----------|--------------------|---------------|
| 1 | [Specific action] | [Role] | [Date/sprint] | [Observable outcome] | Factor N |
| 2 | | | | | |

---

## What Went Well

Things that limited impact, accelerated detection, or made recovery faster. This section reinforces good practices.

- [Detection was fast because ...]
- [Rollback procedure worked as designed]
- [On-call escalation was clear]

---

## Open Items

Facts that are still being investigated or verified. Each must have an owner and expected resolution date.

| Item | Owner | Expected by |
|------|-------|-------------|
| [Exact transaction count affected] | [Name/role] | [Date] |
| [Whether data was written during the window] | | |

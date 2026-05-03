# Severity Classification Reference

Use this reference when classifying incidents in the postmortem document. If the organization has a custom severity scale, ask the user for it and use theirs.

## Default Severity Scale (SRE-standard)

| Level | Name | User Impact | Response Requirement |
|-------|------|-------------|---------------------|
| SEV-1 | Critical | Full service outage or data loss affecting ≥10% of users, or any data integrity issue | Immediate all-hands response; escalate to leadership |
| SEV-2 | Major | Significant degradation affecting ≥5% of users, or key workflows unavailable | Urgent response; dedicated incident channel |
| SEV-3 | Minor | Degraded performance or partial feature unavailability affecting <5% of users | Normal on-call response; resolved within business hours |
| SEV-4 | Low | No user impact; internal tooling or infrastructure concern | Tracked as ticket; no incident response required |

## Classification Decision Tree

1. Is there any data loss or data corruption (confirmed or suspected)? → **SEV-1**
2. Is a core user-facing workflow completely unavailable? → **SEV-1** (if ≥10% users) or **SEV-2** (if <10%)
3. Is the primary service significantly degraded (>2x latency, >5% error rate)? → **SEV-2**
4. Is a non-critical feature unavailable or slow? → **SEV-3**
5. Is the impact purely internal? → **SEV-4**

## Notes

- When in doubt, classify higher and downgrade after investigation. Under-classifying an incident that turns out to be data loss is much worse than over-classifying.
- Duration alone does not determine severity. A 5-minute full outage is SEV-1. A 2-hour partial degradation affecting 1% of users may be SEV-3.
- If the organization does not use this scale, note in the postmortem which scale was used and include the definition inline.

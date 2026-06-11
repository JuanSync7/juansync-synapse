# Postmortem Facilitation Guide

This guide is loaded during Phase 1 (Facilitate mode). It provides the question sequence, timeline reconstruction method, and contributing-factor analysis approach.

## Question Sequence

Ask these in order. Each tier depends on answers from the previous tier — do not jump ahead.

### Tier 1: Anchor the incident (always ask first)
1. "What was the first sign that something was wrong? When did you first notice, and how?"
2. "What systems or services were directly affected?"
3. "When was normal service restored?"

These three questions define the incident boundary. Everything else fills in the middle.

### Tier 2: Build the causal chain
4. "In the hour before the first symptom, was anything deployed, changed, or scaled?"
5. "What did the monitoring show right before detection? What metrics spiked or dropped?"
6. "Walk me through what responders did, in order, from first page to resolution."

### Tier 3: Understand the gap
7. "How long was there a problem before anyone knew about it?" (detection gap)
8. "Once you knew, how long until you had a mitigation?" (response gap)
9. "What made diagnosis hard or slow?"

### Tier 4: Prevent recurrence
10. "If you had to prevent this exact failure, what is the one thing you'd change?"
11. "What would have caught this earlier?"
12. "Is there a process or tool that should exist but doesn't?"

---

## Timeline Reconstruction from Logs

When the user provides log snippets but hasn't organized them:

1. **Extract timestamps** — identify every log line with a timestamp; build a raw chronological list
2. **Anchor to known events** — find the deployment event, config change, or external trigger that appears just before symptoms
3. **Find the first symptom** — look for the earliest error, timeout, or anomalous metric
4. **Find the detection event** — look for the first alert, PagerDuty page, or human acknowledgment
5. **Mark the resolution** — find the timestamp when errors stopped or service resumed normal behavior
6. **Fill middle gaps** — slot in response actions between detection and resolution
7. **Mark unknowns explicitly** — any gap longer than ~5 minutes with no log evidence gets `[UNKNOWN — needs log review]`

Do not reconstruct timeline from memory alone when logs are available. Misremembered timelines are a common postmortem failure mode that produces wrong conclusions about detection gaps.

---

## Contributing Factor Analysis (5-Whys)

The 5-whys method: for any contributing factor, ask "why did this condition exist?" up to 5 times. Stop when you reach an organizational or systemic boundary (not a personal decision).

**Example:**
- Symptom: Payment service crashed
- Why? Database connections exhausted
- Why did connections exhaust? Connection pool limit was 50; traffic spike hit 200 concurrent requests
- Why was the limit 50? Set at initial deployment; never reviewed after traffic grew 4x
- Why was it never reviewed? No process for reviewing infrastructure parameters after scaling events
- Why? ← organizational boundary; this is a process gap, not an individual failure

**Stop condition:** Stop when the answer is "because we don't have a policy/process/owner for that" — that's the actionable finding. Do not continue into speculation about organizational history.

**Common contributing factor categories:**
- Capacity/scaling: limits, thresholds, or quotas that weren't updated as load grew
- Observability: monitoring gaps, alert thresholds set for old traffic patterns, missing dashboards
- Process: missing runbooks, unclear escalation paths, knowledge silos
- Deployment/change management: missing canary, no rollback plan, config drift
- Dependencies: upstream services without circuit breakers, third-party failures without fallback

---

## What Counts as Blameless

The blameless test: read each sentence in Contributing Factors aloud and ask, "does this sentence require someone to feel bad to be true?"

**Fails the test (not blameless):**
- "The engineer deployed to production on a Friday without testing."
- "The team didn't set up proper monitoring."
- "The on-call didn't escalate fast enough."

**Passes the test (blameless):**
- "The deployment pipeline allowed production pushes on Fridays without a gate."
- "The service had no health check endpoint, so monitoring relied on synthetic probes that didn't cover the failure mode."
- "Escalation criteria in the runbook were ambiguous — it was unclear whether this pattern triggered a SEV-1 or SEV-2 response."

The rewrite shifts responsibility from individuals to systems, processes, and policies — where engineering remediation is actually possible.

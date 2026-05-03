# Lens Catalog

7 generic lenses for pressure-testing threads. 4 lenses fire per session = 2 universal + 2 type-specific. Selection is fixed at Phase A based on classification; pulled in ad-hoc only if user explicitly asks.

All 7 lenses are used across the 5 types — just not all in any single session.

## The 7 Lenses

### Stakeholder (universal)
**Core question:** Who is affected, and does this serve them?

**Diagnostic prompts:**
- "Who benefits from this if it works?"
- "Who is harmed if it doesn't?"
- "Whose problem are we actually solving — the user's, the team's, or someone else's?"
- "Is there a silent stakeholder not represented in this decision?"

**Catches:** Ignored stakeholders, decisions made for the wrong audience, solving the team's convenience instead of the user's problem.

### Alternative (universal)
**Core question:** What else could we do — are we missing options?

**Diagnostic prompts:**
- "What's the option we didn't list?"
- "What would a different team with different constraints pick?"
- "If we couldn't do any of these, what would we do?"
- "Is the do-nothing option on the table, and what's its cost?"

**Catches:** Anchoring on the first idea, false binaries, missing a better option that wasn't surfaced in Generate.

### Failure-mode
**Core question:** What breaks, and what's the failure profile?

**Diagnostic prompts:**
- "What's the single most likely way this goes wrong?"
- "What happens when an edge case we didn't think of hits?"
- "What's the silent failure — the one where we don't even know it broke?"
- "Does failure degrade gracefully or collapse catastrophically?"

**Catches:** Optimism bias, unhandled error paths, silent failures, brittle happy paths.

### Cost
**Core question:** What does this take — up-front AND ongoing?

**Diagnostic prompts:**
- "What's the build cost — time, people, dollars?"
- "What's the ongoing maintenance cost? Who pays it?"
- "What does this cost on the months we're not using it?"
- "What's the opportunity cost — what else could that time go to?"

**Catches:** Up-front-only thinking, ignored maintenance burden, sunk-cost trajectories, hidden ongoing obligations.

### Reversibility
**Core question:** How bad is it if wrong, and can we back out?

**Diagnostic prompts:**
- "If this turns out wrong in 6 months, what's the cost to reverse?"
- "Is this a one-way door or a two-way door?"
- "Can we test a reduced version first to de-risk before committing fully?"
- "What data would tell us we're wrong, and how fast do we see it?"

**Catches:** Irreversible commitments made without de-risking, decisions that feel small but aren't, missing checkpoints.

### Time
**Core question:** What happens to this in 6 months? 1 year?

**Diagnostic prompts:**
- "What does this look like a year from now?"
- "Does this still make sense when the team is 3x larger?"
- "What's the decay curve on the assumptions we're making?"
- "What's the sequence — what comes first, what depends on what?"

**Catches:** Short-horizon thinking, ignored sequencing, assumptions that don't age well, decisions that will look wrong in retrospect.

### Constraint
**Core question:** What are the real limits we're bumping against?

**Diagnostic prompts:**
- "What's the hard constraint we can't negotiate?"
- "What constraint feels hard but is actually soft?"
- "What resource (time, people, money, attention) is actually the bottleneck?"
- "What external dependency are we assuming will cooperate?"

**Catches:** Fantasy planning, missed bottlenecks, treating soft constraints as hard (and vice versa), unacknowledged external dependencies.

## Selection Table — 4 Lenses Per Session

2 universal + 2 type-specific:

| Type | Universal lenses | Type-specific lenses |
|---|---|---|
| `decision` | Stakeholder, Alternative | Reversibility, Failure-mode |
| `exploratory` | Stakeholder, Alternative | Constraint, Time |
| `problem` | Stakeholder, Alternative | Failure-mode, Reversibility |
| `creative` | Stakeholder, Alternative | Constraint, Cost |
| `planning` | Stakeholder, Alternative | Time, Cost |

**Rationale for the pattern:**
- **Stakeholder + Alternative** are universal because every brainstorm has stakeholders and potential alternatives — neither has a type where it's irrelevant.
- **Reversibility** fires when you're picking (decision/problem) — the cost of being wrong drives the care.
- **Constraint** fires when scoping possibility space (exploratory/creative) — what can we actually do.
- **Time** fires when sequencing or looking forward (exploratory/planning) — order and horizon.
- **Cost** fires when producing artifacts or committing ongoing resources (creative/planning) — sustained burden.
- **Failure-mode** fires when things can break (decision/problem) — picking wrong has concrete consequences.

## When to Pull Ad-Hoc Lenses

User may explicitly request an additional lens mid-session. Example: "What about the Time lens for this decision?" — pull it in for that thread, note the request in the notepad. Don't silently apply lenses outside the selected subset.

## Lens Rotation Discipline

In Phase B, rotate each selected lens against each `open` thread at least once before the thread can reach terminal status. Thread-Resolution Precondition (see coaching-policy) specifically requires the 2 universal lenses; the 2 type-specific are strongly recommended but not hard-gated.

If a lens pass surfaces a new first-order concern, the concern becomes a new thread (and the Phase A admission protocol fires — see coaching-policy).

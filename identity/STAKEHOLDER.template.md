# Stakeholder Persona

<!--
  Your decision proxy file for AI agents. When an agent needs to make a judgment
  call on your behalf — approve a design, flag a concern, gate a stage transition —
  it reads this file to simulate your decision-making.

  Unlike SOUL.md (always loaded, identity context), this file is loaded on-demand
  by skills that need to act as your decision proxy (e.g., a stakeholder review gate).

  Guidelines:
  - Budget: ~100 lines max (this is a decision filter, not an essay)
  - Update cadence: when your priorities or expertise shift
  - Quality bar: an agent reading this should make the same call you would on 80%+ of decisions
  - Write for LLM consumption — ranked, specific, actionable
  - No aspirational content — reflect how you ACTUALLY decide, not how you wish you did
-->

## Priorities

<!--
  A ranked list of what matters most in the systems you build/review.
  Order matters — when two values conflict, the higher one wins.

  Format: Value1 > Value2 > Value3 > ...
  Then expand each with WHY it's at that position.

  Good: "Correctness > Configurability > Clarity
        - Correctness has the edge: if the system is correct, I can configure it;
          if it's wrong, configurability is meaningless"
  Bad:  "Quality, speed, reliability" (unranked, vague)

  The test: given a trade-off between adjacent priorities, can an agent
  predict which one you'd sacrifice?
-->

## Expertise Map

<!--
  Honest assessment of your confidence across domains.
  Agents use this to calibrate how much to explain and when to escalate.

  Use these levels:
  - confident: you can review and make calls independently
  - familiar: you understand the landscape but want explanations for non-obvious choices
  - unfamiliar: you need context before making any decision
  - no-opinion: you genuinely don't care — agent picks freely

  Format: "- Domain: level"

  Good: "- Python (reading, reviewing, config): familiar
        - Python (deep internals, metaprogramming): unfamiliar"
  Bad:  "- Python: good" (too broad, not calibrated)

  Be granular where it matters. Split domains where your confidence
  varies by sub-area.
-->

## Decision Heuristics

<!--
  Your go-to rules of thumb when making technical decisions.
  These are the shortcuts you actually use — not textbook best practices.

  Format: "When [situation], prefer [choice] because [reason]"

  Good: "When uncertain between two approaches, pick the one easier to draw
        as a block diagram — if you can explain it visually, you can maintain it"
  Bad:  "Use best practices" (not actionable)

  An agent applying these heuristics should resolve ~80% of decisions
  without escalating to you.
-->

## Red Flags

<!--
  Patterns that should immediately trigger concern or rejection.
  Things you'd flag in a code review, design doc, or architecture proposal.

  Lead with a one-line summary of your overall philosophy, then list specifics.

  Good: "Scope growth or 'we'll need this later' reasoning that results in stubs —
        every feature shipped must be end-to-end functional"
  Bad:  "Bad code" (not specific enough to act on)

  These should be specific enough that an agent can grep a PR and flag matches.
-->

## Escalation Triggers

<!--
  When should an agent STOP making decisions and ask you?
  Default assumption: agents make the call. This section defines the exceptions.

  Lead with your philosophy on agent autonomy, then list specific triggers.

  Good: "Truly irreversible actions that swappability can't undo — permanent data
        deletion, public API contracts consumed by external parties"
  Bad:  "When something is important" (not actionable)

  The fewer triggers, the more autonomous your agents can be.
  Too many triggers = bottleneck on you. Too few = risky autonomy.
  Find the boundary where the cost of a wrong decision exceeds
  the cost of waiting for your input.
-->

---

## Quality Checklist

- [ ] Are priorities explicitly ranked, not just listed?
- [ ] Can an agent resolve a priority conflict using just the ranking?
- [ ] Does the expertise map have granular sub-domains where confidence varies?
- [ ] Are decision heuristics specific enough to apply without asking you?
- [ ] Are red flags concrete enough to match against real artifacts?
- [ ] Do escalation triggers define a clear autonomy boundary?
- [ ] Is it under 100 lines (excluding comments)?
- [ ] Does it reflect how you ACTUALLY decide, not how you aspire to?

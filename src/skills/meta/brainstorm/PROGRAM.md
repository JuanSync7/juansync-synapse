# brainstorm — Auto-Research Program

## Objective

Maximize EVAL.md pass rate across all test prompts. Current baseline: 15/20
criteria passing (5 criteria not exercised by clean-path test inputs — the
fragile criteria require adversarial and stress-test prompts to trigger).

## Scoring mode

Numerical

## Metric

Score = number of EVAL.md output criteria (EVAL-O01 through EVAL-O20) that
pass when the subagent simulates skill execution across the test prompts
in EVAL.md's Test Prompts section. Use all 4 categories (Naive, Experienced,
Adversarial, Wrong-tool) — adversarial prompts are required to exercise
EVAL-O03, EVAL-O10, and EVAL-O12.

A criterion passes if the simulated session would produce the artifact or
behavior described in its Pass condition. A criterion scores 0 on crash
(missing frontmatter, execution fence removed, SKILL.md > 500 lines).

## Scoring mechanism

Subagent-executed. Each iteration:
1. Read the modified SKILL.md and all mutable reference files
2. Simulate the skill being executed on 3 representative test prompts:
   one full protocol (Naive/Experienced), one adversarial (early-exit
   pressure or drip-feed trap), one wrong-tool redirect
3. For each simulation, evaluate all applicable EVAL.md criteria
4. Return total passing criteria count (0–20) with per-criterion verdicts

### Correctness guard

Before recording a score, verify:
- SKILL.md frontmatter has all required fields (name, description, domain, intent)
- Execution fence is present
- SKILL.md is under 500 lines

If any guard fails, record as crash and revert — do not score.

## Mutable files

Only modify these — everything else is locked:
- `SKILL.md` — instructions, judgment calls, phase structure
- `references/coaching-policy.md` — coach voice, admission protocol
- `references/moves.md` — move definitions and preconditions
- `references/brainstorm-types.md` — type taxonomy and lens mappings
- `references/lens-catalog.md` — lens definitions and selection table
- `references/wrong-tool-detection.md` — collision points and exclusion rules
- `references/mentor-circuit-breaker.md` — diminishing-returns diagnostic

## Immutable files (DO NOT MODIFY)

- `EVAL.md` — the scoring criteria
- `PROGRAM.md` — this file
- `templates/` — notepad.md, memo.md, meta.yaml
- `SCOPE.md`

## Exploration directions

Try these strategies in priority order:

1. **Enforce notepad-first ordering (EVAL-O12)** — restructure Phase B so
   the notepad write is the explicit first step of each turn; the response
   is composed from what was just written. The current instruction states
   the rule but the agent can satisfy it retroactively. Make the write step
   structurally prior, not just procedurally required.

2. **Auditable lens gate before Agree (EVAL-O03)** — add a required
   confirmation output before the Agree move can fire. The agent must
   produce an explicit line (e.g., "Stakeholder ✓ T[n], Alternative ✓ T[n]
   — gate passes") before issuing Agree. Without this, the precondition is
   unverifiable from session artifacts.

3. **Operational admission protocol trigger (EVAL-O02)** — add a concrete
   decision rule to distinguish first-order concerns (should have been in
   Phase A Opening Inventory) from derived concerns (legitimately emerged
   from thread work). The current protocol states the rule but provides no
   heuristic for when to fire it. Make the trigger operational.

## Constraints

- SKILL.md must stay under 500 lines
- Preserve the execution fence comment
- Keep language imperative and opinionated — no hedging ("consider",
  "you might")
- Do not add tool dependencies the skill doesn't already use
- The 7-shape outcome taxonomy must remain intact (Decision / Plan / Spec /
  Reframe / Decompose / Defer / Abandon)

## Stop conditions

- All 20 EVAL.md criteria pass — success, stop
- 2 consecutive iterations with no score improvement — stop, log in
  changelog.md

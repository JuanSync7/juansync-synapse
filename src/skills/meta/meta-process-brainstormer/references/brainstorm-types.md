# Brainstorm Types

5 types classified in Phase A. Classification is diagnostic — it biases which moves dominate and which lenses fire, but does not restrict. Classification may drift mid-session (see coaching-policy's "Classification Drift Is Permitted").

## The 5 Types

### decision
**Core shape:** The user has candidate options and needs to pick one (or reject them all).

**Diagnostic signals:**
- User names specific options ("X vs Y", "option A or option B")
- Question is "which" or "should I"
- Options exist; pressure-testing them is the work

**Typical outcome shapes:** `Decision` (primary), `Reframe` (if the real question is different), `Defer` (if information is missing).

**Dominant moves:** Pressure-test, Agree, Circle-back.

**Example topics:**
- "Should we use async or sync here?"
- "Rewrite in Rust or keep Python?"
- "Migrate to Postgres or stay on MySQL?"

### exploratory
**Core shape:** The user doesn't know what their options are yet. They need to surface the space before deciding anything.

**Diagnostic signals:**
- Question is "what should I" or "what are my options"
- User describes a goal but no candidate approaches
- Vague or broad framing

**Typical outcome shapes:** `Plan` (after converging on a direction), `Reframe` (if the goal itself shifts), `Decompose` (if the space is too big for one session).

**Dominant moves:** Generate (heavy), Pressure-test (selective), Circle-back.

**Example topics:**
- "What should we work on next quarter?"
- "How should I approach my career pivot?"
- "I have a vague idea for X — help me figure out what it could be."

### problem
**Core shape:** Something is broken or underperforming, and the user needs hypotheses for root cause or fix strategy.

**Diagnostic signals:**
- User describes a symptom ("X is slow", "churn is high", "the metric dropped")
- Question is "why" or "what's wrong"
- Hypotheses are the intermediate output; a decision comes after

**Typical outcome shapes:** `Plan` (fix strategy), `Reframe` (if the symptom is the wrong thing to focus on), `Decompose` (if multiple root causes interact).

**Dominant moves:** Generate (hypotheses), Pressure-test (each hypothesis), Reframe (if the real problem is elsewhere).

**Example topics:**
- "Onboarding churn is high, why?"
- "Why is the build pipeline flaky?"
- "Customers keep asking for X — what's the unmet need underneath?"

### creative
**Core shape:** The user wants to produce something — a piece of writing, a design, a creative artifact — and needs help shaping what it should be before creating it.

**Diagnostic signals:**
- Output is an artifact the user will make (post, design, talk, proposal)
- Question is "what should this be" or "help me shape X"
- Generate-then-prune cycle is required before any structure emerges

**Typical outcome shapes:** `Spec` (structured description of what to build), `Plan` (sections/sequence), `Reframe` (if the artifact's purpose is unclear).

**Dominant moves:** Generate (broad), Pressure-test (prune for audience fit), Decompose (structure).

**Example topics:**
- "Help me draft a blog post on X."
- "I want to design a talk about Y — what are the angles?"
- "Help me shape a proposal for Z."

### planning
**Core shape:** Options are known; the work is sequencing — what order, what dependencies, what to defer, what comes first.

**Diagnostic signals:**
- User has a clear goal and candidate actions; the question is order/dependency
- Question is "how do I tackle X" or "what's the sequence"
- Decomposition and sequencing are the work, not option selection

**Typical outcome shapes:** `Plan` (primary — ordered steps with dependencies), `Decompose` (if the work is too big for one plan).

**Dominant moves:** Decompose (sequencing), Pressure-test (risk in each step), Circle-back.

**Example topics:**
- "How do I migrate us to Postgres step-by-step?"
- "What's the rollout sequence for this feature?"
- "How do I split this work across the team?"

## Classification Diagnostic

If uncertain, ask yourself (or the user) in order:

1. **Does the user have concrete options on the table?** Yes → `decision` or `planning`. No → `exploratory` or `problem` or `creative`.
2. **If yes: is the question which to pick, or what order to do them?** Pick → `decision`. Order → `planning`.
3. **If no: is there a problem to diagnose, or a goal to shape?** Diagnose → `problem`. Shape → `creative` or `exploratory`.
4. **If shaping: is the output an artifact (post, design, talk)?** Yes → `creative`. No (broader direction) → `exploratory`.

## When Types Blur

Some topics sit across two types. Pick the primary based on where the coach's work lies:

- A `decision` that needs options first → `exploratory` until options are on the table, then `decision`. Use `Reframe` move to transition classification.
- A `problem` that turns into a `creative` task once the root cause is clear → start as `problem`, reclassify after root cause is agreed.
- A `planning` topic where the plan turns out to be wrong → `Reframe` to `decision` (or back to `exploratory`).

Classification is not sticky — see coaching-policy for drift handling.

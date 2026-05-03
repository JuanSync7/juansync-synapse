# Wrong-Tool Detection

Run at Phase A start. 5 collision points. If any fires, redirect; do not proceed with this skill.

## Exclusion Is Direction-Based, Not Verb-Based

The trigger for this skill is **lack of clear direction**, not the verb the user uses. A user saying "I want to build a dashboard" with no clear requirements IS a brainstorm candidate. A user saying "think through this" with a fully specified spec is not.

The relevant signal: does the user have a concrete, decided answer to "what are we doing and why"? If yes → not brainstorm, regardless of verb. If no → brainstorm, regardless of verb.

## The 5 Collision Points

### 1. Skill-shaped topic → `/synapse-brainstorm`

**Signals:**
- Mentions "skill," "SKILL.md," "slash command," "Claude command"
- Topic is "I want Claude to always do X" or "I want a command that does Y"
- Topic describes agentic behavior extension

**Action:** Hard redirect: *"This looks skill-shaped. `/synapse-brainstorm` is purpose-built for thinking through new skill ideas — redirecting there."* Do not offer to keep here; the skill-shaped topic needs artifact-aware lenses that this skill does not carry.

### 2. Clear direction already → implementation skill

**Signals:**
- User has a written spec, plan, or design document referenced in the request
- User names concrete requirements and is asking for execution, not deliberation
- Nothing is left to decide; what remains is to build/write/implement

**Action:** Don't fire brainstorm. Suggest the appropriate implementation skill based on the artifact:
- Want a spec written → `/write-spec-docs`
- Want a plan from existing spec → `/build-plan` or `/write-implementation-docs`
- Want to execute → appropriate coding workflow

**Key test:** Ask, "Is there anything the user still needs to decide?" If no, don't brainstorm.

### 3. Factual question with a definite answer → just answer

**Signals:**
- Question has a single correct answer that Claude knows or can look up
- User wants a fact, not a deliberation
- "What is X," "how does Y work," "which library supports Z"

**Action:** Answer directly. Don't wrap a factual question in brainstorm ceremony.

### 4. Specific concrete bug with clear trace → debug directly

**Signals:**
- User has a specific error, stack trace, or reproducible failure
- Question is "why is this broken" with concrete artifacts attached
- Fix is a code change, not a decision

**Exception:** If root cause is architectural (the bug is a symptom of a design problem that requires options-weighing to fix), brainstorm fires on the architectural question. But the specific bug itself is not the brainstorm — the architecture is.

**Action:** Debug the specific bug directly. Only elevate to brainstorm if the *fix strategy* has multiple non-obvious paths.

### 5. End-to-end pipeline request → `/autonomous-orchestrator`

**Signals:**
- User wants brainstorm → spec → code → docs as a single flow
- User asks for a "full feature" or "complete build"
- User references the autonomous pipeline explicitly

**Action:** Redirect to `/autonomous-orchestrator`, which drives the multi-stage pipeline. This skill handles only the interactive brainstorm step.

## When Detection Is Ambiguous

If the user's request sits on the line between two collision points (e.g., "help me build a dashboard" — brainstorm the direction, or implement?):

- **Ask one disambiguating question.** "Do you have a clear direction for the dashboard already (purpose, audience, key metrics), or is the direction itself what you want to work out?"
- **Default to firing brainstorm** if the user hasn't ruled out the deliberation need. It's easier to exit brainstorm quickly (lightweight mode, or early memo) than to rebuild brainstorm context later if the implementation skill discovers direction is missing.

## Mid-Session Re-Detection

Wrong-tool detection is primarily Phase A. But if mid-session the topic clearly transforms into a skill-shaped discussion or a purely implementation question, surface the observation to the user:

> "This has turned into a skill-design question — want to pause here and reopen with `/synapse-brainstorm`, or keep going?"

Don't silently redirect mid-session. Offer.

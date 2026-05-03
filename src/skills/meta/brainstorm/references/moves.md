# Moves

> This file is the detailed reference for Phase B moves. SKILL.md defines the compact node format (Load/Do/Don't/Exit); this file provides voice examples, state effects, and rejected candidates per move.

The 7 moves available during Phase B. All moves are valid "chess moves" at any time — type classification biases which moves dominate in a session but does not restrict them. Each move maps to a `[B:<move>]` node in the flow graph with fully-connected exits.

Every session uses a mix. Circle-back is always available; a final Circle-back is mandatory before Done Signal.

## The 7 Moves

### 1. Generate
**Purpose:** Open up possibility — surface candidate options, hypotheses, angles, or concerns.

**When to use:**
- A thread's option space is empty (user arrived without ideas for this thread)
- Phase A Opening Inventory generation
- Late Phase B when lens rotation reveals a gap that needs options before pressure-testing

**State effect:** Adds items to a thread (no state transition by itself); populates new threads as `open`.

**Voice:** "What if we tried X? Or Y? Or from another angle, Z?"

### 2. Pressure-test
**Purpose:** Evaluate existing options against lenses. The evaluative move.

**When to use:**
- A thread has options; rotate the selected lenses against them
- Always required before a thread can move to `resolved` (see Thread-Resolution Precondition in `coaching-policy.md`)

**State effect:** Does not transition state directly. Outcomes feed into `Agree` (`open → resolved`) or `Reject` via pressure (`open → discarded`). Pressure-test that kills an option = thread closes as `discarded` with reason recorded.

**Voice:** "Stakeholder lens: who's affected by X, and does it serve them? Alternative lens: are we missing Y or Z?"

### 3. Agree
**Purpose:** Explicit convergence. The counterweight to Pressure-test — without `Agree` as a named move, the coach pressure-tests forever.

**When to use:**
- User's reasoning on a thread has survived the required lenses (Stakeholder + Alternative minimum)
- You genuinely concur, not cheerleading

**Precondition:** Both universal lenses (Stakeholder, Alternative) must have been applied to this thread. `Agree` without the lens gate is cheerleader drift — reject it yourself.

**Required gate output:** Before issuing Agree, you MUST produce a visible confirmation line in your response:
> `Stakeholder ✓ T[n], Alternative ✓ T[n] — gate passes`
This line is mandatory — it makes the lens gate auditable. If either lens has not been applied, produce `Stakeholder ✗ T[n]` or `Alternative ✗ T[n]` instead and apply the missing lens before attempting Agree again.

**State effect:** `open → resolved`, reason recorded.

**Voice:** "Stakeholder ✓ T3, Alternative ✓ T3 — gate passes. Your reasoning holds. The Alternative lens didn't surface anything stronger, and the Stakeholder impact is acceptable. Locking T3 as resolved."

### 4. Reframe
**Purpose:** Shift the question itself. Use when you sense the user is asking the wrong question — the real decision is somewhere else.

**When to use:**
- The surface question is a symptom of a deeper question ("should we use Rust or Go?" → "should we rewrite at all?")
- Multiple threads keep colliding because they share a hidden root
- User's framing embeds an assumption that pressure-testing surfaces as invalid

**State effect:** May rewrite existing threads, discard threads that dissolve under the new frame, and spawn new `open` threads. Update `(type, shape)` classification in `meta.yaml` if the reframe changes the session's direction.

**Voice:** "I think we're asking the wrong question. The real question isn't 'Rust vs Go' — it's 'do we rewrite at all?' Want to reframe around that, or is the rewrite decision actually settled?"

### 5. Decompose
**Purpose:** Split a thread that is too big for a single decision. Creates parent-child relationships.

**When to use:**
- A thread keeps generating sub-questions and can't be resolved at its current level
- A topic spans multiple independent decisions that would collide if brainstormed together

**State effect:** `open → decomposed`. The parent thread becomes a container; new child threads are created as `open` and become the real work. The parent cannot reach Done Signal until every child is in a terminal state.

**Voice:** "T5 is actually three decisions in a trench coat. Let me split it: T5a (auth model), T5b (session storage), T5c (token rotation). We'll work them separately."

### 6. Circle-back
**Purpose:** Procedural sweep — walk the notepad thread-by-thread and confirm status. Forces every `open` thread toward a terminal state before ending.

**When to use:**
- Anytime thread-tracking feels cloudy (after long Generate burst, after Decompose spawned children, mid-session drift)
- **MANDATORY** before Done Signal — final Circle-back walks every thread explicitly

**State effect:** Does not transition state directly, but surfaces threads that need attention. Result is that every `open` thread must be resolved, discarded, deferred, or decomposed before the session can end.

**Voice:** "Let me circle back — T1 resolved, T2 discarded (reason: T5 superseded), T3 deferred (waiting on user's profiling data), T4 decomposed into T4a/T4b. T6 is still open — what's your take there?"

### 7. Pause
**Purpose:** Suspend the session cleanly when the mentor circuit breaker fires. Makes "continue tomorrow" possible.

**When to use:**
- Two consecutive lens passes have surfaced no new concerns AND threads aren't ready to close (user needs time or external input)
- Session has grown long and cognitive load is dropping the quality of responses
- User shows signs of decision fatigue

**State effect:** `meta.yaml` status transitions from `active` to `paused`. Notepad saved as-is. Session ends without memo. Resume flow on next invocation picks up where we left off.

**Voice:** "We've worked this for a while. T5 and T7 are at a point where sleeping on them would probably surface more than pushing through tonight. Want to pause and resume tomorrow? I'll save the notepad."

See `mentor-circuit-breaker.md` for the full pause protocol.

## Side-quest Protocol

When a user raises a tangential concern mid-thread, [B:Generate] opens it as a new thread with the turn number noted in the notepad. The agent records it in Zone 2 and returns to the prior move. Side-quests are not interruptions — they are new threads with a parent context. The many-to-many transitions between moves handle this naturally.

## Multi-move Turns

The agent may traverse multiple move-nodes in one turn. For example, the user says "Yeah T4 is settled, and actually that makes me wonder about versioning" — the agent:
1. Enters [B:Agree] — checks lens gate, locks T4 as resolved
2. Enters [B:Generate] — opens T5 (versioning) as a new thread

Record the **landing position** after all moves in that turn are complete. The notepad captures all state changes from all moves made in the turn — not just the last one.

## Move Vocabulary — Quick Map

| Common activity | Named move |
|---|---|
| Listing options, surfacing concerns | Generate |
| Challenging, applying lenses, stress-testing | Pressure-test |
| Ratifying, conceding, locking in | Agree |
| Shifting the question, changing the frame | Reframe |
| Splitting, breaking down | Decompose |
| Sweeping, reviewing state | Circle-back |
| Saving state, suspending | Pause |

## Rejected Candidates (Not Moves)

The following were considered and rejected as distinct moves; they fold into existing moves:

- **Reject/Kill** → fold into Pressure-test outcome (`open → discarded`)
- **Handoff to sibling skill** → Phase A wrong-tool detection, not a Phase B move
- **Prioritize** → implicit in coach's thread-picking, not a discrete action
- **Connect** → notepad operation (Connections section), not a first-class move
- **Clarify / Summarize / Observe** → tactics within other moves, not standalone

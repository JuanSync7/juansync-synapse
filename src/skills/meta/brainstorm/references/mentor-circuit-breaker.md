# Mentor Circuit Breaker

The mechanism that makes "enough for today — pick up tomorrow" possible. Without this, brainstorm sessions spiral indefinitely. The circuit breaker has two parts: a **diagnostic** (when to fire) and an **action** (the `Pause` move).

## Diagnostic: Sensing Diminishing Returns

No hardcoded thresholds. The coach uses judgment on these signals:

- **Lens pass silence** — two consecutive lens passes against `open` threads surfaced no new concerns. The threads are either resolved (hit Done Signal conditions) or the coach is unable to see more gaps from this angle.
- **Thread reopening without progress** — the same threads keep reopening (e.g., user raises a concern, you pressure-test it, user accepts, then a turn later the same concern resurfaces). Diminishing progress per turn.
- **Response quality decay** — your own responses are getting shorter, more hedging, or repeating prior points. You're running low on fresh angles.
- **User fatigue signals** — terse replies, "idk whatever you think," decreasing engagement, time-of-day cues if mentioned. User is not bringing fresh input.
- **Stuck on one thread** — N turns on a single thread without state change. Something is missing (external info, time to reflect, stakeholder input).

These are judgment calls. The point is not to fire automatically but to **notice** when you've stopped being useful.

## Action: The Pause Move

When the diagnostic fires, don't just "keep trying." Surface the observation to the user and let them decide:

> "Feels like we're circling on T5 without new signal. Options: (a) I'm missing an angle and you can help me find it; (b) we genuinely need external input (sleep, data, another person); (c) we're done enough on T5 and should mark it `deferred` and move on. Your call."

This is a Pause offer, not an automatic Pause. User may say:
- **(a) New angle** — coach tries again, potentially with a Reframe
- **(b) Need external input** — the thread moves to `deferred` with conditions noted; session can continue on other threads or Pause entirely
- **(c) Mark deferred and move on** — thread closes as `deferred`, session continues

## When to Pause the Whole Session

If **multiple** threads are hitting the circuit breaker, or if the user explicitly says they're done for now, execute a full `Pause` of the session:

1. **Final notepad update** — record every thread's current status, including any threads mid-Pressure-test
2. **Update `meta.yaml`** — `status: paused`, `last_updated` to current date
3. **Write a clean handoff line** in your response:

> "Paused. Notepad saved at `<path>`. Threads still open: T3 (needs profiling data), T7 (needs input from Sarah). When you're ready, invoke `/brainstorm` and I'll offer to resume."

4. **Do NOT produce the memo** — Pause is a suspend, not a completion. The memo is only produced at Done Signal.

## User-Triggered Pause

User may ask to pause directly — "let's pick this up tomorrow," "I need to think," "stopping here." Respect the request immediately. Execute the same 4-step Pause protocol above.

## Resume Flow (Next Session)

On next invocation of `/brainstorm`:

1. Scan the persistence directory for sessions with `status: paused`
2. If a slug match exists with the new topic, offer resume explicitly:

> "Existing brainstorm on `<topic>` from `<date>`, paused. Open threads: T3, T7. Resume, or start fresh?"

3. If resuming, read the full notepad before composing the next response. Re-establish context. Do not start "clean."

## Never Pause to Avoid Work

Pause is a legitimate move when signal is genuinely diminishing. It is **not** an escape from a hard thread the coach doesn't want to pressure-test.

Self-diagnostic before firing Pause:

- "Am I pausing because the signal is genuinely low, or because this thread is uncomfortable?"
- "Have I actually rotated the selected lenses against the problem thread, or am I pausing before the work is done?"

If the answer is "avoiding work," don't pause. Do the work.

## Pushback Budget

A companion rule for the coach's honest-disagreement voice (see coaching-policy's "Rationality Over Agreeableness"):

- You challenge user reasoning freely.
- If user explicitly overrides your challenge with reasoning you find adequate, concede and remember — do not re-raise the same point later.
- If user overrides without reasoning that convinces you, you may flag it once more with new angle; after that, defer.

"Pushback budget" prevents the coach from becoming adversarial through repeated re-opening of the same challenge. It also prevents the coach from caving silently — disagree clearly, hear the response, concede or defer explicitly, note the resolution in the notepad.

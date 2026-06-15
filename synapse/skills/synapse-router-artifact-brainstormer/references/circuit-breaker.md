# Circuit Breaker

Senses diminishing returns during [B] lens rotation. Without this, brainstorm sessions grind past the point of usefulness — the coach keeps rotating lenses mechanically when signal has stopped. Two parts: a **diagnostic** (when to fire) and an **action** (what to do).

---

## Diagnostic: Sensing Diminishing Returns

No hardcoded thresholds. Use judgment on these signals:

- **Lens pass silence** — two consecutive lens passes across any artifact surfaced no new concerns. The artifacts are either resolved or the coach can't see more gaps from this angle.
- **Stuck Open sections** — an artifact's Open section has items unchanged for 3+ turns. Something is missing (external info, time to reflect, stakeholder input).
- **User fatigue signals** — terse replies, "idk whatever you think," decreasing engagement. User is not bringing fresh input.
- **Response quality decay** — your own responses are getting shorter, more hedging, or repeating prior points. Running low on fresh angles.
- **Thread reopening without progress** — the same concern keeps resurfacing after being addressed. Diminishing progress per turn.

These are judgment calls. The point is not to fire automatically but to **notice** when you've stopped being useful.

---

## Action: Surface and Offer

When the diagnostic fires, don't just keep grinding. Surface the observation to the user:

> "Feels like we're circling on [artifact/concern] without new signal. Options: (a) I'm missing an angle and you can help me find it; (b) we need external input (sleep, data, another person); (c) this is resolved enough — mark it and move on. Your call."

User may respond:
- **(a) New angle** — coach tries again, potentially reframing the question
- **(b) Need external input** — mark the artifact's Open items as `deferred (awaiting: <what>)`, continue with other artifacts or Pause session
- **(c) Mark and move on** — move items to Resolved (not fleshed), continue rotation

---

## Session-Level Pause

If **multiple** artifacts are hitting the circuit breaker, or user explicitly wants to stop:

1. Final notepad update — record every artifact's current state
2. Update `meta.yaml` — `status: paused`, `position` to current node
3. Surface what's still open:

> "Paused. Notepad saved. Artifacts still open: [list with what each needs]. Resume with `/synapse-router-artifact-brainstormer` when ready."

4. Do NOT produce memos — Pause is a suspend, not a completion

---

## Never Pause to Avoid Work

Pause is legitimate when signal is genuinely diminishing. It is **not** an escape from a hard artifact the coach doesn't want to pressure-test.

Self-diagnostic before firing:

- "Am I pausing because signal is genuinely low, or because this artifact is uncomfortable?"
- "Have I actually rotated all scheduled lenses, or am I pausing before the work is done?"

If the answer is "avoiding work," don't pause. Do the work.

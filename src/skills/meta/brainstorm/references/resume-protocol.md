# Resume Protocol

Procedure for resuming a paused brainstorm session. Loaded at [RESUME].

---

## Procedure

1. **Read meta.yaml** — check `status`, `position`, `type`, `shape`
2. **Read notepad fresh** — full read, not skimming. Re-establish thread states, lens rotation progress, and open items.
3. **Determine resume point from position:**
   - Position starts with `[A]` → resume at [A], continue discovery
   - Position starts with `[B:]` → resume at the recorded move node, continue lens rotation
   - Position starts with `[D]` → resume at [D], re-run done signal checks
4. **Offer resume to user:**

> "Existing session on `<topic>` from `<date>`, paused at `<position>`. Open threads: <list>. Resume, or start fresh?"

5. If resuming, compose first response from notepad state — do not start "clean"
6. If starting fresh, create new session directory with new slug

---

## Why This Exists

Without explicit resume, the agent either:
- Tries to reconstruct context from memory (unreliable after context window reset)
- Starts over, losing all prior work

The notepad + meta.yaml ARE the resume state. Reading them fresh is the protocol.

---

## Legacy Notepads

If the notepad uses the old flat format (has `## Threads (indexed)` instead of Zone 2 sections), regenerate to the two-zone format on resume. Migrate thread content to Zone 2 per-thread sections.

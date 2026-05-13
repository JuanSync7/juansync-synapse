# Hygiene Check

Quick 1-turn scan to combat context window attention decay. Loaded at [H] on ~10 turn cadence. This is NOT a full lens rotation — it's a focused refresh of accumulated state.

---

## Procedure

1. **Read the notepad** — full read, not skimming
2. **Scan for stale open points** — items marked Open that have actually been resolved in discussion but not updated in the notepad
3. **Check for forgotten artifacts** — are there artifacts discussed in conversation but missing from the Artifacts Discovered table?
4. **Check for drifted threads** — have any decisions been implicitly contradicted by later discussion? A decision made 20 turns ago may have been superseded without the notepad reflecting it
5. **Verify artifact table matches discussion state** — are lens-complete flags accurate? Are artifact types still correct?
6. **Quick summary** — what's stale, what's forgotten, what's drifted

---

## Why This Exists

Context window attention decays over turns. Information from 30 turns ago receives less attention weight than recent turns. Decisions made early in a session may have been implicitly contradicted, refined, or superseded by later discussion without anyone noticing.

Hygiene refreshes the agent's awareness of accumulated state by forcing a deliberate re-read.

---

## Cadence

- **During [B] rotation:** ~every 10 turns sets a flag. On the next user reply, process the reply normally (update notepad, note findings), then run [H] before composing the next coaching response. Never interrupt mid-exchange — finish the current turn's work first, then checkpoint.
- **Before Done Signal:** Mandatory final hygiene check (part of Done Signal checklist)

---

## Duration

1 turn. If major issues surface (stale decisions, forgotten artifacts, contradictions), they route back to [B] for focused attention. Hygiene identifies problems; it doesn't fix them.

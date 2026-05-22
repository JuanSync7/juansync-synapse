# Resume Protocol

Loaded at [RESUME] when re-entering a paused brainstorm session. The goal is to reconstruct context from persistent state without assuming anything survived from the previous conversation.

---

## Procedure

### 1. Read meta.yaml for Machine State

- `status`: should be `paused` (if `done`, inform user the session is already complete)
- `position`: which node was last active + context string (e.g., `[B] — lens-robustness on artifact-3`)
- `artifacts`: list with `lens_complete` flags per artifact
- `artifacts_discovered`: count for quick sanity check against notepad

### 2. Read Notepad for Thread Context

- **Zone 1 (session-level):** Check Open/Orphaned for pending items
- **Zone 2 (per-artifact):** Check per-artifact Open sections for pending items
- **Process section:** Review recent entries for context on where discussion left off

### 3. Determine Resume Node

| Position contains | Resume at | Notes |
|---|---|---|
| `[A]` | [A] | Discovery phase — continue inventory |
| `[B]` | [B] | Check which artifact + lens was active |
| `[D]` | [D] | Re-run Done Signal checklist |
| `[N]` | [N] | Resume artifact focus for the specific artifact |

### 4. Always Re-Read Both Files Fresh

Do not assume previous context survived. meta.yaml gives machine state; notepad gives human-readable thread context. The two together reconstruct the session.

### 5. Handle Missing or Corrupt State

- **meta.yaml missing or corrupt:** Treat as [NEW]. Create fresh meta.yaml from notepad state if notepad exists, or start entirely fresh.
- **Notepad missing:** Treat as [NEW]. A session without a notepad has no recoverable state.
- **Both exist but conflict:** Trust meta.yaml for position, trust notepad for content. Flag the inconsistency to the user.

### 6. Brief the User

Summarize: what was in progress, what's resolved, what's open. Ask if they want to continue from where they left off or adjust direction.

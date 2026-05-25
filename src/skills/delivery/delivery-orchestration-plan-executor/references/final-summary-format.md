# final-summary-format

Loaded at `[TERMINATION]`. Defines the structure of the inline summary the skill emits when the loop exits. The summary is the user's primary handoff artifact — it must be scannable in under 30 seconds and complete enough that a fresh session can resume without re-reading the closeout trail.

## Format (verbatim shape)

```markdown
## Run summary — <ISO-date> — <plan-source-pointer>

**Exit reason:** `all_slices_green` | `escalated_blocked` | `escalated_replan_cap` | `user_interrupt`

### Slice rollup

| Status | Count |
|---|---|
| green (pass) | N |
| blocked | N |
| superseded | N |
| undispatched | N |
| **total** | N |

### Slice detail

| Slice ID | Status | Attempts | Outcome test | Note |
|---|---|---|---|---|
| <id> | green | <n> | <path> | — |
| <id> | blocked | 2 | — | <blocked_reason from last closeout> |
| <id> | superseded | <n> | — | superseded by <id> at <CHANGELOG ref> |

### Lessons tail (last 5–10)

- <verbatim lesson string from .delivery/lessons.md, most recent N>
- ...

### Pointers

- Plan: `.delivery/plan/INDEX.md`
- Closeouts: `.delivery/closeouts/`
- Lessons (full): `.delivery/lessons.md`
- Audit log: `.delivery/plan/CHANGELOG.md`

### Next move

<one sentence — what the user should do based on exit reason>
```

## Field semantics

| Field | Required | Source | Notes |
|---|---|---|---|
| Exit reason | Always | Stop condition that fired in `[REPLAN]` or `[TERMINATION]` | Pick exactly one from the enum; never invent new values |
| Slice rollup counts | Always | INDEX.md status walk | Sum of statuses must equal `total`; `total` must equal INDEX.md slice count |
| Slice detail | Always | INDEX.md + last closeout per slice | Include every slice, even undispatched — omission hides plan reality |
| Lessons tail | If lessons.md non-empty | Tail of `.delivery/lessons.md` | 5 minimum, 10 maximum; verbatim — no rephrasing |
| Pointers | Always | Static paths | The user uses these to resume; missing pointers break resumability |
| Next move | Always | Derived from exit reason | One sentence; not a paragraph |

## Exit-reason → next-move mapping

| Exit reason | Suggested next move |
|---|---|
| `all_slices_green` | "Review the diff and merge — all slices closed green." |
| `escalated_blocked` | "Inspect the blocked slice(s) in INDEX.md and the last closeout; decide whether to re-frame the slice or unblock the dependency." |
| `escalated_replan_cap` | "Plan likely misframed — return to `/write-story` or `/build-plan` to re-shape before re-running." |
| `user_interrupt` | "Resume by invoking this skill again — the closeout trail will pick up at the next un-closed slice." |

## What NOT to do in the final summary

- Do not emit free-form prose conclusions ("the run went well overall...") — the rollup speaks for itself.
- Do not summarize lessons — quote the tail verbatim. Summarization is the next session's job.
- Do not include subagent stdout/stderr — that lives in closeouts, linked via the pointer.
- Do not propose retries or auto-rerun — the user owns the next move.

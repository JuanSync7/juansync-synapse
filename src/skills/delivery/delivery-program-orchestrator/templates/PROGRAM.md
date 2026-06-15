---
program_name: "<one-line program description>"
program_started: "<ISO-date>"
program_ended: null
customer_seat: open  # open | paused | closed
current_node: "[INTAKE]"
pipeline_shape: null  # vertical | horizontal
entry_stage: null     # spec | arch | scope | plan
routing_rule: null    # R1 | R2 | ... | R8 from pipeline-routing.md
selected_tag: null
paused_at_node: null
paused_at: null
exit_reason: null     # merge | done | abort | paused | horizontal-handoff
artifacts:
  spec: null          # path/to/SPEC.md when written
  architecture: null
  scope: null
  stories: null       # path/to/STORIES.md when written
---

# Program — <program_name>

## Customer input — <ISO-date>

<verbatim customer thought-dump captured at [INTAKE]>

## Captured intent

(populated during [Q] discovery; one row per minimum-schema field)

- **problem:** <one sentence>
- **in-scope:** <list>
- **out-of-scope:** <list>
- **constraints:** <list>

## Gate history

| ISO-date | stage-id | event | writer-skill | note |
|---|---|---|---|---|
| <date> | [INTAKE] | start | — | program seeded |

(Two rows per gate cycle: `emit` then `approve`/`revise`/`pause`/`abort`. Walked by [RESUME] to reconstruct state. Append-only — never edit or delete a row.)

## Routing notes

(Any non-trivial routing decisions, drift detections, or conflict resolutions surfaced during the program. One entry per event, dated.)

## Run pointers

(Populated at [EXEC] / [HANDOFF])

- Plan: `.delivery/plan/INDEX.md`
- Stories: `.delivery/stories/STORIES.md`
- Closeouts: `.delivery/closeouts/`
- Lessons: `.delivery/lessons.md`
- Audit log: `.delivery/plan/CHANGELOG.md`

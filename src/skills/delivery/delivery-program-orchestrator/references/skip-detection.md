# Skip Detection (Point-of-Emit at [RESUME] and every *-GATE)

Loaded at `[RESUME]` and at every gate's idempotency check. Decides when a gate can be skipped because its artifact already exists, and when filesystem drift requires demotion back to the writer.

## The two checks

**1. Idempotency check** (every gate entry): Is the writer's target artifact already on disk? If yes AND its content was not invalidated by an upstream revise, skip the invoke and go straight to gate presentation. This makes the orchestrator restart-safe — a customer can re-invoke /delivery-program-orchestrator any time without re-running already-completed writer turns.

**2. Drift check** ([RESUME] only): For every gate the PROGRAM.md audit trail says was `approve`d, is the artifact still on disk? If not, the program drifted (file deleted, moved, or never written) — demote that gate back to its writer node.

## Idempotency table (per gate)

| Gate | Skip-invoke when | Re-invoke when |
|---|---|---|
| `[SPEC-GATE]` | `SPEC.md` exists at the search path (project root or `docs/`) | absent, OR PROGRAM.md last decision was `revise` and no newer `SPEC.md` mtime than the revise event |
| `[ARCH-GATE]` | `architecture.md` exists AND its `foundations:` frontmatter is non-empty | absent, OR `foundations:` empty, OR revise pending |
| `[SCOPE-GATE]` | `scope.md` exists AND defines ≥1 phase with a TAG | absent, OR no TAG-bearing phase, OR revise pending |
| `[PLAN-GATE]` | `.delivery/stories/STORIES.md` exists AND its frontmatter `tag:` equals PROGRAM.md `selected_tag` | absent, OR tag mismatch, OR revise pending |
| `[EXEC]` | (no skip — executor is invoked every entry to [EXEC]; executor itself handles closeout-trail resume) | always invoke |
| `[HANDOFF]` | (no skip — handoff is presented every time [EXEC] returns) | always present |

Tag mismatch at [PLAN-GATE] is special: it means the program is already mid-plan on a different TAG. Do NOT silently overwrite — halt loud:

```
HALT — STORIES.md found with tag=<X>, but PROGRAM.md selected_tag=<Y>.
Either:
  (a) reply `approve --tag X` to switch this program to the in-progress plan
  (b) move .delivery/stories/ aside and reply `revise` to plan tag=Y fresh
```

## Drift check (at [RESUME])

Walk the PROGRAM.md gate-history table in order. For each row with `event: approve`:

| Stage | Drift signal | Action |
|---|---|---|
| `[SPEC-GATE]` | `SPEC.md` missing | demote `current_node` to `[SPEC-GATE]`; append PROGRAM.md note "drift: SPEC.md missing on resume" |
| `[ARCH-GATE]` | `architecture.md` missing | demote to `[ARCH-GATE]`; note |
| `[SCOPE-GATE]` | `scope.md` missing OR no longer contains `selected_tag` | demote to `[SCOPE-GATE]`; note |
| `[PLAN-GATE]` | `STORIES.md` missing OR `tag:` doesn't match `selected_tag` | demote to `[PLAN-GATE]`; note |
| `[EXEC]` | `.delivery/plan/INDEX.md` missing | demote to `[PLAN-GATE]` (plan must be re-shaped before re-execute); note |

After drift detection, surface the demotion to the customer with the specific missing artifact named — do not re-emit the gate block silently, the customer needs to know state was lost.

## What this reference does NOT do

- It does not validate artifact content beyond presence + the single load-bearing field per stage (`foundations:` for arch, TAG for scope, tag-match for stories). Deep validation belongs to the writer that owns the artifact.
- It does not auto-restore deleted artifacts. Drift = halt + surface. The customer (or the writer on re-invoke) restores.
- It does not skip [EXEC] or [HANDOFF] — those nodes own their own idempotency via PROGRAM.md state and the executor's closeout trail.

## Failure mode if skipped

Without idempotency check: re-entering the orchestrator after a partial run re-invokes the spec-writer, which prompts the customer again, who is confused that their already-approved SPEC.md is being re-litigated. The customer loses trust in the orchestrator's state model and starts working around it.

Without drift check: resume picks up at `[EXEC]` but `STORIES.md` was moved aside; plan-executor pre-flight fails with a cryptic error. The customer sees an executor error instead of an orchestrator note explaining what happened.

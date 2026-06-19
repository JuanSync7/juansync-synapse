# Parallel Phase Review Model

Loaded at `[HANDOFF]`. This is the review discipline the executor follows when running the plan's parallel phases. Sequential tasks (single-agent execution) use a per-task review loop; parallel phases use the phase-gate model below.

## Phase Gate Rule

Before any phase can start, ALL agents from the previous phase must be:
1. Complete (returned a result)
2. Reviewed (spec compliance confirmed)
3. Approved (no open issues)

A single unapproved agent blocks the entire next phase. Fix the issue before proceeding.

## Per-Agent Review (runs as agents complete)

As each parallel agent finishes, dispatch its spec compliance reviewer immediately — do not wait for other agents. Reviews run in parallel with remaining agents.

**Review weight by phase:**

| Phase | Review type | What to check |
|---|---|---|
| Phase A (spec tests) | Spec compliance only | All FR numbers covered? Each test tagged with FR? Tests expected to FAIL? |
| Phase B (implementation) | Full two-stage: spec compliance + code quality | Spec: all FRs implemented, nothing extra. Quality: clean code, TDD followed, tests pass. |
| Phase C-parallel (module docs) | Spec compliance only | All 6 sub-sections present? Error behavior documented? Test guide has boundary conditions? |
| Phase D (white-box tests) | Spec compliance only | Tests derived from guide's Error behavior + Test guide sub-sections? Known gaps noted? Tests FAIL? |

## Review Loop Per Agent

For each parallel agent:
1. Agent completes → dispatch spec reviewer immediately
2. If ❌ Issues: re-dispatch the same agent to fix, then re-review
3. If ✅ Approved (spec): for Phase B only, dispatch code quality reviewer
4. If ✅ Approved (quality): mark agent done
5. Record agent as approved in the phase gate tracker

## Phase Gate Tracker

Maintain a simple checklist after dispatching each parallel phase:

```markdown
Phase A gate — all must be ✅ before Phase B starts:
- [ ] Task A-1: spec review ✅
- [ ] Task A-2: spec review ✅
- [ ] Task A-3: spec review ✅
```

Do not advance to the next phase until all boxes are checked.

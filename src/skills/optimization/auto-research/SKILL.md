---
name: auto-research
description: "Use when asked to autonomously improve a skill or artifact through repeated experimentation, or to set up an automated improvement loop. Triggered by 'auto-research', 'optimize this overnight', 'run autonomous improvement'."
domain: optimization
intent: improve
tags: [auto-research, experiment-loop, optimization]
user-invocable: true
argument-hint: "setup [target path] | run [path to PROGRAM.md]"
---

# Auto-Research

Runs autonomous iterative improvement on any target with a scorable metric — skills, code, prompts, configs, Dockerfiles, documents. The agent modifies a mutable target, scores it against an immutable metric, keeps improvements, reverts regressions, and repeats until a stop condition is met.

**Two roles, one skill.** Auto-research in run mode is architecturally split into an **orchestrator** (the main agent — reads state, picks strategies, logs results, decides when to checkpoint and when to stop) and an **iteration subagent** (dispatched via the `Task` tool once per iteration — makes one focused change, commits, scores, returns a structured result). Keeping them separate is what makes the loop robust over long runs: the subagent has no stale context to drift from, and the orchestrator has no ambient edit state to worry about.

## Mental model

The current loop is not random — it's **under-scaffolded**. A single-context loop at iteration 15+ has accumulated compacted state, stale file readings, and rationalized prior decisions; it pattern-matches the first plausible next move and cross-checks nothing. The fix is grounding, not creativity constraints. Grounding comes for free when each iteration runs in a fresh subagent that can only see what the orchestrator passes it: PROGRAM.md, a baseline snapshot, a diff from that baseline, and the last few `iterations.tsv` rows. There is no ambient context to drift from, because there is no ambient context.

## Wrong-Tool Detection

Reframe by **task shape**, not whether the target is a skill:

- **User wants a one-shot structural pass on an existing skill** (not an iterative loop) → redirect to `/improve-skill`
- **User wants to build a new skill from scratch** → redirect to `/skill-creator`
- **User wants to generate an EVAL.md for an existing skill** → redirect to `/write-skill-eval`
- **User wants to find a root cause or fix a specific bug** → this is debugging, not optimization; auto-research is the wrong shape
- **User has no scorable metric and no way to compare "better"** → auto-research can't help; try to surface a dimension with them, or route them elsewhere

## Progress Tracking

At the start, create a task list based on the mode:

**Setup mode:**
```
TaskCreate: "Understand the target"
TaskCreate: "Define metric and scoring mode"
TaskCreate: "Identify or build scoring mechanism"
TaskCreate: "Draw mutable/immutable boundary"
TaskCreate: "Get optimization strategy and constraints"
TaskCreate: "Define stop conditions"
TaskCreate: "Generate and approve PROGRAM.md"
```

**Run mode:**
```
TaskCreate: "Pre-flight checks + baseline cache"
TaskCreate: "Orchestrator loop (dispatch subagents)"
TaskCreate: "Write changelog and report"
```

Mark each task `in_progress` when starting, `completed` when done.

## Scope boundaries

Auto-research handles autonomous iterative improvement with a measurable metric or A/B-judgeable dimension. It does NOT handle:
- **One-shot structural fixes on a skill** — use `/improve-skill`
- **Greenfield creation** — use `/skill-creator`
- **Debugging / root-cause analysis** — optimization is the wrong shape
- **Targets with no scorable metric and no comparison dimensions** — if you can't measure or compare "better," the loop has no signal

## Two modes

| Mode | Trigger | Input | Output |
|------|---------|-------|--------|
| **Setup** | `auto-research setup [target path]` | A goal and the user's domain knowledge | PROGRAM.md ready for `run` mode |
| **Run** | `auto-research run [path to PROGRAM.md]` | A valid PROGRAM.md | Improved target + research/iterations.tsv + research/changelog.md |

---

## Mode: Setup

A structured conversation that produces a valid PROGRAM.md. The user brings the goal and optimization strategy. The agent brings the format and quality control.

**Principle: ask, don't suggest.** Never generate exploration directions, constraints, or strategies for the user. Prompt them to think, then structure their answers into PROGRAM.md format. The user does the reasoning — the agent does the structuring.

### Setup short-circuit: PROGRAM.md already exists

**Before walking through Steps 1–7, check whether PROGRAM.md already exists in the target directory.** If it does, do not re-elicit everything — the user almost certainly doesn't want to redo setup. Instead, read the existing PROGRAM.md and offer three paths:

1. **Review** — summarize the existing PROGRAM.md (objective, metric, mutable set, exploration directions, stop conditions) and ask "is this still accurate?"
2. **Edit** — let the user point at specific sections to update (e.g., "add a new exploration direction"); do not touch sections they didn't mention
3. **Run** — jump straight to `auto-research run [path]`, skipping setup entirely

Only if the user explicitly asks to start over should you walk through Steps 1–7 again. Overwriting a working PROGRAM.md blindly is a destructive action.

### Step 1: Understand the target

Ask:

- "What are you trying to improve?"
- "What does a *bad* output look like today? What's wrong with it?"
- "If I improved one thing overnight, what would you check first tomorrow morning?"

Capture: the mutable target path and a concrete description of what "better" means.

**Safety gate:** If the optimization goal is destructive — the user wants to optimize toward system crashes, data loss, resource exhaustion, or any outcome that intentionally causes harm — refuse. Auto-research optimizes constructively. "Find the point where it breaks" is load testing or fuzzing, not iterative improvement. Route the user to appropriate tooling instead.

### Step 2: Classify scoring mode and define the metric

First, classify the target's output determinism — this determines the scoring approach:

| Output type | Scoring mode | Examples |
|-------------|-------------|----------|
| **Deterministic** — same input always produces comparable output | **Numerical** — absolute metrics (N/M, seconds, bytes, pass count) | Test suites, build times, Docker image size, binary size, benchmark latencies, binary criteria counts |
| **Semi-deterministic** — output varies per run or requires judgment to evaluate | **Comparative** — A/B preference by LLM judge | Skill quality beyond EVAL.md ceiling, code style / logging quality, document conciseness, error message clarity |

**Comparative is the default when judgment is involved.** For objective dimensions (bytes, seconds, count), numerical is simpler and cheaper.

Then define the metric based on the mode:

**For numerical mode**, ask:
- "How would you know if I made it worse?"
- "What's the number — and what are the units?"
- "Is there a baseline value you know today?"

A valid numerical metric must be: scorable by an agent without human review, producing a concrete number, and able to distinguish "better" from "same" from "worse."

**For comparative mode**, ask:
- "What specific dimensions should I compare when judging version A vs version B?"
- "Which dimensions matter most? Rank them."

A valid comparative metric must define: concrete comparison dimensions (not "overall quality"), a priority ranking of those dimensions, and what "better" looks like for each dimension.

**Good numerical metric:** "API image size in MB, targeting <500 MB from 1400 MB baseline" — concrete number, clear units, baseline and target.
**Good numerical metric:** "5/8 EVAL.md criteria passing, targeting 8/8" — gradient, scorable, concrete target.
**Good comparative metric:** "Compare on: (1) error message specificity, (2) log level correctness, (3) coverage across functions — prioritized in that order."
**Bad metric (either mode):** "the output should be better quality" — subjective, no dimensions, no target.

**Quality gate:** If the user's metric is purely binary ("it passes or fails"), push back — that's a gate, not a gradient. If the user's metric is subjective without dimensions ("it should feel better"), push back — decompose into concrete dimensions the agent can evaluate.

### Step 3: Identify the scoring mechanism

The metric needs something that runs it. Treat these as **equally-valid mechanisms** — pick whichever fits the target. Do not default to EVAL.md.

| Mechanism | When it fits | Example |
|---|---|---|
| **EVAL.md + blind tester** | Target is a skill with an existing EVAL.md | `/write-skill-eval` output |
| **Test suite** | Target has existing tests with a countable pass/fail | `pytest -q \| grep passed` |
| **Benchmark script** | Target has a timing, size, or measured-dimension metric | `./score.sh` that runs `hyperfine`, `docker image inspect`, or a `curl \| jq` probe |
| **LLM judge (comparative)** | Target needs A/B comparison on defined dimensions | Judge prompt with randomized ordering, run inside the agent |

Ask:
- "Does a scoring mechanism already exist in the target repo?"
- "If yes, can you point me at the exact command to run it?"
- "If no, we'll build one in Step 3b."

**If a mechanism exists**, verify it runs on baseline right now (execute it once and confirm it produces a number or verdict). Record the invocation and the output parser in PROGRAM.md.

**If no mechanism exists**, proceed to Step 3b.

> **Read [`references/scorer-patterns.md`](references/scorer-patterns.md)** for the four scorer archetypes (timing/benchmark, counted tests, measured dimension, comparative LLM judge) and correctness-guard patterns.

### Step 3b: Build a scorer from scratch (conversational fallback)

Use this step when the user has a target but no existing way to score it. Walk them through five questions in order — each answer feeds the next:

1. **Input shape.** "What does the target consume? One file? A directory? A running service? A prompt?"
2. **Dimension.** "What single number or judgment captures 'better' for this target? Bytes, seconds, pass count, a ranked A/B comparison on three dimensions?"
3. **Archetype selection.** Match the dimension to one of the four archetypes in `references/scorer-patterns.md`:
   - Timing → Archetype 1 (benchmark)
   - Counted pass/fail → Archetype 2 (counted tests)
   - Measured dimension (size, latency, count) → Archetype 3 (measured dimension)
   - Judgment call → Archetype 4 (comparative LLM judge)
4. **Write the scorer.** Create a file in the target directory (`scorer.sh`, `score.py`, `eval.sh` — whatever fits). Include a **correctness guard** alongside the metric — a probe that fails the iteration when the metric looks good but the target is broken. See `scorer-patterns.md` for guard examples.
5. **Verify on baseline.** Run the scorer once on the current state. It must produce a concrete number or verdict, the guard must pass, and it must run fast enough that calling it once per iteration is tolerable. If any of these fails, fix the scorer now — not in run mode.

Record the scorer file path in PROGRAM.md's immutable files list. The subagent must not modify it during the loop.

**Quality gate:** If you cannot produce a scorer that runs cleanly on baseline, stop setup. Auto-research cannot run without a working scorer.

### Step 4: Draw the mutable/immutable boundary

Ask:

- "Which files should I modify? List them."
- "What should I absolutely not touch?"
- "Are any files mixed — part of them should be off-limits even though the file is mutable?" (This is partial-file immutability — see `references/program-format.md`.)

**Quality gate:** If the mutable set is large (>5 files), push back:

- "You have [N] mutable files — which 3 have the most impact on your metric? Start narrow and expand later."

**Good mutable list:** `SKILL.md`, `templates/report.md`, `containers/Dockerfile.api` — specific paths.
**Good partial-file declaration:** "`pyproject.toml` is mutable in `[project.optional-dependencies]` and `[tool.*]`, immutable in `[project.dependencies]`."
**Bad mutable list:** "the main code files" or "whatever needs changing" — vague, unbounded.

### Step 5: Get the optimization strategy

Ask:

- "What strategies should I try? List them in priority order."
- "What have you already tried that didn't work? I'll avoid those."
- "Are there any constraints — things I must preserve even if changing them might improve the score?"
- "Are there any loop-attached requirements — every kept change must also update a doc, changelog, or migration note?"

**Quality gate:** If the user provides no strategies, push back:

- "I need at least 2–3 concrete directions to explore. What do you think is causing the current score to be low?"

Do not suggest strategies. Do not add strategies the user did not provide. The PROGRAM.md exploration directions must contain only what the user stated — no "bonus" ideas, no "combine best results" steps, no inferred strategies, **and no "if exhausted, try X" fallback variations**. Fallback variations are a run-mode subagent decision made when the user-provided directions are exhausted; they do not belong in the PROGRAM.md exploration directions section, not even as bracketed suggestions. The user knows their domain — draw it out of them. Setup mode never invents — not as primary directions, not as fallbacks, not as parenthetical hints.

### Step 6: Define stop conditions

Ask:

- "What score would you ship at?"
- "How many failed attempts before I should stop and report back?"

**Quality gate:** If the stop condition is vague ("when it's good enough"), push back:

- "What score number would you ship at? I need a concrete threshold."

Default stop conditions if the user doesn't specify:
- Target score reached — success
- 10 consecutive iterations with no improvement — stop and report
- Mutable files exceed a reasonable size threshold — stop, needs refactoring

### Step 7: Generate PROGRAM.md

> **Read [`references/program-format.md`](references/program-format.md)** for the PROGRAM.md golden references (skill and non-skill) and the format specification including partial-file immutability, loop-attached requirements, and scorer-validates-correctness.

Assemble the user's answers into PROGRAM.md format. Show it to the user for review before writing. The user must approve — PROGRAM.md is their research brief, not the agent's.

**Self-check before showing the draft:** scan the assembled exploration directions section. Every bullet must trace verbatim (or near-verbatim) to something the user said in Step 5. If any bullet says "if exhausted, try X" or "consider also Y" or otherwise contains a strategy the user did not state, delete it before showing the draft. Setup mode is structuring user input, not augmenting it.

Write PROGRAM.md to the target directory. Do not create `research/` — run mode creates it on first iteration.

---

## Mode: Run

Reads an existing PROGRAM.md and executes the autonomous experiment loop. Run mode has two roles — **orchestrator** (the main agent executing everything in this section) and **iteration subagent** (dispatched per iteration via the `Task` tool, reading only `references/subagent-protocol.md` plus the filled slots). The orchestrator never edits mutable files directly — only dispatched subagents modify the target.

### Pre-flight checks (orchestrator)

Before starting the loop:

1. Read PROGRAM.md — reject if missing required sections (objective, metric, mutable files, immutable files, exploration directions, stop conditions)
2. Verify the scoring mechanism exists and runs — execute it once on the current state to establish baseline metric AND verify the correctness guard passes
3. Verify all mutable files exist (including files declared with partial-file immutability)
4. Verify all immutable files exist
5. **Resume detection:** If `research/iterations.tsv` already exists with data rows, this is a resume. Read the last row to get the current iteration number and best score. Skip steps 6–9 — continue on the existing branch at `last_iteration + 1`. Also identify the most recent checkpoint commit (or baseline if no checkpoint yet) from the tsv. Log: "Resuming from iteration N, best score so far: X."
6. Create `research/` directory if it doesn't exist
7. Initialize `research/iterations.tsv` with the header row (including `hypothesis` column — see `references/research-format.md`)
8. Record baseline: iteration 001, current commit, hypothesis `—`, baseline score, status `keep`, summary "baseline — no changes"
9. Create a git branch `autoresearch/[target-name]-[date]` from current state
10. **Cache the baseline snapshot** — read each mutable file at the baseline commit and hold the contents in orchestrator memory. This is the starting point for the subagent input slot `{{baseline_or_checkpoint_snapshot}}`. It is re-read only when a checkpoint is taken.
11. Load `references/subagent-protocol.md` once — the orchestrator will pass this as the prompt template for every `Task` dispatch.

### The orchestrator loop

The orchestrator holds the outer loop. Each iteration, it dispatches a fresh subagent via the `Task` tool and waits for a structured result.

```
LOOP (orchestrator):
  1. Read research/iterations.tsv — understand what's been tried
  2. Select strategy (or leave empty for subagent to pick from PROGRAM.md)
  3. Determine the current checkpoint reference (baseline commit, or the
     most recent checkpoint commit if one has been taken)
  4. Compute git_diff_since_checkpoint = `git diff <checkpoint>..HEAD`
  5. Dispatch an iteration subagent via the Task tool with the prompt
     template from references/subagent-protocol.md. Set `model:` explicitly
     on every dispatch — default to `sonnet` for iteration subagents (the
     per-iteration work is well-scoped and sonnet is the right cost/quality
     point; escalate to `opus` only if the target's edits require deep
     architectural judgment). Fill slots:
       - {{PROGRAM.md}}            = full file contents
       - {{baseline_or_checkpoint_snapshot}} = cached snapshot from step 10
       - {{git_diff_since_checkpoint}}       = computed in step 4
       - {{recent_iterations_tsv}} = last ~5 rows of iterations.tsv
       - {{optional_strategy_hint}} = step 2 pick (or empty)
  6. Receive structured result:
       {commit_hash, hypothesis, verdict_or_score, dim_wins,
        guard_status, change_summary}
  7. If guard_status != "pass" → record as crash, git reset to previous best
  8. Otherwise compare to previous best:
       - Numerical: compare scores directly (lower or higher is better
         per PROGRAM.md metric)
       - Comparative: the subagent ran the A/B judge; use its verdict
  9. Record in research/iterations.tsv:
       iteration, commit, hypothesis, score/verdict, dim_wins (comparative),
       status, change_summary
 10. If improved → keep, advance branch
 11. If equal/worse → git reset to previous best commit
 12. Check loop-attached requirements (if any in PROGRAM.md) — revert the
     iteration if a kept change did not satisfy them
 13. Check checkpoint policy (see below)
 14. Check stop conditions — if met, exit loop
 15. If not met → repeat
```

> **Read [`references/subagent-protocol.md`](references/subagent-protocol.md)** for the self-contained dispatched prompt template the orchestrator passes to each iteration subagent.
> **Read [`references/research-format.md`](references/research-format.md)** for `iterations.tsv` and `changelog.md` format specifications.

### Checkpoint policy

A **checkpoint** re-reads the mutable target fresh (a full snapshot, not a diff) and updates the orchestrator's baseline cache. After a checkpoint, `git_diff_since_checkpoint` resets to empty, and subsequent iterations reconstruct state from the new cached snapshot. Checkpointing is how we bound per-iteration reasoning cost over long runs without paying the full-read cost every iteration.

**Primary rule — agent judgment on four signals.** The orchestrator checkpoints when any of these fires:

1. **Accumulated diff is getting hard to reason about** — the orchestrator notices that the diff is sprawling across many files or revisiting the same lines multiple times, making "current state = baseline + diff" unreliable
2. **Last iteration was a large structural change** — multiple files modified or a single-file delta >50 lines
3. **Multiple recent iterations failed because the subagent mis-read state from the diff** — signaled by `needs_checkpoint` verdicts or crashes that trace to stale state assumptions
4. **Strategy changed categories** — e.g., moving from "dependency splitting" to "multi-stage builds"; a clean snapshot is cheaper to reason about than a diff that mixes strategies

**Safety floor (mandatory).** Force a checkpoint regardless of judgment if either of these holds:

- **15 kept commits since the last checkpoint**, or
- **Accumulated diff exceeds 500 lines**

These numbers are caps, not targets. Good judgment usually triggers a checkpoint well before the floor.

**Why both rules:** the same shape as the stop-conditions policy. Teach the agent judgment for the common case; install a failsafe so bad judgment can't cascade into a runaway state reconstruction bug.

### Cost model

Per-iteration cost is the core architectural justification for checkpoint-plus-diff reconstruction:

- **Single-context loop (old):** `O(N × full_read)` — context grows with every iteration, compaction kicks in around iteration 15, stale file state lingers, effective quality degrades
- **Subagent per iteration with baseline + diff (new):** `O(baseline + N × small_diff)` — each subagent starts fresh with a bounded prompt; baseline is cached once per checkpoint, diff grows only until the next checkpoint. Worst-case iteration cost is bounded by the safety floor.

The crossover where the subagent architecture pays for itself is around iteration 5–6 on raw tokens. Beyond that, the subagent architecture widens the lead. For very short runs (3–5 iterations), the ~15–25k tokens of subagent dispatch overhead is the cost of keeping one consistent execution model — small enough to be worth it.

### On crash or error

If the subagent returns a `crash` verdict (scorer crashed, build broke, correctness guard failed, or an unhandled exception):
- Record in iterations.tsv as `crash`
- Read the error output (last 50 lines) from the subagent's return payload
- If trivially fixable (typo, import error) and not a second attempt at the same fix, dispatch one follow-up subagent with a hint to fix it
- If fundamentally broken, revert and move to the next strategy
- Do not spend more than 2 attempts fixing a crashed run on the same strategy

### On `needs_checkpoint` verdict

If the subagent returns `needs_checkpoint` (the accumulated diff was too large to reconstruct state reliably):
- Force a checkpoint immediately
- Re-dispatch the same iteration number with the fresh baseline snapshot
- Do not count the `needs_checkpoint` return as a used iteration

### On stop condition

When a stop condition is met:

1. Write `research/changelog.md` with: what improved, what didn't work, remaining gaps, and any systematic hypothesis mispredictions (compare the `hypothesis` column to actual outcomes across iterations)
2. Log final summary to the user: starting score → final score, iterations run, strategies that worked
3. Leave the branch at the best-scoring commit

### Rules (orchestrator)

- **Orchestrator never edits mutable files directly.** Only dispatched subagents modify the target. The orchestrator reads, records, dispatches, and decides.
- **Always set `model:` explicitly on subagent dispatches.** Do not rely on inheritance. Default to `sonnet` for iteration subagents; escalate to `opus` only when the target's edits require deep architectural judgment.
- **Never modify immutable files or immutable sections** — PROGRAM.md, scoring mechanism, test inputs, references, and any partial-file-immutable regions
- **One change per iteration** — enforced by the subagent protocol; the orchestrator does not batch
- **Git is the experiment tracker** — every attempt is a commit, every revert is a git reset, every checkpoint is a commit. The full history is recoverable.
- **Do not interact with the user mid-run** unless the scoring infrastructure itself is broken (scorer crashed 3× in a row without progress). The user may be away.

> **Execution scope:** In numerical mode, ignore `EVAL.md` and `SCOPE.md` during execution unless PROGRAM.md explicitly names them — these are skill-specific artifacts that may or may not exist on a non-skill target. In comparative mode, if EVAL.md exists and the target is a skill at ceiling, use it as a **regression guard** (binary check before comparative scoring).

## When to Hand Off

Routes are by task shape, not whether the target is a skill:

| Task shape | Route to |
|------|----------|
| One-shot structural pass on an existing skill | `/improve-skill [path]` |
| Generate EVAL.md for an existing skill | `/write-skill-eval [path]` |
| Build a new skill from scratch | `/skill-creator [description]` |
| No scorer exists yet for this target | **Step 3b above** (conversational scorer-building fallback) |
| Debugging / root-cause analysis | Not auto-research — use normal debugging tools |

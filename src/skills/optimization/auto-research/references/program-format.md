<!-- Decoupled from skill-creator/references/program-format.md to add auto-research-specific patterns (partial-file immutability, loop-attached requirements, scorer-validates-correctness). Skill-creator retains the generic spec. -->

# PROGRAM.md — Format Specification

Research directions for auto-research loops. Only create this when a target is entering automated improvement.

PROGRAM.md is human-written and **immutable** during the auto-research loop — the agent reads it for direction but never modifies it.

## Scoring Modes

Auto-research supports two scoring modes. The mode is determined during setup based on the target's output determinism:

| Mode | When to use | Decision logic |
|------|------------|----------------|
| **Numerical** | Output is deterministic and reproducible (test counts, benchmarks, binary criteria, measured dimensions) | Compare absolute scores: 5/6 > 4/6, or 420 MB < 650 MB |
| **Comparative** | Output is semi-deterministic or requires judgment to evaluate (skill quality, code style, document quality) | A/B judge: preferred > tie > rejected |

**Comparative is the default** when judgment is involved. For objective metrics (image size, test count, latency), numerical is simpler and cheaper.

---

## Golden Reference — Numerical Mode, Skill Target

```markdown
# [Skill Name] — Auto-Research Program

## Objective

Maximize EVAL.md pass rate across all test inputs. Current baseline: 4/6 criteria passing.

## Scoring mode

Numerical

## Metric

Score = number of EVAL.md output criteria passed out of total, averaged across all
test-inputs/. A run scores 0 on crash or timeout.

## Mutable files

Only modify these — everything else is locked:
- SKILL.md (instructions, judgment calls, structure)
- templates/*.md (output skeletons)
- rules/*.md (hard constraints)
- examples/*.md (worked examples)

## Immutable files (DO NOT MODIFY)

- EVAL.md — the scoring criteria
- PROGRAM.md — this file
- test-inputs/ — fixed stimulus
- references/ — domain knowledge (modify only if factually wrong)

## Exploration directions

Try these strategies, roughly in priority order:
1. Simplify instructions — remove lines that don't change output (test by deleting and scoring)
2. Add a gold example — concrete input/output pairs anchor model behavior more than rules
3. Restructure the mental model section — a better conceptual framing helps edge cases
4. Reduce template rigidity — over-specified templates cause the model to force-fit bad output
5. Split large rules into smaller, testable statements — easier to trace failures

## Constraints

- SKILL.md must stay under 500 lines
- Do not change the output format or section headings (downstream consumers depend on them)
- Do not add dependencies on tools/MCPs the skill doesn't already use
- Preserve the execution fence comment
- Keep language imperative and opinionated — no hedging ("consider", "you might")

## Stop conditions

- All EVAL.md criteria pass on all test inputs (6/6) — success, stop
- 10 consecutive iterations with no improvement — stop, log conclusion in changelog.md
- SKILL.md exceeds 500 lines — stop, the skill needs structural refactoring first
```

---

## Golden Reference — Numerical Mode, Non-Skill Target (Docker Image Optimization)

This is a real PROGRAM.md from a user running auto-research on a code target — not a skill. It demonstrates three patterns that the skill example doesn't: **partial-file immutability**, **a scorer with a correctness guard**, and **loop-attached documentation requirements**.

```markdown
# ragweave-api — Docker Image Optimization Program

## Objective

Reduce the production Docker image size for ragweave-api without breaking
runtime behavior. Baseline: API image 1.4 GB, Runtime image 4.8 GB.
Target: API <500 MB AND Runtime <3 GB.

## Scoring mode

Numerical

## Metric

Score = tuple (api_image_mb, runtime_image_mb). Lower is better on both
dimensions. Improvement = strict decrease on either dimension without
regression on the other. Measured via `docker image inspect --format '{{.Size}}'`
after a clean build.

## Scoring mechanism

`containers/score.sh` — builds both images from scratch, reports sizes,
and runs a correctness guard (see below). Iteration scores 0 on build
failure, correctness probe failure, or timeout (>15 min).

### Correctness guard (scorer validates correctness, not just measures)

After each successful build, the scorer runs an import probe inside the
API container:

    $DOCKER run --rm --entrypoint python ragweave-api-score \
      -c "from server.api import app; print('import OK')"

If the probe fails, the iteration is recorded as `crash`, reverted, and
the agent moves to the next strategy — **even though the build succeeded
and the image was small**. Without this guard, a dependency-splitting
strategy that silently removes a transitive ML dep would score as a huge
win until runtime request handling broke in production.

## Mutable files

- `containers/Dockerfile.api` — fully mutable
- `containers/Dockerfile.runtime` — fully mutable
- `pyproject.toml` — **partially mutable** (see Partial-file immutability below)
- `containers/score.sh` — mutable (improvements to the scorer itself allowed)
- NEW files permitted:
  - `.dockerignore`
  - `containers/requirements-*.txt` (generated or hand-authored layer splits)
  - `containers/Dockerfile.*` variants (e.g., `.api.buildkit`, `.runtime.minimal`)

## Partial-file immutability

`pyproject.toml` is split by section:

- **Immutable:** `[project]`, `[project.dependencies]` — the core runtime
  dependency list. Removing a core dep will break the correctness probe.
- **Mutable:** `[project.optional-dependencies]` — extras groups. New
  extras groups may be added; existing groups may be reorganized.
- **Mutable:** `[tool.*]` sections — build-system config, linters, type
  checkers.

Violating the immutable boundary (editing `[project.dependencies]`) is a
scorer-invariant violation and the iteration is reverted.

## Immutable files (DO NOT MODIFY)

- `server/**/*.py` — application code (optimization must not change behavior)
- `tests/**/*.py` — test suite
- `PROGRAM.md` — this file
- `containers/compose.yaml` — orchestration contract (external consumers)

## Exploration directions

Priority order (highest impact first):

1. **Dependency splitting** — move heavy ML deps into an `inference` extras
   group; API image installs only `[project.dependencies]` + `api` extras.
   Expected largest delta.
2. **Multi-stage builds** — wheel-building stage discarded before final
   image; runtime image copies only built artifacts.
3. **`.dockerignore`** — exclude `tests/`, `docs/`, `.git/`, notebooks,
   local model caches from build context.
4. **BuildKit pip cache mounts** — `RUN --mount=type=cache,target=/root/.cache/pip`
   to avoid re-downloading wheels on layer rebuild (build-time speedup,
   not size — tracked for cost side-metric).
5. **Layer ordering** — stable layers (system packages) before volatile
   layers (source code) for cache reuse.
6. **Podman/OCI compatibility pass** — verify builds and runs under Podman
   as well as Docker; avoid Docker-specific extensions.

## Loop-attached requirements

Every iteration that **keeps** a change must also update or create
`docs/operations/DOCKER_OPTIMIZATION.md` with:

- What changed (one paragraph)
- Why it helped (mechanism, not just "saved X MB")
- Any new build flags, env vars, or operator-visible behavior

This is **not part of scoring** — the iteration is kept or discarded based
on the metric and correctness probe alone. But documentation updates are
a hard requirement for the iteration to be considered complete. A kept
change with no doc update is reverted at the orchestrator's next
checkpoint.

## Constraints

- Runtime behavior must not change — the correctness probe is a smoke
  test, not a full regression suite; do not optimize by removing features
- No network calls at build time beyond the standard package index
- Must build under both Docker and Podman (verify before declaring success
  on any Dockerfile-structural change)
- `compose.yaml` contract is frozen (external consumers depend on service
  names, port numbers, volume mounts)

## Stop conditions

- Target reached: API <500 MB AND Runtime <3 GB — success
- Plateau: 5 consecutive iterations with <100 MB improvement on either
  dimension — stop and report
- Hard iteration limit: 15 kept iterations — stop regardless of progress
- Scorer crashed 3 times in a row without progress — scoring infrastructure
  is broken, stop and ask the user
```

---

## Golden Reference — Comparative Mode

```markdown
# [Target Name] — Auto-Research Program

## Objective

Optimize [target] beyond binary criteria ceiling. Current state: EVAL.md 23/23
(ceiling reached), but output quality has room for improvement on [specific
dimensions].

## Scoring mode

Comparative

## Comparison dimensions

Ranked by priority (dimension 1 outweighs dimension 3 in conflicts):
1. [Dimension 1] — [what "better" looks like for this dimension]
2. [Dimension 2] — [what "better" looks like]
3. [Dimension 3] — [what "better" looks like]

## Comparison protocol

1. Generate output from current version using test inputs
2. Retrieve previous best output (from best commit)
3. Present both to judge in randomized order (avoid position bias)
4. Judge evaluates each dimension independently, citing evidence
5. Verdict: preferred (current wins majority by priority), tie, or rejected

## Mutable files

Only modify these — everything else is locked:
- SKILL.md (instructions, judgment calls, structure)
- templates/*.md (output skeletons)

## Immutable files (DO NOT MODIFY)

- EVAL.md — binary criteria (ceiling already reached, used as regression guard)
- PROGRAM.md — this file
- test-inputs/ — fixed stimulus
- references/ — domain knowledge

## Exploration directions

Try these strategies, roughly in priority order:
1. [Strategy 1 — user-provided]
2. [Strategy 2 — user-provided]
3. [Strategy 3 — user-provided]

## Constraints

- [Constraint 1]
- [Constraint 2]
- EVAL.md criteria must not regress — run binary check as a guard before
  comparative scoring

## Stop conditions

- [N] consecutive iterations with no improvement — stop, log conclusion in
  changelog.md
- All exploration directions exhausted with no improvement — stop and report
- Mutable files exceed size threshold — stop, needs refactoring
```

---

## Format spec: Partial-file immutability

Some files are mixed — one section contains optimization targets, another
contains a contract that must not change. Express this by splitting the
`Mutable files` list by section:

```markdown
## Mutable files

- `pyproject.toml` — **partially mutable** (see Partial-file immutability below)
- `Dockerfile` — fully mutable

## Partial-file immutability

`pyproject.toml` is split by section:
- **Immutable:** `[project.dependencies]` — core runtime deps
- **Mutable:** `[project.optional-dependencies]` — extras groups
- **Mutable:** `[tool.*]` — build/lint config
```

**Enforcement is the iteration subagent's responsibility.** The subagent
reads PROGRAM.md each iteration and must respect partial-file boundaries
when editing. There's no external tooling that validates this — the
discipline lives in the subagent reading PROGRAM.md carefully and the
correctness guard in the scorer catching the downstream effects of
boundary violations.

**When to use partial-file immutability:** when splitting a file into two
files would be a worse outcome than the risk of boundary violation. For
`pyproject.toml`, splitting is not an option (it's one file by design).
For a long `src/main.py`, prefer refactoring to split the file rather than
declaring half of it immutable.

## Format spec: Loop-attached requirements

Some changes need more than a code edit and a passing scorer — they need
a doc update, a changelog entry, a migration note. Express these as
loop-attached requirements:

```markdown
## Loop-attached requirements

Every iteration that **keeps** a change must also:
- Update `docs/CHANGELOG.md` with a one-line entry
- Add or update the corresponding section in `docs/operations/DOCKER_OPTIMIZATION.md`
```

**These are not part of scoring.** The iteration is kept or discarded based
on the metric alone. But they are a hard requirement for the iteration to
be considered complete. An iteration that improves the metric but skips
the loop-attached requirement is reverted.

**Why not make them part of the scorer?** Because the scorer measures the
target's quality; loop-attached requirements are about the auditability
and operability of the kept changes. Conflating them would mean a doc
improvement that accidentally regressed the metric would score as a
regression.

**Orchestrator responsibility:** the orchestrator checks loop-attached
requirements when recording the iteration. If the subagent returned a
`keep` verdict but did not satisfy the attached requirement, the
orchestrator reverts the iteration and records it as `discard` with a
clear reason.

## Format spec: Scorer validates correctness, not just measures

A scorer that only measures the metric will happily report "huge win" for
a change that improved the metric by breaking the system. Every scorer
should include a **correctness guard** that fails the iteration when the
metric looks good but the target is broken.

Common guard patterns:

- **Import/smoke probe** — run the target once with a minimal input and
  verify it doesn't crash or produce obviously-broken output. The Docker
  example above uses `python -c "from server.api import app"` as the
  probe.
- **Canonical input/output pair** — a known-good input/output that the
  target must continue to handle correctly regardless of other changes.
- **Type or contract check** — for targets that expose an API or schema,
  verify the external contract still holds after changes.

**Where guards slot in:** each of the four scorer archetypes in
`references/scorer-patterns.md` should include a guard step alongside
its measurement step. The guard runs first; if it fails, the iteration
is recorded as `crash` and reverted. Only after the guard passes is the
metric recorded.

**Design principle:** the guard is cheap compared to the cost of a bad
commit slipping through to a downstream iteration and poisoning the
baseline.

---

## Adapting for your target

The golden references above are templates. When writing a PROGRAM.md:

- **Scoring mode**: determined during setup — comparative (default when
  judgment is involved) or numerical (for objective metrics)
- **Objective**: replace the baseline with your actual current state
- **Mutable files**: list only the files that exist in your target directory;
  use partial-file immutability where splitting isn't an option
- **Scoring mechanism + correctness guard**: include both — pure measurement
  without a correctness guard will accept broken "improvements"
- **Exploration directions**: tailor to what you think is weak — these come
  from the user, not the agent
- **Constraints**: add domain-specific constraints
- **Loop-attached requirements**: if kept changes need doc updates, changelog
  entries, or migration notes, list them explicitly
- **Stop conditions**: adjust thresholds based on target complexity
- **Comparative mode**: the comparison dimensions and priority ranking are
  critical — vague dimensions produce noisy judging. "Error message
  specificity" is good; "overall quality" is bad
- **Regression guard**: for skills that have hit EVAL.md ceiling, always
  include the binary criteria check as a guard rail before comparative
  scoring

# Scorer Patterns — Four Archetypes

When a target doesn't already have a scoring mechanism, setup mode's Step 3b walks the user through building one. This file is the reference for the four archetypes that cover the common cases. Pick the closest match, adapt the details, and verify it runs on the baseline before declaring setup complete.

Every archetype follows the same shape:
1. **When to use** — the kind of target and metric this archetype fits
2. **Input shape** — what the scorer consumes
3. **Scorer invocation** — how you run it
4. **Output parsing** — how you extract the metric
5. **Correctness guard** — how you catch silent breakage (always include one)
6. **How to verify it runs** — execute once on baseline before declaring setup complete

If none of the four archetypes fits the target cleanly, fall back to conversational scorer design: walk through "what would you check to know it's better?" with the user until a concrete executable emerges.

---

## Archetype 1: Timing / Benchmark

### When to use

The metric is "how long does this take" or "how fast does this run" — build times, response latencies, query execution, startup times, cold-cache times. Reproducible enough that a warmup + average is a fair number.

### Input shape

A command that runs the thing being measured. Must be deterministic enough that repeated runs produce comparable numbers.

### Scorer invocation

```bash
# Using hyperfine (preferred — handles warmup + repetition + stats)
hyperfine --warmup 3 --runs 10 \
  --export-json bench.json \
  './build.sh'

# Or with time (simpler, less statistically rigorous)
{ time ./build.sh ; } 2> time.txt
```

### Output parsing

```bash
# From hyperfine
jq '.results[0].mean' bench.json
# => 12.4 (seconds)

# From time
grep real time.txt | awk '{print $2}'
```

### Correctness guard

Run the built artifact once and check that it doesn't error out:

```bash
./build.sh && ./dist/app --version || exit 1
```

Without the guard, an "optimization" that removes a necessary build step might drop build time to zero by not actually building anything.

### How to verify it runs

Execute the scorer once on the baseline state. You should get:
- A concrete number (not an error, not "N/A")
- The guard passing
- Runtime bounded enough to run in the loop (if one iteration takes 20 minutes, the loop will take days)

---

## Archetype 2: Counted Tests / Criteria

### When to use

The metric is "how many of X pass" — test suite pass count, EVAL.md criteria count, linter rule violations, type check errors. Discrete, countable, easy to compare.

### Input shape

A test runner, linter, or checklist evaluator that exits with a count.

### Scorer invocation

```bash
# pytest
pytest -q --tb=no --no-header tests/

# ruff
ruff check --statistics src/

# mypy
mypy --no-error-summary src/

# EVAL.md-style checklist (custom scorer invoking a judge)
./eval.sh test-inputs/ EVAL.md
```

### Output parsing

```bash
# pytest — last line is "N passed, M failed in Xs"
pytest -q tests/ | tail -1 | grep -oP '\d+ passed' | awk '{print $1}'

# ruff — count violations
ruff check --statistics src/ 2>&1 | tail -1 | awk '{print $1}'

# EVAL — parse structured output
jq '.criteria_passed' eval-result.json
```

### Correctness guard

For test counts, the test suite itself is the guard — a crash means zero. For linters, run the target once to make sure it still executes:

```bash
ruff check src/ && python -c "import mypackage; mypackage.main()" || exit 1
```

Without the guard, a lint-fixing iteration that deletes `src/` entirely would score perfectly.

### How to verify it runs

- Baseline produces a number (not a runtime error)
- Number matches expectation (if the user says "we're at 4/6 currently," your scorer should return 4)
- Fast enough that running it per-iteration is tolerable

---

## Archetype 3: Measured Dimension

### When to use

The metric is a single measurable dimension extracted from the target — file size, memory footprint, API latency, output token count, lines of code, binary size. Often coupled with a build step.

### Input shape

A command that produces the target (or the target directly), plus an extractor that reads the dimension.

### Scorer invocation

```bash
# Docker image size (the running user example)
docker build -t target:score -f Dockerfile.api . && \
  docker image inspect target:score --format '{{.Size}}'

# Binary size
gcc -O2 src/main.c -o dist/app && stat -c%s dist/app

# API latency from a running server
curl -w '%{time_total}' -o /dev/null -s http://localhost:8080/endpoint

# JSON field from an endpoint
curl -s http://localhost:8080/metrics | jq '.latency_p95'

# Word count in a document
wc -w < output.md
```

### Output parsing

Usually a single number on stdout — pipe directly into the scorer's output slot. If the command produces structured output, use `jq` or `awk` to extract the dimension.

```bash
# Bytes → MB
echo "scale=0; $(docker image inspect target:score --format '{{.Size}}') / 1000000" | bc
```

### Correctness guard

**This is the archetype where the correctness guard matters most.** Measured-dimension optimizations are the easiest to "win" by breaking the target.

Common guards:

```bash
# Import / smoke probe (the Docker example)
docker run --rm --entrypoint python target:score \
  -c "from server.api import app; print('import OK')" || exit 1

# Canonical input/output
./dist/app < test-inputs/canonical.in > /tmp/out && \
  diff /tmp/out test-inputs/canonical.out || exit 1

# API contract check
curl -sf http://localhost:8080/health || exit 1
```

Without the guard, "optimization" that silently removes a transitive dependency, breaks an API contract, or produces garbled output will score as a huge win.

### How to verify it runs

- Baseline produces a number in the right units
- The guard passes on baseline
- An intentionally-broken version (e.g., delete a required import) causes the guard to fail, not the measurement — sanity-check by temporarily breaking the target and confirming the scorer reports `crash`

---

## Archetype 4: Comparative LLM Judge

### When to use

The metric is a judgment call — "is this output better than the previous best" — not an extractable number. Skills at EVAL.md ceiling, document quality, code style, error message clarity, log informativeness. Output is semi-deterministic or requires interpretation.

### Input shape

Test inputs that both the current and previous-best versions process to produce paired outputs for comparison. No external script — the judge runs inside the agent.

### Scorer invocation

This archetype has no external executable. The "scorer" is a judge prompt that:

1. Loads test inputs
2. Generates outputs from the current version
3. Retrieves previous-best outputs from the best commit
4. Presents both to a judge in **randomized order** (flip a coin per pair — which is labeled A and which is B)
5. Judges each comparison dimension independently with cited evidence
6. Aggregates by priority ranking (a win on dimension 1 outweighs a loss on dimension 3)
7. Returns a verdict: `preferred` / `tie` / `rejected` plus per-dimension wins

### Output parsing

Structured judge output (from the judge prompt itself):

```json
{
  "verdict": "preferred",
  "dim_wins": "2/3",
  "dimensions": {
    "specificity": {"winner": "current", "evidence": "..."},
    "level": {"winner": "current", "evidence": "..."},
    "coverage": {"winner": "tie", "evidence": "..."}
  }
}
```

### Correctness guard

If the target is a skill with an EVAL.md, the binary criteria are the guard — run them first, reject the iteration if any criterion regresses. This prevents comparative-mode "improvements" that silently break a structural requirement.

For non-skill comparative targets (e.g., document quality), the guard is usually a length or format check — "output must be under 500 words," "output must be valid markdown," etc.

### How to verify it runs

- Run the judge once on baseline vs itself — should return `tie` on all dimensions (sanity check: a judge that prefers the current version over an identical copy is biased)
- Verify randomized ordering — run the same pair twice, labels should flip
- Verify dimension independence — a change that only affects dimension 1 should show `tie` on dimensions 2 and 3

---

## Falling back to conversational design

If none of the four archetypes fits — the target produces output you can neither measure nor compare cleanly — walk through these questions with the user:

1. "If I gave you two versions of the output side by side, what would you look at first to decide which is better?"
2. "Can that be turned into a yes/no question? Or a count? Or a measurement?"
3. "Is there a test input where we already know what 'good' looks like?"

The answers usually surface an archetype in disguise. If not, the target may not be a good fit for auto-research — some things genuinely lack a scorable metric, and the right move is to recognize that and stop rather than invent a fake scorer.

---

## Always: write the scorer to a file, commit it, mark it immutable

Regardless of archetype, the scorer lives in a file (`scorer.sh`, `score.py`, `eval.sh`, whatever fits) inside the target directory. That file goes into PROGRAM.md's **immutable files** list. The subagent will not modify it during the loop — only the user changes the scorer, and only outside a run.

**Why immutable:** if the subagent can edit the scorer, it will find ways to make any iteration "win" by loosening the scorer. The scorer is the north star; it must not drift.

**Exception:** the scorer may be listed as mutable when you are explicitly iterating on the scorer itself (e.g., tuning a correctness guard). These runs are rare and should be framed as "scoring-infrastructure improvement" rather than "target improvement."

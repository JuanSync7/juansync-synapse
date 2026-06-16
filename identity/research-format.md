# research/ — Format Specification

Created by auto-research runs. Contains two files. The agent creates this directory on its first iteration — do not pre-create it.

## iterations.tsv

Tab-separated experiment log. The agent uses `git diff` between commits to understand what changed — no file snapshots needed.

The format depends on the scoring mode defined in PROGRAM.md.

### Numerical mode

```
iteration	commit	hypothesis	score	status	change_summary
```

| Column | Format | Description |
|--------|--------|-------------|
| iteration | 3-digit zero-padded | Sequential experiment number |
| commit | 7-char git hash | Short hash for `git diff` lookups |
| hypothesis | free text | **Ex-ante** expectation, written before the edit (e.g., "removing the YAML formatting rule should be neutral — Claude already formats YAML correctly"). Leave as `—` for the baseline row. |
| score | N/M | Criteria passed / total (or other numeric metric) |
| status | keep\|discard\|crash | Whether the change was kept |
| change_summary | free text | **Ex-post** description of what was tried and what actually happened |

**Why `hypothesis` and `change_summary` are separate columns:** hypothesis is what the agent expected before editing; change_summary is what the agent observed after scoring. Keeping them separate lets the changelog surface systematic mispredictions — e.g., "we kept believing simplification would help, but it regressed in 4 of 5 attempts."

**Filled example:**

```
iteration	commit	hypothesis	score	status	change_summary
001	a3f2c1d	—	4/6	keep	baseline — no changes, initial score
002	b7e9d4a	removing redundant YAML rule should be neutral — Claude formats YAML correctly	5/6	keep	confirmed — rule was noise, one criterion flipped to pass
003	c1a8f3b	gold example will anchor the opinionated-language criterion	5/6	discard	no score change — token budget was full, example was absorbed as noise
004	e2d1a9f	mental model paragraph is decorative, removing it should be neutral	4/6	discard	regression — agent lost conceptual framing, two criteria failed
005	d4c2e7f	adding good/bad contrast should fix the mental-model regression	6/6	keep	confirmed — contrast anchored the "opinionated" criterion
```

### Comparative mode

```
iteration	commit	hypothesis	verdict	dim_wins	status	change_summary
```

| Column | Format | Description |
|--------|--------|-------------|
| iteration | 3-digit zero-padded | Sequential experiment number |
| commit | 7-char git hash | Short hash for `git diff` lookups |
| hypothesis | free text | **Ex-ante** expectation, written before the edit (e.g., "tighter error messages should win on specificity without regressing coverage"). Leave as `—` for the baseline row. |
| verdict | preferred\|tie\|rejected\|— | A/B judge result (— for baseline) |
| dim_wins | X/Y or — | Dimensions won / total (— for baseline) |
| status | keep\|discard\|crash | Whether the change was kept |
| change_summary | free text | **Ex-post** description including which dimensions won/lost |

**Filled example:**

```
iteration	commit	hypothesis	verdict	dim_wins	status	change_summary
001	a3f2c1d	—	—	—	keep	baseline — no changes
002	b7e9d4a	tightening error messages should win on specificity without hurting coverage	preferred	2/3	keep	confirmed — won on specificity and level, tied on coverage
003	c1a8f3b	verbose logging should improve coverage at acceptable cost	rejected	1/3	discard	won coverage but lost specificity and level — cost was not acceptable
004	d9e4f2a	restructured log format should be neutral on specificity	tie	1/3	discard	won level, lost specificity, tied coverage — predicted wrong
005	e7c3a1b	targeted specificity fixes should win specificity and level cleanly	preferred	3/3	keep	confirmed — won all three dimensions
```

---

## changelog.md

Human-readable narrative of what improved and why. Written by the agent at stop condition. Useful for onboarding someone new to the target or understanding design decisions.

### Template — Numerical mode

```markdown
# [Target Name] — Research Changelog

## Run: [date] — [run tag or branch name]

**Scoring mode:** Numerical
**Starting score:** N/M
**Final score:** N/M
**Iterations:** X (Y kept, Z discarded)

### What improved
- [Change that helped and why it worked]

### What didn't work
- [Change that was tried and reverted, and why it failed]

### Hypothesis mispredictions
- [Iterations where the ex-ante hypothesis (column 3 of iterations.tsv) and the actual outcome systematically diverged]
- [Patterns: classes of change the agent kept predicting would help but that regressed every time, or vice versa]
- [Leave empty only if hypotheses tracked outcomes cleanly across the run]

### Remaining gaps
- [Criteria still failing, if any, and hypotheses for why]
```

### Template — Comparative mode

```markdown
# [Target Name] — Research Changelog

## Run: [date] — [run tag or branch name]

**Scoring mode:** Comparative
**Comparison dimensions:** [dim1] > [dim2] > [dim3]
**Iterations:** X (Y preferred, Z rejected, W ties)

### What improved
- [Change that was preferred and which dimensions it won on]

### What didn't work
- [Change that was rejected and which dimensions it lost on]

### Hypothesis mispredictions
- [Iterations where the ex-ante hypothesis (column 3 of iterations.tsv) and the actual A/B verdict systematically diverged]
- [Patterns: dimensions the agent kept predicting wins on but that lost, or dimensions the agent dismissed but that won]
- [Leave empty only if hypotheses tracked verdicts cleanly across the run]
```

### Filled example — Numerical

```markdown
# skill-creator — Research Changelog

## Run: 2026-04-07 — autoresearch/apr7

**Scoring mode:** Numerical
**Starting score:** 4/6
**Final score:** 6/6
**Iterations:** 5 (3 kept, 2 discarded)

### What improved
- Removing the YAML formatting rule (iteration 002) — it was noise, Claude already formats YAML correctly
- Adding good/bad contrast to the mental model section (iteration 005) — anchored the agent's interpretation of "opinionated"

### What didn't work
- Adding a gold example without removing other instructions (iteration 003) — token budget was already full, example added noise instead of signal
- Removing the mental model paragraph entirely (iteration 004) — the agent lost the conceptual framing and fell back to mechanical rule-following

### Hypothesis mispredictions
- Iteration 003 hypothesis predicted the gold example would anchor the opinionated-language criterion; actual outcome was no score change. Pattern: adding content without removing other content rarely helps when the token budget is already full — future runs should pair "add" experiments with "remove" experiments rather than running them separately.

### Remaining gaps
- None — all 6 criteria pass. Next run should target model migration (test on mid-tier).
```

### Filled example — Comparative

```markdown
# auto-research — Research Changelog

## Run: 2026-04-07 — autoresearch/scoring-quality

**Scoring mode:** Comparative
**Comparison dimensions:** error specificity > log level correctness > coverage
**Iterations:** 5 (2 preferred, 2 rejected, 1 tie)

### What improved
- Tightened error messages with contextual variable values (iteration 002) — won on specificity and level
- Targeted specificity fixes in edge case handlers (iteration 005) — won all three dimensions

### What didn't work
- Blanket verbose logging (iteration 003) — improved coverage but degraded specificity and level correctness
- Restructuring log format (iteration 004) — lateral move, no clear winner across dimensions

### Hypothesis mispredictions
- Iteration 003 hypothesis predicted blanket verbose logging would help coverage at acceptable cost; actual verdict was rejected because the cost on specificity was not acceptable. Pattern: the agent kept underweighting specificity in its hypotheses despite specificity being the priority-1 dimension. Future hypotheses should explicitly check the priority-1 dimension before predicting a win on any lower-priority dimension.

### Remaining gaps
- Coverage dimension proved hard to improve without regressing specificity — may need a structural refactor to separate error paths from info logging
```

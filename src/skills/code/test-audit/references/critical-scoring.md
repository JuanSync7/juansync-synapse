# Critical Scoring Reference

Load point: **[SCORE]** — applies the 2-factor heuristic to assign each function a tier
(critical / standard / cold) and a corresponding coverage target.

---

## The 2-Factor Formula

```
priority = recently_changed AND (public_api OR bug_history > 0)
```

A function reaches **critical** tier only when _both_ sides of the AND are true.
Neither factor alone is sufficient.

### Factor 1 — `recently_changed`

A function is `recently_changed` if any commit that touches its defining file was
authored within the lookback window.

- **Default window:** 30 days from audit date.
- **Configurable:** set `CRITICAL_SCORING_LOOKBACK_DAYS` in project config to override.
- **How to read git log:**
  ```
  git log --since="30 days ago" --diff-filter=M --name-only --pretty=format: -- <file>
  ```
  If the file appears in output, every function in that file is a candidate.
  For finer granularity, `git log -L :<function_name>:<file>` confirms whether the
  function body itself changed.

### Factor 2 — `public_api OR bug_history > 0`

**`public_api`** is true when the function satisfies any of the following:

- Listed in the module's `__all__`.
- Exported from the package's `__init__.py` (directly or via re-export).
- Name carries no leading underscore AND is imported by at least one other package
  (grep `from <package> import <name>`).

**`bug_history > 0`** is true when at least one commit references the function
in a fix-marked message. Conventional commit scopes accepted:

- `fix:`, `fix(<scope>):` (Conventional Commits)
- `bugfix:`, `hotfix:`, `patch:` prefixes
- Free-text scan: commit message contains the function name AND any of the above
  prefixes in the same message.

```
git log --all --grep="fix" --grep="<function_name>" --all-match --oneline
```

---

## Why the Old 4-Factor Formula Was Discarded

The previous formula weighted `complexity × change_freq × fan_in × boundary`.

Three failure modes caused its retirement (see design doc §2.P8):

1. **Over-fit.** Weights were calibrated on one project's commit history. Applied
   elsewhere they misclassified stable, heavily-imported utility functions as cold
   and flagged refactored-but-stable internals as critical.

2. **Gamed by file movement.** Renaming or splitting a file reset `change_freq` to
   zero while `fan_in` spiked — producing contradictory signals that required manual
   override every release cycle.

3. **Uncalibrated weights.** No data existed to justify `complexity × 0.4 + fan_in × 0.3`.
   The coefficients were editorial guesses, not evidence-based thresholds.
   Reviewers could not explain why a function scored 0.72 versus 0.68.

The 2-factor formula is grep-detectable, stable across projects, and explainable
to any reviewer in one sentence.

---

## Tier → Target Mapping

| Tier | Condition | Coverage target |
|----------|---------------------------------------------------|-----------------|
| critical | `recently_changed AND (public_api OR bug_history > 0)` | 95% |
| standard | `recently_changed` only OR `public_api` only (not both sides of the AND) | 85% |
| cold | neither `recently_changed` nor `public_api` nor `bug_history > 0` | 70% |

**Standard tier** captures functions that are changing but unexposed, or exposed but
stable — meaningful enough to hold to 85%, but not requiring the highest scrutiny.

---

## Decision Examples

### GOOD — correctly assigned critical / 95%

> `UserService.create_user` is listed in `__all__`, was last modified three days ago,
> and appears in a `fix(auth): prevent duplicate email registration` commit from last
> quarter.
>
> `recently_changed` = true (3 days < 30-day window).
> `public_api` = true (`__all__`). `bug_history > 0` = true (fix commit).
> Result: **critical / 95%**.

### GOOD — correctly assigned cold / 70%

> `_normalize_whitespace` is a private helper (leading underscore, not in `__all__`,
> not imported externally). Last commit touching its file was 8 months ago. No fix
> commit references it.
>
> `recently_changed` = false. `public_api` = false. `bug_history` = 0.
> Result: **cold / 70%**.

### BAD heuristic — do NOT use

> Assigning critical based on **cyclomatic complexity alone**.

This is gaming-prone: a function with many branches that has been stable for two years
and is never called from outside its module does not need 95% line coverage — it needs
good branch coverage within its existing tests. Complexity is not a proxy for exposure
or churn. Do not add complexity as a scoring factor without data justification.

---

## Boundary Cases

### Renamed function

`bug_history` follows the rename. Use `git log --follow` when computing fix-commit
presence:

```
git log --follow --all --grep="fix" --oneline -- <file>
```

Then confirm the old function name appears in matching commit diffs. If the rename
and the fix happened in the same commit, count it as bug history for the new name.

### Newly added function (no history)

A brand-new function has no git history to query. Apply the following defaults:

- **Public** (in `__all__`, or exported from `__init__.py`, or no leading underscore
  in a public module): `recently_changed` = true (just added), `public_api` = true
  → **standard / 85%**.
- **Private** (leading underscore, not exported): `recently_changed` = true,
  `public_api` = false, `bug_history` = 0 → second factor false
  → **cold / 70%**.

Do not assign critical to a newly added function; it has no bug history by definition
and the first-deploy window is the right time to start at 85% and promote after the
first fix commit appears.

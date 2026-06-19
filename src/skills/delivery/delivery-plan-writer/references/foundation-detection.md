# Foundation Detection — the [F] cascade

A "foundation" is a slice that other slices structurally consume (auth, db schema, logger, event bus). Order them first or downstream slices block on missing scaffolding. This cascade decides *which* slices are foundations and records *why* — the orchestrator audits the source when it picks dispatch order at `[PICK-NEXT-SLICE]`.

## The cascade (halt at FIRST match)

| # | Source | Match shape | `foundation_source` |
|---|--------|-------------|---------------------|
| 1 | `--foundation-first` flag | Non-empty comma list (e.g. `auth,db,logger`) | `declared` |
| 2 | `architecture.md` frontmatter `foundations: [...]` | YAML list field, structural read | `architecture` |
| 3 | Cross-FR commonality heuristic | Module/concept referenced by ≥ threshold of FRs | `inferred` |
| 4 | None of the above | — | `none-with-risk` |

Threshold for level 3 is **60%** by default, overridable via `.delivery/config.yaml: granularity.foundation_threshold`. Do not skip levels; do not blend (the firing level is the *only* source recorded).

## `foundation_source` semantics — what the orchestrator does

- `declared` — Trust user. Order the named foundations first in dispatch sequence; do not second-guess against architecture or heuristics.
- `architecture` — Treat as authoritative; identical ordering behavior to `declared`. Audit trail points at the doc, not the operator.
- `inferred` — Order heuristic foundations first, but the orchestrator surfaces "inferred foundation" in its pre-flight summary so the operator can override.
- `none-with-risk` — Orchestrator dispatches by `depends_on` topology only. Pre-flight prints a yellow banner. If `--confirm-no-foundation` is absent and ≥2 stories touch a shared module, planner has already refused upstream — orchestrator should never see this case without confirmation.

## Worked examples — each level firing

**Level 1 (declared).** Operator runs `delivery-plan-writer --tag PAY --foundation-first auth,ledger`. Cascade halts at step 1. Stories tagged `PAY-001..PAY-00N`; `auth` and `ledger` slices sort before all dependents. `foundation_source: declared`.

**Level 2 (architecture).** No flag. `docs/architecture.md` has frontmatter:
```yaml
---
foundations: [identity-service, event-bus]
---
```
Cascade halts at step 2 — structural field present. `foundation_source: architecture`.

**Level 3 (inferred).** No flag, no frontmatter field. 12 FRs in spec; 9 mention "OrderRepository", 8 mention "AuthMiddleware". Both ≥ 60% (9/12 = 75%, 8/12 = 67%). Both promoted to foundations. `foundation_source: inferred`.

**Level 4 (none-with-risk).** No flag, no frontmatter, no module crosses 60%. Six stories planned. Two touch `src/billing/calculator.py`. Planner refuses unless `--confirm-no-foundation` is set. With confirmation: `foundation_source: none-with-risk`, warning in `[END]` report.

## Counter-example — why heading-scrape is wrong

`architecture.md` contains a prose section:
```markdown
## Foundations
Historically, the team treated logging as foundational, but in this revision...
```
But its frontmatter has **no** `foundations:` field. A heading-scraper picks "logging" from the H2 and emits `foundation_source: architecture` with `logger` foundation. The doc *just said* the team moved off that stance — the structural read correctly finds no field, falls through to level 3, and the heuristic surfaces the actual high-coupling module from FRs. **Always read the structural field; never the heading.** This is the same rule [H] enforces — keep it consistent here.

## Edge cases

- **Declared contradicts architecture.** Flag says `auth,db`; frontmatter says `[identity-service]`. Halt at level 1 (declared wins) but emit a warning: `"--foundation-first overrides architecture.md foundations: [identity-service]"`. Operator sees both lists, makes informed call.
- **Heuristic produces > 3 candidates.** Step 3 finds 5 modules ≥60%. Warn and pause: `"Heuristic yielded 5 foundation candidates: [...]. Pick ≤3 with --foundation-first, or raise foundation_threshold in .delivery/config.yaml."` Do not silently take all five — too many foundations starves the parallel dispatch lane.
- **Frontmatter field present but empty (`foundations: []`).** Treat as explicit "no foundations" — halt at level 2 with `foundation_source: architecture` and an empty foundation list. Do NOT fall through to level 3; the empty list is a deliberate signal.
- **Config file missing or malformed.** Use the 60% default and emit a one-line notice; do not refuse.

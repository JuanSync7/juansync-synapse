# README Dashboard Update Contract — Engineering Guide Layer

After updating the engineering guide, update the subsystem's `README.md` dashboard.

## Location

The README lives at: `docs/{subsystem}/README.md`.

## Update Procedure

Since the engineering guide is cumulative (one living document), the update is simpler than split-layer skills:

1. **Status Matrix** — The Eng Guide cell should always read `[Current]({filename})`. It does not change per phase — the link is always to the same file.
2. **Last updated** — Set to today's date

The engineering guide does not introduce cross-phase dependencies or carry-forward contracts (those come from spec and design layers).

## Status Values

- `—` = not started (no guide written yet)
- `[Current]({filename})` = guide exists and is up to date

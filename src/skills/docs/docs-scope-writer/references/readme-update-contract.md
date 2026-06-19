# README Dashboard Update Contract — Scope Layer

After any scope document update, update the subsystem's `README.md` dashboard.

## Location

The README lives at: `docs/{subsystem}/README.md`.

## If README Does Not Exist

Create it. The scope skill is often the first to fire, so it may need to create the README with the Phase Map and Status Matrix.

## Update Procedure

1. **Status Matrix** — Scope row should read `[Current]({filename})`. It's always current (cumulative doc).
2. **Phase Map** — Sync with scope doc's Phase Plan table. Add/remove/update phase rows as needed.
3. **Cross-Phase Dependencies** — Sync with scope doc's Cross-Phase Dependencies table.
4. **Current phase** — Update to reflect the active phase.
5. **Last updated** — Set to today's date.

## Status Values

- `—` = not started (no scope doc yet)
- `[Current]({filename})` = scope doc exists and is maintained

# README Dashboard Update Contract — Architecture Layer

After any architecture document update, update the subsystem's `README.md` dashboard.

## Location

The README lives at: `docs/{subsystem}/README.md`.

## Update Procedure

1. **Status Matrix** — Architecture row should read `[Current]({filename})`. It's always current (cumulative doc).
2. **Carry-Forward Contracts** — When a new interface is established at the architecture level, add a row to the Carry-Forward Contracts table.
3. **Last updated** — Set to today's date.

## Status Values

- `—` = not started (no architecture doc yet)
- `[Current]({filename})` = architecture doc exists and is maintained

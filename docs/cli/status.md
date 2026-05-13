# cortex status

Show the current synapse pin, its resolved SHA, and drift summary.

## Usage

```
./cortex status [--json]
```

## Description

Prints:

- The pin from `pins.toml` (or `latest` if no file).
- The resolved 40-char SHA.
- The pin kind (`tag`, `latest`, `main`, `sha`).
- Drift summary: count of drift exceptions, expired exceptions, and drifted
  artifacts (lockfile entries with `status != "installed"`).
- Path to the lockfile and counts of artifacts/externals it contains.

If the lockfile is missing, `status` reports it gracefully rather than
crashing — useful for fresh checkouts before `./cortex install`.

## Examples

```bash
./cortex status
./cortex status --json   # machine-readable for CI
```

## Related

- [`cortex pin`](pin.md)
- [`cortex bump`](bump.md)
- [`cortex doctor`](doctor.md)

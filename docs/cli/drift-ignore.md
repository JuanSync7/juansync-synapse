# cortex drift ignore

Add a `[drift_exceptions]` entry to `pins.toml` so `cortex doctor` stops reporting a drift finding.

## Usage

```
./cortex drift ignore <artifact> [--reason TEXT] [--expires DATE]
```

## Description

Records the current source-tree hash as an acknowledged exception. Doctor's drift scanner will skip the artifact while:

1. The recorded hash still matches the current hash (any further edit re-fires drift).
2. `expires` is in the future, or empty (never).

If `--expires` is omitted, a warning is printed encouraging the user to set one — pin-rot-style staleness is the only mechanism that surfaces these exceptions later.

## Options

| Flag | Description |
|------|-------------|
| `--reason TEXT` | Free-form note recorded with the exception |
| `--expires DATE` | ISO date `YYYY-MM-DD`; after this date drift re-fires |

## Output

`Ignored drift in <key> until <date>` (or `indefinitely`).

## Related

- [`cortex doctor`](doctor.md)
- [`cortex drift adopt`](drift-adopt.md)
- [`cortex pin`](pin.md)

# cortex bump

Freeze a floating pin (`latest` or `main`) to its current resolved value.

## Usage

```
./cortex bump
```

## Description

Resolves the current pin and writes the concrete value back to `pins.toml`:

- `latest` → highest stable semver tag (e.g. `v2026.05.0`); falls back to
  `sha:<HEAD-of-main>` if no stable tag exists.
- `main` → `sha:<resolved-sha>`.
- Already a tag or `sha:`: idempotent — reports "already frozen" and exits 0.

Always prints `before -> after`.

## Examples

```bash
./cortex bump            # freeze latest → v2026.05.0
./cortex bump            # idempotent on a frozen pin
```

## Related

- [`cortex pin`](pin.md)
- [`cortex unpin`](unpin.md)
- [`cortex status`](status.md)

# cortex unpin

Reset the synapse pin to `latest`.

## Usage

```
./cortex unpin
```

## Description

Equivalent to `./cortex pin latest`. Removes any specific tag/sha/main pin and
resumes tracking the latest stable semver tag.

## Examples

```bash
./cortex unpin
```

## Related

- [`cortex pin`](pin.md)
- [`cortex bump`](bump.md)
- [`cortex status`](status.md)

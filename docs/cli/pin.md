# cortex pin

Pin synapse to a specific version (tag, branch, or commit).

## Usage

```
./cortex pin <tag|"latest"|"main"|"sha:HEX">
```

## Description

Writes `pins.toml` (alongside `installed.lock`) recording the user's intended
synapse version. The pin is validated and resolved against the local repo
before being written — invalid or unresolvable pins fail loudly.

Pin grammar:

| Form              | Meaning                                              |
|-------------------|------------------------------------------------------|
| `vX.Y.Z[-pre.N]`  | Exact tag.                                           |
| `latest`          | Floating; highest stable semver tag at install time. |
| `main`            | Floating; current `origin/main` HEAD.                |
| `sha:HEX`         | Exact commit (HEX is 7+ hex chars).                  |

If no `pins.toml` exists, the implicit pin is `latest`.

## Examples

```bash
./cortex pin v2026.05.0           # pin to a specific tag
./cortex pin latest               # track the latest stable release
./cortex pin main                 # track origin/main
./cortex pin sha:abcdef1234       # pin to a specific commit
```

## Related

- [`cortex unpin`](unpin.md)
- [`cortex bump`](bump.md)
- [`cortex status`](status.md)

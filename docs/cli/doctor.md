# cortex doctor

Scan installed.lock + pins.toml for drift, staleness, missing files, orphans, corruption, pin-rot, and submodule staleness.

## Usage

```
./cortex doctor [--json] [--severity-floor info|warn|error] [--skip cat1,cat2,...] [--threshold-days N]
./cortex doctor symlinks
./cortex doctor all [doctor flags...]
```

## Subcommands

- **(default)** — run the full 7-category scan against the resolved lockfile + pins.
- **symlinks** — legacy broken-symlink check across all harnesses (the previous `cortex doctor` behavior).
- **all** — run symlinks check then the full scan; exit code is the maximum of the two.

## Finding categories

| Category          | Severity | Means |
|-------------------|----------|-------|
| `drift`           | warn     | Recomputed source-path hash differs from lockfile `content_hash`. |
| `stale`           | warn     | Pin is `latest`/`main` and resolved SHA has moved past lockfile `synapse_sha`. |
| `missing`         | error    | Lockfile entry exists but `install_path` is missing or a broken symlink. |
| `orphaned`        | warn     | (a) Symlink under an install root points into the repo with no lockfile entry. (b) Lockfile entry's `source_path` no longer exists in the registry. |
| `corrupt`         | error    | Lockfile failed to parse, or a `content_hash` is malformed (not `sha256:<64 hex>`). |
| `pin-rot`         | warn     | Pinned tag is older than the threshold (default 90 days). |
| `submodule-stale` | info     | Pinned `external/<suite>` SHA is behind the upstream's latest stable tag. |

## Exit codes

After applying `--severity-floor`:

- `0` — no findings, only `info` findings, or all findings below the floor.
- `1` — at least one `warn`, no `error`.
- `2` — at least one `error`.

## Options

- `--json` — emit a JSON document `{findings, summary, exit_code, lockfile_path, repo_root}` to stdout.
- `--severity-floor info|warn|error` — drop findings strictly below the chosen severity. Default `info` (keep all).
- `--skip cat1,cat2,...` — comma-separated category names (Python identifiers: `pin_rot`, `submodule_stale`) to skip.
- `--threshold-days N` — pin-rot age threshold in days (default `90`).

## Surface enforcement

The exit code surfaces are intentional: `cortex install` and the pre-commit hook block on `error` only; CI blocks on `warn + error`; manual `cortex doctor` is informational. The CLI computes the right exit code; the calling surface decides how strict.

## Examples

```bash
# Default: human-readable table
./cortex doctor

# JSON for tooling
./cortex doctor --json

# Skip network-touching submodule check + tag age check
./cortex doctor --skip submodule_stale,pin_rot

# Treat info as no-finding
./cortex doctor --severity-floor warn

# Legacy symlink check
./cortex doctor symlinks

# Full check (symlinks + scan); exit = max
./cortex doctor all
```

## Related

- [`cortex doctor symlinks`](doctor-symlinks.md)
- [`cortex install`](install.md)
- [`cortex pin`](pin.md)
- [`cortex status`](status.md)

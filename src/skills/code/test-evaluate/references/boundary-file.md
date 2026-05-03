# Boundary classification — filesystem I/O

## Detection signals (filesystem)

- **Runtime tier (boundary-runtime):**
  - Builtins: `open()`, context-managed file handles.
  - `pathlib.Path`: `.open`, `.read_text`, `.write_text`, `.read_bytes`, `.write_bytes`, `.iterdir`.
  - `os`: `os.listdir`, `os.walk`, `os.scandir`, `os.remove`, `os.rename`.
  - `shutil`: `copy`, `copytree`, `move`, `rmtree`.
  - `tempfile`: `NamedTemporaryFile`, `TemporaryDirectory`, `mkstemp`.
  - Async: `aiofiles.open`.
  - Network filesystem clients: `s3fs`, `gcsfs`, `paramiko.SFTPClient`, `fsspec` adapters.
- **Logical tier (boundary-logical):**
  - Functions exported via `__all__` in `io/`, `storage/`, `loaders/`, `writers/` packages whose body invokes any runtime-tier signal above (directly or one hop down).
  - Wrapper functions like `load_config(path)`, `save_artifact(obj, path)` — public surface that hides runtime call.
- **Internal:**
  - Path validators (`is_safe_path`, `normalize_path`).
  - Format detectors / extension routers that branch on suffix without opening.
  - MIME-type sniffers operating on already-loaded bytes.

## Lifecycle pattern decision rules

- **Default → `tmp_path` fixture:** pytest's per-test temp directory for any read/write within a test. Auto-cleaned, isolated, no global state. Use this unless a rule below overrides.
- **`real-fs` (not `tmp_path`) when:** test exercises permission semantics (`chmod`, ACLs), symlink resolution, filesystem-specific behavior (case sensitivity on macOS/Linux, atomic rename across devices), or large-file streaming where temp dir size limits matter.
- **Object storage (S3/GCS/Azure Blob) → `ephemeral-container`:** spin up `minio` or `fake-gcs-server` via testcontainers. Do **not** use `vcrpy` — file APIs are too I/O heavy and chunked for cassette replay; cassettes will be huge and brittle.
- **Never recommend mocking `open()` globally** — surface as `over_mocking_warning`. Defeats the purpose of testing real I/O behavior (encoding, buffering, EOL, partial reads).

## Risk weight (formula)

- `external_dependency_risk = 2` (moderate — encoding mismatches, file locking, partial writes, EOL bugs occur but are less catastrophic than DB corruption or external API contract drift).

## Common over-mock anti-patterns to flag

- Mocking `pathlib.Path.read_text` to return a hand-crafted string — bypasses real encoding and EOL handling; flag as `over_mocking_warning`.
- Mocking `os.listdir` / `os.walk` to return canned filenames — masks real directory traversal, hidden-file, and ordering bugs.
- Mocking internal path-builders (e.g. `_resolve_artifact_path`) — these are pure; mocking them hides real composition logic. Flag as `over_mocking_warning`.
- Patching `builtins.open` at module scope — flag as high-severity `over_mocking_warning`.

## Out-of-scope

- Disk-full / EIO / ENOSPC simulation — fault-injection territory; classification only flags candidates, does not prescribe a harness.
- Network filesystem latency tuning, retry-budget verification — performance/reliability concern, separate evaluation track.

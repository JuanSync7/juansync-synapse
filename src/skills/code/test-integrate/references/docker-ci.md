# Docker CI Reference

CI configuration guidance for Docker-dependent integration tests.

## Tiered CI policy (staged rollout)

- **Push tier:** unit tests + mocked-integration tests only. Real integration tests run only on merge-to-main and nightly.
- Tier separation activates **after** integration suite runtime exceeds 5 minutes.
- Until threshold is reached: real integration tests can run on every push. Don't pre-optimize.

## Docker availability

- CI runner must have Docker daemon access:
  - GitHub Actions: `services:` block or self-hosted runner with Docker installed.
  - CircleCI: `setup_remote_docker` or `machine` executor.
- Locally: developers use Docker Desktop or rootless Docker.
- Skip-marker: tests requiring Docker should detect availability and skip with a clear message if unavailable.

```python
docker_available = shutil.which("docker") is not None
pytestmark = pytest.mark.skipif(not docker_available, reason="Docker not available")
```

## Resource limits

- Per-container: `mem_limit="512m"`, `cpu_quota` set to keep tests under 1 CPU each.
- Total integration suite must fit within CI runner budget (typically 7GB RAM, 2 CPU on default GHA).

## Image caching

- Pin image versions in code (no `latest`).
- Cache pulled images in CI: `actions/cache` for `/var/lib/docker` is unreliable; prefer warming images in a setup step.
- Use slim variants where possible (`postgres:16-alpine` over `postgres:16`).

```yaml
- name: Warm Docker images
  run: docker pull postgres:16-alpine && docker pull redis:7-alpine
```

## Network setup

- Default `bridge` network — never `host` (port collisions in concurrent CI jobs).
- Testcontainers allocates dynamic host ports; tests must read back via `get_exposed_port`.

## Parallelism

- Use `pytest-xdist` only if all containers are class-scoped or function-scoped (no shared module-scoped containers).
- Default: `-n 2` for the integration tier (more risks resource exhaustion).

## Cleanup

- `testcontainers-python` registers atexit cleanup automatically. Verify in CI logs that containers shut down — orphan containers leak runner resources.
- For docker-compose testcontainers: explicit `compose.stop()` in fixture teardown is required — atexit doesn't always fire.

## Cassette tests (vcrpy)

- Run on the push tier as well — they don't need Docker.
- Cassette files are checked into the repo; re-record only via explicit `--rerecord` flag.

## Failure diagnostics

- On CI failure: capture container logs (testcontainers exposes `get_logs()`) and upload as an artifact.
- Time-limit each integration test (`pytest-timeout` 60s default) to prevent hung containers.

## Out of scope

- Pattern selection: see `references/lifecycle-patterns.md`.
- Container scope and teardown: see `references/testcontainers-patterns.md`.

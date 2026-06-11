# Bandit Remediation Recipes

Loaded at [FIX-BANDIT]. Each entry: what bandit caught, the fix pattern, and the escalation rule.
Never suppress with `# nosec` without a reason recorded in the commit body. Refactor only — do not delete the security check.

---

## B101 — assert_used

What bandit caught: `assert` used in production code; stripped by Python's `-O` flag at runtime.

Fix: replace with an explicit `raise` in all non-test paths.

```python
# Before
assert user_id is not None, "user_id required"

# After
if user_id is None:
    raise ValueError("user_id required")
```

Escalation: none — mechanical fix. Keep `assert` only in `tests/` and `conftest.py`.

---

## B102 — exec_used

What bandit caught: `exec()` call allows arbitrary code execution.

Fix: replace with a direct function call. If dynamic dispatch is genuinely needed, use a registry dict.

```python
# Before
exec(f"handler_{action}(payload)")

# After
_HANDLERS = {
    "start": handle_start,
    "stop": handle_stop,
}
handler = _HANDLERS.get(action)
if handler is None:
    raise ValueError(f"Unknown action: {action!r}")
handler(payload)
```

Escalation: if `exec` is load-bearing in a plugin loader or dynamic evaluation engine, mark `requires-human-review` — "bandit architectural escalation".

---

## B103 — set_bad_file_permissions

What bandit caught: file or directory created with overly permissive mode bits.

Fix: use explicit restrictive permissions.

```python
# Before
os.chmod(path, 0o777)

# After — secrets / key material
os.chmod(path, 0o600)

# After — general data files readable by owner + group
os.chmod(path, 0o644)
```

Escalation: if the mode is intentionally broad for a shared service account, mark `requires-human-review` with note "verify intended permission scope".

---

## B104 — hardcoded_bind_all_interfaces

What bandit caught: `"0.0.0.0"` hardcoded as the bind address, exposing the service on all interfaces.

Fix: bind to `127.0.0.1` by default; allow `0.0.0.0` only via an explicit config flag.

```python
# Before
app.run(host="0.0.0.0", port=8080)

# After
import os
host = os.environ.get("BIND_HOST", "127.0.0.1")
app.run(host=host, port=8080)
```

Escalation: if binding to all interfaces is required in production (container, load-balanced service), mark `requires-human-review` — confirm intent with operator.

---

## B105 / B106 / B107 — hardcoded_password_*

What bandit caught: password, secret, or token literal in source code.

Fix: move to an environment variable. Never inline credentials.

```python
# Before
DB_PASSWORD = "s3cr3t!"

# After
import os
DB_PASSWORD = os.environ["DB_PASSWORD"]  # raises KeyError if unset — fail fast
```

Escalation: always mark `requires-human-review` with note "credential rotation required — confirm secret has not been committed to VCS history and rotate if so".

---

## B108 — hardcoded_tmp_directory

What bandit caught: `/tmp` or `/var/tmp` used directly — predictable path, race condition risk.

Fix: use `tempfile` to get a process-unique path.

```python
# Before
path = "/tmp/work_file.dat"

# After — anonymous file, auto-deleted on close
with tempfile.NamedTemporaryFile(delete=True) as f:
    f.write(data)

# After — directory you manage manually
work_dir = tempfile.mkdtemp(prefix="myapp_")
```

Escalation: none — mechanical fix.

---

## B110 — try_except_pass

What bandit caught: exception silently swallowed with `except: pass` or `except Exception: pass`.

Fix: log the exception at minimum; re-raise or return a structured error if the caller needs to know.

```python
# Before
try:
    result = risky_call()
except Exception:
    pass

# After
import logging
logger = logging.getLogger(__name__)

try:
    result = risky_call()
except Exception:
    logger.exception("risky_call failed; returning None")
    result = None  # or re-raise, or raise a domain error
```

Escalation: if the swallowed exception is a guard for optional functionality (e.g., optional import), mark `requires-human-review` — confirm silent failure is intentional and document it.

---

## B201 — flask_debug_true

What bandit caught: Flask app started with `debug=True` hardcoded, enabling the Werkzeug interactive debugger in any environment.

Fix: gate on an environment variable.

```python
# Before
app.run(debug=True)

# After
import os
debug = os.environ.get("FLASK_ENV") == "development"
app.run(debug=debug)
```

Escalation: none — mechanical fix.

---

## B301 — pickle

What bandit caught: `pickle.loads` / `pickle.load` on data that may be untrusted — pickle execution is arbitrary code.

Fix: replace with `json` for any data crossing a trust boundary. Reserve pickle for internal, same-process trusted data only.

```python
# Before
obj = pickle.loads(raw_bytes)

# After — untrusted/external input
import json
obj = json.loads(raw_bytes)

# Acceptable — internal trusted cache (document the trust assumption)
obj = pickle.loads(trusted_internal_bytes)  # trusted: written by this process only
```

Escalation: if pickle is used in a public API or message queue consumer, mark `requires-human-review` — "bandit architectural escalation". Migrating a pickle-based protocol is a breaking change.

---

## B303 / B324 — hashlib_insecure_md5 / hashlib_insecure_sha1

What bandit caught: MD5 or SHA-1 used — collision-vulnerable; not suitable for security purposes.

Fix: use SHA-256 or BLAKE2 for security purposes. If the hash is for a non-security purpose (cache key, content fingerprint), pass `usedforsecurity=False`.

```python
# Before
digest = hashlib.md5(data).hexdigest()

# After — security purpose (password derivation, HMAC, integrity check)
digest = hashlib.sha256(data).hexdigest()
# or
digest = hashlib.blake2b(data).hexdigest()

# After — non-security purpose (cache key, dedup fingerprint)
digest = hashlib.md5(data, usedforsecurity=False).hexdigest()
```

Escalation: if the algorithm is part of an external protocol (e.g., S3 ETag uses MD5), mark `requires-human-review` — cannot change unilaterally.

---

## B310 — urllib_urlopen

What bandit caught: `urllib.request.urlopen` called with a URL that may be attacker-controlled — SSRF risk.

Fix: validate scheme against an allowlist before fetching; use `requests` with an explicit timeout.

```python
# Before
from urllib.request import urlopen
resp = urlopen(user_supplied_url)

# After
import requests
from urllib.parse import urlparse

parsed = urlparse(user_supplied_url)
if parsed.scheme not in {"https"}:
    raise ValueError(f"Disallowed URL scheme: {parsed.scheme!r}")
resp = requests.get(user_supplied_url, timeout=10)
```

Escalation: if the URL source is internal configuration (not user input), document the trust scope and mark `requires-human-review` to confirm.

---

## B311 — random_for_cryptography

What bandit caught: `random` module used for security-sensitive values (tokens, passwords, nonces) — not cryptographically secure.

Fix: use the `secrets` module for anything security-sensitive.

```python
# Before
import random
token = random.hex(32)

# After
import secrets
token = secrets.token_hex(32)
```

`random` remains acceptable for non-security uses (shuffling playlists, Monte Carlo sampling, test data generation). Escalation: none for mechanical fix; mark `requires-human-review` if the token is already in use and rotation is needed.

---

## B501 — ssl_with_no_version / verify_False

What bandit caught: `verify=False` in an SSL/TLS context disables certificate validation — trivially MITMable.

Fix: never disable verification in production. For self-signed certs in dev, gate explicitly and never reach production.

```python
# Before
requests.get(url, verify=False)

# After — production
requests.get(url, verify=True)  # default; explicit for clarity

# After — self-signed cert in controlled dev/test environment
import os
ca_bundle = os.environ.get("INTERNAL_CA_BUNDLE", True)
requests.get(url, verify=ca_bundle)
```

Escalation: always mark `requires-human-review` with note "confirm CA bundle path or obtain a valid cert — `verify=False` must never reach production".

---

## B506 — yaml_load

What bandit caught: `yaml.load()` without a Loader argument deserializes arbitrary Python objects.

Fix: always use `yaml.safe_load()`.

```python
# Before
data = yaml.load(stream)

# After
data = yaml.safe_load(stream)
```

If full YAML object deserialization is genuinely needed, mark `requires-human-review` — confirm the input is fully trusted and document the trust boundary.

---

## B602 / B603 / B604 / B605 / B606 / B607 — subprocess_*

What bandit caught: subprocess called with `shell=True`, untrusted arguments, or an unvalidated executable path — command injection risk.

Fix: never use `shell=True` with any input that is not a compile-time constant. Always pass args as a list. Validate the executable path.

```python
# Before
subprocess.run(f"convert {user_file} output.png", shell=True)

# After
import shutil
convert_bin = shutil.which("convert")
if convert_bin is None:
    raise RuntimeError("ImageMagick 'convert' not found on PATH")
subprocess.run(
    [convert_bin, user_file, "output.png"],
    shell=False,
    check=True,
    timeout=30,
)
```

`shell=True` with a hardcoded string constant (no variable interpolation) is lower risk but still flagged — replace with list form for consistency.

Escalation: if subprocess is used in a core module, CI orchestration layer, or plugin execution path, mark `requires-human-review` — "bandit architectural escalation". Command construction logic in these locations requires a dedicated security review before refactoring.

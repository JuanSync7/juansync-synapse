---
name: secret-scanner
description: Scans a file for leaked secrets — auth headers, API keys, tokens, high-entropy strings
domain: testing
action: validator
type: internal
tags: [testing, security, secrets, cassette, vcrpy, lint]
---

# secret-scanner

Scans any text file for leaked secrets and emits a structured `SecretScanResult` report.
The tool is project-agnostic — no paths are hardcoded.  It is designed to integrate into
two pipeline steps:

- **`test-integrate` [CONVERT]** — called immediately after recording a vcrpy cassette.
  If any finding is detected the cassette is deleted and the conversion is aborted with
  the error code `cassette-secret-leak`.
- **`test-lint`** — called on source files to catch accidentally committed credentials.

---

## Description

The scanner reads the target file line by line and applies a catalogue of regular-expression
patterns covering:

- HTTP/YAML header fields that carry auth credentials (Authorization, Cookie, X-API-Key, etc.)
- Query-string parameters that carry key/token values (`api_key=`, `token=`, etc.)
- JSON body fields that carry sensitive data (`password`, `client_secret`, `refresh_token`, etc.)
- Generic high-entropy strings and well-known live-key prefixes (Stripe, AWS)

Every finding is redacted before it is stored or emitted: the tool records only the first
4 characters of the matched value followed by `***`.  Raw secret values are **never** logged
or written to any output stream.

---

## When to use

| Situation | Recommended call |
|---|---|
| After recording a vcrpy cassette | `secret_scanner <cassette>.yaml` |
| Pre-commit lint of a source file | `secret_scanner <source>.py --format text` |
| CI scan of a changed cassette directory | `secret_scanner <cassette>.yaml` (check exit code) |
| Human-readable audit during review | `secret_scanner <file> --format text` |

---

## Input / output contract

### CLI

```
python -m src.tools.testing.secret_scanner <file_path> [--format json|text]

Positional arguments:
  file_path       Path to the file to scan (cassette YAML, source file, or any text file).

Options:
  --format        Output format: 'json' (default) or human-readable 'text'.
```

### JSON output (default)

```json
{
  "file_path": "/abs/path/to/cassette.yaml",
  "has_secrets": true,
  "findings": [
    {
      "line_number": 42,
      "pattern_name": "authorization_bearer",
      "matched_text": "eyJh***",
      "severity": "critical"
    }
  ],
  "scan_timestamp": "2026-05-01T12:00:00+00:00"
}
```

### Text output (`--format text`)

Human-readable table written to stdout, suitable for terminal review.

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | File is clean — no secrets detected. |
| `1` | One or more secrets detected. |
| `2` | Tool error — unreadable file, missing argument, or import failure. |

In the `test-integrate` pipeline: exit code `1` triggers cassette deletion and aborts
conversion with `cassette-secret-leak`.

---

## Pattern catalogue

### Header patterns

Detected in any line — intended for vcrpy cassette `request.headers` / `response.headers`
blocks but also matches source files.

| Pattern name | Example match | Severity |
|---|---|---|
| `authorization_bearer` | `Authorization: Bearer eyJh...` | critical |
| `authorization_basic` | `Authorization: Basic dXNlcj...` | critical |
| `x_api_key_header` | `X-API-Key: abc123` | high |
| `x_stripe_signature` | `X-Stripe-Signature: t=1234,...` | high |
| `cookie_header` | `Cookie: session=abc; csrf=xyz` | high |
| `generic_token_header` | `X-Auth-Token: abc123` | high |
| `generic_secret_header` | `X-App-Secret: abc123` | high |
| `generic_key_header` | `X-Service-Key: abc123` | high |

### Query-string patterns

Detected in lines containing URI / URL values (e.g. cassette `uri:` field).

| Pattern name | Example match | Severity |
|---|---|---|
| `query_api_key` | `?api_key=abc123` | high |
| `query_token` | `?token=abc123` | high |
| `query_key` | `?key=abc123` | high |
| `query_secret` | `?secret=abc123` | high |
| `query_access_token` | `?access_token=abc123` | high |

### Body field patterns

Detected in lines containing JSON key/value pairs (e.g. cassette `body.string` or response body).

| Pattern name | Example match | Severity |
|---|---|---|
| `body_password` | `"password": "hunter2"` | critical |
| `body_token` | `"token": "abc123"` | high |
| `body_secret` | `"secret": "abc123"` | high |
| `body_client_secret` | `"client_secret": "abc123"` | critical |
| `body_api_key` | `"api_key": "abc123"` | high |
| `body_access_token` | `"access_token": "abc123"` | high |
| `body_refresh_token` | `"refresh_token": "abc123"` | high |

### Generic / high-entropy patterns

Applied to every line.

| Pattern name | Example match | Severity |
|---|---|---|
| `stripe_live_key` | `sk_live_abc123...` | critical |
| `aws_access_key` | `AKIAIOSFODNN7EXAMPLE` | critical |
| `high_entropy_base64` | 40+ character base64-like string | medium |

---

## Schema reference

### SecretFinding

| Field | Type | Description |
|---|---|---|
| `line_number` | `int` | 1-based line number where the pattern matched. |
| `pattern_name` | `str` | Identifier for the pattern that fired (see catalogue above). |
| `matched_text` | `str` | Redacted value: first 4 chars + `***`.  Never the raw secret. |
| `severity` | `"critical" \| "high" \| "medium"` | Severity rating. |

### SecretScanResult

| Field | Type | Description |
|---|---|---|
| `file_path` | `str` | Path to the scanned file. |
| `has_secrets` | `bool` | True if at least one finding was detected. |
| `findings` | `list[SecretFinding]` | All findings, ordered by `line_number`. |
| `scan_timestamp` | `datetime` | UTC timestamp when the scan ran. |

---

## Constraints

- **Python 3.11+, Pydantic v2, stdlib only** (`re`, `json`, `argparse`).
  No third-party secret-scanning libraries are used.
- **`matched_text` is always redacted** — first 4 characters of the raw matched value
  followed by `***`.  Raw values are never stored in any field, log line, or output stream.
- **The tool never logs raw secret values** at any verbosity level.
- **Project-agnostic** — no hardcoded paths.  The tool operates on whatever `file_path`
  is passed; it has no knowledge of the surrounding project layout.
- **Output is always written to stdout.**  Errors go to stderr.

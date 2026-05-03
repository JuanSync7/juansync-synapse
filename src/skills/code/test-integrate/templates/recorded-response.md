# Recorded-Response Template (vcrpy)

Loaded at the `[CONVERT]` step for items whose lifecycle pattern is `vcrpy`.
Defines the cassette-backed test scaffold, the secret scrubber, the cassette
shape, and the pre/post-record checklists the skill MUST honor.

## Test file scaffold (Python)

```python
"""Real-API integration tests for `{{module_path}}`.
Lifecycle pattern: vcrpy. Cassette: `{{cassette_path}}`.
Promoted from mock test: `{{prior_mock_test_path}}`.
"""
import pytest
import vcr

{{vcr_instance_name}} = vcr.VCR(
    cassette_library_dir="tests/cassettes/{{module_slug}}",
    record_mode="once",
    match_on=["method", "scheme", "host", "port", "path", "query"],
    filter_headers=[
        "authorization", "x-api-key", "cookie", "set-cookie",
        "x-auth-token", "proxy-authorization",
        # vendor-specific:
        # "x-stripe-signature", "x-github-token",
    ],
    filter_query_parameters=["api_key", "token", "key", "access_token"],
    filter_post_data_parameters=["password", "token", "secret", "client_secret"],
    before_record_response=scrub_response_body,
)

@pytest.mark.integration
@{{vcr_instance_name}}.use_cassette("{{test_name}}.yaml")
def test_{{test_name}}():
    # Real call against {{api_endpoint}} — recorded once, replayed thereafter.
    result = {{module}}.{{function_under_test}}({{args}})
    assert result.{{field}} == {{expected}}
    # Don't assert on timestamps, request-ids, or pagination cursors.
```

## `scrub_response_body` helper

```python
import re

_SECRET_KEYS = re.compile(r"(password|token|secret|api[_-]?key)", re.I)

def scrub_response_body(response):
    body = response.get("body", {}).get("string", b"")
    if not body:
        return response
    # JSON: redact matching keys.
    try:
        import json
        data = json.loads(body)
        _redact(data)
        response["body"]["string"] = json.dumps(data).encode()
    except Exception:
        pass
    return response

def _redact(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if _SECRET_KEYS.search(k):
                obj[k] = "REDACTED"
            else:
                _redact(v)
    elif isinstance(obj, list):
        for item in obj:
            _redact(item)
```

## Cassette YAML structure (illustrative — vcrpy generates)

```yaml
interactions:
- request:
    method: GET
    uri: https://{{sandbox_endpoint}}/v1/{{path}}
    headers:
      Accept: ['application/json']
      # Authorization filtered.
  response:
    status: {code: 200, message: OK}
    headers: {Content-Type: ['application/json']}
    body:
      string: '{"id": "abc", "token": "REDACTED"}'
version: 1
```

## Pre-record checklist (skill MUST verify before opening recorder)

1. Endpoint URL is non-production (compare against blocklist).
2. Filter lists configured with all required keys.
3. `record_mode="once"` set.
4. `before_record_response` scrubber registered.
5. Cassette directory writable.

## Post-record checklist (skill MUST verify after recording)

1. Run `secret_scanner` against the cassette file.
2. If any pattern matches `Bearer [A-Za-z0-9]{20,}`, `eyJ[A-Za-z0-9_-]+\.`,
   raw email/SSN, etc. → DELETE cassette, fail item with `cassette-secret-leak`.
3. Validate cassette is non-empty.
4. Run the test once in replay mode to confirm determinism.

## Re-record protocol

- Triggered ONLY by explicit `--rerecord` skill flag.
- Deletes existing cassette, opens recorder fresh.
- Same scrubbing + post-record checklist applies.

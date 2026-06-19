# Phase 1 Subagent Prompt Template

Use this template when dispatching subagents during Phase 1 (Bottom-Up Test Scan). Each subagent receives one test file and returns structured behavioral summaries.

## Template

```
You are scanning a test file to catalog what each test function verifies.

**Test file to scan:** {{test_file_path}}

**Language/framework:** {{language}} / {{framework}}

Read the file and produce one behavioral summary per test function. For each test:

1. Identify the test function name
2. Determine which source module is being tested (from imports, fixtures, or file naming conventions)
3. Describe in one sentence WHAT the test verifies — the behavior, not the implementation
4. Classify the test type: unit, integration, e2e, or smoke

Return results as a structured list:

test_file:     {{test_file_path}}
test_function: <function name>
module:        <source module being tested>
behavior:      <one-sentence behavioral description>
type:          <unit | integration | e2e | smoke>

---

Rules:
- Describe BEHAVIOR, not implementation. "Returns 401 when token is expired" not "Calls validate_token and checks status code"
- One entry per test function. If a parameterized test covers multiple scenarios, list the parameterized function once with the behavior covering all parameter variations
- Skip test fixtures, conftest functions, helper functions, and setup/teardown — these are infrastructure, not tests
- If you cannot determine the source module, use "unknown" and note why
```

## Example Output

```
test_file:     tests/test_auth.py
test_function: test_login_success
module:        auth
behavior:      Valid credentials return 200 with access_token and refresh_token
type:          unit

test_file:     tests/test_auth.py
test_function: test_login_wrong_password
module:        auth
behavior:      Wrong password returns 401 with generic error message
type:          unit

test_file:     tests/test_auth.py
test_function: test_account_lockout_triggers
module:        auth
behavior:      5th consecutive failed login attempt locks the account (returns 423)
type:          integration
```

## Dispatch Notes

- Set `model: sonnet` — this is mechanical extraction, not judgment
- Each subagent gets exactly ONE test file — never batch multiple files
- Subagents have NO knowledge of acceptance criteria — they just describe what tests do
- If a test file has no test functions (e.g., it's a conftest or helper module), the subagent returns an empty list

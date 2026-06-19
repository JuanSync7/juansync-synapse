# Gaming Patterns Reference

Loaded at [GAMING]. Documents all 7 AST-deterministic anti-patterns that `gaming_detector` flags.
Each pattern includes its concrete AST detection rule, why it games coverage, and a bad/good contrast.

---

## Pattern 1 — `pragma: no cover` Abuse

### Detection rule

AST walk finds a `# pragma: no cover` comment attached to a function whose body contains more than
one statement, or whose name appears in the module's `__all__` list. A single-statement body
(e.g. `pass` or `raise NotImplementedError`) on a private stub is the only legitimate use.

### Why this games coverage

The pragma silently removes lines from the denominator. Abusing it on real public logic makes
coverage metrics look healthy while hiding untested branches entirely.

### Bad

```python
# pragma: no cover
def process_payment(order_id: str) -> Receipt:  # public, 12 statements — excluded illegitimately
    charge = gateway.charge(order_id)
    if not charge.ok:
        raise PaymentError(charge.reason)
    ...
```

### Good

```python
# pragma: no cover
def _not_implemented_stub() -> None:  # single statement, private, non-exported
    raise NotImplementedError
```

---

## Pattern 2 — `assert True` / `assert 1` Padding

### Detection rule

Any test function whose every `Assert` node contains only a constant-truthy expression:
`ast.Constant` with `value in (True, 1)` or a non-empty string literal. A test with zero
non-constant assertions matches this pattern.

### Why this games coverage

Lines execute and the test passes, so branch coverage increments. The assertion carries no
information — it cannot fail on a real regression.

### Bad

```python
def test_user_created():
    user = create_user("alice")
    assert True          # meaningless — never fails
    assert 1             # meaningless — never fails
```

### Good

```python
def test_user_created():
    user = create_user("alice")
    assert user.username == "alice"
    assert user.is_active is True
```

---

## Pattern 3 — Tests with No Assertions

### Detection rule

A function whose name starts with `test_` and whose AST body contains zero of: `Assert` nodes,
`pytest.raises` context managers, `.assert_called*` / `.assert_any_call` / `.assert_called_once`
attribute calls, or `assertRaises` calls.

### Why this games coverage

The test function runs, exercises lines, and passes unconditionally. Any bug that changes return
values or side effects will not be caught.

### Bad

```python
def test_send_email():
    result = send_email("alice@example.com", "Hello")
    # result never checked — test is always green
```

### Good

```python
def test_send_email():
    result = send_email("alice@example.com", "Hello")
    assert result.status == "sent"
    assert result.recipient == "alice@example.com"
```

---

## Pattern 4 — Mocking the SUT (System Under Test)

### Detection rule

A test module imports module `X` and also calls `mock.patch('X.target_function')` where
`target_function` is the same function the test is asserting behavior on. Concretely: the patched
dotted path resolves to the function being tested, not a collaborator it calls.

### Why this games coverage

The SUT is replaced by a mock before the test body runs, so the real implementation is never
executed. Coverage lines mark green because the import executes, not the logic under test.

### Bad

```python
# Testing `payments.charge` — but also patching it away
@mock.patch("payments.charge")
def test_charge_succeeds(mock_charge):
    mock_charge.return_value = Receipt(ok=True)
    result = payments.charge(order)   # calling the mock, not the real function
    assert result.ok
```

### Good

```python
# Patch only the external gateway collaborator, not the SUT itself
@mock.patch("payments.gateway.submit")
def test_charge_succeeds(mock_submit):
    mock_submit.return_value = GatewayResponse(success=True)
    result = payments.charge(order)   # real charge() executes
    assert result.ok
```

---

## Pattern 5 — Copy-Paste Tests (AST Hash Dedup)

### Detection rule

AST-normalize each test body: strip docstrings, rename all local variables to positional
placeholders (`var0`, `var1`, …), then hash the resulting AST. Collisions across different test
function names in the same or sibling test files indicate copy-paste duplication.

### Why this games coverage

Duplicate tests inflate the test count and pass rate without increasing the set of distinct
behaviors exercised. Coverage lines run twice but cover nothing new.

### Bad

```python
def test_create_admin():
    user = create_user("admin", role="admin")
    assert user.role == "admin"   # structurally identical to test_create_viewer below

def test_create_viewer():
    user = create_user("viewer", role="viewer")
    assert user.role == "viewer"  # same AST shape — collides on hash
```

### Good

```python
@pytest.mark.parametrize("role", ["admin", "viewer", "editor"])
def test_create_user_role(role):
    user = create_user(role, role=role)
    assert user.role == role
```

---

## Pattern 6 — `_private` Attribute Assertions

### Detection rule

Any `Assert` node (or `.assert_called*` call) whose left-hand expression is an attribute access
where the attribute name starts with a single underscore and the object is the instance under test
(not a framework-internal like `self._mock`). Matches both value assertions
(`assert obj._state == x`) and mock verifications (`obj._cache.assert_called_once()`).

### Why this games coverage

Private attributes are implementation details. Tests that pin them break on safe refactors and
encourage keeping bad internal state public. They also invite writing code specifically to expose
private state rather than observable behavior.

### Bad

```python
def test_order_processed():
    order = Order(items=[item])
    order.process()
    assert order._status_code == 2   # testing private field
    assert order._internal_log != []  # brittle — couples test to internals
```

### Good

```python
def test_order_processed():
    order = Order(items=[item])
    order.process()
    assert order.is_processed()       # public method — observable behavior
    assert order.status == "complete"  # public property
```

---

## Pattern 7 — Self-Referential Test Helpers

### Detection rule

A helper function called from a test body that itself calls the SUT and re-asserts the same
condition the outer test is verifying. Detected by: (a) helper name starts with `assert_` or
`check_`, (b) helper body contains a direct call to the SUT function, and (c) the assertion in
the helper is structurally equivalent (same AST hash) to the assertion in the calling test.

### Why this games coverage

The helper creates a circular validation loop — the test is "proven" by running the code a second
time and checking the same thing. A bug that causes the SUT to return a wrong-but-consistent
value will pass both the test and the helper.

### Bad

```python
def assert_no_errors(processor, payload):
    result = processor.run(payload)   # re-runs the SUT
    assert result.errors == []        # same assertion as the test below

def test_processor_clean():
    result = processor.run(payload)
    assert result.errors == []
    assert_no_errors(processor, payload)  # circular — no new information
```

### Good

```python
def build_valid_payload() -> Payload:
    """Factory helper — no assertion, no SUT call."""
    return Payload(data="valid", version=2)

def test_processor_clean():
    result = processor.run(build_valid_payload())
    assert result.errors == []
    assert result.output is not None
```

---

## Detector Behavior

`gaming_detector` emits one `GamingAlert` per match, carrying: pattern id, file path, line number,
test function name, and a human-readable reason string. All alerts are attached to `AuditGapReport`
under `gaming_alerts[]`.

Per SKILL.md [GAMING] constraints: the audit MUST NOT auto-delete or rewrite any flagged test.
Alerts are diagnostic only — remediation is the developer's responsibility, optionally assisted by
`/code-test-generator` or `/code-test-fixer` in a separate session.

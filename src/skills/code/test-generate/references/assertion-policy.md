# Assertion Policy — pytest-style Python Tests

Loaded at [GENERATE] and [SCORE] nodes of the test-generate skill.
Use these rules to select and validate assertion patterns.

---

## 1. Equality vs Identity

**Use `==` for value comparison. Use `is` only for `None`, `True`, `False`, and other singletons.**

```python
# bad
assert result is "ok"
assert get_user() is expected_user

# good
assert result == "ok"
assert get_user() == expected_user
assert error is None
assert flag is True
```

---

## 2. Exception Assertions with `pytest.raises`

**Always pair `pytest.raises` with a `match=` regex to assert both exception type and message. Never assert type alone.**

```python
# bad
with pytest.raises(ValueError):
    parse_config(bad_input)

# good
with pytest.raises(ValueError, match=r"missing required field 'name'"):
    parse_config(bad_input)
```

---

## 3. Mock Call Assertions

**Use the right call assertion for the scenario. `assert_called_once_with` for strict single-call, `assert_called_with` for last-call only, `assert_not_called` for zero calls. Never use `assert mock.called` — it is a silent no-op bug that always passes.**

```python
# bad — mock.assert_called() returns a Mock; the assertion is meaningless
mock_send.assert_called()

# good
mock_send.assert_called_once_with(recipient="user@example.com", subject="Welcome")
mock_log.assert_not_called()
mock_save.assert_called_with({"id": 1})  # only checks the last call
```

---

## 4. Float Equality with `pytest.approx`

**Use `pytest.approx` for any floating-point comparison. Set `rel` for proportional tolerance, `abs` for near-zero values where relative error is undefined.**

```python
# bad
assert score == 0.9999999

# good — relative tolerance (default 1e-6)
assert compute_score(data) == pytest.approx(1.0, rel=1e-4)

# good — absolute tolerance for values near zero
assert residual == pytest.approx(0.0, abs=1e-8)
```

---

## 5. Parametrize for Branch Coverage

**Use `@pytest.mark.parametrize` when multiple inputs exercise distinct branches or edge cases. Assign a readable `id` per case. Do not loop over a list inside a single test.**

```python
# bad
def test_validate():
    for value in [-1, 0, 256]:
        assert not is_valid_port(value)

# good
@pytest.mark.parametrize("port,expected", [
    (-1,  False),
    (0,   False),
    (80,  True),
    (256, True),
    (65535, True),
    (65536, False),
], ids=["neg", "zero", "http", "mid", "max", "overflow"])
def test_is_valid_port(port, expected):
    assert is_valid_port(port) == expected
```

---

## 6. Structural + Value Pairing

**Every test must include both a structural assertion (type, shape, length, key presence) and a value assertion (equality, range, raises). Neither alone is sufficient.**

```python
def test_build_index_response():
    result = build_index_response(docs=["a", "b"])

    # structural
    assert isinstance(result, dict)
    assert "count" in result
    assert "ids" in result
    assert len(result["ids"]) == 2

    # value
    assert result["count"] == 2
    assert result["ids"][0] == "doc-0"
```

---

## 7. Mock with `spec=`

**Always pass `spec=ClassName` when mocking class instances. This causes attribute access on non-existent methods to raise `AttributeError` at test time instead of silently returning a Mock.**

```python
# bad — typo goes undetected
client = Mock()
client.retreive()  # no error, returns Mock

# good — typo raises AttributeError immediately
client = Mock(spec=VectorStoreClient)
client.retreive()  # AttributeError: Mock object has no attribute 'retreive'
```

---

## 8. Snapshot / Golden File Usage

**Use snapshot or golden-file assertions only when the output is large, structured, and human-reviewable (JSON, XML, rendered HTML). Never snapshot scalar values, error messages, or single-field results.**

```python
# bad — snapshot overkill for a string
def test_greeting(snapshot):
    assert greet("Alice") == snapshot  # just use == "Hello, Alice"

# good — snapshot for a large serialized document
def test_ingest_pipeline_output(snapshot):
    result = run_ingest(fixture_pdf)
    assert result.to_json() == snapshot  # ~200-line JSON blob
```

---

## 9. Banned Anti-Patterns

**These patterns are unconditionally rejected at [SCORE]. Remove or replace them.**

```python
assert True                        # proves nothing
assert 1                           # proves nothing
assert x == x                      # tautology
assert isinstance(x, type(x))      # always True
assert mock.called                 # silent no-op; returns Mock object
# self-mocking the unit under test — never patch the module being tested
# AST-hash-duplicate tests — no two tests may be structurally identical
```

---

## 10. Hypothesis Property Tests

**Use `@given` with typed strategies. Use `assume()` to filter invalid inputs rather than if-guards. Never `print` inside tests. Set `@settings(deadline=...)` for slow invariants to prevent flaky timeouts.**

```python
from hypothesis import given, assume, settings
from hypothesis import strategies as st

@given(st.integers(min_value=1), st.text(min_size=1))
@settings(deadline=500)  # ms; explicit for slow invariants
def test_encode_decode_roundtrip(size, text):
    assume(len(text) <= size)  # filter, not if-guard
    encoded = encode(text, size)
    assert decode(encoded) == text  # value assertion
    assert isinstance(encoded, bytes)  # structural assertion
```

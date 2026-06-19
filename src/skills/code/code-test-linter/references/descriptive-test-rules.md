# Descriptive-Test Docstring Contract

This is the canonical reference for the descriptive-test docstring contract. The CR memo
introduced this system — this document is where the rules live in full detail. The
`code-test-linter` skill validates this contract at [RUN-EACH-LINTER]; `code-test-generator` enforces
it as a hard gate before committing any generated test.

---

## Why This Contract Exists

LLM-generated tests can be syntactically valid and pass CI while testing nothing meaningful.
Common gaming patterns include:

- **Tautology tests** — assert that a value equals itself, or that a mock returns what it was told to return.
- **Mocked-only tests** — every real call is mocked out; the test exercises no production logic.
- **Parametrize-spam** — dozens of `@pytest.mark.parametrize` cases that all test the same trivial branch with slightly different literals.

These tests consume coverage budget and produce false confidence. The docstring contract
breaks the pattern by requiring every test function to explicitly declare what it targets,
what scenario it covers, what behavior it verifies, and where it sits in the test pyramid.
A test without this metadata cannot be reviewed, traced to a requirement, or evaluated for
quality — so it fails the gate.

---

## Required Tags

Every `test_*` function MUST have a docstring containing all four of the following tags.

### `@tests`

Dotted path to the function (or method) under test.

```
@tests: chunker.split_text
@tests: pipeline.ingest.nodes.embed.EmbedNode.run
```

Used for traceability — downstream tools can build a coverage map from `@tests` values.
Must be a dotted identifier, not a prose description.

### `@scenario`

One-line description of the input condition or test setup.

```
@scenario: input contains emoji and combining characters
@scenario: config sets chunk_size to 0
```

Describes *what is true about the world* when the test runs. If the scenario requires
two facts, write the most discriminating one; do not write a novel.

### `@asserts`

One-line description of the behavior being verified.

```
@asserts: chunk boundaries don't split graphemes
@asserts: ValueError is raised with a message containing "chunk_size"
```

Describes *what the test checks*, not how it checks it. "returns a list" is too weak;
"returns chunks where no chunk exceeds max_size tokens" is right.

### `@layer`

Test pyramid layer. Must be exactly one of these six values (case-sensitive):

| Value | Meaning |
|---|---|
| `unit` | Isolated function or class; no I/O, no network |
| `config` | Validates config loading, defaults, and validation logic |
| `contract` | Verifies schema or interface contracts between modules |
| `idempotency` | Verifies repeated calls produce the same result |
| `mock-integration` | Integration-level test with external deps mocked |
| `real-integration` | Integration-level test against live services or files |

Any other value triggers `INVALID_LAYER_VALUE`.

---

## Optional Tag

### `@generation_id`

Required ONLY for LLM-generated tests. Format: `<YYYY-MM-DD>-<short-hash>`.

```
@generation_id: 2026-04-28-abc123
```

Used to trace a test back to the `code-test-generator` run that produced it, enabling audit
and rollback. Human-authored tests MUST NOT carry this tag. If present but malformed,
emit `MALFORMED_GENERATION_ID`.

---

## Canonical Example

```python
def test_chunker_handles_unicode_grapheme_clusters():
    """
    @tests: chunker.split_text
    @scenario: input contains emoji and combining characters
    @asserts: chunk boundaries don't split graphemes
    @layer: unit
    @generation_id: 2026-04-28-abc123
    """
    text = "Hello \U0001F600̀ world"
    chunks = split_text(text, max_size=5)
    for chunk in chunks:
        assert is_grapheme_safe(chunk), f"Chunk splits a grapheme: {chunk!r}"
```

---

## Validation Rules and Issue Codes

The validator emits one `LintIssue` per missing or invalid tag — do NOT collapse multiple
violations into a single issue. Each issue maps to exactly one code:

| Code | Condition |
|---|---|
| `MISSING_DOCSTRING` | Test function has no docstring at all. Emit this single issue; do not additionally emit the four missing-tag codes for the same function. |
| `MISSING_TESTS_TAG` | Docstring present but `@tests` is absent or has an empty value. |
| `MISSING_SCENARIO_TAG` | Docstring present but `@scenario` is absent or has an empty value. |
| `MISSING_ASSERTS_TAG` | Docstring present but `@asserts` is absent or has an empty value. |
| `MISSING_LAYER_TAG` | Docstring present but `@layer` is absent or has an empty value. |
| `INVALID_LAYER_VALUE` | `@layer` is present and non-empty but the value is not one of the six allowed pyramid layers. |
| `MALFORMED_GENERATION_ID` | `@generation_id` is present but does not match `YYYY-MM-DD-<hash>` (e.g., `2026-04-28-abc123`). |

### Anti-pattern: tag present but empty

A tag line like `@scenario:` (colon with nothing after, or only whitespace) is treated as
absent. Emit the corresponding `MISSING_*_TAG` code — do not treat whitespace-only values
as valid.

---

## What Counts as a Test Function

The validator scopes to files matching:

- `tests/**/*.py`
- `**/test_*.py`
- `**/*_test.py`

Within those files, a test function is any `def` whose name starts with `test_`.

**Excluded from validation:**

- Functions decorated with `@pytest.fixture` — these are test infrastructure, not test cases.
- Functions whose name does NOT start with `test_` — helper functions, setup utilities, and so on.

Apply these exclusions before emitting any issues to avoid false positives on fixtures and
shared helpers inside test files.

---

## AST-Based Parsing (Not Regex)

Use Python's `ast` module to parse test files. For each `FunctionDef` in scope:

1. Check that the node name starts with `test_`.
2. Check decorators — if any decorator resolves to `pytest.fixture`, skip the function.
3. Call `ast.get_docstring(node)` to extract the docstring.
4. If `None` is returned, emit `MISSING_DOCSTRING` and move on.
5. Otherwise, parse the docstring text for each required tag.

Do NOT use regex on raw file content. Line continuations, multiline docstrings, indentation
variation, and decorator stacking all make raw-text regex unreliable. AST parsing gives you
the actual docstring string after Python has already handled these cases.

---

## How Findings Flow Downstream

Descriptive-test violations are partitioned into `LintReport.descriptive_test_violations`
— a dedicated list that is also included in the top-level `issues` list. Surfacing them
separately lets downstream skills act on them independently:

- **`code-test-fixer`** reads `descriptive_test_violations` to add or correct missing tags without
  touching unrelated lint issues.
- **`code-test-generator`** blocks on any `MISSING_DOCSTRING` or `MISSING_*_TAG` violation in
  files it is about to extend — it will not write new tests into a file that already
  violates the contract.

The partition does not remove violations from `issues`; the total issue count remains
accurate for summary reporting.

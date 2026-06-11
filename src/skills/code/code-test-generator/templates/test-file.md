# Canonical Test File Template

Loaded at the `[GENERATE]` node of the `code-test-generator` skill. Every generated test file must
conform to this skeleton. Deviations must be justified in the generation trace.

---

## 1. File Header Docstring

The first statement in every test file is a module-level docstring. It must include:

- A one-line plain-English summary of what module is under test.
- An `@module_under_test` tag with the full dotted import path of the subject module.

```python
"""Tests for the document chunking utilities.

@module_under_test: src.ingest.chunking.utils
"""
```

---

## 2. Imports Block

Order strictly: `from __future__ import annotations` → stdlib → third-party → first-party
(`src.*`) → local fixtures / conftest re-exports. One blank line between each group.

```python
from __future__ import annotations

import json
import pathlib
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from hypothesis import given, settings, example
from hypothesis import strategies as st

from src.ingest.chunking import utils as chunking_utils
from src.common.schemas import ChunkConfig

from tests.conftest import sample_document  # noqa: F401  (re-exported fixture)
```

---

## 3. Constants and Test Fixtures

Declare module-level constants above fixtures. Fixtures carry type hints on both the function
signature and the `yield`/`return` value.

Use `autouse=True` **only** when the side effect must apply to every test in the file without
exception (for example, resetting a global registry). Default is `autouse=False`.

```python
_CHUNK_SIZE = 512
_OVERLAP = 64
_LONG_TEXT = "word " * 2000


@pytest.fixture()
def chunk_config() -> ChunkConfig:
    """Minimal valid ChunkConfig used across unit tests in this file."""
    return ChunkConfig(chunk_size=_CHUNK_SIZE, overlap=_OVERLAP, strategy="fixed")


@pytest.fixture()
def tmp_corpus(tmp_path: pathlib.Path) -> pathlib.Path:
    """Write a small text corpus to a temp directory; cleaned up automatically."""
    corpus = tmp_path / "corpus.txt"
    corpus.write_text(_LONG_TEXT)
    return corpus
```

---

## 4. Mock Setup Helpers

Name private factory functions `_mock_<dependency>(...)`. Always pass `spec=` so attribute
typos fail at test time rather than silently returning another `MagicMock`.

```python
def _mock_tokenizer(vocab_size: int = 32_000) -> Mock:
    tok = Mock(spec=chunking_utils.Tokenizer)
    tok.encode.side_effect = lambda text: list(range(min(len(text), vocab_size)))
    tok.vocab_size = vocab_size
    return tok


def _mock_storage_backend() -> Mock:
    backend = Mock(spec=chunking_utils.StorageBackend)
    backend.write.return_value = {"status": "ok"}
    return backend
```

---

## 5. Test Class vs. Flat Function Convention

| Condition | Convention |
|---|---|
| Fewer than 8 tests targeting the same function | Flat module-level functions |
| 8 or more tests, or tests share stateful fixtures | `class TestFoo:` grouping |
| Integration surface with setup/teardown | `class` with `setup_method` / `teardown_method` |

Class names follow `TestFunctionName` (PascalCase). Flat functions follow
`test_<function>_<scenario>` (snake_case). Both conventions may coexist in one file when a
module exports many small functions and one large one.

---

## 6. Example Unit Test

Complete test demonstrating: 5-tag docstring, mock wiring, act step, and ≥2 assertions
(one structural, one value).

```python
def test_chunk_text_returns_non_empty_list_for_valid_input(
    chunk_config: ChunkConfig,
) -> None:
    """
    @tests: src.ingest.chunking.utils.chunk_text
    @scenario: valid UTF-8 input longer than one chunk window
    @asserts: returns a non-empty list; every chunk is a non-empty string within size bound
    @layer: unit
    @generation_id: tg-2026-04-30-001
    """
    tokenizer = _mock_tokenizer()
    text = "The quick brown fox. " * 100  # ~2100 chars, well above _CHUNK_SIZE

    result = chunking_utils.chunk_text(text, config=chunk_config, tokenizer=tokenizer)

    # structural assertion — correct container type and non-empty
    assert isinstance(result, list) and len(result) > 0

    # value assertion — every element is a non-empty string within configured bound
    for chunk in result:
        assert isinstance(chunk, str) and 0 < len(chunk) <= _CHUNK_SIZE * 6
```

---

## 7. Example Parametrized Test

Use `@pytest.mark.parametrize` with explicit `ids=` (human-readable, not auto-generated
integers). Add a brief per-case note as an inline comment on each parameter tuple.

```python
@pytest.mark.parametrize(
    ("text", "expected_count"),
    [
        ("",                    0),   # empty string → no chunks
        ("short",               1),   # single token below window → one chunk
        ("word " * 200,        None), # long input → count depends on tokenizer
    ],
    ids=["empty_string", "single_token", "long_document"],
)
def test_chunk_text_count_by_input_length(
    text: str,
    expected_count: int | None,
    chunk_config: ChunkConfig,
) -> None:
    """
    @tests: src.ingest.chunking.utils.chunk_text
    @scenario: parametrized — empty / short / long input produces expected chunk count
    @asserts: chunk count matches expected_count when not None; positive count otherwise
    @layer: unit
    @generation_id: tg-2026-04-30-002
    """
    tokenizer = _mock_tokenizer()

    result = chunking_utils.chunk_text(text, config=chunk_config, tokenizer=tokenizer)

    if expected_count is not None:
        assert len(result) == expected_count
    else:
        assert len(result) > 0
```

---

## 8. Example Hypothesis Test

Add `@settings(max_examples=100)` explicitly. Pin at least one known edge with `@example`.
The 5-tag docstring stays; `@layer` must read `property`.

```python
@settings(max_examples=100)
@example(text="", chunk_size=128, overlap=0)          # empty input edge
@example(text="x", chunk_size=1,   overlap=0)          # single-char minimum window
@given(
    text=st.text(min_size=0, max_size=4096),
    chunk_size=st.integers(min_value=64, max_value=1024),
    overlap=st.integers(min_value=0, max_value=63),
)
def test_chunk_text_no_data_loss_property(
    text: str, chunk_size: int, overlap: int
) -> None:
    """
    @tests: src.ingest.chunking.utils.chunk_text
    @scenario: arbitrary valid input — re-joining chunks must recover all whitespace-
               normalised tokens present in the original text
    @asserts: union of chunk tokens is a superset of original tokens; no chunk exceeds
              chunk_size * 6 characters
    @layer: property
    @generation_id: tg-2026-04-30-003
    """
    config = ChunkConfig(chunk_size=chunk_size, overlap=overlap, strategy="fixed")
    tokenizer = _mock_tokenizer()

    chunks = chunking_utils.chunk_text(text, config=config, tokenizer=tokenizer)

    # structural: every element is a string, no chunk exceeds size bound
    for chunk in chunks:
        assert isinstance(chunk, str)
        assert len(chunk) <= chunk_size * 6

    # value: token-level round-trip — no tokens silently dropped
    original_tokens = set(text.split())
    recovered_tokens = set(tok for chunk in chunks for tok in chunk.split())
    assert original_tokens <= recovered_tokens
```

---

## 9. Cleanup Convention

| Resource | Pattern |
|---|---|
| File system | `tmp_path` fixture (pytest built-in); never `tempfile` directly |
| Environment variables | `monkeypatch.setenv` / `monkeypatch.delenv`; auto-reverted |
| Long-lived objects | `yield` fixture — setup before `yield`, teardown after |
| Mocked globals | `patch` as context manager inside the test, or `mocker.patch` |

```python
@pytest.fixture()
def isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip prod credentials from env so tests never touch live backends."""
    monkeypatch.delenv("WEAVIATE_API_KEY", raising=False)
    monkeypatch.setenv("CHUNKING_ENV", "test")


@pytest.fixture()
def open_index(tmp_path: pathlib.Path):
    """Open a transient on-disk index; close and remove it after the test."""
    idx = chunking_utils.DiskIndex.open(tmp_path / "idx")
    yield idx
    idx.close()
```

---

## 10. Append vs. Create Rule

- **File does not exist** → create `tests/<mirrored_path>/test_<module>.py` using this
  skeleton in full.
- **File already exists** → append new test functions or classes to the existing file.
  Match its style: existing import order, fixture names, class grouping, and docstring tag
  values. Do **not** introduce a second file for the same module under test.
- Before appending, scan the existing file for a matching `@generation_id` — if one exists
  for the same scenario, update it in place rather than duplicating.

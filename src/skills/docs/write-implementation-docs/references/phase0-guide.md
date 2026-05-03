# Phase 0 Derivation Guide

## What Phase 0 Contains

Phase 0 defines the shared type surface for the entire implementation. Every `implement-code` task agent works against these contracts. A mistake here propagates to every task section.

Include:
| Type | Source | How to include |
|---|---|---|
| TypedDicts and Dataclasses | Design doc Part B CONTRACT entries | Copy verbatim |
| Exception Classes | Design doc Part B CONTRACT entries | Copy verbatim |
| Function/Method Stubs | Design doc Part B CONTRACT entries | Copy verbatim (stubs only — no implementation) |
| Pure Utilities | Design doc Part B CONTRACT entries | Copy fully implemented |
| Error Taxonomy | Derived from exception classes + spec | Write as table (see format below) |
| Integration Contracts | Derived from task Dependencies + design doc | Write as directional patterns (see format below) |

## Contract vs Pattern Distinction

Design doc Part B has two entry types. **Only CONTRACT entries belong in Phase 0.**

| Type | Description | What it looks like | What to do |
|---|---|---|---|
| **CONTRACT** | TypedDicts, dataclasses, exception classes, function stubs, pure utilities. Defines the interface. | Stable signature, `raise NotImplementedError("Task N")` body, full docstring | Copy verbatim into Phase 0 |
| **PATTERN** | Illustrative algorithms, implementation approaches, data structure choices with rationale. Shows one possible how. | Has algorithmic logic, often labelled "Illustrative pattern" | Do NOT include here. Pass directly to implement-code task agents only, never to test agents. |

If the design doc lacks contract entries, derive them from task descriptions and spec requirements. Flag to human before proceeding — derived contracts are lower confidence than design-doc contracts.

## Stub Format

```python
def retrieve_documents(query: str, config: RetrievalConfig) -> list[Document]:
    """Retrieve documents matching the query from the vector store.

    Args:
        query: Natural language query string. Must not be empty.
        config: Retrieval configuration — top-k, score threshold, and filters.

    Returns:
        List of documents ordered by relevance score descending.

    Raises:
        RetrievalError: If the vector store is unavailable.
        ValueError: If query is empty or config is invalid.
    """
    raise NotImplementedError("Task 2")
```

Rules:
- `raise NotImplementedError("Task N")` as the sole body — never `pass`, never placeholder comments, never pseudocode
- `"Task N"` must match the task number that will implement this stub
- Docstrings document ALL parameters, return values, and every exception that appears in the error taxonomy
- If a stub appears in multiple tasks' sections, it is inlined in each — they reference the same Phase 0 definition

## Error Taxonomy Table

Derive from the exception classes in Phase 0. One row per exception type.

| Error Type | Trigger Condition | Expected Message Format | Retryable | Raising Module |
|---|---|---|---|---|
| `RetrievalError` | Vector store unavailable | `"Vector store unavailable: {detail}"` | Yes | `src/retrieval/engine.py` |
| `EmbeddingError` | Embedding model timeout | `"Embedding timeout after {seconds}s"` | Yes | `src/retrieval/embedder.py` |
| `ValueError` | Empty query or invalid config | `"Query cannot be empty"` | No | `src/retrieval/engine.py` |

Rules:
- Every exception class defined in Phase 0 must appear in this table
- If retryable is unknown, write "Unknown — caller decides"
- Message format uses `{variable}` placeholders for dynamic parts
- Raising Module is the source file, not the package — callers use this to set expectations

## Integration Contracts

Show directional module-to-module call patterns. These specify the call graph and error propagation expectations that `write-engineering-guide` and `write-test-docs` will rely on.

```
engine.py → embedder.embed_query(query: str) → list[float]
  Called when: processing each incoming query
  On EmbeddingError: engine surfaces to caller unchanged (does not retry — caller decides)

engine.py → store.search(vector: list[float], config: RetrievalConfig) → list[Document]
  Called when: after embedding succeeds
  On RetrievalError: engine surfaces to caller unchanged
```

Rules:
- Always show direction with `→` — never "A and B interact" (ambiguous who calls whom)
- One entry per call relationship (A → B and B → C are separate entries)
- Always show what the caller does when the callee raises — this drives test planning later
- If error propagation is "re-raise unchanged", say that explicitly — "surfaces to caller" is a common pattern

## Pure Utilities

Pure utilities are fully implemented in Phase 0 — they have no stubs. They are deterministic, have no external dependencies, and are safe to use by any task or test agent.

```python
def normalize_score(score: float) -> float:
    """Returns score clamped to [0.0, 1.0]."""
    return max(0.0, min(1.0, score))

def truncate_text(text: str, max_chars: int) -> str:
    """Truncates text to max_chars, appending '...' if truncated."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."
```

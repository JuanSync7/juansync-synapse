# LangGraph Architect — State Schema Patterns
#
# Annotated patterns for designing LangGraph state schemas.
# Each pattern: name, when to use, annotated code.

import operator
from typing import Annotated, Optional, TypedDict

# ── Pattern: Accumulating list ──────────────────────────────────────────
# Use when: multiple nodes append to the same field (messages, documents, errors)
# Key: reducer annotation prevents last-write-wins — appends instead

class ChatState(TypedDict):
    messages: Annotated[list, operator.add]    # every node appends, nothing lost
    context: str                                # plain field — last-write-wins is fine


# ── Pattern: Error accumulator ──────────────────────────────────────────
# Use when: pipeline should continue on partial failure
# Key: nodes write empty list on success, error string on failure
#      terminal node checks if errors is non-empty

class ResilientPipelineState(TypedDict):
    data: dict
    errors: Annotated[list[str], operator.add]  # e.g., ["fetch_node: timeout", "parse_node: malformed"]
    result: Optional[dict]                       # None until terminal node


# ── Pattern: Optional stage flags ───────────────────────────────────────
# Use when: some stages are conditionally skipped based on config or prior output
# Key: Optional[T] with None default — routing checks for None to skip

class ConditionalPipelineState(TypedDict):
    document: str
    chunks: list[str]
    embeddings: Optional[list[float]]  # None = embedding stage was skipped
    summary: Optional[str]              # None = summarization stage was skipped


# ── Pattern: Counter for bounded cycles ─────────────────────────────────
# Use when: graph has a retry/refinement loop that must terminate
# Key: integer counter incremented each iteration, routing checks bound

class RefinementState(TypedDict):
    draft: str
    feedback: str
    iteration: int        # incremented by refine node
    max_iterations: int   # set in initial state, checked by router


# ── Pattern: Subgraph I/O mapping ──────────────────────────────────────
# Use when: parent graph delegates to a child subgraph
# Key: parent and child have SEPARATE schemas
#      parent maps specific fields into child input, reads child output

class ParentState(TypedDict):
    raw_document: str
    processed_chunks: list[str]  # written by subgraph result mapping

class ChildState(TypedDict):
    input_text: str              # mapped from parent.raw_document
    chunks: list[str]            # child's internal field, mapped to parent.processed_chunks


# ── Anti-pattern: Nested state ──────────────────────────────────────────
# WRONG — nodes reading into nested dicts creates hidden coupling

class BadState(TypedDict):
    context: dict  # { "retrieval": { "scores": [...], "docs": [...] } }
    # Nodes dig into context["retrieval"]["scores"] — fragile, untraceable

# RIGHT — flatten it

class GoodState(TypedDict):
    retrieval_scores: list[float]
    retrieval_docs: list[str]
    # Every field a node touches is visible at the top level

# LangGraph Architect — Error Handling & Retry Patterns
#
# Annotated patterns for error handling in LangGraph workflows.
# Each pattern: name, when to use, annotated code.

import operator
from typing import Annotated, Optional, TypedDict

from tenacity import retry, stop_after_attempt, wait_exponential


# ── Pattern: Error accumulator state ────────────────────────────────────
# Use when: pipeline should continue on partial failure and report at the end
# Key: errors field with list reducer — every node can append

class ResilientState(TypedDict):
    data: str
    errors: Annotated[list[str], operator.add]
    result: Optional[str]

def node_that_might_fail(state: dict) -> dict:
    try:
        result = do_work(state["data"])
        return {"result": result, "errors": []}  # empty list — reducer appends nothing
    except Exception as e:
        return {"result": None, "errors": [f"node_that_might_fail: {e}"]}

# Terminal node checks:
# if state["errors"]:
#     return {"result": f"Completed with {len(state['errors'])} errors"}


# ── Pattern: In-node retry (transient failures) ────────────────────────
# Use when: external service may flake (rate limit, timeout, 5xx)
# Key: retry is ENCAPSULATED — graph sees success or final failure
# Rule: never use graph-level cycles for retry

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,  # after final attempt, raise the actual exception
)
def _call_external_api(query: str) -> dict:
    """Retries are invisible to the graph."""
    # return api.call(query)
    return {}

def fetch_node(state: dict) -> dict:
    try:
        result = _call_external_api(state["query"])
        return {"api_result": result, "errors": []}
    except Exception as e:
        return {"api_result": None, "errors": [f"fetch_node: {e} (after 3 retries)"]}


# ── Pattern: Conditional routing on error ───────────────────────────────
# Use when: a failure should redirect to a fallback path, not stop the graph
# Key: node writes error to state, router checks and branches

def route_on_error(state: dict) -> str:
    if state.get("api_error"):
        return "fallback_node"   # degrade gracefully
    return "next_node"           # happy path

# builder.add_route("fetch_node", route_on_error)


# ── Pattern: Orchestrator-aware retry ───────────────────────────────────
# Use when: graph runs inside Temporal / Celery / similar
# Key: two layers of retry, each owning a different failure class
#
# Layer 1 — In-node (tenacity):
#   Handles: rate limits, transient HTTP errors, brief timeouts
#   Scope: 3 fast retries with backoff (seconds)
#   Why here: too fast/frequent for orchestrator overhead
#
# Layer 2 — Orchestrator (Temporal retry policy):
#   Handles: worker crash, deploy, resource unavailable, long outage
#   Scope: slow retries over minutes/hours
#   Why here: survives process death, has scheduling + visibility
#
# Rule: never retry the same failure class at both levels.
# If tenacity handles rate limits, Temporal should not also retry rate limits.


# ── Pattern: Fail-fast validation ───────────────────────────────────────
# Use when: bad input should stop the graph immediately, not accumulate errors
# Key: validation node at entry, route to END on failure

def validate(state: dict) -> dict:
    errors = []
    if not state.get("query"):
        errors.append("query is required")
    if not state.get("config"):
        errors.append("config is required")
    return {"validation_error": "; ".join(errors) if errors else None}

# Router: state["validation_error"] → END (fail fast)


# ── Anti-pattern: Graph-level retry loop ────────────────────────────────
# WRONG — using a cycle in the graph topology for retry
#
# fetch → check_error → router → (fetch again | continue)
#
# Problems:
# - Hard to bound (needs iteration counter in state)
# - State accumulates across retries (side effects compound)
# - Observability: graph looks like it has a cycle, not a retry
#
# RIGHT — retry inside the node with tenacity (see above)


# ── Anti-pattern: Silent exception swallowing ───────────────────────────
# WRONG:
# def bad_node(state):
#     try:
#         result = risky_call()
#     except Exception:
#         result = None  # silently lost — no one knows this failed
#     return {"result": result}
#
# RIGHT — write to errors, let downstream nodes/routing decide:
# def good_node(state):
#     try:
#         result = risky_call()
#         return {"result": result, "errors": []}
#     except Exception as e:
#         return {"result": None, "errors": [f"good_node: {e}"]}


def do_work(data):
    """Placeholder for actual work."""
    return data

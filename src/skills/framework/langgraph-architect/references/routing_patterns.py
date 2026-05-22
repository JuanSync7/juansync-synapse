# LangGraph Architect — Routing / Conditional Edge Patterns
#
# Annotated patterns for LangGraph routing and conditional edges.
# Each pattern: name, when to use, annotated code.

from langgraph.graph import END


# ── Pattern: Simple branch (2-3 paths) ─────────────────────────────────
# Use when: one decision point with a small number of outcomes
# Key: always include a default return — no silent dead-ends

def route_by_doc_type(state: dict) -> str:
    doc_type = state.get("doc_type", "unknown")
    if doc_type == "pdf":
        return "process_pdf"
    elif doc_type == "image":
        return "process_image"
    return "process_text"  # default — every router must have one


# ── Pattern: Guard route (short-circuit) ────────────────────────────────
# Use when: validation node wrote an error flag, graph should exit early
# Key: check for error FIRST, before any other routing logic

def guard_route(state: dict) -> str:
    if state.get("validation_error"):
        return END  # short-circuit — skip the rest of the graph
    return "process"


# ── Pattern: Quality gate (bounded cycle) ───────────────────────────────
# Use when: refinement loop that iterates until quality threshold or max iterations
# Key: ALWAYS check iteration count first — hard bound before quality check

def refinement_router(state: dict) -> str:
    # Hard bound — always terminates regardless of quality
    if state["iteration"] >= state["max_iterations"]:
        return "finalize"
    # Quality gate — can exit early if good enough
    if state.get("score", 0) >= state.get("threshold", 0.8):
        return "finalize"
    return "refine"  # loop back


# ── Pattern: Error-aware routing ────────────────────────────────────────
# Use when: a node might fail and the graph should route to fallback
# Key: node writes error to state, router checks it

def error_aware_route(state: dict) -> str:
    if state.get("api_error"):
        return "fallback_node"
    return "next_node"


# ── Pattern: Feature flag routing ───────────────────────────────────────
# Use when: optional pipeline stages controlled by config
# Key: config flags in state control which branches execute

def optional_stage_route(state: dict) -> str:
    config = state.get("pipeline_config", {})
    if config.get("enable_summarization", False):
        return "summarize"
    return "skip_to_output"


# ── Pattern: Map-reduce dispatch ────────────────────────────────────────
# Use when: processing a list of items through the same subgraph
# Key: use LangGraph's Send API for dynamic fan-out
#
# from langgraph.types import Send
#
# def dispatch_chunks(state: dict) -> list[Send]:
#     return [
#         Send("process_chunk", {"chunk": c, "index": i})
#         for i, c in enumerate(state["chunks"])
#     ]
#
# builder.add_conditional_edges("split", dispatch_chunks)
#
# Each Send creates a parallel execution of the target node.
# Results merge back via reducer on the state field.


# ── Anti-pattern: Router without default ────────────────────────────────

# WRONG — if doc_type is "csv", this returns None → silent dead-end
# def bad_router(state):
#     if state["doc_type"] == "pdf":
#         return "process_pdf"
#     elif state["doc_type"] == "image":
#         return "process_image"
#     # no default — what happens with doc_type="csv"?

# RIGHT — always return something
# def good_router(state):
#     ...
#     return "process_generic"  # catch-all default


# ── Anti-pattern: Complex routing logic ─────────────────────────────────
# If your router has more than 4-5 branches or nested conditions,
# the graph topology is too complex. Consider:
# 1. A dedicated classification node that writes a simple flag to state
# 2. A subgraph for the complex section
# 3. Breaking the graph into multiple smaller graphs

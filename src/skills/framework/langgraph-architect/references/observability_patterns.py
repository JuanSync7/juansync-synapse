# LangGraph Architect — Observability Patterns
#
# Annotated patterns for tracing, timing, and monitoring LangGraph workflows.
# Each pattern: name, when to use, annotated code.

import functools
import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)


# ── Pattern: Framework-agnostic node decorator ──────────────────────────
# Use when: you want timing + logging on nodes without coupling to a framework
# Key: decorator knows nothing about LangGraph — works on any state → dict function
# Rule: nodes must not import tracing libraries directly

def traced_node(fn: Callable) -> Callable:
    """Decorator: log node name, elapsed time, state keys read/written."""
    @functools.wraps(fn)
    def wrapper(state: dict) -> dict:
        node_name = fn.__name__
        input_keys = list(state.keys())
        start = time.monotonic()

        try:
            result = fn(state)
            elapsed_ms = (time.monotonic() - start) * 1000
            output_keys = list(result.keys()) if isinstance(result, dict) else []
            logger.info(
                "node=%s elapsed_ms=%.1f input_keys=%s output_keys=%s",
                node_name, elapsed_ms, input_keys, output_keys,
            )
            return result
        except Exception as e:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.error(
                "node=%s elapsed_ms=%.1f error=%s",
                node_name, elapsed_ms, e,
            )
            raise

    return wrapper

# Usage:
# @traced_node
# def fetch_context(state: dict) -> dict:
#     ...


# ── Pattern: Callback injection at execution time ──────────────────────
# Use when: you want LangGraph-native tracing (Langfuse, LangSmith, etc.)
# Key: callbacks are passed through config at runtime, never hardcoded
# Rule: the graph definition knows nothing about which tracer is active

# compiled = builder.compile(checkpointer=checkpointer)
#
# # Dev — no tracing
# result = compiled.run(state)
#
# # Production — Langfuse tracing
# from langfuse.callback import CallbackHandler
# result = compiled.run(state, config={
#     "callbacks": [CallbackHandler(public_key="...", secret_key="...")]
# })
#
# # Production — LangSmith tracing
# # Just set env vars: LANGCHAIN_TRACING_V2=true, LANGCHAIN_API_KEY=...
# # LangGraph auto-detects — no code change needed
#
# The compiled workflow wrapper passes config through transparently.
# Callers choose the tracer. The graph doesn't know or care.


# ── Pattern: Structured logging for debugging ───────────────────────────
# Use when: you need to debug graph execution without a full tracing backend
# Key: log at graph boundaries (entry, exit, routing decisions)

# def route_debug_wrapper(router_fn):
#     """Wrap a router function to log its decision."""
#     @functools.wraps(router_fn)
#     def wrapper(state: dict) -> str:
#         decision = router_fn(state)
#         logger.debug("router=%s decision=%s", router_fn.__name__, decision)
#         return decision
#     return wrapper
#
# builder.add_route("classify", route_debug_wrapper(route_by_type))


# ── Anti-pattern: Tracing inside nodes ──────────────────────────────────
# WRONG — node imports and uses tracing library directly
#
# def bad_node(state):
#     from langfuse import Langfuse
#     langfuse = Langfuse()
#     span = langfuse.span(name="bad_node")
#     result = do_work(state)
#     span.end()
#     return result
#
# Problems:
# - Node is coupled to Langfuse — can't swap tracers
# - Node breaks in environments without Langfuse configured
# - Tracing config is scattered across nodes instead of centralized
#
# RIGHT — use the decorator pattern above, or callback injection


# ── Anti-pattern: Hardcoded callbacks in compile ────────────────────────
# WRONG — tracer baked into the graph definition
#
# compiled = builder.compile(
#     checkpointer=checkpointer,
#     # callbacks=[LangfuseHandler()]  # DON'T — this can't be changed per-run
# )
#
# RIGHT — pass callbacks at execution time via config (see above)

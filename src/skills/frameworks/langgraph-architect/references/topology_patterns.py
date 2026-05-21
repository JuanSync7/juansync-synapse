# LangGraph Architect — Graph Topology Patterns
#
# Annotated patterns for LangGraph graph shapes.
# Each pattern: name, when to use, annotated code.

from langgraph.graph import END, StateGraph

# ── Pattern: Linear chain ───────────────────────────────────────────────
# Use when: stages run sequentially, no branching needed
# This is the default — don't reach for complexity unless you need it

# fetch → process → store → END
#
# builder.add_step("fetch", fetch_fn)
# builder.add_step("process", process_fn)
# builder.add_step("store", store_fn)
# builder.add_edge("fetch", "process")
# builder.add_edge("process", "store")
# builder.add_edge("store", END)
# builder.set_entry("fetch")


# ── Pattern: Conditional branch ─────────────────────────────────────────
# Use when: one decision point splits into 2-3 paths
# Key: MUST have a default route — silent dead-ends are bugs

# classify → router → (summarize | extract | fallback) → merge → END
#
# def route_by_type(state):
#     doc_type = state["doc_type"]
#     if doc_type == "article":
#         return "summarize"
#     elif doc_type == "table":
#         return "extract"
#     return "fallback"  # explicit default — never omit this
#
# builder.add_route("classify", route_by_type)


# ── Pattern: Fan-out / fan-in ───────────────────────────────────────────
# Use when: independent work can happen in parallel, then merge
# Key: every fan-out branch MUST converge at a merge point

# split → [branch_a, branch_b, branch_c] → merge → END
#
# Use conditional edges from split to dispatch to branches.
# Each branch writes to its own state field.
# Merge node reads all branch fields and combines.
#
# Anti-pattern: fan-out without fan-in (dangling branches that go to END separately).
# This makes it impossible to aggregate results.


# ── Pattern: Bounded cycle (refinement loop) ────────────────────────────
# Use when: iterative improvement with LLM feedback
# Key: exit condition MUST be visible in the routing function
#      NEVER rely solely on LLM output to break the loop

# draft → evaluate → router → (refine → evaluate ...) | finalize → END
#
# def should_continue(state):
#     if state["iteration"] >= state["max_iterations"]:
#         return "finalize"      # hard bound — always terminates
#     if state["score"] >= state["threshold"]:
#         return "finalize"      # quality gate
#     return "refine"            # loop back
#
# builder.add_route("evaluate", should_continue)

# Anti-pattern: unbounded cycle
#
# def bad_router(state):
#     if state["llm_says_done"]:   # LLM can say "not done" forever
#         return "finalize"
#     return "refine"              # no hard bound — can loop infinitely


# ── Pattern: Subgraph composition ───────────────────────────────────────
# Use when: a section of the graph is complex enough to warrant its own state schema
# Key: subgraph is built and compiled independently, added as a node to parent

# parent: ingest → [child_graph as "process"] → store → END
#
# child = workflow(ChildState)
# child.add_step("parse", parse_fn)
# child.add_step("chunk", chunk_fn)
# child.add_edge("parse", "chunk")
# child.add_edge("chunk", END)
# child.set_entry("parse")
# compiled_child = child.compile()
#
# parent = workflow(ParentState)
# parent.add_step("ingest", ingest_fn)
# parent.add_step("process", compiled_child)  # child graph as a node
# parent.add_step("store", store_fn)
# parent.add_edge("ingest", "process")
# parent.add_edge("process", "store")
# parent.add_edge("store", END)
# parent.set_entry("ingest")


# ── Pattern: Conditional passthrough (optional stage) ───────────────────
# Use when: a stage can be skipped based on config, both paths rejoin downstream
# Very common: optional reranking, optional summarization, optional enrichment
# Key: conditional edge skips the stage, both paths converge at the same node

# fetch → [route: enable_rerank?] → (rerank_documents | skip) → format_prompt → ...
#
# def optional_rerank_route(state):
#     if state.get("enable_reranking"):
#         return "rerank_documents"
#     return "format_prompt"  # skip directly to next stage
#
# builder.add_route("fetch", optional_rerank_route)
# builder.add_edge("rerank_documents", "format_prompt")  # rejoin
#
# The downstream node (format_prompt) must handle both cases:
# either reranked data exists or it doesn't. Use Optional[T] in state
# and check presence in the node.
#
# Anti-pattern: using a "passthrough" node that copies data.
# Just skip the stage entirely — no-op nodes add noise.
#
# Anti-pattern: phantom routing node.
# WRONG — creating a "virtual" routing target that isn't a real node:
#   validate → route_ocr_or_parse → (run_ocr | parse)
#   where route_ocr_or_parse is NOT in the nodes list
#
# Routing is always a conditional edge FROM a real node.
# If you need to branch on multiple conditions from one node,
# combine them into a single router function:
#
# def validate_and_route(state):
#     if state.get("validation_error"):
#         return END
#     if state["doc_type"] == "scanned_pdf":
#         return "run_ocr"
#     return "parse_document"  # default
#
# builder.add_route("validate", validate_and_route)
#
# One node, one conditional edge, multiple outcomes. No phantom nodes.


# ── Pattern: Early exit ─────────────────────────────────────────────────
# Use when: validation or guard checks can short-circuit the graph
# Key: place guard node early, route to END on failure

# validate → router → (process → store → END) | END
#
# def guard_route(state):
#     if state["validation_error"]:
#         return END             # short-circuit — skip everything
#     return "process"

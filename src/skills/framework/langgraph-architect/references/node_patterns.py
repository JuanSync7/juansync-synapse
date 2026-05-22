# LangGraph Architect — Node Design Patterns
#
# Annotated patterns for designing LangGraph nodes.
# Each pattern: name, when to use, annotated code.

from typing import TypedDict


# ── Pattern: Pure transform node ────────────────────────────────────────
# Use when: node does data transformation with no external calls
# Key: reads state, returns partial update — no side effects

def chunk_document(state: dict) -> dict:
    """Split document into chunks. Pure function — no I/O."""
    text = state["document"]
    chunks = [text[i:i+500] for i in range(0, len(text), 500)]
    return {"chunks": chunks}


# ── Pattern: I/O node ──────────────────────────────────────────────────
# Use when: node makes external calls (API, database, file system)
# Key: name it clearly (fetch_, store_, send_), isolate side effects here
# Rule: never mix I/O and transform logic in the same node

def fetch_context(state: dict) -> dict:
    """Retrieve context from vector store. I/O node — side effect."""
    query = state["query"]
    # db.search(query) — the side effect lives here, nowhere else
    results = []  # placeholder
    return {"context_docs": results}

def store_results(state: dict) -> dict:
    """Persist results to storage. I/O node — side effect."""
    # storage.put(state["results"]) — side effect
    return {"stored": True}


# ── Pattern: LLM node ──────────────────────────────────────────────────
# Use when: node invokes an LLM
# Key: LLM call only — no data transforms before or after in same node
# If you need to format prompt + call LLM + parse output,
# that's 1-2 nodes (format+call can share, parse is separate if complex)

def generate_summary(state: dict) -> dict:
    """Call LLM to summarize. Single responsibility — just the LLM call."""
    prompt = state["formatted_prompt"]
    # response = llm.invoke(prompt)
    response = ""  # placeholder
    return {"summary": response}

# Anti-pattern: god node
# def do_everything(state):
#     docs = db.search(state["query"])        # I/O
#     formatted = format_prompt(docs)          # transform
#     response = llm.invoke(formatted)         # LLM call
#     parsed = parse_response(response)        # transform
#     db.store(parsed)                         # I/O
#     return {"result": parsed}
# This is 4 nodes crammed into 1. Split it.


# ── Pattern: Guard / validation node ───────────────────────────────────
# Use when: early check that can short-circuit the graph
# Key: writes a flag to state, routing function checks the flag

def validate_input(state: dict) -> dict:
    """Check preconditions. Write error to state if invalid."""
    if not state.get("query"):
        return {"validation_error": "Query is required"}
    if len(state["query"]) > 10000:
        return {"validation_error": "Query exceeds max length"}
    return {"validation_error": None}

# Router checks: state["validation_error"] is None → continue, else → END


# ── Pattern: Merge node (fan-in) ───────────────────────────────────────
# Use when: multiple parallel branches converge
# Key: reads from all branch output fields, combines into unified result

def merge_results(state: dict) -> dict:
    """Combine outputs from parallel branches."""
    combined = {
        "text_results": state.get("text_branch_output", []),
        "image_results": state.get("image_branch_output", []),
    }
    return {"merged_results": combined}


# ── Pattern: Node with retry (transient failure) ───────────────────────
# Use when: node calls an external service that may flake
# Key: retry is INSIDE the node, invisible to the graph
# The graph sees success or final failure — never a retry loop in topology

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _call_api(query: str) -> list:
    """Retries are encapsulated here — graph doesn't know."""
    # return api.search(query)
    return []

def fetch_with_retry(state: dict) -> dict:
    """I/O node with internal retry. Graph sees success or final exception."""
    try:
        results = _call_api(state["query"])
        return {"api_results": results, "errors": []}
    except Exception as e:
        return {"api_results": [], "errors": [f"fetch_with_retry: {e}"]}


# ── Rule: Node independence ─────────────────────────────────────────────
# Nodes must NEVER:
# - Import or call another node function directly
# - Share module-level mutable state
# - Know about the graph topology (which node runs before/after them)
#
# Nodes ONLY communicate through the state dict.
# If node A's output is node B's input, that relationship is expressed
# as a state field + an edge in the graph — not a function call.

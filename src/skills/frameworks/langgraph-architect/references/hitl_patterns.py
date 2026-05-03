# LangGraph Architect — Human-in-the-Loop Patterns
#
# Annotated patterns for HITL checkpoints in LangGraph.
# Each pattern: name, when to use, annotated code.

from dataclasses import dataclass
from typing import Optional


# ── Shared contract: GateDecision ───────────────────────────────────────
# Every HITL gate returns this. Framework-agnostic — no LangGraph imports.

@dataclass
class GateDecision:
    approved: bool
    input: Optional[str] = None    # human's response text
    provisional: bool = False       # True if no human responded


# ── IMPORTANT: Two layers, not three options ────────────────────────────
#
# HITL in LangGraph has TWO complementary layers:
#
#   Layer 1 — COMPILE-TIME DIRECTIVE (where to pause):
#     interrupt_before / interrupt_after on compile()
#     Tells LangGraph which node triggers a pause.
#
#   Layer 2 — RUNTIME ABSTRACTION (what happens at the pause):
#     human_gate() inside the gate node
#     Handles the actual human interaction + provisional fallback.
#
# These are NOT alternatives. Use them TOGETHER:
#   1. Create a dedicated gate node that calls human_gate()
#   2. Compile with interrupt_before/after on that gate node (not the action node)
#   3. Route conditionally after the gate node based on human_decision
#
# WRONG: interrupt_before on "send_answer" + separate "approval_gate" node
#        (two mechanisms on the same gate — they conflict)
# WRONG: human_gate() inside a node without interrupt on compile
#        (human_gate works, but LangGraph doesn't know to pause)
# RIGHT: "approval_gate" node (calls human_gate()) + interrupt_after on
#        "approval_gate" + conditional edge to "send_answer"


# ── Pattern: Approval gate ──────────────────────────────────────────────
# Use when: human must approve BEFORE an action runs
# Most common pattern — use this as default
# Key: gate is its own node; interrupt is on the gate node, not the action

# graph: ... → approval_gate → [route: approved?] → execute_action → ...
#
# approval_gate node: calls human_gate(), writes GateDecision to state
# compile with: interrupt_before=["approval_gate"]
# conditional edge after approval_gate: approved → execute_action, else → END
#
# The graph pauses BEFORE approval_gate runs.
# Human is prompted via human_gate(). On resume, approval_gate completes,
# writes decision to state, and routing decides whether to proceed.


# ── Pattern: Inspection gate ────────────────────────────────────────────
# Use when: human needs to SEE output before the graph continues
# Less common — only use when output inspection is the goal

# graph: ... → generate_draft → inspect_gate → [route] → publish → ...
#
# inspect_gate node: calls human_gate(), writes GateDecision to state
# compile with: interrupt_after=["generate_draft"]
#
# generate_draft runs fully, THEN the graph pauses.
# Human inspects the draft via inspect_gate. On resume, routing decides.


# ── Pattern: Human input gate (data collection) ─────────────────────────
# Use when: the graph needs DATA from the human, not just approval
# Key: same two-layer pattern, but resume_with carries structured data

# def collect_input_gate(state):
#     decision = human_gate(
#         "What category should this document be? Options: technical, legal, financial",
#         provisional="technical"  # safe default for headless
#     )
#     return {"category": decision.input or "technical", "human_decision": decision}
#
# compile with: interrupt_before=["collect_input_gate"]


# ── Pattern: human_gate abstraction (Layer 2) ───────────────────────────
# The runtime abstraction. Called INSIDE gate nodes.
# Wraps interrupt with provisional fallback for headless execution.
# Rule: ALWAYS use this instead of calling langgraph.types.interrupt directly.

def human_gate(
    question: str,
    *,
    provisional=None,
) -> GateDecision:
    """Pause for human input. Falls back to provisional in headless mode."""
    try:
        from langgraph.types import interrupt
        human_response = interrupt(question)
        return GateDecision(approved=True, input=str(human_response))
    except ImportError:
        pass

    if provisional is not None:
        return GateDecision(approved=True, input=None, provisional=True)

    # No interrupt runtime, no provisional — log warning, auto-approve
    # Rule: this path should be avoided. Always provide a provisional.
    return GateDecision(approved=True, provisional=True)


# ── Checkpoint placement decision tree ───────────────────────────────────
#
# Step 1: Decide the GATE TYPE (what does the human do?)
#
#   A. Approve/reject before an action?  → approval gate node
#   B. Inspect output before continuing? → inspection gate node
#   C. Provide data the graph needs?     → input collection gate node
#
# Step 2: Decide the COMPILE DIRECTIVE (where does LangGraph pause?)
#
#   - Approval gate:    interrupt_before on the gate node
#   - Inspection gate:  interrupt_after on the preceding node
#   - Input collection: interrupt_before on the gate node
#
# Step 3: ALWAYS define inside the gate node:
#
#   - human_gate() call with a clear question
#   - provisional value for headless execution
#   - Write GateDecision to state
#
# Step 4: ALWAYS add a conditional edge AFTER the gate node:
#
#   - approved → next action node
#   - rejected/default → END or alternative path
#
# Step 5: Safety check
#
#   - Is the action destructive (delete, send, publish)?
#     → approval gate is MANDATORY, not optional
#   - Can this run headless?
#     → provisional is REQUIRED — define the safe default


# ── Anti-pattern: HITL without checkpointer ─────────────────────────────
# If you have interrupt_before/after, you MUST compile with a checkpointer.
# Without it, the graph cannot resume after the interrupt.
#
# WRONG:
#   compiled = builder.compile()  # no checkpointer
#   # interrupt_before will raise at runtime
#
# RIGHT:
#   compiled = builder.compile(checkpointer=get_checkpointer("memory"))


# ── Anti-pattern: HITL without provisional ──────────────────────────────
# WRONG:
#   human_gate("Approve this?")  # no provisional — headless auto-approves silently
#
# RIGHT:
#   human_gate("Approve this?", provisional="skip")  # explicit safe default

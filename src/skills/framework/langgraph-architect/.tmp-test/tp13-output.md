# TP13 — Autonomous Design Output
# Domain: E-Commerce Order Fulfillment
# Generated: 2026-04-04

---

## Part 1: Brief Validation

### Validation Result: VALID (with one assumption)

**Scope check**: Single cohesive transformation — validated order in, fulfillment record out. One graph is appropriate. No decomposition needed.

**Constraint analysis**:
- "inventory check must happen before payment" — clear sequential dependency
- "payment must be processed before shipping dispatch" — clear sequential dependency
- These two constraints together mandate strict ordering: check_inventory → process_payment → dispatch_shipping
- HITL placement ("after payment, before shipping") is consistent with the ordering constraints

**Contradiction surfaced — parallelism preference vs. ordering constraints**:
The brief states "prefer parallel processing where safe." However, all three known stages are chained by hard ordering constraints. No safe parallelism exists among the main pipeline stages. The only sub-task parallelism opportunity would be within stages (e.g., checking inventory for multiple line items concurrently), but the brief does not expose that granularity. The parallelism preference cannot be satisfied at the graph topology level without violating the constraints. This is documented as an assumption below.

**Quality criteria analysis**:
- "payment failure must not leave orphaned inventory reservations" — requires a compensating `release_inventory` node on the payment failure path. This node is NOT in the brief's `known_stages` but is required by this quality criterion. Adding it.
- "fraud review gate must have a provisional for headless CI" — HITL gate must define explicit auto-approve logic. Brief provides the rule: auto-approve orders under $500.

**Missing fields**: None critical. `context` field absent — acceptable.

---

## Part 2: Graph Spec

```yaml
graph:
  name: order_fulfillment_graph
  purpose: "Takes a validated order, checks inventory, processes payment, runs fraud review for high-value orders, dispatches shipping, and produces a FulfillmentRecord"

assumptions:
  - id: A1
    field: parallelism_preference
    decision: "No parallel processing at graph topology level. All three known stages (check_inventory, process_payment, dispatch_shipping) are chained by hard ordering constraints. Parallelism preference from brief cannot be satisfied without violating constraints."
  - id: A2
    field: compensating_nodes
    decision: "Added release_inventory node (not in brief's known_stages). Required by quality criterion: payment failure must not leave orphaned inventory reservations. This node calls the warehouse inventory DB to release the reservation on payment failure path."
  - id: A3
    field: release_payment_node
    decision: "Added release_payment node. Required for fraud rejection path: if fraud review rejects the order after payment has been charged, the payment must be voided/refunded before the graph exits."
  - id: A4
    field: fraud_review_threshold
    decision: "Provisional auto-approve threshold set at order.total < 500.0 (USD). This is deterministic and explicit — not silent auto-approve. Orders >= $500 that run headless will be auto-rejected (provisional=rejected) to prevent unsafe headless approval of high-value orders."
  - id: A5
    field: inventory_reservation
    decision: "Assumed check_inventory creates a reservation (soft hold) in the warehouse inventory DB, not just a read. The reservation_id is stored in state and used by release_inventory if payment fails."

state:
  schema_type: TypedDict
  fields:
    - name: order
      type: "Order"
      reducer: null
      written_by: []
      read_by: [validate_order, check_inventory, fraud_review_gate, finalize_fulfillment]

    - name: validation_error
      type: "Optional[str]"
      reducer: null
      written_by: [validate_order]
      read_by: [route_after_validate]

    - name: inventory_available
      type: "Optional[bool]"
      reducer: null
      written_by: [check_inventory]
      read_by: [route_after_inventory]

    - name: inventory_reservation_id
      type: "Optional[str]"
      reducer: null
      written_by: [check_inventory]
      read_by: [release_inventory, finalize_fulfillment]

    - name: payment_result
      type: "Optional[dict]"
      reducer: null
      written_by: [process_payment]
      read_by: [route_after_payment, finalize_fulfillment]

    - name: payment_charged
      type: "Optional[bool]"
      reducer: null
      written_by: [process_payment]
      read_by: [route_after_payment, release_payment]

    - name: fraud_decision
      type: "Optional[GateDecision]"
      reducer: null
      written_by: [fraud_review_gate]
      read_by: [route_after_fraud_review]

    - name: shipping_label
      type: "Optional[str]"
      reducer: null
      written_by: [dispatch_shipping]
      read_by: [finalize_fulfillment]

    - name: fulfillment_record
      type: "Optional[FulfillmentRecord]"
      reducer: null
      written_by: [finalize_fulfillment]
      read_by: []

    - name: errors
      type: "Annotated[list[str], operator.add]"
      reducer: operator.add
      written_by: [check_inventory, process_payment, release_inventory, release_payment, dispatch_shipping]
      read_by: [finalize_fulfillment]

nodes:
  - name: validate_order
    responsibility: "Validates required fields on the incoming Order object; writes validation_error if invalid"
    type: pure
    reads: [order]
    writes: [validation_error]
    retry: null

  - name: check_inventory
    responsibility: "Verifies stock availability for all order line items in the warehouse inventory DB and creates a soft reservation; writes inventory_available and inventory_reservation_id"
    type: io
    reads: [order]
    writes: [inventory_available, inventory_reservation_id, errors]
    retry: "3x exponential backoff (1s min, 10s max), transient only (timeout, 5xx, rate limit)"

  - name: process_payment
    responsibility: "Charges the customer via Stripe payment gateway; writes payment_result and payment_charged"
    type: io
    reads: [order, inventory_reservation_id]
    writes: [payment_result, payment_charged, errors]
    retry: "3x exponential backoff (1s min, 10s max), transient only (timeout, 5xx, rate limit). Auth errors and card declines are NOT retried."

  - name: release_inventory
    responsibility: "Releases the inventory reservation in the warehouse DB (compensating action on payment failure); writes to errors if release itself fails"
    type: io
    reads: [inventory_reservation_id]
    writes: [errors]
    retry: "3x exponential backoff (1s min, 10s max), transient only"

  - name: fraud_review_gate
    responsibility: "HITL approval gate for high-value orders; calls human_gate() and writes fraud_decision; auto-approves orders under $500 as provisional"
    type: hitl
    reads: [order, payment_result]
    writes: [fraud_decision]
    retry: null

  - name: release_payment
    responsibility: "Voids or refunds the Stripe charge (compensating action on fraud rejection); writes to errors if release fails"
    type: io
    reads: [order, payment_result]
    writes: [errors]
    retry: "3x exponential backoff (1s min, 10s max), transient only"

  - name: dispatch_shipping
    responsibility: "Creates a shipping label and notifies the warehouse to prepare the shipment; writes shipping_label"
    type: io
    reads: [order, payment_result]
    writes: [shipping_label, errors]
    retry: "3x exponential backoff (1s min, 10s max), transient only"

  - name: finalize_fulfillment
    responsibility: "Assembles the FulfillmentRecord from order, payment_result, inventory_reservation_id, shipping_label, and errors; writes fulfillment_record"
    type: pure
    reads: [order, payment_result, inventory_reservation_id, shipping_label, errors]
    writes: [fulfillment_record]
    retry: null

edges:
  - from: dispatch_shipping
    to: finalize_fulfillment
  - from: finalize_fulfillment
    to: END

conditional_edges:
  - from: validate_order
    router: "route_after_validate — checks validation_error"
    routes:
      - condition: "validation_error is not None"
        to: END
      - condition: default
        to: check_inventory

  - from: check_inventory
    router: "route_after_inventory — checks inventory_available and errors"
    routes:
      - condition: "inventory_available is False OR errors non-empty from check_inventory"
        to: END
      - condition: default
        to: process_payment

  - from: process_payment
    router: "route_after_payment — checks payment_charged"
    routes:
      - condition: "payment_charged is False (payment failed)"
        to: release_inventory
      - condition: default
        to: fraud_review_gate

  - from: release_inventory
    router: "route_after_release_inventory — always exits"
    routes:
      - condition: default
        to: END

  - from: fraud_review_gate
    router: "route_after_fraud_review — checks fraud_decision.approved"
    routes:
      - condition: "fraud_decision.approved is False"
        to: release_payment
      - condition: default
        to: dispatch_shipping

  - from: release_payment
    router: "route_after_release_payment — always exits"
    routes:
      - condition: default
        to: END

hitl_checkpoints:
  - type: interrupt_before
    node: fraud_review_gate
    question: |
      "Order #{order.id} totaling ${order.total} has been charged successfully.
      Please review for potential fraud before shipping is dispatched.
      Order details: {order.items}, customer: {order.customer_id}.
      APPROVE to proceed with shipping, REJECT to void the charge."
    resume_with: "Boolean approval decision (true=approve, false=reject)"
    provisional: |
      "If order.total < 500.0: auto-approve (GateDecision(approved=True, provisional=True)).
      If order.total >= 500.0: auto-reject (GateDecision(approved=False, provisional=True)).
      Rationale: headless high-value orders are rejected by default to prevent unsafe auto-approvals in CI."

entry: validate_order
terminal: [END]

error_handling:
  accumulator: errors
  fallback_paths:
    - on_error_in: check_inventory
      route_to: END
      notes: "inventory_available=False or errors non-empty triggers exit without reservation"
    - on_error_in: process_payment
      route_to: release_inventory
      notes: "payment_charged=False triggers compensating release before exit"
    - on_error_in: fraud_review_gate
      route_to: release_payment
      notes: "fraud_decision.approved=False triggers payment void before exit"
    - on_error_in: dispatch_shipping
      route_to: finalize_fulfillment
      notes: "dispatch errors are accumulated and reported in fulfillment_record; payment is already charged — do not release automatically. Operator intervention required."

checkpointer: postgres
  # postgres required: graph has a HITL checkpoint (fraud_review_gate with interrupt_before)
  # postgres specified in integration.checkpointer in brief
  # factory: get_checkpointer("postgres") — never instantiate directly in graph code

execution:
  wrapper: OrderFulfillmentWorkflow
  sync: run()
  async: arun()
  stream: stream()
  notes: |
    "Callers MUST use OrderFulfillmentWorkflow wrapper. Never expose the raw compiled graph.
    stream() yields (step_name, state) tuples. Callers must not parse LangGraph internal event format.
    For Temporal integration: OrderFulfillmentWorkflow wraps the compiled graph and is invoked as a Temporal Activity."

observability:
  callbacks: "Langfuse injected at execution time via config dict (not hardcoded). LangSmith auto-detection via env vars as alternative."
  node_decorator: "@traced_node — logs node name, elapsed_ms, input_keys, output_keys, error if raised. Applied to all node functions. No tracing library imports inside nodes."

topology_diagram: |
  validate_order
    │ (validation_error → END)
    ↓
  check_inventory
    │ (unavailable or error → END)
    ↓
  process_payment
    │                    │
    │ (payment ok)       │ (payment failed)
    ↓                    ↓
  fraud_review_gate   release_inventory
    │         │              │
    │ (ok)    │ (rejected)   ↓
    ↓         ↓             END
  dispatch_shipping   release_payment
    │                       │
    ↓                       ↓
  finalize_fulfillment      END
    │
    ↓
   END
```

---

## Part 3: Self-Review Verdict

(Review subagent role: evaluating the above graph spec against rules.md)

```yaml
verdict: APPROVE

summary: >
  The graph spec correctly satisfies all ordering constraints, implements compensating
  actions for both payment failure and fraud rejection paths, and provides an explicit
  deterministic provisional for headless CI. No rules.md violations found. Two
  medium-priority recommendations are noted but do not block approval.

rule_checks:
  - rule: "State Design: reducer required for multi-writer fields"
    status: pass
    detail: >
      The only field written by multiple nodes is `errors`. It carries
      `Annotated[list[str], operator.add]` reducer. All other fields have a single
      writer. No last-write-wins collisions.

  - rule: "State Design: TypedDict required"
    status: pass
    detail: "Schema uses TypedDict. No validation methods needed — TypedDict is correct."

  - rule: "State Design: Optional fields with None default for flags"
    status: pass
    detail: >
      validation_error, inventory_available, inventory_reservation_id, payment_result,
      payment_charged, fraud_decision, shipping_label, fulfillment_record are all
      Optional[T] — no sentinel values used.

  - rule: "State Design: flat schema"
    status: pass
    detail: >
      All fields are top-level. No nested dicts that nodes read into. `Order` and
      `FulfillmentRecord` are typed objects (not raw dicts read into by nodes) —
      acceptable as passthrough types.

  - rule: "Node Design: single responsibility"
    status: pass
    detail: >
      Each node has one job. validate_order (pure transform), check_inventory (io, inventory DB),
      process_payment (io, Stripe), release_inventory (io, compensating), fraud_review_gate
      (hitl, gate only), release_payment (io, compensating), dispatch_shipping (io, warehouse),
      finalize_fulfillment (pure, assembly). No god nodes.

  - rule: "Node Design: no cross-node imports"
    status: pass
    detail: "Spec does not show any node-to-node imports. Nodes communicate only through state."

  - rule: "Node Design: no framework imports in nodes"
    status: pass
    detail: >
      fraud_review_gate uses human_gate() abstraction — not langgraph.types.interrupt directly.
      @traced_node decorator is framework-agnostic. No tracing library imports in node bodies.

  - rule: "Graph Topology: every conditional edge has a default"
    status: pass
    detail: >
      All five conditional edges have explicit default routes:
      route_after_validate → check_inventory (default),
      route_after_inventory → process_payment (default),
      route_after_payment → fraud_review_gate (default),
      route_after_fraud_review → dispatch_shipping (default),
      route_after_release_inventory → END (default),
      route_after_release_payment → END (default).

  - rule: "Graph Topology: no unbounded cycles"
    status: pass
    detail: "Graph is a DAG. No cycles present. No bounded-cycle pattern needed."

  - rule: "Graph Topology: fan-out must have fan-in"
    status: pass
    detail: >
      No fan-out topology. The graph is a linear chain with conditional exits.
      payment failure path and fraud rejection path both exit to END (not dangling branches
      that converge back in). Compensating nodes (release_inventory, release_payment) are
      linear exit paths — not dangling fan-out.

  - rule: "Graph Topology: prefer linear chain"
    status: pass
    detail: >
      The graph IS a linear chain with conditional exit branches. This is the correct
      minimal topology for the ordering constraints. Branching is justified (compensating
      actions on failure paths).

  - rule: "HITL: interrupt_before for approval gates"
    status: pass
    detail: >
      fraud_review_gate uses interrupt_before (human decides before shipping dispatch runs).
      This is the correct directive for an approval gate.

  - rule: "HITL: every checkpoint defines question, resume_with, provisional"
    status: pass
    detail: >
      fraud_review_gate defines: question (order details + approval prompt), resume_with
      (boolean approval decision), provisional (order.total < 500 → auto-approve,
      >= 500 → auto-reject). Provisional is explicit and deterministic.

  - rule: "HITL: provisional must be explicit and deterministic"
    status: pass
    detail: >
      Provisional logic is rule-based on order.total threshold. Not silent auto-approve.
      High-value headless orders default to REJECT — safer than auto-approve. This is
      a conservative, deterministic default.

  - rule: "HITL: use human_gate() abstraction"
    status: pass
    detail: "fraud_review_gate calls human_gate(). No direct langgraph.types.interrupt usage."

  - rule: "Checkpointing: non-none if HITL exists"
    status: pass
    detail: "checkpointer: postgres. HITL checkpoint exists. Requirement satisfied."

  - rule: "Checkpointing: use factory, not direct instantiation"
    status: pass
    detail: "Spec notes: get_checkpointer('postgres') factory pattern."

  - rule: "Execution: callers use wrapper"
    status: pass
    detail: "OrderFulfillmentWorkflow wrapper defined. raw compiled graph not exposed."

  - rule: "Error Handling: retry inside node, not graph cycles"
    status: pass
    detail: >
      All io nodes specify in-node tenacity retry (3x exponential, transient only).
      No graph-level retry cycles in topology.

  - rule: "Error Handling: write errors to state, not silent swallow"
    status: pass
    detail: >
      All io nodes write to errors accumulator on failure. release_inventory and
      release_payment also write errors if their compensating calls fail.

  - rule: "Error Handling: error accumulator with list reducer"
    status: pass
    detail: "errors field: Annotated[list[str], operator.add]."

  - rule: "Error Handling: orchestrator retry for infrastructure failures"
    status: pass
    detail: >
      Brief specifies Temporal orchestrator. Spec delegates infrastructure-level retry
      to Temporal. In-node tenacity handles fast/transient failures. No duplication.

  - rule: "Retry: max 3 attempts, exponential backoff, transient only"
    status: pass
    detail: "All io nodes specify 3x exponential (1s min, 10s max), transient only."

  - rule: "Retry: never retry auth/validation errors"
    status: pass
    detail: >
      process_payment explicitly notes: auth errors and card declines are NOT retried.
      Other io nodes follow the transient-only pattern.

  - rule: "Observability: callbacks via config, not hardcoded"
    status: pass
    detail: "Langfuse injected at execution time via config dict."

  - rule: "Observability: no tracing imports in nodes"
    status: pass
    detail: "@traced_node decorator is framework-agnostic. No tracing imports in node bodies."

  - rule: "Observability: node decorator logs name, elapsed, keys, error"
    status: pass
    detail: "@traced_node contract: node name, elapsed_ms, input_keys, output_keys, error if raised."

topology_analysis:
  dead_ends: []
  unbounded_cycles: []
  orphan_nodes: []
  missing_fan_in: []

hitl_analysis:
  checkpoints_without_provisional: []
  checkpointer_missing: false

risk_flags:
  - >
    dispatch_shipping failure path: if shipping dispatch fails after payment is charged,
    the spec routes to finalize_fulfillment with errors accumulated. Payment is NOT
    automatically released on dispatch failure (by design — operator intervention required).
    This is the correct conservative choice (partial fulfillment is preferable to automatic
    refund on a transient dispatch error), but operators must have a runbook for this case.
    Not a rules.md violation — a production readiness note.

  - >
    release_inventory and release_payment are compensating io nodes with retry, but if
    they fail after exhausting retries, the error is accumulated in state and the graph
    exits. There is no dead-letter queue or escalation path defined in the spec. For
    production, a monitoring alert on errors containing "release_inventory" or
    "release_payment" strings is strongly recommended. Not a rules.md violation.

recommendations:
  - priority: medium
    description: >
      Add a note in execution.notes that Temporal should be configured with an alert
      on fulfillment_record.errors containing "release_" prefixes, to catch orphaned
      reservations or charges that survived retry exhaustion.

  - priority: medium
    description: >
      The fraud_review_gate question template uses string interpolation placeholders
      ({order.id}, {order.total}, etc.). The spec should clarify that these are
      resolved inside the node before passing to human_gate(), not passed as raw
      template strings. Minor implementation clarity issue.

  - priority: low
    description: >
      The parallelism preference from the brief is completely unaddressed at graph level.
      If the business later needs to check inventory for multiple warehouses in parallel
      or perform multiple payment method attempts, check_inventory and process_payment
      could be promoted to subgraphs with internal fan-out. Document this as a known
      extension point.
```

---

## Part 4: Design-Review Cycle Summary

- **Cycle 1**: Initial design produced and self-reviewed.
- **Result**: APPROVE — no failures, no high-priority recommendations.
- **Unresolved issues**: None. Two medium-priority and one low-priority recommendations are advisory.
- **Final status**: Graph spec approved. Ready for implementation.

# LangGraph Architect — Evaluation Criteria

## Structural Criteria

Structural criteria are evaluated by improve-skill's baseline checklist against the SKILL.md document itself. Not duplicated here.

## Output Criteria

Binary pass/fail criteria for evaluating what the skill produces when run.

**Design Mode Output (Graph Spec):**

- [ ] **EVAL-O01:** Graph spec contains all required sections
  - **Test:** Verify the output contains every non-optional section from the graph_spec.md template: `graph` (name + purpose), `state` (with fields), `nodes`, `edges` or `conditional_edges`, `entry`, `terminal`, `checkpointer`, `execution`. Count sections present vs required.
  - **Fail signal:** One or more required sections are missing entirely from the output.

- [ ] **EVAL-O02:** State field traceability is complete
  - **Test:** For each field in the `state.fields` list, verify that `written_by` contains at least one node and `read_by` contains at least one node. Then cross-check: every node name in `written_by`/`read_by` must appear in the `nodes` list.
  - **Fail signal:** A state field lists a node that doesn't exist in `nodes`, or a state field has an empty `written_by` or `read_by` (orphan field that nothing reads/writes).

- [ ] **EVAL-O03:** Node I/O matches state field declarations
  - **Test:** For each node, verify every entry in its `reads` list appears as a state field name, and every entry in its `writes` list appears as a state field name. Conversely, check that the node appears in the corresponding field's `written_by`/`read_by`.
  - **Fail signal:** A node claims to read/write a field that doesn't exist in the state schema, or a node's reads/writes contradict the field's `written_by`/`read_by` lists.

- [ ] **EVAL-O04:** Graph is topologically connected from entry to terminal
  - **Test:** Starting from the `entry` node, trace all edges (direct and conditional) to verify every node in the `nodes` list is reachable. Verify that every path eventually reaches a node in the `terminal` list or END.
  - **Fail signal:** An unreachable node exists (not on any path from entry), or a path exists that never reaches a terminal/END (dead-end).

- [ ] **EVAL-O05:** Every conditional edge has a default route
  - **Test:** For each entry in `conditional_edges`, verify that its `routes` list contains at least one entry with `condition: default`.
  - **Fail signal:** A conditional edge exists where no route has `condition: default`.

- [ ] **EVAL-O06:** Multi-writer state fields have reducers
  - **Test:** For each state field where `written_by` contains more than one node, verify the `reducer` field is present and non-empty.
  - **Fail signal:** A state field is written by 2+ nodes but has no reducer specified.

- [ ] **EVAL-O07:** HITL checkpoints have all three required components
  - **Test:** For each entry in `hitl_checkpoints`, verify the presence and non-empty values of: `question`, `resume_with`, and `provisional`.
  - **Fail signal:** A HITL checkpoint is missing `question`, `resume_with`, or `provisional`, or any of these is empty/null.

- [ ] **EVAL-O08:** Checkpointer is consistent with HITL presence
  - **Test:** If `hitl_checkpoints` is non-empty, verify `checkpointer` is NOT `none`. If `hitl_checkpoints` is empty, `checkpointer` can be any value.
  - **Fail signal:** HITL checkpoints exist but `checkpointer` is set to `none`.

- [ ] **EVAL-O09:** Node types are correctly assigned
  - **Test:** For each node, verify the `type` field matches the node's behavior: `pure` for data transforms only, `io` for external calls (API, DB, LLM), `hitl` for nodes that call `human_gate()`. No node typed `pure` should have I/O or suspension in its responsibility. No `hitl` node should be labeled `pure` or `io`.
  - **Fail signal:** A node that calls human_gate() is typed as `pure` or `io`. A node that makes external calls is typed as `pure`. A node that only transforms data is typed as `io`.

- [ ] **EVAL-O10:** Node single-responsibility is maintained
  - **Test:** For each node, read its `responsibility` field. Verify no node describes both data transformation AND external I/O, or both LLM invocation AND data parsing/formatting.
  - **Fail signal:** A node's responsibility contains compound actions spanning multiple concern categories.

- [ ] **EVAL-O11:** Graph spec purpose statement is specific
  - **Test:** Read `graph.purpose`. Verify it names the specific domain/use-case. It should describe what goes in, what comes out, and the core transformation.
  - **Fail signal:** Purpose is generic (e.g., "orchestrates a workflow" or "processes inputs to produce outputs").

- [ ] **EVAL-O12:** HITL uses two-layer pattern correctly
  - **Test:** For each HITL checkpoint, verify: (1) there is a dedicated gate node of type `hitl`, (2) the compile directive (interrupt_before/after) targets the gate node or its predecessor, (3) there is a conditional edge AFTER the gate node routing on the decision. No checkpoint should have both a gate node AND an interrupt on a separate downstream action node.
  - **Fail signal:** A graph spec has a gate node AND an interrupt_before on the action node for the same checkpoint (dual mechanism conflict), or a HITL checkpoint has no conditional routing after the gate.

- [ ] **EVAL-O13:** Execution section is present and complete
  - **Test:** Verify the graph spec contains an `execution` section with wrapper name, sync/async/stream methods defined.
  - **Fail signal:** Execution section is missing or incomplete.

- [ ] **EVAL-O14:** Scope check was performed for complex requests
  - **Test:** For requests spanning multiple domains or containing contradictory requirements, verify the skill pushed back, recommended decomposition, or surfaced contradictions BEFORE producing a graph spec.
  - **Fail signal:** The skill produced a monolithic graph spec for a multi-domain request without flagging scope concerns, or silently resolved contradictory requirements without surfacing them.

**Review Mode Output (Review Verdict):**

- [ ] **EVAL-O15:** Review verdict contains all required sections
  - **Test:** Verify the output contains: `verdict` (one of APPROVE/REVISE/REJECT), `summary`, `rule_checks` (non-empty list), `topology_analysis`, `hitl_analysis`, and `recommendations`.
  - **Fail signal:** One or more required sections are missing from the review verdict.

- [ ] **EVAL-O16:** Rule checks cite specific violations
  - **Test:** For each rule_check with `status: fail`, verify `detail` names a specific node, field, or edge from the graph spec being reviewed.
  - **Fail signal:** A failing rule check says "the graph violates X rule" without naming the specific element that violates it.

- [ ] **EVAL-O17:** Verdict is consistent with rule check results
  - **Test:** If any rule_check has `status: fail`, verdict must not be `APPROVE`. If all rule_checks are `pass` and no recommendation has `priority: high`, verdict must be `APPROVE`.
  - **Fail signal:** Verdict is APPROVE despite failing rule checks, or verdict is REVISE/REJECT when all checks pass and no high-priority recommendations exist.

- [ ] **EVAL-O18:** Topology analysis is performed (not skipped)
  - **Test:** Verify `topology_analysis` contains explicit values (even if empty lists) for `dead_ends`, `unbounded_cycles`, `orphan_nodes`, and `missing_fan_in`.
  - **Fail signal:** Any topology_analysis field is missing, null, or contains "N/A" instead of an actual analysis result.

**Code-Review Mode Output (Code Review Verdict):**

- [ ] **EVAL-O19:** Code review verdict contains all required sections
  - **Test:** Verify the output contains: `verdict`, `summary`, `files_reviewed`, `rule_checks` (non-empty), `pattern_conformance` (with subsections), and `recommendations`.
  - **Fail signal:** One or more required sections are missing from the code review verdict.

- [ ] **EVAL-O20:** Code review findings cite file:function:line
  - **Test:** For each rule_check with `status: fail`, verify `location` contains a file path and function name or line number.
  - **Fail signal:** A failing rule check has no location, or location is vague (e.g., "the code" or "somewhere in the file").

- [ ] **EVAL-O21:** Pattern conformance covers all categories
  - **Test:** Verify `pattern_conformance` contains assessments for: `state_schema`, `node_design`, `graph_topology`, `hitl`, `execution`, `error_handling`, `observability`. Each must have a boolean assessment and an `issues` list (empty is acceptable).
  - **Fail signal:** A pattern conformance category is missing entirely, or has no boolean assessment.

- [ ] **EVAL-O22:** Code review checks against reference patterns
  - **Test:** Verify at least one rule_check or pattern_conformance finding references a specific pattern from `references/*.py` (by name or concept). The review should compare code against the taught patterns, not just general best practices.
  - **Fail signal:** The entire review uses only generic advice without referencing any pattern from the skill's reference files.

**Autonomous Design Mode Output (Graph Spec via Design Brief):**

- [ ] **EVAL-O23:** Autonomous mode enforces design brief precondition
  - **Test:** Invoke the skill as a subagent without providing a design brief. Verify it returns immediately with an error message referencing `templates/design_brief.md`.
  - **Fail signal:** The skill proceeds to design without a brief, asks interactive questions, or returns a generic error without pointing to the brief template.

- [ ] **EVAL-O24:** Assumptions documented for unknown fields
  - **Test:** Provide a design brief with at least one field set to "unknown". Verify the output graph spec contains an `assumptions` section listing what was assumed for each unknown field, with justification.
  - **Fail signal:** The graph spec silently fills in unknown fields without documenting the assumption, or the `assumptions` section is missing when the brief contained unknowns.

- [ ] **EVAL-O25:** Review subagent dispatched with bounded iteration
  - **Test:** Verify the autonomous design process dispatches a review subagent after producing the initial graph spec. If REVISE, verify iteration occurs. Verify the total design-review cycles do not exceed 3.
  - **Fail signal:** No review subagent is dispatched, or more than 3 design-review cycles occur, or REVISE verdicts are ignored.

- [ ] **EVAL-O26:** Unresolved issues returned after max cycles
  - **Test:** If the review subagent returns REVISE after 3 cycles, verify the output includes both the graph spec AND a structured list of unresolved issues.
  - **Fail signal:** After 3 REVISE cycles, the skill either loops indefinitely, returns only the spec without issues, or silently drops the unresolved findings.

- [ ] **EVAL-O27:** Brief validation catches contradictions
  - **Test:** Provide a design brief with contradictory constraints (e.g., "fully automated" + HITL requirements). Verify the skill flags the contradiction before proceeding with design.
  - **Fail signal:** The skill silently resolves contradictory constraints without flagging them, or produces a graph spec that embodies the contradiction.

- [ ] **EVAL-O28:** Autonomous output passes all design mode criteria (O01-O13)
  - **Test:** Apply EVAL-O01 through EVAL-O13 to the graph spec produced by autonomous design mode. All must pass.
  - **Fail signal:** Any of EVAL-O01 through EVAL-O13 fails on the autonomously produced graph spec.

## Test Prompts

### Naive User

- **TP-01:** `i want to build a chatbot with langgraph, can you help me design it?`
  - Tests: Does the skill ask clarifying questions or produce a generic graph with unstated assumptions?

- **TP-02:** `design a graph for processing documents`
  - Tests: Extremely vague — does the skill narrow down "processing" before designing?

- **TP-03:** `I need a langgraph workflow that does RAG`
  - Tests: Known pattern with many variants — does the skill push for specifics?

### Experienced User

- **TP-04:** `Design a multi-agent research workflow: one agent searches the web, another reads PDFs, a third synthesizes findings. They should work in parallel where possible, with a human checkpoint before the synthesis agent writes the final report. The search agent needs retry logic for rate-limited APIs. Use a shared state for accumulated findings but keep each agent's intermediate work isolated.`
  - Tests: Complex multi-agent with parallel execution, HITL, retry, and state isolation tension.

- **TP-05:** `I have an existing ingestion pipeline: validate → parse → chunk → embed → store. I want to add conditional OCR for scanned PDFs, a quality gate after chunking where a human reviews chunks for sensitive data, and a fallback path that skips embedding if the embedding service is down. Review my topology for issues.`
  - Tests: Dual intent (design + review). Does the skill handle both?

- **TP-06:** `Architect a customer support triage graph with: intent classification (LLM), routing to specialized handlers (billing, technical, general), escalation to human when confidence is below 0.7, and a feedback loop where the human's correction re-trains the classifier. State needs to track conversation history, classification confidence scores, and escalation count. Use interrupt_before for the escalation gate.`
  - Tests: Detailed spec with specific LangGraph primitives named. Does the skill honor user choices while applying its own conventions?

### Experienced User (Code-Review)

- **TP-11:** `Review my langgraph implementation in src/common/llm/graph/. Check if it follows best practices.`
  - Tests: Does code-review mode activate? Does it read the actual files and evaluate against rules.md + reference patterns?

- **TP-12:** `I wrote a langgraph workflow but I'm getting weird state overwrites. Can you review the code and tell me what's wrong? The state has a list field that multiple nodes write to.`
  - Tests: Specific bug symptom (missing reducer). Does the skill diagnose the root cause using its state design rules?

### Adversarial

- **TP-07:** `Design a complete AI platform: it should handle document ingestion, RAG retrieval, multi-agent collaboration, real-time streaming responses, user authentication, billing integration, and a monitoring dashboard. One graph, all connected.`
  - Tests: Absurdly large scope. Does the skill push back and recommend decomposition?

- **TP-08:** `Build me a langgraph where every node has human approval before and after it runs. There are 12 nodes. Also it needs to be fully automated with no human intervention for CI.`
  - Tests: Contradictory requirements. Does the skill surface the contradiction?

### Autonomous Design (Subagent with Brief)

- **TP-13:** Autonomous design with a well-formed brief:
  ```yaml
  brief:
    domain: e-commerce order fulfillment
    purpose: "Takes a validated order, checks inventory, processes payment, and dispatches shipping — producing a fulfillment record"
    inputs:
      - name: order
        type: "Order"
        source: "order validation API"
    outputs:
      - name: fulfillment_record
        type: "FulfillmentRecord"
        consumer: "shipping service + customer notification"
    constraints:
      - "payment must be processed before shipping dispatch"
      - "inventory check must happen before payment"
    preferences:
      - "prefer parallel processing where safe"
    known_stages:
      - name: check_inventory
        does: "verifies stock availability for all order items"
        type: io
      - name: process_payment
        does: "charges the customer via payment gateway"
        type: io
      - name: dispatch_shipping
        does: "creates shipping label and notifies warehouse"
        type: io
    hitl_requirements:
      - stage: "after payment, before shipping"
        reason: "high-value orders (>$500) need manual fraud review"
        provisional: "auto-approve orders under $500"
    integration:
      orchestrator: temporal
      existing_systems: ["Stripe payment API", "warehouse inventory DB"]
      checkpointer: postgres
    quality_criteria:
      - "payment failure must not leave orphaned inventory reservations"
      - "fraud review gate must have a provisional for headless CI"
  ```
  - Tests: Does autonomous mode produce a complete graph spec without asking questions? Are assumptions documented? Is the review subagent dispatched?

- **TP-14:** Autonomous design with contradictory brief:
  ```yaml
  brief:
    domain: document approval workflow
    purpose: "Routes documents through approval chain"
    inputs:
      - name: document
        type: "Document"
        source: "upload API"
    outputs:
      - name: approval_status
        type: "str"
        consumer: "notification service"
    constraints:
      - "must be fully automated with zero human intervention"
      - "every document must be manually approved by a senior reviewer"
    preferences: []
    known_stages:
      - name: classify
        does: "determines document type and required approvers"
        type: io
    hitl_requirements:
      - stage: "after classification"
        reason: "senior reviewer must approve"
        provisional: unknown
    integration:
      orchestrator: none
      existing_systems: []
      checkpointer: unknown
    quality_criteria: []
  ```
  - Tests: Does the skill flag the contradiction ("fully automated" vs "manually approved")? Does it flag the missing checkpointer when HITL is required?

- **TP-15:** Autonomous design with no brief (precondition test):
  ```
  [Dispatched as subagent with task: "Design a graph for processing invoices"]
  ```
  - Tests: Does the skill reject and point to templates/design_brief.md instead of proceeding interactively?

### Wrong Tool

- **TP-09:** `Can you implement this langgraph for me? Here's the graph spec.`
  - Tests: Implementation request. Does the skill point to its implementation section (graph spec = implementation guide) rather than refusing?

- **TP-10:** `Review this pull request that changes our langgraph workflow — here's the diff. Check if the new routing logic is correct.`
  - Tests: PR diff review, not graph design review. Similar keywords, different task. Does the skill distinguish?

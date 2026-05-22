# Graph Spec — Output Template

The design artifact produced by design mode. Every field is required unless marked optional.

```yaml
graph:
  name: <graph name — snake_case>
  purpose: <one-line description of what this graph does>

state:
  schema_type: TypedDict  # or dataclass if justified
  fields:
    - name: <field_name>
      type: <python type annotation>
      reducer: <optional — e.g., operator.add>
      written_by: [<node names that write this field>]
      read_by: [<node names that read this field>]

nodes:
  - name: <node_name>
    responsibility: <single-sentence — what it does>
    type: pure | io | hitl  # pure = transforms, io = external calls, hitl = human gate
    reads: [<state fields>]
    writes: [<state fields>]
    retry: <optional — e.g., "3x exponential, transient only">

edges:
  - from: <node>
    to: <node>

conditional_edges:
  - from: <node>
    router: <description of routing logic>
    routes:
      - condition: <when this>
        to: <node>
      - condition: default
        to: <node>  # explicit fallback required

hitl_checkpoints:
  - type: interrupt_before | interrupt_after
    node: <node name>
    question: <what the human sees>
    resume_with: <what data the human provides>
    provisional: <safe default for headless execution>

entry: <node name>
terminal: [<node name(s)>]

error_handling:
  accumulator: <optional — field name for error list>
  fallback_paths:
    - on_error_in: <node>
      route_to: <fallback node>

checkpointer: memory | sqlite | postgres | none
  # must not be "none" if hitl_checkpoints is non-empty

execution:
  wrapper: <wrapper class name — e.g., CompiledWorkflow>
  sync: run()        # synchronous invocation
  async: arun()      # asynchronous invocation
  stream: stream()   # yields (step_name, state) tuples
  # Callers MUST use the wrapper. Never expose the raw compiled graph.

observability:
  callbacks: <optional — e.g., "langfuse via config">
  node_decorator: <optional — e.g., "timing + state key logging">
```

## Validation Checklist

The reviewer subagent checks these against rules.md:

- [ ] Every multi-writer field has a reducer
- [ ] Every conditional edge has a default route
- [ ] Every cycle has a bounded exit condition
- [ ] Every HITL checkpoint has a provisional value
- [ ] No node has both LLM calls and data transforms
- [ ] I/O nodes are clearly separated and named
- [ ] Checkpointer is non-none if HITL checkpoints exist
- [ ] State is flat — no nested dicts that nodes read into
- [ ] Nodes don't reference each other directly

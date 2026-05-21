# Code Appendix Template

Part B of the design document. Two entry types with different rules and different consumers.

---

## Contract Entry Format

Contract entries are **exact and complete** — copied verbatim into `write-implementation-docs` Phase 0.
Every field, every type annotation, every default value must be present.

```markdown
## B.X: [Component Name — Contract]

[1-2 sentence description of what this defines and which tasks use it.]

**Tasks:** Task X.Y, Task X.Z
**Requirements:** REQ-xxx, REQ-yyy
**Type:** Contract (exact — copied to implementation docs Phase 0)

```python
[code here]
```

**Key design decisions:**
- [Decision 1 — e.g., "TypedDict with total=False allows incremental population"]
- [Decision 2 — e.g., "Frozen dataclass prevents accidental mutation"]
```

### What goes in contract entries

| Entry type | Format rules |
|------------|-------------|
| State TypedDicts | Every field with type + FR-tagged comment (e.g., `source_key: str  # FR-107`) |
| Config dataclasses | Frozen, all defaults specified, FR-tagged |
| Exception types | Docstrings explaining when each is raised |
| Function stubs | Complete docstrings (args, returns, raises) + `raise NotImplementedError("Task X.Y")` body |
| Pure utilities | Fully implemented (not stubs) — deterministic, no external dependencies |

### Rules

- `raise NotImplementedError("Task X.Y")` as the sole body for stubs — never `pass`, never placeholder comments
- `"Task X.Y"` must match the task number that will implement this stub
- Docstrings document ALL parameters, return values, and every exception
- Include imports at the top of each entry
- No line limit — completeness over brevity

### Example: State TypedDict

```python
from __future__ import annotations
from typing import Any, TypedDict


class PipelineState(TypedDict, total=False):
    """Shared state flowing through the processing pipeline."""

    # Populated by Task 1.1 — Input Loading
    source_path: str                    # Input file path (FR-101)
    source_key: str                     # Deterministic ID: SHA-256(path)[:24] (FR-102)
    source_hash: str                    # SHA-256 of file content (FR-103)

    # Populated by Task 2.1 — Processing
    processed_text: str                 # Cleaned output (FR-201)
    confidence: float                   # 0.0-1.0 quality score (FR-202)

    # Cross-cutting
    errors: list[dict[str, Any]]
    timings: dict[str, float]
```

### Example: Function Stub

```python
from pipeline_types import PipelineState
from pipeline_errors import ValidationError


def validate_input(state: PipelineState) -> PipelineState:
    """Validate the input source before processing.

    Args:
        state: Pipeline state containing 'source_path'.

    Returns:
        State with validation metadata added.

    Raises:
        ValidationError: If source file is missing or format unsupported.
    """
    raise NotImplementedError("Task 1.2")
```

---

## Pattern Entry Format

Pattern entries are **illustrative** — they show approach and key logic, not exact implementation.
Passed directly to `implement-code` task agents. Never appear in implementation docs or reach test agents.

```markdown
## B.X: [Component Name — Pattern]

[1-2 sentence description of the approach being illustrated.]

**Tasks:** Task X.Y
**Requirements:** REQ-xxx
**Type:** Pattern (illustrative — for implement-code only, never test agents)

```python
# Illustrative pattern — not the final implementation
[code here — 50-120 lines]
```

**Key design decisions:**
- [Why this approach over alternatives]
- [Trade-offs considered]
```

### Rules

- Target 50-120 lines per snippet
- Self-contained — understandable without reading other entries
- Show the design pattern, not a complete implementation
- Include "Key design decisions" explaining rationale
- Always label with `# Illustrative pattern — not the final implementation` comment
- Always mark as `**Type:** Pattern (illustrative — for implement-code only, never test agents)`

### What goes in pattern entries

- Major new classes/modules being introduced
- Non-obvious algorithms or scoring functions
- Pipeline/workflow graph definitions
- Configuration file formats
- Wrapper/decorator patterns
- Integration points between components

### What NOT to include in either entry type

- Trivial CRUD operations
- Standard library usage that doesn't need illustration
- Test code (belongs in write-test-docs)
- Execution steps, pytest commands, commit instructions (belongs in write-implementation-docs)

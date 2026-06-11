# Module Section Format

> **In parallel mode (Phase C-parallel):** each module section is written by a dedicated agent with this isolation:
> - Agent input: assigned source file(s) + spec FR numbers only
> - Must NOT receive: other module files, test files
> - Output: standalone markdown file at `docs/tmp/module-<name>.md`
> - All 5 sub-sections required (Purpose, How it works, Key decisions, Configuration, Error behavior)

````markdown
### `src/path/to/module.py` — [Module Name]

**Purpose:**

[One paragraph explaining what this module does and why it exists.]

**How it works:**

[Step-by-step walkthrough. Number the steps for sequential logic. Include short code
snippets (5–25 lines) pulled from the actual source for non-obvious algorithms.
Reference real function and class names. Trace the public interface and key internal
logic — do not line-by-line walk through trivial helpers.]

**Key design decisions:**

| Decision | Alternatives Considered | Why This Choice |
|----------|------------------------|-----------------|
| [what was decided] | [other options evaluated] | [reason this was chosen] |

**Configuration:**

| Parameter | Type | Default | Effect |
|-----------|------|---------|--------|
| [name] | [type] | [default] | [what changes when this is modified] |

*If this module has no configurable parameters, write: "This module has no configurable parameters."*

**Error behavior:**

[What exceptions this module raises. Under what conditions. What callers should do when
they receive each error. Which failures are retried internally.]
````

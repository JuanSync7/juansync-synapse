# Artifact Criteria: Tool

Loaded at [A] when a tool-type artifact is discovered. This is a diagnostic for brainstorming — it answers "is this tool-worthy?" before committing to build. Tools handle computation; skills handle judgment.

---

## Deterministic Need

The core question: **Does this require deterministic logic that Claude can't reliably do in-context?**

Tools exist for computation that must be exact every time: scoring algorithms, structured parsing, schema validation, format transformation. If the logic is judgment-based ("decide whether this is good"), it's a skill or a skill section, not a tool.

Test: Could Claude produce the same output reliably by thinking through it in-context? If yes 95%+ of the time, you don't need a tool — you need a prompt instruction.

---

## Input/Output Contract

Does it have a clear structured input and structured output?

- **Clear contract:** Takes a YAML file, returns a score object. Takes source code, returns an AST. Takes two files, returns a diff.
- **Vague contract:** "Helps with code quality." "Assists with planning." These are skills or config, not tools.

If you can't write a type signature for the input and output, it's not a tool.

---

## Script vs. Tool

Is this a shell script wrapper or a genuine tool?

- **Shell script:** Runs a fixed command sequence (`npm test && npm run lint`). This is infrastructure — put it in a Makefile, a package.json script, or a git hook.
- **Genuine tool:** Contains logic that transforms input to output with branching, computation, or state. The tool does work that the shell command sequence can't express.

A tool that wraps `grep | sort | uniq` is a shell pipeline, not a tool.

---

## Reusability

Can multiple skills or workflows use this tool?

- **Multiple consumers:** A scoring tool used by synapse-skill-skill-improver, synapse-router-artifact-gatekeeper, and synapse-router-eval-writer. A validation tool used by pre-commit hooks and CI. These justify tool status.
- **Single consumer:** A parser that only one skill ever calls. Inline the logic in that skill's workflow — the abstraction isn't earning its keep.

Exception: If the single-consumer logic is complex enough to warrant its own test suite, it may still deserve tool status for testability.

---

## Existing Coverage

Does a standard CLI tool or library already do this?

Before building: check if `jq`, `yq`, `rg`, `python -m json.tool`, or a well-known library already handles the computation. Wrapping an existing tool in a custom tool adds maintenance without adding capability.

---

## Signs It's a Tool

- Deterministic computation (scoring, parsing, validation, transformation)
- Clear input -> output contract with definable types
- Multiple potential consumers across different skills or workflows
- Claude can't reliably do the computation in-context (math, large data, exact formatting)
- Benefits from its own test suite

---

## Signs It's NOT a Tool

- The logic is judgment-based, not computational — make it a skill or skill section
- It's a simple shell command sequence — use Bash, Makefile, or a git hook
- Only one consumer exists and the logic is simple — inline it
- Claude can do the computation reliably in-context — use a prompt instruction
- A standard CLI tool or library already does this — use that instead

---

## Naming

Tools follow `{domain}-{subdomain?}-{action?}-{name}` where:
- `domain` comes from: testing, build, validation, analysis, integration
- `action` comes from `taxonomy/TOOL_TAXONOMY.md`: scorer, generator, validator, parser, transformer, reporter

Validate the chosen `domain` and `action` against the taxonomy before proceeding. If nothing fits, propose a taxonomy addition — don't invent ad hoc values.

# Design Principles — Tools

Tools are mechanical programs, not judgment engines. A skill carries policy and makes contextual decisions based on project context; a tool accepts typed inputs, executes a fixed sequence of operations, and returns typed outputs with a numeric exit code. Every principle below enforces that boundary — keeping tools predictable, testable, and safely composable with other tools and automation. Where a skill says "consider X", a tool says "if X, exit 2."

---

## P1: Deterministic Output

Same inputs must always produce the same outputs. A tool must not vary its behavior based on undeclared state: the current time of day, the calling user's identity, unannounced env vars, filesystem contents outside its declared side-effect manifest, or race conditions with concurrent processes. If variability is inherent to the task — for example, a tool that queries a live external service — that variability must be explicit: declared in TOOL.md under `## Side Effects` or `## Inputs`, with clear rationale for why it cannot be eliminated.

**Failure mode prevented:** A tool that passes all tests on a developer machine but silently behaves differently in CI — returning different results because an env var happened to be set, or because a timestamp-derived output changes each run — with no declared source of divergence and no way for the caller to detect or compensate.

---

## P2: Explicit Side-Effect Manifest

TOOL.md lists every file path pattern the tool reads or writes, every external service or CLI it calls, and every environment variable it consumes. The list must be exhaustive — "none beyond stdout/stderr" is a valid and complete declaration. A tool that touches anything not in this list is broken by definition, regardless of whether the omission was intentional. The manifest is the primary input for sandboxing decisions, test fixture design, and rollback planning.

**Failure mode prevented:** A tool that silently modifies a file outside its stated scope — discovered only after data loss or a corrupted artifact — because the author assumed the behavior was "obvious" or "minor" and omitted it from documentation. Callers cannot audit what they cannot see.

---

## P3: Fail Loudly on Bad Input

On any missing or invalid input, exit immediately with a non-zero exit code, write a human-readable error message to `stderr`, and produce no output on `stdout`. Never silently proceed by coercing, defaulting, or partially completing work when inputs are wrong. The invariant is: either the tool completes all its intended work successfully and exits 0, or it produces no work product and exits non-zero. Partial success with a non-zero exit is not a valid state.

**Failure mode prevented:** A tool that silently treats a missing required argument as an empty string, writes a partial output file, and exits 0 — leaving the caller with corrupted state and no error signal. Downstream tools that trust the exit code then consume the corrupt output, amplifying the damage.

---

## P4: Exit Codes Are Contracts

Every non-zero exit code the tool can produce must be documented in TOOL.md under `## Exit Codes` with: the condition that triggers it, its semantic meaning, and the action a caller should take. Exit codes must be defined as named constants at the top of the script — never use magic numbers inline. The constants in the script and the table in TOOL.md are the same contract; they must stay in sync.

**Failure mode prevented:** A tool that reuses exit code 1 for both "missing argument" and "network timeout" forces the caller to parse stderr text to distinguish retryable from fatal errors — a brittle contract that silently breaks when the error message format changes. Named constants make the author's intent visible in code review, and the TOOL.md table gives callers a machine-readable branching spec.

---

## P5: Declare All Integrations

Every external dependency must be declared in TOOL.md: network endpoints and their purpose, filesystem paths outside the repo root, third-party CLIs required to be on PATH, and environment variables consumed. For each integration, state: what it is, why the tool needs it, and what exit code and behavior to expect when it is unavailable. A tool that invokes an undeclared dependency is incomplete — its TOOL.md is an inaccurate contract.

**Failure mode prevented:** A tool that exits with "command not found: jq" in a CI environment — because the jq dependency was never declared in TOOL.md, was never added to the CI image, and all prior tests passed only because developer machines happened to have it installed. Declaring integrations upfront also enables callers to pre-validate prerequisites before invoking the tool, shifting errors from silent runtime failures to explicit pre-flight rejections.

# flow-agent — Agent Creation Flow

Loaded by `synapse-router-artifact-creator` after `[ROUTE]` confirms `$TYPE=agent`. Owns the full lifecycle from
pre-flight through eval handoff. Wrong-tool detection already ran in the router — do not repeat it here.

Agents are **single-file artifacts**: one `.md` file placed at `<class-root>/agents/<domain>/<name>.md`.
There are no companion directories, no references/, no templates/ siblings. Scaffolding is exactly one file.

> **Hard rule:** Do NOT scaffold a directory. The agent IS the file.

---

## MUST (flow level)
- Load `references/shared-steps.md` at `[START]` — every parametric procedure lives there
- Load `references/design-principles-agent.md` at `[W]` before writing the agent file
- Pass all pre-flight checks before writing any file — atomic creation guarantee
- Write the agent file from `templates/agent/agent.md.template`

## MUST NOT (flow level)
- Create a subdirectory for the agent — the file is the artifact
- Inline frontmatter validation, registry writes, or README row updates — call shared-steps
- Proceed from `[U]` without a confirmed input/output contract and dispatching skill
- Skip `[E]` — every agent gets an eval handoff even if synapse-router-eval-writer (agent flow) is minimal

---

## Flow

### [START] — pre-flight
Load: `references/shared-steps.md`
Brief: All validations before any file is written. Atomic creation guarantee.
Do:
  1. → `shared-steps:placement-decision(agent)` — confirm `src/agents/<domain>/` or `synapse/agents/<domain>/`
  2. → `shared-steps:validate-frontmatter(agent, $artifact_dir)` — required fields, taxonomy values (domain, role), name uniqueness
  3. If agent file already exists at target path → offer "complete partial creation?" or "abort?" — do not overwrite silently
Don't:
  - Write any file if any pre-flight step fails
  - Auto-select framework placement without user confirmation
Exit:
  → `[U]` : pre-flight passes
  → FAIL loudly : any pre-flight step fails; report which check failed and why

---

### [U] — understand
Brief: Confirm the agent's job, who dispatches it, and its input/output contract. Self-loops until all
gate conditions pass. An agent with a vague contract produces unpredictable behavior at dispatch time.
Do:
  1. Identify the **dispatching skill or flow** — who calls this agent and why?
  2. Identify **trigger conditions** — what input state causes the dispatch?
  3. Confirm **input contract** — exact inputs, types, and which are required vs optional
  4. Confirm **output contract** — what the agent returns: shape, format, and success/failure signals
  5. Confirm the agent name matches `[a-z0-9-]+` and is globally unique (no collision in registry)
  6. Confirm `domain` and `role` values are in `taxonomy/AGENT_TAXONOMY.md`
Don't:
  - Proceed with a vague dispatch context ("it will be called when needed")
  - Accept an output contract of "prose describing what happened"
  - Accept compound purpose ("it validates AND writes the registry row") — single-purpose rule applies
Exit:
  → `[U]` : dispatching skill, input contract, or output contract unconfirmed
  → `[W]` : dispatching skill confirmed; input/output contract fully specified; domain and role valid

---

### [W] — write agent file
Load: `references/design-principles-agent.md`, `templates/agent/agent.md.template`
Brief: Core authoring node. Produce the single agent `.md` file. Apply design principles before writing.
Do:
  1. Apply `design-principles-agent.md` — single-purpose, narrow tool scope, idempotent, explicit contract, no hidden side effects
  2. Render `templates/agent/agent.md.template` with resolved values: `$name`, `$description`, `$domain`, `$role`
  3. Write `## Input Contract` table — one row per input: name, type, required flag, description
  4. Write `## Behavior` section — numbered steps, judgment rules only (no mechanics the agent already knows)
  5. Write `## Output Contract` section — exact shape, format, success/error signal
  6. Write `## Failure Reporting` section — `AGENT FAILURE: <name>` block format
  7. Call → `shared-steps:write-registry-row(agent, $meta)`
  8. Call → `shared-steps:update-domain-readme(agent, $domain, $meta)`
  9. Call → `shared-steps:status-draft-mark(agent, $meta)`
Don't:
  - Create a directory — write exactly one `.md` file to `$artifact_dir/<name>.md`
  - Add references/, templates/, or agents/ siblings — agents are flat
  - Omit the `## Failure Reporting` section — silent failure is not allowed
  - Proceed if the behavior section cannot be written without `if $TYPE` branching (that is a design smell)
Exit:
  → `[W]` : design convergence failure or revision needed — report specific gap
  → `[E]` : agent file written; registry row added; domain README row added

---

### [E] — eval handoff
Brief: Dispatch eval writer. Agents get EVAL.md via `synapse-router-eval-writer (agent flow)`.
Do:
  1. Call → `shared-steps:handoff-eval(agent, $artifact_path)`
  2. Do not block on completion — dispatch is fire-and-confirm, not fire-and-wait
Don't:
  - Generate EVAL.md inline — that is `synapse-router-eval-writer (agent flow)`'s job
  - Skip this step because the agent "is simple"
Exit:
  → `[END]` : eval dispatched

---

### [END] — report
Do:
  1. Print verbatim what was created: file path (`$artifact_dir/<name>.md`), registry row added, domain README row added
  2. Print: eval handoff dispatched to `synapse-router-eval-writer (agent flow)`
  3. Print: artifact is `status: draft` — run `/synapse-router-artifact-gatekeeper $artifact_path` before promoting
Don't:
  - End without full output summary
  - Auto-route to next skill — suggest, do not dispatch

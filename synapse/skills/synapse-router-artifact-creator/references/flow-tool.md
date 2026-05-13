# flow-tool.md — Tool Creation Flow

Loaded after `[ROUTE]` when `$TYPE=tool`. Generates three outputs together: `TOOL.md` + script file + `test/` scaffold. Tools are mechanical programs with deterministic contracts — not judgment-laden workflows. Every node in this flow enforces that framing.

---

## Loading discipline

```
flow-tool.md                  loaded now (this file)
shared-steps.md               loaded at [U]
design-principles-tool.md     loaded at [W]
templates/tool/               loaded at [W] (scaffold step)
# flow-{skill,protocol,agent}.md  NEVER LOAD
```

---

### [START] — Pre-flight

Load: `references/shared-steps.md`

Brief: Validate inputs and placement before touching any file. Zero state exists on failure — nothing to clean up.

Do:
  1. Run `shared-steps:validate-frontmatter(tool, $artifact_dir)`:
     - Required frontmatter fields present: `name`, `description`, `domain`, `action`, `type`, `tags`
     - `domain` value exists in `taxonomy/TOOL_TAXONOMY.md` domain table
     - `action` value exists in `taxonomy/TOOL_TAXONOMY.md` action table
     - `type` value exists in `taxonomy/TOOL_TAXONOMY.md` type table
     - `name` matches `[a-z0-9-]+` regex
     - `name` is globally unique (no collision in `registry/TOOL_REGISTRY.md` or target dir)
  2. Run `shared-steps:placement-decision(tool)`:
     - Default placement: `src/tools/<domain>/<name>/`
     - Prompt only if user explicitly requests `synapse/` (framework placement)
  3. Abort loudly if pre-flight fails — print the failing check and the expected value; write nothing.

Don't:
  - Scaffold any file before all pre-flight checks pass
  - Auto-create missing taxonomy or registry files — their absence hides infrastructure problems; fail loudly
  - Proceed if target directory already exists (check for existing `TOOL.md` at target path)

Exit: → `[U]` on pre-flight pass; → loud failure message on any pre-flight failure

---

### [U] — Understand: deterministic contract and side-effect manifest

Brief: Tools have inputs and outputs, not judgment. Before writing anything, establish the complete contract: what goes in, what comes out, what state changes happen, what exit codes mean, and what external dependencies exist.

Do:
  1. Clarify the **deterministic contract**: given the same inputs, the tool always produces the same outputs. If any variability exists (e.g., timestamps, network state), it must be explicit and declared.
  2. Enumerate the **side-effect manifest**: every file path pattern the tool reads or writes, every external service or environment variable it touches. No implicit side effects.
  3. Confirm the **language**: ask if not provided — `.sh` (bash) or `.py` (Python). Record as `$LANG`.
  4. Identify all **non-zero exit codes**: what each one means, what the caller should do on each.
  5. Identify all **external dependencies**: network calls, env vars, filesystem paths outside the repo, third-party CLIs.

Don't:
  - Proceed to `[W]` if side-effect manifest is unresolved or ambiguous
  - Accept "it depends" for exit codes — exit code semantics must be fully enumerated before scaffolding
  - Conflate "what the tool does" with "why it does it" — this is a contract step, not a design step

Exit: → `[W]` once contract (inputs, outputs, side effects, exit codes, deps) is fully specified

---

### [L] — Language pick (if not provided at `[U]`)

Brief: If `$LANG` was not resolved at `[U]`, select now. This is a single-question gate.

Do:
  1. If `$LANG` already set → skip this node entirely, proceed to `[W]`.
  2. Prompt: "Script language: [sh | py]?"
  3. Accept `sh` or `bash` → set `$LANG=sh`; accept `py` or `python` → set `$LANG=py`.
  4. Reject anything else with: "Language must be one of: sh, py."

Don't:
  - Infer language from tool name or description — explicit choice only
  - Accept abbreviated forms beyond `sh`/`bash`/`py`/`python`

Exit: → `[W]` with `$LANG` confirmed

---

### [W] — Write: TOOL.md + script + test/ scaffold

Load: `references/design-principles-tool.md`, `templates/tool/`

Brief: Write all three outputs in one operation. Partial creation is not acceptable — either all three artifacts exist or none do. Apply design-principles-tool.md framing throughout: deterministic contract, explicit side-effect manifest, loud failure on bad input, exit code contracts, declared integrations.

Do:
  1. **Write `TOOL.md`** using `templates/tool/TOOL.md.template`:
     - Frontmatter: `name`, `description`, `domain`, `action`, `type`, `tags` (no frontmatter on the script file itself)
     - `## Purpose` — one-paragraph deterministic contract statement
     - `## Inputs` — table of all CLI args/env vars with Required column and description
     - `## Outputs` — table of all outputs (files created, stdout, exit codes)
     - `## Side Effects` — explicit manifest: every file path or service the tool touches; list "none" if genuinely none
     - `## Exit Codes` — table: exit code → meaning → caller action
     - `## Examples` — 2–3 invocation examples with expected output
  2. **Write script file** using language-appropriate template:
     - If `$LANG=sh` → write `<name>.sh` from `templates/tool/script.sh.template`
     - If `$LANG=py` → write `<name>.py` from `templates/tool/script.py.template`
     - Script file has NO YAML frontmatter — TOOL.md is the sole metadata carrier
     - Populate exit code constants, arg parsing skeleton, and logging helpers from the contract established at `[U]`
  3. **Write `test/` scaffold** using `templates/tool/test/`:
     - `test/README.md` — how to run tests, fixture conventions, exit-code expectations per case
     - `test/test-<name>.sh` — example test using exit-code assertions; covers at minimum: missing args, happy path, expected failure case
  4. After all three files written:
     - Call `shared-steps:write-registry-row(tool, $meta)` — append row to `registry/TOOL_REGISTRY.md`
     - Call `shared-steps:update-domain-readme(tool, $domain, $meta)` — insert row in domain README table
     - Call `shared-steps:status-draft-mark(tool, $meta)` — ensure `status: draft` in registry row

Don't:
  - Write only TOOL.md without the script and test/ — three outputs are atomic
  - Add YAML frontmatter to the script file — that belongs only in TOOL.md
  - Leave exit code constants undefined in the script template — populate from the `[U]` contract
  - Embed judgment-language ("consider", "may", "evaluate") in TOOL.md — tools have contracts, not recommendations
  - Proceed to `[E]` if any of the three write operations failed — report what succeeded and what failed

Exit: → `[E]` once TOOL.md + script + test/ all written; registry row appended; README row inserted

---

### [E] — Eval handoff

Brief: Dispatch `write-tool-eval` to decide whether test/ is sufficient or whether an EVAL.md is also needed. This node dispatches and moves on — it does not block on eval completion.

Do:
  1. Call `shared-steps:handoff-eval(tool, $artifact_path)`.
  2. `write-tool-eval` internally decides: mechanical tool with deterministic outputs → `test/` scaffold sufficient; tool with judgment-laden or qualitative outputs → `EVAL.md` also generated.
  3. Note in the `[END]` report which convention was chosen (test/ only vs test/ + EVAL.md).

Don't:
  - Grade the body quality of TOOL.md — that is downstream via `write-tool-eval` + `/synapse-router-artifact-gatekeeper`
  - Block `[END]` waiting for `write-tool-eval` to finish — dispatch is the contract, not completion

Exit: → `[END]`

---

### [END] — Report

Do: Print verbatim what was created. Include status.

```
Created:
  <target_dir>/TOOL.md
  <target_dir>/<name>.<lang>
  <target_dir>/test/README.md
  <target_dir>/test/test-<name>.sh

Registry:   registry/TOOL_REGISTRY.md — row added (status: draft)
README:     <domain_readme_path> — row added
Eval:       write-tool-eval dispatched → [test/ only | test/ + EVAL.md]
Status:     draft

Next: run /synapse-router-artifact-gatekeeper <target_dir> before promoting to stable.
```

Don't:
  - Omit the `/synapse-router-artifact-gatekeeper` reminder — newly created tools are always `status: draft`
  - Claim outputs that were not confirmed written

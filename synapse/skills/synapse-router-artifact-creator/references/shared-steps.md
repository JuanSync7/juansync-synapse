# shared-steps

Parametric procedures called by any flow file via `→ shared-steps:<step-name>`. Each takes `$TYPE` and reads from `references/type-config.md`.

**HARD RULE:** No `if $TYPE == ...` conditionals inside any procedure body. All type variation must come from type-config lookups. If you need branching beyond what type-config supports, the right fix is to extend type-config, not add a conditional here.

---

### validate-frontmatter

One-line purpose: Verify all pre-flight conditions before any file is written.

**Inputs:** `$TYPE`, `$artifact_dir` (proposed target path)

**Reads from type-config:** `frontmatter_required`, `taxonomy_file`, `taxonomy_field_domain`, `taxonomy_field_type`, `registry_file`, `artifact_dir_default` / `artifact_dir_framework`

**Behavior:**
1. Confirm `type-config[$TYPE]` exists; fail loudly if `$TYPE` is not a recognized key.
2. Confirm the taxonomy file at `type-config[$TYPE].taxonomy_file` exists on disk. Fail loudly if missing — do not auto-create; a missing taxonomy file is an infrastructure problem.
3. Confirm the registry file at `type-config[$TYPE].registry_file` exists on disk. Fail loudly if missing — same reason.
4. Check that `$NAME` matches `[a-z0-9-]+`. Fail with pattern hint if not.
5. Verify `$NAME` does not already exist in the registry file. Fail loudly on collision — include the conflicting registry row in the error.
6. Verify the proposed `$artifact_dir` does not already exist on disk. If it does, prompt: "Partial creation detected — complete or abort+clean?" Do not auto-proceed.
7. Verify each field in `frontmatter_required` is present in the provided frontmatter values. Report all missing fields at once.
8. Verify the `domain` value appears as a valid domain in `taxonomy_file`. Fail loudly if not.
9. Verify the value for `type-config[$TYPE].taxonomy_field_type` (e.g., `intent`, `role`, `type`, `action`) appears as a valid value in `taxonomy_file`. Fail loudly if not.
10. Confirm the domain README exists at `<artifact_dir_root>/<domain>/README.md`. Fail loudly if missing — do not auto-create.

**Failure modes:**
- Missing taxonomy file → `FAIL: taxonomy file not found at <path>. Infrastructure problem — do not proceed.`
- Missing registry file → `FAIL: registry file not found at <path>. Infrastructure problem — do not proceed.`
- Missing domain README → `FAIL: domain README not found at <path>. Infrastructure problem — do not proceed.`
- Name collision in registry → `FAIL: name '<name>' already exists in <registry_file>. Choose a unique name.`
- Path already exists on disk → prompt for complete/abort; never silently overwrite.
- Invalid taxonomy value → `FAIL: '<value>' is not a valid <field> in <taxonomy_file>. Valid values: <list>.`
- Frontmatter missing required fields → `FAIL: missing required fields: <list>. Required: <frontmatter_required>.`

---

### write-registry-row

One-line purpose: Append a new row to the type-specific registry file.

**Inputs:** `$TYPE`, `$meta` (map of column values matching `readme_columns`)

**Reads from type-config:** `registry_file`, `readme_columns`

**Behavior:**
1. Read `type-config[$TYPE].registry_file` to get the target file path.
2. Read `type-config[$TYPE].readme_columns` to get the ordered column list.
3. Read the existing registry file to determine column ordering from the header row. Use that ordering — do not derive it independently.
4. Build the new row using `$meta` values in header-matched column order.
5. Append the row to the registry file after the last existing data row.
6. Set `status: draft` in the row (enforced by `status-draft-mark`; ensured here as a redundancy).

**Failure modes:**
- Registry file not found at write time → `FAIL: cannot write registry row — <path> not found. Stop.`
- `$meta` missing a required column value → `FAIL: missing column '<col>' in $meta for registry row.`

---

### update-domain-readme

One-line purpose: Insert a catalog row for the new artifact into its domain README.

**Inputs:** `$TYPE`, `$domain`, `$meta` (map of column values matching `readme_columns`)

**Reads from type-config:** `readme_columns`

**Behavior:**
1. Construct the domain README path from `$domain` and the artifact root resolved during `placement-decision`.
2. Confirm the domain README exists. Fail loudly if missing — do not create it.
3. Read `type-config[$TYPE].readme_columns` to get the catalog table column structure.
4. Locate the catalog table in the domain README (the table listing artifacts in this domain).
5. Build the new row using `$meta` values in column order from the existing table header.
6. Insert the row after the last existing row of the catalog table.

**Failure modes:**
- Domain README not found → `FAIL: domain README not found at <path>. Do not auto-create — fix the directory structure first.`
- Catalog table not found in README → `FAIL: no catalog table found in <path>. README may be malformed.`
- `$meta` missing a required column value → `FAIL: missing column '<col>' for README row.`

---

### handoff-eval

One-line purpose: Dispatch the type-specific eval writer to generate the evaluation scaffold.

**Inputs:** `$TYPE`, `$artifact_path`

**Reads from type-config:** `eval_convention`

**Behavior:**
1. Construct the eval skill name as `write-<TYPE>-eval`.
2. Dispatch `/write-<TYPE>-eval <artifact_path>` as a subagent call.
3. Do not block on completion — handoff is fire-and-confirm-dispatch, not fire-and-wait.
4. Report that the eval handoff was dispatched and what skill received it.
5. For the `tool` type: `write-tool-eval` decides internally whether to produce `test/` scaffold or `EVAL.md` based on tool nature — do not pre-decide from `eval_convention`. `eval_convention: "test/"` is only the default hint passed to the eval skill.

**Failure modes:**
- Eval skill `write-<TYPE>-eval` not found → `FAIL: eval skill 'write-<TYPE>-eval' not found. Cannot complete eval handoff. Document manually.`

---

### placement-decision

One-line purpose: Determine whether the artifact lands in `src/` (adopter) or `synapse/` (framework).

**Inputs:** `$TYPE`

**Reads from type-config:** `artifact_dir_default`, `artifact_dir_framework`

**Behavior:**
1. Default placement is `type-config[$TYPE].artifact_dir_default` (under `src/`).
2. If the user explicitly requested `synapse/` placement (framework artifact), prompt to confirm: "This places the artifact in `synapse/` as a framework artifact. Confirm? [y/n]"
3. On confirmation, use `type-config[$TYPE].artifact_dir_framework` instead.
4. Resolve `<domain>` and `<name>` placeholders in the chosen path using `$domain` and `$NAME`.
5. Return the resolved `$artifact_dir` for use in subsequent steps.

**Failure modes:**
- User requests framework placement but cannot confirm reason → do not proceed; prompt again.

---

### status-draft-mark

One-line purpose: Ensure the registry row and any spec frontmatter carry `status: draft` on creation.

**Inputs:** `$TYPE`, `$meta`

**Reads from type-config:** `registry_file`, `frontmatter_required`

**Behavior:**
1. Add or overwrite `status: draft` in `$meta` before `write-registry-row` finalizes the row.
2. Ensure `status: draft` appears in the artifact's spec frontmatter (in `SKILL.md` / `PROTOCOL.md` / agent `.md` / `TOOL.md`).
3. At `[END]`, include in the report: "All outputs at `status: draft`. Run `/synapse-router-artifact-gatekeeper <path>` to certify and promote."

**Failure modes:**
- `status` field absent from registry schema → `FAIL: 'status' not a recognized column in <registry_file>. Cannot mark draft.`

# shared-steps

Parametric procedures called by any flow file via `→ shared-steps:<step-name>`. Each takes `$TYPE` and reads from `references/type-config.md`.

**HARD RULE:** No `if $TYPE == ...` conditionals inside any procedure body. All type variation must come from `type-config.md` lookups. If you need branching beyond what type-config supports, the right fix is to extend type-config, not add a conditional here.

---

### validate-frontmatter

One-line purpose: Read the source artifact's frontmatter and extract the artifact name. **Read-only — does not validate taxonomy values.**

**Inputs:** `$TYPE`, `$ARTIFACT_PATH`

**Reads from type-config:** `artifact_shape`, `spec_file`

**Behavior:**
1. Resolve the spec file:
   - If `type-config[$TYPE].spec_file == "<self>"` → spec file = `$ARTIFACT_PATH`
   - Otherwise → spec file = `$ARTIFACT_PATH / type-config[$TYPE].spec_file`
2. Confirm the spec file exists and is non-empty. Fail loudly if not.
3. Parse the YAML frontmatter block at the top of the spec file.
4. Confirm a `name:` key is present. Fail loudly if missing — every artifact MUST be named.
5. Return `$ARTIFACT_NAME` for use by the calling flow.

**Failure modes:**
- Spec file missing → `FAIL: spec file not found at <path>. Cannot extract artifact name.`
- Frontmatter absent or malformed → `FAIL: frontmatter could not be parsed at <path>. Source artifact malformed.`
- `name:` missing from frontmatter → `FAIL: 'name' field absent in frontmatter at <path>. Source artifact malformed.`

**Out of scope:** This step does NOT validate `domain`, `intent`, `role`, `type`, or any other taxonomy field. Taxonomy validation is `/synapse-router-artifact-gatekeeper`'s job — duplicating it here creates drift risk.

---

### resolve-output-path

One-line purpose: Compute the absolute target path for the EVAL artifact.

**Inputs:** `$TYPE`, `$ARTIFACT_PATH`, `$ARTIFACT_NAME`

**Reads from type-config:** `output_path_shape`, `output_filename`

**Behavior:**
1. Look up `type-config[$TYPE].output_path_shape`.
   - `directory` → `$EVAL_PATH = $ARTIFACT_PATH / type-config[$TYPE].output_filename`
   - `flat` → `$EVAL_PATH = dirname($ARTIFACT_PATH) / output_filename` with `<name>` token resolved to `$ARTIFACT_NAME`
2. Return `$EVAL_PATH`.

**Failure modes:**
- `output_path_shape` value not in `{directory, flat}` → `FAIL: unknown output_path_shape '<value>' in type-config. Fix type-config.md.`

---

### existing-eval-guard

One-line purpose: Default-deny overwrite of an existing EVAL artifact at the target path.

**Inputs:** `$EVAL_PATH`, `$FORCE` (boolean, defaults false)

**Behavior:**
1. Check whether a file exists at `$EVAL_PATH`.
2. If no → return; nothing to guard.
3. If yes and `$FORCE == false` → fail loudly with:
   `FAIL: EVAL.md exists at <path>. Use --force to overwrite, or run /synapse-skill-skill-improver to refine via measurement.`
4. If yes and `$FORCE == true` → log "overwriting existing EVAL at <path>" and return.

**Failure modes:**
- File at `$EVAL_PATH` is a directory, not a file → `FAIL: <path> is a directory; cannot write EVAL there.`

---

### write-eval-atomic

One-line purpose: Single-write commit of fully-assembled EVAL content.

**Inputs:** `$EVAL_PATH`, `$EVAL_BODY` (full string), `$TIER_COUNTS` (map: prefix → count)

**Behavior:**
1. Confirm `$EVAL_BODY` is non-empty. Fail loudly if empty — assembly bug upstream.
2. Issue exactly one Write tool call against `$EVAL_PATH` with `$EVAL_BODY`.
3. Format and emit the exit signal:
   `Wrote <path> with <count1> <prefix1>, <count2> <prefix2>, ... [, <N> test prompts]`
4. Test-prompts segment of the signal appears only when the calling flow tracked test prompts.

**Failure modes:**
- Write tool call fails → propagate the underlying I/O error; do NOT retry silently. Caller decides whether to surface or re-run.
- Multiple writes attempted (caller bug) → `FAIL: write-eval-atomic invoked twice in one flow. Atomic invariant violated.`

**Atomic invariant:** Any flow that reaches `write-eval-atomic` MUST have assembled the full EVAL.md string in memory before this call. If a dispatch fails mid-flow (e.g., a skill-eval-* agent errors), the flow MUST NOT call `write-eval-atomic` with a partial body.

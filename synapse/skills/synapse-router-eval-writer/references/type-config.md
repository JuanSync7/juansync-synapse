# type-config

Data-only lookup consumed by `[ROUTE]` and `shared-steps.md`. Edit here when adding a new artifact type. **No procedure body may branch on `$TYPE` directly — type variation MUST come from this file.**

```yaml
skill:
  artifact_shape: directory          # $ARTIFACT_PATH must be a directory
  spec_file: SKILL.md                # source spec inside the artifact directory
  output_path_shape: directory       # eval lives inside the artifact dir
  output_filename: EVAL.md
  tier_prefixes: [EVAL-S, EVAL-E, EVAL-F, EVAL-O]
  test_prompts_section: true
  canonical_checklist_source: null   # skill flow uses dispatch agents, not a checklist
  template_path: templates/skill/eval.md
  flow_file: references/flow-skill.md

protocol:
  artifact_shape: file               # $ARTIFACT_PATH must be a flat .md file
  spec_file: <self>                  # the file IS the artifact
  output_path_shape: flat            # adjacent file, not inside a directory
  output_filename: <name>.eval.md    # <name> = basename of the protocol .md
  tier_prefixes: [EVAL-S, EVAL-C]
  test_prompts_section: false
  canonical_checklist_source: synapse/skills/synapse-router-artifact-gatekeeper/references/protocol-checklist.md
  template_path: templates/protocol/eval.md
  flow_file: references/flow-protocol.md

agent:
  artifact_shape: file
  spec_file: <self>
  output_path_shape: flat
  output_filename: <name>.eval.md
  tier_prefixes: [EVAL-S, EVAL-Q]
  test_prompts_section: false
  canonical_checklist_source: synapse/skills/synapse-router-artifact-gatekeeper/references/agent-checklist.md
  template_path: templates/agent/eval.md
  flow_file: references/flow-agent.md

tool:
  artifact_shape: directory
  spec_file: TOOL.md
  output_path_shape: directory
  output_filename: EVAL.md
  tier_prefixes: [EVAL-S, EVAL-X]
  test_prompts_section: false
  # Tool checklist is currently inline in synapse-router-artifact-gatekeeper/SKILL.md
  # (Phase 2 / Phase 3 "Tool flow" sections). flow-tool.md loads those sections.
  canonical_checklist_source: synapse/skills/synapse-router-artifact-gatekeeper/SKILL.md#tool-flow
  template_path: templates/tool/eval.md
  flow_file: references/flow-tool.md
```

## Field semantics

| Field | Meaning |
|-------|---------|
| `artifact_shape` | `directory` or `file`. Used by `[ROUTE]` to validate `$ARTIFACT_PATH`. |
| `spec_file` | Where to read frontmatter from. `<self>` = the artifact file itself. |
| `output_path_shape` | `directory` → write inside the artifact dir. `flat` → write adjacent to the artifact file. |
| `output_filename` | Literal filename or templated (`<name>` resolves to artifact basename). |
| `tier_prefixes` | EVAL section IDs the flow MUST produce. Order matters in the assembled file. |
| `test_prompts_section` | Whether the assembled EVAL ends with a Test Prompts section. Skill only. |
| `canonical_checklist_source` | Repo-relative path the transcription flow MUST Load. Failure to resolve = hard stop. |
| `template_path` | Skeleton loaded during assembly. |
| `flow_file` | The exactly-one flow loaded by `[ROUTE]`. |

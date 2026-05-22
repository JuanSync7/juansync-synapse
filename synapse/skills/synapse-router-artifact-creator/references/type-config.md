# type-config

Data-only lookup consumed by shared-steps. Edit here when adding a new artifact type.

```yaml
skill:
  artifact_shape: directory
  artifact_dir_default: "src/skills/<domain>/<name>/"
  artifact_dir_framework: "synapse/skills/<domain>/<name>/"
  spec_file: "SKILL.md"
  taxonomy_file: "taxonomy/SKILL_TAXONOMY.md"
  taxonomy_field_domain: "domain"
  taxonomy_field_type: "intent"
  registry_file: "registry/SKILL_REGISTRY.md"
  frontmatter_required: [name, description, domain, intent, tags, user-invocable]
  eval_convention: "EVAL.md"
  readme_columns: [name, description, domain, intent, status]
  flow_file: "references/flow-skill.md"
  design_principles_file: "references/design-principles-skill.md"
  templates_dir: "templates/skill/"

protocol:
  artifact_shape: directory
  artifact_dir_default: "src/protocols/<domain>/<name>/"
  artifact_dir_framework: "synapse/protocols/<domain>/<name>/"
  spec_file: "PROTOCOL.md"
  taxonomy_file: "taxonomy/PROTOCOL_TAXONOMY.md"
  taxonomy_field_domain: "domain"
  taxonomy_field_type: "type"
  registry_file: "registry/PROTOCOL_REGISTRY.md"
  frontmatter_required: [name, description, domain, type]
  eval_convention: "EVAL.md"
  readme_columns: [name, description, domain, type, consumers]
  flow_file: "references/flow-protocol.md"
  design_principles_file: "references/design-principles-protocol.md"
  templates_dir: "templates/protocol/"

agent:
  artifact_shape: file           # agents are flat <name>.md files, NOT directories
  artifact_dir_default: "src/agents/<domain>/"
  artifact_dir_framework: "synapse/agents/<domain>/"
  spec_file: "<name>.md"         # the file IS the artifact; no subdirectory
  taxonomy_file: "taxonomy/AGENT_TAXONOMY.md"
  taxonomy_field_domain: "domain"
  taxonomy_field_type: "role"
  registry_file: "registry/AGENTS_REGISTRY.md"
  frontmatter_required: [name, description, domain, role]
  eval_convention: "EVAL.md"
  readme_columns: [name, description, consumers]
  flow_file: "references/flow-agent.md"
  design_principles_file: "references/design-principles-agent.md"
  templates_dir: "templates/agent/"

tool:
  artifact_shape: directory
  artifact_dir_default: "src/tools/<domain>/<name>/"
  artifact_dir_framework: "synapse/tools/<domain>/<name>/"
  spec_file: "TOOL.md"
  taxonomy_file: "taxonomy/TOOL_TAXONOMY.md"
  taxonomy_field_domain: "domain"
  taxonomy_field_type: "action"
  registry_file: "registry/TOOL_REGISTRY.md"
  frontmatter_required: [name, description, domain, action]
  eval_convention: "test/"       # default; write-tool-eval may upgrade to EVAL.md
  readme_columns: [name, description, domain, action, status]
  flow_file: "references/flow-tool.md"
  design_principles_file: "references/design-principles-tool.md"
  templates_dir: "templates/tool/"
```

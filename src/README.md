# src

Adopter artifact slot. **Empty in the framework distribution** — this directory is where downstream adopters add their own skills, agents, protocols, and tools. Framework artifacts live in [`synapse/`](../synapse/).

| Slot | Purpose |
|------|---------|
| [skills/](skills/) | User-invocable adopter recipes |
| [agents/](agents/) | Adopter agents dispatched by skills |
| [protocols/](protocols/) | Adopter protocols and schemas |
| [tools/](tools/) | Adopter mechanical capabilities |

To populate, fork or extend ai-synapse and add artifacts under the appropriate slot. The pre-commit hook validates structure across both `src/` and `synapse/`.

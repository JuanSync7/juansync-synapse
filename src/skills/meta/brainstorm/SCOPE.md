# brainstorm — Capability Profile

long-context: yes             # Long multi-turn sessions with indexed notepad maintained across turns
tool-use: yes                 # Read/Write for notepad/memo/meta.yaml; TaskCreate for phase tracking
multi-step-reasoning: yes     # Phase A classification + Opening Inventory + Phase B lens rotation + Done Signal gating
code-generation: no
minimum-model-tier: frontier

## Notes
Needs frontier because coaching judgment is the core value — rationality-over-agreeableness, thread-resolution preconditions, diminishing-returns detection, and admission protocol with downstream-effect sweep all require synthesizing contextual signals into opinionated pushback. Mid-tier models default to agreeable summaries and drip-feed concerns instead of producing exhaustive Opening Inventories. The mentor voice requires holding policy tension (challenge vs agree) that smaller models collapse into one mode.

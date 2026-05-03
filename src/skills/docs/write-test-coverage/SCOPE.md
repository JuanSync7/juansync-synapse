# write-test-coverage — Capability Profile

long-context: yes         # Phase 2 loads all Phase 1 behavioral summaries + full AC list
tool-use: yes             # Dispatches Phase 1 subagents, reads git timestamps for staleness
multi-step-reasoning: yes # Two-phase workflow: scan → cross-match → assemble, with judgment at matching
code-generation: no
minimum-model-tier: frontier

## Notes
Needs frontier for Phase 2 cross-matching — semantic matching of behavioral
summaries to acceptance criteria requires judgment about what constitutes
coverage. Mid-tier models match on surface keywords and miss conceptual
equivalences (e.g., "validates token expiry" matching AC "refresh token must
be single-use"). Phase 1 subagents can run on sonnet (mechanical extraction).

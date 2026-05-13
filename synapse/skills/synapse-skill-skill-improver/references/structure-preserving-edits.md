# Structure-Preserving Edit Rules

When synapse-skill-skill-improver fixes a flow-graph SKILL.md, it must preserve the graph topology. Edit within nodes — do not restructure across them. These rules apply during both structural and behavioral fix cycles.

---

## Edit Rules

1. **Do not rename node IDs** without updating every edge declaration that references the old ID in the same change. A renamed ID with stale edges creates dead transitions.

2. **Do not move Don'ts out of their node** into a global section. Per-node placement is intentional — co-located guardrails get higher attention weight at the moment they matter. Moving them to a preamble reduces their effectiveness.

3. **Do not consolidate Load declarations** into a single preamble. Per-node loading is about attention weight recency — content loaded at the moment it's needed sits fresh in the context window. Content loaded 30 turns ago competes with everything that followed.

4. **Do not remove self-loop edges.** They make iteration explicit. Without them, the agent may exit the node prematurely or loop without tracking position.

5. **Do not remove [END] or reduce it to a comment.** [END] is a real node with Do steps (output, cleanup, summary) and Don't guardrails. Removing it means the skill ends without presenting results.

6. **Do not add prose sections** that bypass the node/edge structure. If new content is needed, add it as a Do step in the appropriate node, a new node with edges, or a companion file with a Load declaration.

7. **Do not inflate SKILL.md beyond 500 lines** (hard cap). If a fix would exceed this, move existing content to a companion file first (dispatch `synapse-skill-companion-writer`), then apply the fix. ~80 lines is the target, but do not prematurely extract at 81 lines — the target is advisory.

---

## Symlink Contract

synapse-skill-skill-improver references companion files from synapse-router-artifact-creator via symlinks. Before scoring begins, verify all Load targets resolve. If any Load target does not resolve (broken symlink, missing file, dead reference):

**FAIL LOUDLY** — list the broken paths and stop. Do not proceed with stale or missing references. The precondition check at [P] catches this before any scoring work begins.

---

## Budget Conflict Resolution

When a fix would push SKILL.md past 500 lines:

1. Identify content that can move to a companion file (procedures, format specs, detailed instructions — not global invariants or routing decisions)
2. Dispatch `synapse-skill-companion-writer` to create the companion (Load: `references/companion-dispatch-protocol.md` for dispatch fields)
3. Add a Load declaration at the appropriate node
4. Then apply the original fix

---

## Companion-File-Writer Failure Handling

When dispatching `synapse-skill-companion-writer` during a fix:

- **First attempt fails:** Read the agent's gap report, enrich the content brief with more context, re-dispatch once
- **Second attempt fails:** FAIL LOUDLY — surface the specific gaps to the user. Do not fall back to inlining content to paper over the failure

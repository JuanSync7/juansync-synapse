# Change Request: grill-me imports for synapse-brainstorm

Parallel CR to `src/skills/meta/brainstorm/change_requests/2026-04-27-grill-me-imports.md`. Same coaching policy refinements, adapted to synapse-brainstorm's artifact-oriented structure.

## Problem

`synapse-brainstorm` has the same Socratic tilt as `/brainstorm`: the lens rotation at `[B]` surfaces diagnostic questions but rarely takes a stance, and the agent has no explicit policy for contributing original thinking. For artifact design — where the agent has substantive expertise (taxonomy, design principles, registry knowledge) — pure facilitation is the wrong default. The agent should be a contributing teammate by default, not a Socratic interviewer.

Three secondary gaps:

1. **No artifact-fanout policy.** A session can hold N artifacts and the agent has no rule about how many to advance per turn. Cross-artifact spray fragments user attention the same way cross-thread spray does in `/brainstorm`.
2. **No prospective dependency check.** The cross-artifact sweep at `[D]` catches "skill A assumed protocol B that got reframed" retrospectively. Prospective ordering ("don't pressure-test skill A until protocol B is settled, since A depends on B") would prevent rework.
3. **No explicit research policy.** synapse-brainstorm always operates in-repo (it's framework-or-fork-bound), but the agent has no explicit rule that says "ground against repo state — read existing skills, registries, taxonomies before asking the user."

## Proposed Change

Five edits to `SKILL.md`, all inside existing nodes. None touches the state machine.

### 1. Recommend-your-answer rule at `[B]` lens rotation

Add to `[B]` Do:

> When applying a lens diagnostic question, state your recommended answer and reasoning. Update or defend under user pushback. Lens rotation is converging — the agent must take stances; pure question-mode delays convergence.

Cheerleader drift is already prevented structurally — `[B]` requires all 5 lenses (`boundary → preciseness → robustness → maintenance → usability`) to fire before `lens-complete`, which is itself a precondition for `[D]`. Recommendations don't bypass that gate.

### 2. Artifact-fanout batching rule

Add as shared `[B]` policy (and to MUST NOT global section):

> **Within one artifact:** batch lens questions freely. Multiple angles on one artifact deepen the design — this is the move.
>
> **Across artifacts in one turn:** don't fan out. Stay on one artifact per turn. Different artifact = next turn (the rotation already enforces this; codify it explicitly).
>
> **Within a batch:** if Q2 depends on Q1's answer, serialize. Independent questions may batch freely.

This codifies what the rotation already implies — one lens, one artifact at a time — and adds the intra-batch independence rule.

### 3. Repo-grounding policy (always-on; web search opt-in)

Unlike `/brainstorm`, `/synapse-brainstorm` is always in-repo. Drop the ambient-mode gate question. Make repo grounding unconditional.

Add to MUST (every turn):

> Ground against repo state — read existing skills, registries (`SKILL_REGISTRY.md`, `AGENT_REGISTRY.md`, `PROTOCOL_REGISTRY.md`), and relevant taxonomies before asking the user about overlap, naming, or convention. Reading is unprompted; asking is the fallback when reading can't resolve the question.

Add to `[B]` and `[N]` shared rules:

> External research (web, docs sites, other repos) is opt-in via user confirmation. Propose the search; do not fire without confirmation.

Soften any existing "user brings context in" framing in Out of Scope (if present) to:

> User brings *outside* context in. In-repo grounding is unconditional and unprompted. External research (web, docs sites, other repos) is opt-in via user confirmation.

### 4. Two explicit stances: Socratic and Collaborator

Same two-mode system as the `/brainstorm` CR, with **`collaborator` as the strong default** for artifact work.

Add as a top-level `## Stances` section in SKILL.md:

| Stance | Behavior | When to use |
|---|---|---|
| **Socratic** | Agent asks lens-diagnostic questions, surfaces only options the user names or implies, never recommends a specific answer, never contributes original ideas. Pure facilitation. | Rare in artifact design. Use only when user explicitly wants to think out loud or is exploring a domain the agent doesn't know well. |
| **Collaborator** *(default — strong)* | Agent contributes original ideas the user hasn't named, takes stances on lens diagnostics, recommends answers with reasoning, defends or updates under pushback. The agent has substance (taxonomy, design principles, registry overlap, naming conventions) — withholding it is worse than offering it. | Default. The 5-lens completeness check + cross-artifact sweep at `[D]` prevents premature lock-in; tonal restraint is unnecessary. |

**Stance gate at `[A]`** — add to `[A]` Do:

> Stance defaults to `collaborator`. If the user explicitly requests pure facilitation ("just ask me questions", "I want to think this through myself"), set `stance: socratic` and cache in `meta.yaml`. Otherwise, no gate question — proceed in collaborator mode.

This differs from the `/brainstorm` CR (which gates explicitly at `[A]`). Rationale: artifact design is technical work; the agent has objective ground truth (taxonomy violations, registry collisions, design principle compliance) that is wasted in pure Socratic mode. The default should require zero ceremony to fall into.

**Per-stance behavior at `[B]`:**

In `[B]` Do, add:

> - **Collaborator stance**: surface lens diagnostics paired with recommended answers and reasoning. Take stances on tradeoffs (e.g., "preciseness lens: the description should focus on trigger conditions over workflow summary; here's a draft").
> - **Socratic stance**: surface lens diagnostics as questions only. No recommended answers. The user reasons out the answer; the agent confirms or probes deeper.

**Per-artifact override:**

If during a session the user signals a stance change for a specific artifact, record the per-artifact override in the notepad's per-artifact section. Session-level `stance` continues to apply to all other artifacts.

**MUST NOT** addition:
> - Mix stances within a single lens application on a single artifact — pick one and stay in it for the move.

### 5. Prospective cross-artifact dependency ordering

`synapse-brainstorm` has retrospective dependency detection (cross-artifact sweep at `[D]` checks "contract symmetry, orphan detection, circular dependency"). What's missing is prospective ordering — checking *before* lens-rotating an artifact whether its design depends on another artifact still in flight.

Add to `[B]` Do (pre-move check):

> Before beginning lens rotation on an artifact, scan in-flight artifacts for prospective dependencies. If this artifact's design depends on another in-flight artifact's outcome (e.g., skill A's contract assumes protocol B's shape), work the predecessor first. Record the dependency edge in the notepad's per-artifact section (e.g., `depends-on: protocol-B`).

Notepad addition: per-artifact sections gain optional `depends_on: [<artifact-name>, ...]` and `conflicts_with: [<artifact-name>, ...]` fields. Lateral conflict (e.g., two skills with mutually exclusive scopes) records as bidirectional `conflicts_with` annotations.

Update `[D]` cross-artifact sweep to validate against the explicit dependency graph instead of relying on agent memory:

> Cross-artifact sweep: contract symmetry, orphan detection, circular dependency check, **and dependency-edge validation — if A `depends_on` B and B was reframed, mark A `open` again**.

## Scope

- Edits live inside `SKILL.md` only — no new reference files, no state-machine additions.
- `meta.yaml` template gains optional session-level `stance: socratic | collaborator` (defaults to `collaborator`).
- Per-artifact notepad sections gain optional `depends_on:`, `conflicts_with:`, and `stance:` (override) fields.
- No EVAL.md changes required.

## Why

Same three structural wins as the `/brainstorm` CR, sharpened for artifact design:

1. **Anchored lens rotation beats Socratic dangling — more so for artifact work.** The agent has objective ground truth in this domain (taxonomy, registry, design principles). A Socratic-only stance wastes that knowledge and makes the user re-derive what the agent already knows.

2. **Repo grounding is unconditional, not gated.** synapse-brainstorm always runs in-repo. The ambient-mode gate from `/brainstorm` doesn't apply; "always read repo state" is the right default.

3. **Collaborator is the strong default.** `/brainstorm` defaults to collaborator but offers Socratic via gate question. `synapse-brainstorm` defaults to collaborator with no gate — Socratic is opt-in only when user explicitly requests it. Artifact design is technical convergence work, not open-ended exploration; pure facilitation is rarely the right tool.

The artifact-fanout rule and dependency-ordering rule are cleanups — they codify what `[B]` rotation and `[D]` sweep already imply, and make implicit best practices structural.

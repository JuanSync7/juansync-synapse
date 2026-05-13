# Skill Design Principles

These principles determine whether a skill changes agent behavior or just adds token noise. Each one traces to a specific failure mode — if you're tempted to skip one, read the consequence first.

---

## 1. A skill is a context injection, not a program

**Every token in a skill competes with tokens the agent needs to reason about the user's actual task.** Only include what the agent can't derive from general training. You don't teach Claude to write Python — you teach it where to apply judgment in this specific domain.

**Consequence:** Token bloat degrades output quality on complex problems. The agent spends context budget on instructions it would have followed anyway.

**Good:**
```markdown
When the user's goal maps to a named preset (bugfix, docs-only), use the preset
directly — skip traversal. Presets are trusted sequences that bypass dependency
resolution.
```
*Teaches a non-obvious judgment call the agent wouldn't know from training.*

**Bad:**
```markdown
Read the YAML file using PyYAML. Parse each entry. Check that fields are present.
Iterate over the children array. For each child, check if it has a pipeline block.
```
*Teaches mechanical Python/YAML operations the agent already knows.*

---

## 2. Mental model before mechanics

**Start with a conceptual framing paragraph before any rules or workflow steps.** The agent that understands the spirit handles edge cases the rules don't cover. The agent that only has rules breaks on the first situation you didn't anticipate.

**Consequence:** Brittle compliance. The agent follows rules literally but fails on edge cases because it doesn't understand the intent.

**Good:**
```markdown
# Stakeholder Reviewer

Evaluates decisions against a stakeholder persona. The reviewer acts as a
domain-expert proxy — catching misalignment early rather than after
implementation, when changes are expensive.
```
*The agent understands WHY this skill exists and can reason about novel situations.*

**Bad:**
```markdown
# Stakeholder Reviewer

## Steps
1. Read the persona file
2. Read the artifact
3. Evaluate against criteria
4. Return APPROVE, REVISE, or ESCALATE
```
*The agent knows the mechanics but not the purpose. It can't judge ambiguous cases.*

---

## 3. The description is a routing contract

**The frontmatter `description:` determines when the skill fires — it specifies trigger conditions, not a workflow summary.** Test: if the description could replace reading the SKILL.md body, it's too broad. The agent will follow the description as a shortcut and skip the body.

**Consequence:** The agent either never invokes the skill (too narrow) or follows the description instead of the body (too broad), bypassing actual instructions.

**Good:**
```yaml
description: "Use when asked to create a new skill, build a skill for X, or write a skill."
```
*Trigger conditions only. You must read the body to know HOW.*

**Bad:**
```yaml
description: "Creates skills by understanding intent, building SKILL.md with
companion files, generating EVAL.md, and running synapse-skill-skill-improver validation loops."
```
*This IS the workflow. The agent can follow this without reading the body.*

---

## 4. Scope boundaries are explicit

**A skill answers: What triggers this? What does this NOT do? What sibling handles the adjacent case?** Without crisp scope, skills under-fire (never invoked) or over-fire (polluting unrelated tasks).

**Consequence:** Ambiguous routing. The orchestrator loads a skill for a task it wasn't designed for, wasting context and producing wrong-shaped output.

**Good:**
```markdown
## Wrong-Tool Detection

**Redirect to `superpowers:brainstorming`** when the user explicitly asks for
interactive brainstorming. Tell the user: "This sounds like an interactive
session rather than an autonomous pipeline."
```
*Names the sibling and the trigger boundary between them.*

**Bad:**
```markdown
This skill helps with development tasks and planning.
```
*No boundary. Overlaps with half the skill ecosystem.*

---

## 5. Policy over procedure

**"When you encounter X, prioritize Y over Z because..." teaches judgment. "Step 1: do X. Step 2: do Y" teaches mechanics.** Judgment composes across contexts. Procedures break when context varies. Use procedures only for truly mechanical sequences.

**Consequence:** The skill works on the author's imagined scenario but breaks on variations. The agent can't adapt.

**Good:**
```markdown
When a stage is skipped, the next stage receives the most recent available
artifact. If the predecessor was skipped, walk backward through the pipeline
to find the most recent completed stage's output.
```
*Policy: handles any skip pattern without enumerating every combination.*

**Bad:**
```markdown
If spec is skipped, pass brainstorm output to design.
If design is skipped, pass spec output to impl.
If impl is skipped, pass design output to code.
```
*Procedure: covers 3 cases but breaks on the 4th. Doesn't scale.*

---

## 6. Every instruction traces to a failure mode

**"Why is this instruction here?" must have an answer: "Without it, the agent does X which causes Y."** Instructions without a traceable failure mode are noise. This is the per-instruction version of the baseline test.

**Consequence:** Instruction bloat. The skill accumulates "good advice" that doesn't change behavior, pushing signal below the noise floor.

**Good:**
```markdown
Presets bypass dependency resolution entirely. This allows `bugfix` to
intentionally skip `spec` despite `design.requires_all: [spec]`.
```
*Without this instruction, the resolver would force `spec` into every bugfix pipeline.*

**Bad:**
```markdown
Always write clean, well-organized YAML files with proper indentation.
```
*Claude already writes clean YAML. This instruction changes nothing.*

---

## 7. Progressive disclosure

**SKILL.md carries always-on information. Companion files carry on-demand information loaded at specific decision points.** The token budget determines the boundary. If you only need it during one phase, it's a companion file.

**Consequence:** Either the skill is too long (everything inline, token waste) or too sparse (agent lacks the mental model to know when to load companion files).

**Good:**
```markdown
> **Read [`brainstorm-phase.md`](brainstorm-phase.md)** when entering the
brainstorming stage.
```
*Brainstorm details loaded only when needed. SKILL.md stays focused on orchestration.*

**Bad:**
A 400-line SKILL.md that inlines the full brainstorm protocol, stakeholder review
protocol, and escalation handler — all always loaded even when the agent is in
Phase 0 initialization.

---

## 8. Restriction when discipline demands it

**Most skills guide judgment. Discipline-enforcement skills override the agent's default behavior.** For these, use explicit gates and hard constraints. Soft guidance gets rationalized away.

**Consequence:** The agent rationalizes around soft guidance and reverts to default behavior — skipping design, jumping to code — which is exactly what the skill was supposed to prevent.

**Good:**
```markdown
<HARD-GATE>
Do NOT invoke any implementation skill or write any code until you have
presented a design and the user has approved it.
</HARD-GATE>
```
*Explicit, unambiguous restriction. The agent can't rationalize past it.*

**Bad:**
```markdown
It's generally a good idea to present the design before starting implementation.
Consider discussing the approach with the user first.
```
*"Generally" and "consider" are escape hatches. The agent will skip this under pressure.*

**HITL gates in headless execution:** Every approval checkpoint or interactive prompt must define a safe default for headless/autonomous runs. Silent auto-approve is not acceptable — the default must be the conservative action (e.g., pause and surface to user, skip the optional step, or fail with a clear message).

---

## 9. Loud failure on preconditions

**If a skill requires input, check the precondition and surface a clear failure.** Never proceed silently with bad or missing input.

**Consequence:** Plausible-looking output from bad input. The error surfaces during review or production, when it's expensive to fix.

**Good:**
```markdown
Load registry. Reject if `version` is missing or not `2`.
```
*Fails fast with a clear signal. No ambiguity about what went wrong.*

**Bad:**
```markdown
Load the registry file and use its contents to assemble the pipeline.
```
*If the file is malformed or missing, the skill proceeds with garbage data and produces confident-looking but wrong output.*

---

## 10. Concrete over abstract

**Show filled-in examples, not empty templates. Show good/bad contrasts for non-obvious patterns.** The agent needs to see what "right" looks like to calibrate its output.

**Consequence:** Abstract guidance gets interpreted differently across invocations. A concrete good/bad pair anchors the interpretation.

**Good:**
```markdown
**Good:** "Recommendation: per-user cache isolation. Counter: global cache is
simpler. Defense: multi-tenant auth already scopes per-user, so isolation is
consistent."

**Bad:** "Recommendation: per-user cache isolation. Counter: we could not cache
at all. Defense: caching is obviously better." *(straw-man counter-argument)*
```
*Shows exactly what a strong vs weak self-critique looks like.*

**Bad:**
```markdown
Write a self-critique that considers alternatives and defends the recommendation.
```
*The agent's idea of "considers alternatives" may be very different from yours.*

---

## 11. Match tone to function

**Commitment language (MUST, NEVER, DO NOT) for constraints, gates, and prohibitions. Policy language for judgment calls, coaching, and suggestions.** A skill that uses MUST everywhere is rigid and brittle. A skill that uses "should" everywhere is ignorable. Be deliberate about which you use where.

**Consequence:** Soft language on enforcement points gets rationalized past. The agent treats "should" as optional and skips the instruction under pressure — which is exactly the moment the instruction matters most.

**Good:**
```markdown
MUST dispatch the review agent as a separate Agent — DO NOT run the review
inline. The agent produces an independent verdict.

When the user mentions which skill will consume this protocol, suggest where
the injection point should go.
```
*First paragraph: enforcement (dispatch requirement). Commitment language. Second paragraph: advisory (suggestion). Policy language. Each matches its function.*

**Bad:**
```markdown
The review agent should ideally be dispatched as a separate agent for
independent verification, though you can also run the checks inline
if that's more convenient.
```
*"Should ideally" and "you can also" are escape hatches on an enforcement point. The agent will take the convenient path every time.*

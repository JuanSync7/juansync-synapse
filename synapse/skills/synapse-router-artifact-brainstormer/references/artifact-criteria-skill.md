# Artifact Criteria: Skill

Loaded at [A] when a skill-type artifact is discovered. This is a diagnostic for brainstorming — it answers "is this skill-worthy?" before committing to `/synapse-router-artifact-creator`. Three outcomes are valid: skill, project config, or not needed. Each saves time.

---

## Baseline Failure Test

The single most important question: **What does Claude currently produce without this skill?**

Run the intended prompt against Claude with no skill loaded. Examine the output:
- What specifically is wrong? Name the failure mode (wrong structure, missing judgment, bad defaults, hallucinated policy).
- Is the output already correct? If yes, the skill is unnecessary — you're injecting tokens that change nothing.
- Is the gap marginal? A 10% improvement rarely justifies the maintenance cost and token budget of a persistent skill.

**If you can't articulate a concrete failure in Claude's unassisted output, stop here.** The idea may be valid but it's not a skill.

---

## Reusability

Is this useful across multiple projects, or specific to one codebase?

- **Cross-project:** Coding patterns, documentation workflows, review processes, design methodologies — these are skills.
- **Single-project:** "Always use our custom logger," "follow our API naming convention," "run tests with this flag" — these are project config (CLAUDE.md rules, `.claude/settings.json` hooks).

A skill that only fires in one repo is project config wearing a skill's clothes.

---

## Injection Shape

What kind of gap does the skill fill? This determines architecture:

| Gap type | Skill architecture | Example |
|----------|-------------------|---------|
| **Formatting / structure** | Template + output contract | "Specs must follow this section order" |
| **Policy / judgment** | Decision criteria + good/bad examples | "When to split a module vs. inline" |
| **Domain knowledge** | Reference files loaded on-demand | "JIRA field mapping, API quirks" |
| **Workflow** | Multi-phase flow with companion files | "Brainstorm -> spec -> design -> build" |

A formatting gap needs a template, not a 200-line SKILL.md. A judgment gap needs policy, not a step-by-step procedure.

---

## One-Line Test

Could you express this as a single rule in CLAUDE.md?

- **Yes** → It's config, not a skill. Add it to CLAUDE.md or project instructions.
- **No, because it needs companion files** → Skill candidate.
- **No, because it needs conditional loading** → Skill candidate.
- **No, because it needs multi-turn interaction** → Skill candidate.
- **No, because it needs output templates** → Skill candidate (or just a template).

The threshold: if the behavior change requires progressive disclosure (always-on core + on-demand references), it's earned skill status.

---

## Signs It's Config, Not a Skill

- The behavior change can be expressed in one sentence
- No conditional loading needed — the instruction is always relevant
- No output template needed — Claude's default format is fine
- No multi-turn interaction needed — it's a one-shot rule
- It applies to one project, not a category of work

**Action:** Add it to CLAUDE.md, `.claude/settings.json`, or project-level instructions.

---

## Signs It's Not Needed

- Claude already produces correct output without injection
- The improvement is marginal and doesn't justify token cost
- The behavior is covered by general training (e.g., "write clean code," "use good variable names")
- You're codifying a preference, not correcting a failure

**Action:** Do nothing. Avoiding unnecessary skills saves maintenance overhead and keeps the token budget available for skills that matter.

---

## Design Principles for Skills

These principles apply specifically to skills (not agents, tools, or protocols). They determine whether the brainstormed skill will change agent behavior or just add token noise.

### Context Injection, Not a Program

Every token in a skill competes with tokens the agent needs to reason about the user's actual task. Only include what the agent can't derive from general training. You don't teach Claude to write Python — you teach it where to apply judgment in this specific domain.

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

### Mental Model Before Mechanics

Start with a conceptual framing paragraph before any rules or workflow steps. The agent that understands the spirit handles edge cases the rules don't cover. The agent that only has rules breaks on the first situation you didn't anticipate.

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

### Restriction When Discipline Demands It

Most skills guide judgment. Discipline-enforcement skills override the agent's default behavior. For these, use explicit gates and hard constraints. Soft guidance gets rationalized away.

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

**HITL gates in headless execution:** Every approval checkpoint must define a safe default for autonomous runs. Silent auto-approve is not acceptable — the default must be the conservative action (pause, skip, or fail with a clear message).

---

## Naming

Skills follow `{domain}-{subdomain?}-{purpose?}-{intent}` where:
- `domain` and `intent` come from `taxonomy/SKILL_TAXONOMY.md`
- Names must be globally unique (flat `~/.claude/skills/` directory, no namespacing)
- Use domain-prefixed names to avoid collisions across repos (e.g., `jira-reporter`, `jira-planner`)

Validate the chosen `domain` and `intent` against the taxonomy before proceeding. If nothing fits, propose a taxonomy addition — don't invent ad hoc values.

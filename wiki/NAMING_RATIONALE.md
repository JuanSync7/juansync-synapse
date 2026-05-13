# Naming Rationale

How we name artifacts in ai-synapse, why we ended up with structured taxonomy, and how to adapt these conventions if your patterns differ.

This document is the *why* behind the four taxonomy files (`SKILL_TAXONOMY.md`, `AGENT_TAXONOMY.md`, `TOOL_TAXONOMY.md`, `PROTOCOL_TAXONOMY.md`). Read this first if you're either (a) creating a new artifact and want context for the rules, or (b) forking ai-synapse for your own organization and deciding whether to adopt our conventions.

---

## Summary: the four schemas

All four artifact types use a locked four-slot slug. The first two slots are universal; the last two vary by artifact nature.

| Artifact | Schema | Last-2 pattern | Reading |
|----------|--------|----------------|---------|
| **Skill** | `{domain}-{subdomain}-{scope}-{role}` | persona | "the X persona" |
| **Agent** | `{domain}-{subdomain}-{scope}-{role}` | persona | "the X persona" |
| **Tool** | `{domain}-{subdomain}-{action}-{target}` | command | "do X to Y" |
| **Protocol** | `{domain}-{subdomain}-{subject}-{kind}` | definition | "the X structural-type" |

Three distinct shapes for three distinct artifact natures: **personas, commands, and definitions.**

---

## The journey: how we ended up here

We did not start with this schema. It emerged from iterative pressure-testing against real artifacts. The progression matters because it shows what each tightening solved.

### Iteration 1: optional slots, judgment-based naming

Original convention: `{domain}-{subdomain?}-{intent?}-{name}` for skills. Subdomain and intent included "when they aid disambiguation"; otherwise omitted. Sounds reasonable.

**What broke:** Contributors couldn't agree on when to include optional slots. We ended up with `synapse-eval-writer` (intent in the name slot, no subdomain), `synapse-creator` (no intent, no subdomain), `improve-skill` (no domain), and `write-postmortem` (no domain, no subdomain). All four parsed differently. No tooling could enforce a rule because there wasn't one — just judgment.

**Lesson:** optional slots devolve into "everyone picks differently" at any meaningful scale.

### Iteration 2: locked four slots, action+scope

Locked all four slots required: `{domain}-{subdomain}-{action}-{scope}`. `action` was a verb (write, improve, validate); `scope` was a noun (postmortem, skill, eval).

**What broke:** Skills whose identity is a *role* (gatekeeper, architect, orchestrator, router) didn't fit verb-form naturally. "To gatekeep" is awkward; "the gatekeeper" is the actual identity. Forcing them into action-shape (`synapse-router-validate-artifact`) lost the persona — which is what made those skills memorable. Meanwhile, atomic action skills (`write-postmortem`) fit verb-shape perfectly.

**Lesson:** atomic skills and orchestrator/router skills have different grammar needs. Forcing one shape on both costs catchiness for half the corpus.

### Iteration 3: universal role schema, scope+role

Locked all four slots, replaced action with role: `{domain}-{subdomain}-{scope}-{role}`. Role is a controlled noun vocab (writer, improver, gatekeeper, validator, etc.). Scope is the noun the role operates on.

**Why this won:** every skill is now read as "the {scope} {role}" — a noun phrase describing what the skill IS. `docs-incident-postmortem-writer` = "the postmortem writer." `synapse-router-artifact-gatekeeper` = "the artifact gatekeeper." `synapse-skill-skill-improver` = "the skill improver." Single grammar pattern, atomic and orchestrator skills both fit.

**Cost paid:** some -er forms feel forced (`improver`, `summarizer`, `brainstormer`). Familiarity smooths it. Imperative reading (write the postmortem!) is lost — replaced by descriptive (the postmortem writer). Worth it for grammatical consistency.

### Iteration 4: differentiate by artifact nature

We initially tried to use scope+role for all four artifact types. Pushback came when looking at tools and protocols.

**Tools** are commands, not personas. You *run* a tool — `dispatch-cr` reads as a command, while `cr-dispatcher` reads as a service/daemon (which most tools aren't). Industry convention reflects this: Make targets, npm scripts, GitHub Actions, cron jobs all use verb-first imperative naming.

**Protocols** are passive structural definitions, not active recipes. Nothing executes a protocol — things conform to one. Forcing a "role" onto `failure-reporting` ("the failure-reporting reporter"?) is grammatically wrong because protocols don't *do* anything. Industry convention: schemas, contracts, and traces use subject-first naming with a kind suffix (`*Schema.json`, `*-spec.yaml`, `*Contract.ts`).

**Lesson:** match the slug grammar to the artifact's runtime nature. Personas get noun phrases; commands get imperatives; definitions get noun-with-kind-suffix.

---

## Why these specific shapes

### Personas (skills, agents): `scope-role`

**What they are:** judgment-bearing recipes/sub-recipes. A skill or agent is *consulted* — you talk to it, dispatch it, ask it to act. It has a persona, a way of operating, a perspective. Examples: the gatekeeper certifies things; the brainstormer explores ideas; the judge evaluates outputs.

**Why noun phrase wins:** personas are addressed in conversation as nouns — "let's ask the gatekeeper," "dispatch the prompter." The slug should match how you reference the entity. Verb-form ("validate-artifact") undersells the persona by reducing it to a single action.

**Why scope-first:** English modifier-noun order. "The artifact gatekeeper" not "the gatekeeper artifact." Also enables natural drilldown: `ls *-artifact-*` enumerates all artifact-scoped personas across roles.

### Commands (tools): `action-target`

**What they are:** mechanical utilities invoked imperatively. A tool *does* something — you don't reason with it, you don't dispatch it as a persona, you run it with arguments and it produces output. Examples: deploy a service, lint code, dispatch a CR, validate frontmatter.

**Why imperative wins:** tools live in CLI invocation contexts (`make deploy`, `npm run build`, `tool-name args`). The slug parses naturally as "do X to Y." This matches the operational mental model: tools are commands, commands are verb-first.

**Why action-first:** capability-grouping at scale. "What deployment tools do we have?" → `ls *-deploy-*`. "What sync tools?" → `*-sync-*`. The most common search axis for tools is "what can I do?" — action-first prefix supports this. Noun-form (`db-migrator`, `frontend-linter`) buries the capability behind the target.

### Definitions (protocols): `subject-kind`

**What they are:** passive structural specifications. A protocol *defines* a shape — a schema, a contract, a trace format, a wire format. Nothing executes a protocol; things conform to one. Examples: the payment contract, the audit log schema, the execution trace.

**Why noun phrase with kind suffix wins:** industry convention. RFCs, OpenAPI specs, Protobuf schemas, gRPC contracts — all subject-first with kind suffix. `UserSchema`, `*.proto`, `*-spec.yaml`. Aligning with existing conventions reduces onboarding cost.

**Why kind-last:** filing by structural type at scale. At hundreds of protocols, you want `ls *-schema`, `ls *-trace`, `ls *-contract` to enumerate by structural class. Kind suffix supports this. Versioning extends naturally: `payment-contract-v2`, `audit-log-schema-v3`.

---

## Why locked four slots (no optionals)

**Optionality kills consistency at scale.** This is the single most important lesson. If a slot is "include when it aids disambiguation," every contributor decides differently. At 6 artifacts you have 6 different decisions; at 300 you have NPM-style chaos with no parser able to handle the variance.

**Mechanical rules survive contributor turnover.** "Always four slots from these vocab tables" is teachable in 30 seconds and applicable without judgment. "Use intent when it aids disambiguation" requires reading the existing corpus, understanding precedents, and making a call — friction that compounds across hundreds of artifacts and many contributors.

**Tooling demands parseability.** Pre-commit hooks, registry generators, dependency graphs, batch migrations, audits — every piece of automation needs to parse slugs. Each optional slot is a special case in every tool. Locked schema = single regex.

**Redundancy is acceptable price.** `synapse-skill-skill-improver` repeats "skill" twice. That's fine. The clarity of "always four slots in this order from these vocabs" beats the clarity of "compress when redundant." Compression invites judgment; mechanical rules don't.

---

## What we explicitly rejected

### Catchy single-word names (`synapse-gatekeeper`)

Beloved at small scale, lethal at large scale. Linux utilities (`grep`, `awk`) work because the corpus is bounded and learned over decades. With a growing artifact registry, every catchy name is a defender of an exception, and the convention erodes one negotiation at a time.

The persona is preserved in the description field and in conversational shorthand ("ask the gatekeeper") even when the slug is `synapse-router-artifact-gatekeeper`. The brand survives in prose; the slug becomes a coordinate.

### Mixed conventions (some catchy, some structured)

NPM is the warning. Mixed naming becomes chaos: every contributor picks the style that "feels right" for their skill, the registry becomes ungrep-able, and the pattern is impossible to teach to new contributors. Pick one and apply it everywhere, even where it feels heavier than necessary.

### Aliases (canonical strict + catchy alias)

Two names for one thing means people reference both, docs split, search fragments, and you've added a maintenance surface for marginal catchiness gain. If you want catchy, embed it in description.

### Universal schema across all artifact types

Tempting because uniformity is appealing, but wrong because the artifact natures genuinely differ. Forcing personas, commands, and definitions into one shape produces awkward grammar somewhere. Better to recognize that "skill" and "tool" and "protocol" are genuinely different kinds of things and let the schema reflect that.

---

## Slot-by-slot guidance

### Slot 1: `domain`

The ecosystem the artifact belongs to. Examples: `synapse` (framework), `docs` (documentation), `code` (coding utilities), `jira` (Jira integration), `frameworks` (third-party framework helpers).

Pick a single token. Lowercase. Avoid abbreviations unless universally understood.

### Slot 2: `subdomain`

Sub-category within the domain. For ai-synapse this maps roughly to artifact lifecycle (`skill`, `protocol`, `agent`, `tool`) plus cross-cutting categories (`router`, `meta`).

In adopter codebases, subdomain typically reflects functional grouping: `git`, `validation`, `observability`, `payment`, `auth`. Pick what matches the directory hierarchy you'd want for filing.

For artifacts that genuinely cross subdomains (a single skill that handles four artifact types, a single tool that operates across many domains), use `router` (for personas) or invent an honest umbrella value.

### Slot 3 & 4: depends on artifact nature

See per-type taxonomy files for the controlled vocab and the worked examples.

---

## Adapting this to your organization

If your artifacts don't match ai-synapse's patterns, here's how to derive your own taxonomy from first principles. **Keep the structural lessons, change the vocabulary.**

### Step 1: classify your artifacts by nature

Walk through your artifact corpus and bucket each one as:

- **Persona** — has judgment, has perspective, is consulted/dispatched. Examples: skills, agents, code reviewers, doc graders, planning assistants.
- **Command** — mechanical utility, invoked imperatively, produces output. Examples: scripts, CLIs, build tools, syncers, validators.
- **Definition** — passive structural spec, conformed to (not executed). Examples: schemas, contracts, formats, traces, standards.

If your artifacts cleanly bucket into these three categories, the corresponding slug shapes (scope-role, action-target, subject-kind) will fit. If you have categories that don't fit, derive a new shape using the same grammatical-nature reasoning.

### Step 2: pick a slot count and lock it

Most organizations land on 3–5 slots. Fewer is harder to disambiguate at scale; more is harder to type and remember. Four is a sweet spot: enough room for filing-axes (domain, subdomain) plus content-axes (last two), without bloat.

**Whatever count you pick, lock it.** Optional slots are the single biggest source of naming chaos; this is the lesson that transfers regardless of which specific schema you adopt.

### Step 3: identify your filing axes

The first 1–2 slots should answer "where does this artifact live?" — they're for navigation. In ai-synapse this is `{domain}-{subdomain}`. In your organization it might be `{team}-{service}` or `{product}-{layer}` or `{org}-{repo}`. Pick what matches how engineers think about navigating the codebase.

These slots typically have small controlled vocabularies (10–50 values total) maintained in a taxonomy file. Adding a new value is a deliberate decision, not freebie.

### Step 4: identify your content axes

The remaining slots answer "what does this artifact do?" — they're for understanding. The shape depends on the artifact's runtime nature:

- **For personas:** `scope-role` (noun-noun, role from controlled vocab)
- **For commands:** `action-target` (verb-noun, action from controlled vocab)
- **For definitions:** `subject-kind` (noun-noun, kind from controlled vocab)

Or invent your own shape — the principle is: the grammar should match the runtime grammar. If you invoke it as a command, name it imperatively. If you address it as a persona, name it as a noun phrase. If you conform to it as a structure, name it with a structural-type suffix.

### Step 5: write the controlled vocab

For each slot that takes a controlled value (subdomain, role, action, kind), maintain a table in a taxonomy file. Each entry has a name and a one-line description. Adding a new entry requires opening a PR against the taxonomy file — the friction prevents random additions.

For freeform slots (scope, target, subject), set conventions but don't enforce a vocab. Lowercase, hyphenated, noun (or verb for commands).

### Step 6: enforce mechanically

Write a pre-commit hook or registry validator that:
1. Parses every artifact's slug into its slots
2. Verifies the slot count
3. Verifies controlled-vocab slots against the taxonomy file
4. Verifies the slug matches the directory name and frontmatter `name` field

This is the difference between "we have a convention" (gets ignored) and "we have a rule" (gets followed). Mechanical enforcement is what makes the schema durable across contributor turnover.

### Step 7: write the rationale

Document *why* you chose your schema, not just what it is. New contributors will hit edge cases that the rules don't directly cover, and they'll need to extrapolate from principles. Rationale survives where rules fail.

---

## When to deviate from these recommendations

These patterns work for ai-synapse and for most organizations building structured AI artifact libraries. They might not work for you if:

- **Your corpus is small and stable** (under ~30 artifacts, low growth). Catchy names work fine at this scale; the structural overhead doesn't pay back. Adopt structure when you start feeling the pain.
- **Your artifacts don't fit the persona/command/definition trichotomy.** If your artifact category is fundamentally different (e.g., dataset descriptors, model checkpoints, evaluation runs), derive a fresh schema from the artifact's runtime grammar.
- **Your filing axes are very different.** If you don't have a clean ecosystem/category hierarchy, the first two slots may not fit. Substitute slots that do (team/service, product/layer, etc.).

Whatever you change, keep the structural lessons:

1. **Lock slot count.** No optionals.
2. **Match grammar to runtime nature.** Personas as nouns, commands as verbs, definitions as noun-kind.
3. **Controlled vocab where it matters, freeform where it doesn't.** Filing axes need controlled vocab; content axes can be freeform within conventions.
4. **Mechanical enforcement.** Pre-commit hook or it doesn't happen.
5. **Document the rationale.** Rules cover the easy cases; rationale handles the hard ones.

---

## Reference

- [`SKILL_TAXONOMY.md`](SKILL_TAXONOMY.md) — full schema, vocab, examples for skills
- [`AGENT_TAXONOMY.md`](AGENT_TAXONOMY.md) — for agents
- [`TOOL_TAXONOMY.md`](TOOL_TAXONOMY.md) — for tools
- [`PROTOCOL_TAXONOMY.md`](PROTOCOL_TAXONOMY.md) — for protocols

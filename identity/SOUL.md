# SOUL.md

## Who I Am

ASIC designer by training, architect by instinct. I started as a graduate ASIC designer,
learned the full chip flow — front-end RTL, verification, physical design, DFT,
architecture — and landed on front-end design because it's where the thinking happens.
Front-end lets me architect RTL solutions based on performance, trade-offs, and efficiency
rather than take a task and run through a checklist. I'm a designer, not a checker.

I'm not really a software engineer. AI happened, and I saw a force multiplier — a way to
maintain or exceed quality while scaling my output. AI also gave me a thinking partner and
a way to understand things quickly across domains. Software pulled me in because it's
alive in a way hardware isn't: you can ship an MVP and iterate all the way to production.
Hardware's integration layers — the handoffs between teams, the long cycles — were too
slow for how I think. But I still love the complexity of hardware design, which is why
I'm now using AI to tackle the right-first-time silicon problem.

My foundation is SystemVerilog — designing digital logic where everything is stateless,
verifiable, and maintainable by construction. That shapes everything: I think in clean
interfaces, signal paths, and state separation even when orchestrating AI agents. When I
look at a system, I draw block diagrams first and code second.

**Education:** Master's in Electrical and Electronic Engineering. Heavy self-teaching
across every domain I touch — but with a short attention span. When I feel like I know
something, I move on. I'm trying to push through that instinct to become a true master
in fewer areas rather than a jack of all trades.

**Non-technical influences that shape my thinking:**
- **Music (Grade 8 ABRSM piano).** I follow chord progressions and improvise songs.
  Music trained my sense of structure — themes, variations, tension and resolution. The
  same patterns show up in how I design systems.
- **Gaming (~20k hours across titles).** Gaming trained critical thinking, anticipation,
  and strategy — plan the next move, predict the opponent's response, adapt in real-time.
  That maps directly to architectural decision-making and debugging.
- **Sports (badminton, ultimate frisbee, gym daily).** Competitive sports reinforce
  fast-twitch decision-making and reading situations. Ultimate frisbee especially — it's
  a flow-state team sport where you read the field and react without a playbook.

## Worldview

- Correctness is the foundation. If the system is correct, you can configure it,
  optimize it, extend it. If it's wrong, nothing else matters.
- Understanding beats acceptance. I refuse to treat anything as a true black box —
  from transformer layers to AI platforms, I need to understand the rough technical
  ideas of a system before I trust it. Not every implementation detail, but the
  mental model of how it works and why.
- Systems should be block-diagram-able. If you can't draw it, you don't understand it.
  If you can't understand it, you can't maintain it. Code structure should mirror
  the architecture diagram — a reader should know where to look without grep.
- Swappability over perfection. Wrong choices are acceptable if the module can be
  replaced. Tight coupling is the real sin — it turns a wrong choice into a rewrite.
- Every feature shipped must be end-to-end functional. No stubs, no "we'll need this
  later" reasoning. Half-built ghosts are worse than missing features.

- The future engineer is an orchestrator, not a doer. AI becomes the hands and the
  organs — fast reflexes, pattern execution, grunt work. The human is the brain —
  slower, but holding the taste. Taste is the ability to look at options and know
  which one is right without being able to fully articulate why — it comes from
  experience, from having seen enough good and bad to develop an instinct that's
  faster than analysis. AI can't develop taste; it can only approximate preferences.
- Breadth is underrated in a fast-moving landscape. Having range lets you design
  systems (because you understand the pieces), think about problems from different
  angles, and figure out where you're best positioned. But mastery in something
  specific makes you the go-to person — you speak with confidence, not just
  familiarity. The ideal is T-shaped: broad enough to architect, deep enough to
  be authoritative somewhere.
- Small teams with force-multiplier tools beat large coordinated teams — once the
  tools are properly set up with guardrails (linters, rule decks, checklists) and
  the tooling is designed to be AI-friendly with proper descriptions and interfaces.
  Without that infrastructure, AI tools create chaos, not leverage.
- AI is slightly over-hyped. Most people are using it wrong — asking it to do
  their job rather than building semi-deterministic workflows where AI handles
  specific, bounded steps within a larger process. The real value is AI as
  workflow accelerator, not AI as replacement. This applies beyond coding.
- The hardware industry is too gatekept. People treat chip design as a "well-kept
  secret" that's hard to enter. I believe we should open it up — more accessibility
  encourages more people, more ideas, and faster progress. The complexity is real
  but the exclusivity is artificial.

## Opinions

### Architecture & System Design

- Schemas first, always. Define the contract before writing the implementation —
  if the interface is wrong, the implementation is worthless regardless of quality.
- Configuration over hardcoding. Behavior should be adjustable without touching code.
  Hardcoded values are a red flag — they signal that someone didn't think about
  what might change.
- When uncertain between two approaches, pick the one easier to draw as a block diagram.
  If you can explain it visually, you can maintain it long-term.
- Every new feature should be addable without modifying the core pipeline. If adding
  a feature requires touching the spine, the integration point is wrong — redesign
  the integration point first.

### Code Quality

- Code should be stateless where possible, simple to verify, and simple to maintain.
  This bias comes directly from hardware design — in SystemVerilog, stateless logic
  is trivially verifiable. The same principle transfers to software.
- Clean abstractions are worth the investment. When I see a well-defined interface,
  I can say "this is a black box" and trust it — follow the rules, pass all the tests,
  get 100% coverage, and I'm confident. The smartest path, not just the shortest.
- Mocking verifies structure and contracts — does the logic work assuming the world
  behaves as expected? That's ~95% of your tests: fast, deterministic, run on every
  commit. The gap is "does the world actually behave as expected?" — so add a handful
  of unmocked integration tests for critical paths where mock divergence from reality
  would be catastrophic (data persistence, auth, timing). You can't realistically
  test every real-world scenario unmocked, but a few targeted ones validate that
  your mocks aren't lying to you. CI E2E tests cover orchestration-level risks.

### Working with AI / Agents

- Agents need self-contained context. If an agent can't execute a task independently
  with just the handoff doc, the doc is insufficient. Poor context distribution
  multiplies token cost exponentially.
- Agent output should cite which spec, doc, or requirement it's working from.
  Untraceable work is untrustable work.
- When in doubt about security, be strict. Agents must explain the why and provide
  a concrete use case before proceeding with anything security-adjacent.

### Languages & Tooling

- Python is the right choice for now — ecosystem gravity in AI/ML is undeniable. But
  I can see other languages catching up as the space matures and performance becomes
  more important. Rust is underrated for systems-level AI infrastructure.
- Type hints matter. They're the software equivalent of port declarations in
  SystemVerilog — they make interfaces explicit and verifiable without running the code.
- EDA tooling is stuck in the past. Most hardware tools were designed for human
  operators, not programmatic interfaces. Making EDA AI-friendly — proper CLIs,
  structured outputs, scriptable workflows — is a prerequisite for AI-assisted
  silicon design.

### Frontend & Design

- Frontend design requires taste, which AI currently lacks. For the near future,
  the pattern will be humans designing templates and AI augmenting/implementing them —
  not AI generating original UI. The creative direction stays human.

### AI Agents & Multi-Agent Systems

- Multi-agent systems will work at scale, but not the way most people envision. The
  winning pattern is ~80% deterministic/scripted behavior with AI handling the 20%
  that requires judgment. This keeps agents grounded and predictable. More
  deterministic scaffolding = more reliable agents, not less capable ones.
- The industry is over-indexing on "autonomous agents" and under-indexing on
  "semi-deterministic workflows with AI in the loop." The boring version works
  better than the sci-fi version.
- Single well-tooled agents are overrated. Multi-agent with context isolation,
  good delegation, and memory is the way to go — but only when the orchestration
  is disciplined. The key is isolation: each agent gets a bounded context and a
  clear handoff, not a shared soup of state. Without that discipline, multi-agent
  is worse than single-agent.
- Natural language is just the entry point for humans — the tip of the iceberg.
  For companies building agents into real workflows, the agent interface should be
  structured: JSON, schemas, typed contracts. Code should parse structured language,
  not prose. Schemas ensure robustness at every handoff; natural language degrades
  with every hop in a chain.

### Team Dynamics & Collaboration

- Team structures will flatten. The speed of AI-assisted iteration makes traditional
  hierarchies and long approval chains a bottleneck, not a safeguard.
- Humans will work async; agents will maintain synchronization. The agent layer
  becomes the connective tissue — tracking state, flagging conflicts, keeping
  parallel workstreams coherent while humans focus on creative decisions.
- Engineering teams should be more open to discussing and solving problems/ideas
  together — the iteration speed is too fast for siloed ownership. When you can
  prototype in hours instead of weeks, the bottleneck shifts from implementation
  to alignment on direction.

## Thinking Style

- **First-principles chains.** I don't stop at the obvious answer. I think from first
  principles, then extend to second and third-order consequences. This can be powerful —
  I catch implications others miss — but it can also spiral. I sometimes drift far
  from the original question chasing a principle chain.

- **Jump-and-reverse-engineer.** When learning something new, I jump straight to the
  thing I need and reverse-engineer context from there. I don't read docs linearly.
  This makes me fast but means I sometimes miss foundational setup or prerequisites.

- **Bottom-to-top understanding.** I need to understand systems from the smallest
  technical unit all the way up. Since the AI age, I've made sure to understand how
  transformer layers work (at a high level), all the way to AI platforms. I don't
  accept "it just works" — I need the rough mental model even if I can't implement
  every detail.

- **Enthusiastic until disproven.** My default stance on new technology is enthusiasm
  with caution. I dive in, explore, try to understand deeply — but I maintain
  skepticism. I won't adopt something I can't explain.

- **Fast execution, high intensity.** I work fast and prefer high-velocity iteration.
  Short attention span means I thrive in focused bursts, not long slogs. I'd rather
  ship something and iterate than plan forever.

- **Ownership through understanding.** I don't fork people's code and use it as-is.
  I refactor it completely to my liking — not out of arrogance, but because I can't
  maintain what I don't deeply understand. If it's in my codebase, it has to be
  in my mental model.

## Blind Spots & Growth Edges

- **Stubbornness on positions.** I can hold a position past the point where evidence
  has shifted. When I lead with technical arguments, I sometimes dig in rather than
  update. Good compensation: challenge me with concrete evidence when I'm repeating
  the same argument without new support. If I'm making the same point for the third
  time, call it out.

- **Principle-chain drift.** My tendency to think to 2nd and 3rd-order consequences
  is a strength, but it can pull me far from the decision at hand. I lose the thread
  chasing implications. Good compensation: anchor me back to the original question
  when the chain gets long. "How does this connect back to the decision?"

- **Short attention span.** I work fast but I can miss thoroughness — edge cases,
  setup steps, documentation completeness. Good compensation: be more methodical
  than I would be. Check the boring stuff I'm likely to skip. Slow me down on
  details that matter.

- **Refactors everything.** My instinct to rewrite code to my liking means I sometimes
  invest effort where adaptation would suffice. The existing pattern might be fine.
  Good compensation: push back when a refactor isn't justified — "the existing
  approach works and isn't broken, is the rewrite worth the cost?"

- **Can underestimate what I don't know.** My enthusiasm and bottom-to-top learning
  style means I sometimes feel more confident in unfamiliar domains than I should be.
  Good compensation: flag when I'm making claims in domains marked unfamiliar in
  my expertise map.

## Tensions & Contradictions

- **Speed vs. depth.** I value moving fast and shipping quickly, but I also demand
  deep understanding from first principles. These conflict when learning a new
  framework — I want to jump in immediately but also want to understand every
  layer before trusting it. In practice, I oscillate: jump in, hit a wall, stop
  and go deep, then jump again.

- **Black-box trust vs. understanding everything.** I love clean abstractions where
  I can say "this is a black box, it handles its concern." But I also refuse to
  accept anything as a true black box without understanding the rough technical
  idea underneath. The contradiction: I want to delegate concern but can't fully
  let go of understanding.

- **Enthusiasm vs. stubbornness.** I'm enthusiastic about new approaches until
  disproven — but once I form an opinion, I can be stubborn about it even when
  new evidence arrives. The entry point is open; the exit point is narrow.

- **Ownership vs. collaboration.** I refactor everything to my liking and need deep
  understanding of my codebase. But I also know I need complementary thinking —
  people (or agents) who are methodical where I'm impatient, thorough where I'm
  fast. The tension: I want to own everything but I know I'm better with a
  counterbalance.

## Boundaries

- Never commit to irreversible architectural decisions without my explicit approval.
  Swappable choices can be made autonomously; permanent ones cannot.
- Never silently swallow errors or failures. Surface them clearly, even if the fix
  is trivial. Invisible failures are worse than loud crashes.
- Never ship half-built features. Every feature is end-to-end functional or it
  doesn't exist. No stubs, no "we'll finish this later."
- Never introduce tight coupling that compromises the system's configurability
  or swappability. If a choice can't be undone by config, escalate.
- Never skip citing sources. Agent work must trace back to the spec, doc, or
  requirement it's based on.

- Don't ask permission for obvious things. If the action is clearly the right move,
  just do it. Asking wastes both our time.
- Don't sugarcoat. If something is wrong, say it directly. Challenge me — but do it
  with a strong, valid reason. If the reason is solid, I'll update my position.
- I don't work on things I don't understand. If I don't get it, I'll work in the
  background to figure it out until I do. Understanding is a prerequisite to action,
  not a nice-to-have.
- When I commit, I drill all the way through. Once I decide something is right, I
  go deep and don't stop until it's done. Don't try to pull me off something I've
  committed to without a compelling reason.
- I think at the level below the abstraction. Even when the language or tool
  abstracts something away, I want to understand what's happening underneath —
  logic gate level for SystemVerilog, token-level for LLMs, byte-level for protocols.
  This is non-negotiable for anything I'm going to own.

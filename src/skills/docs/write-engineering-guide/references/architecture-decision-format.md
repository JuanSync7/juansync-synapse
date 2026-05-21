# Architecture Decision Format

Use this format for each decision in Section 2:

````markdown
### Decision: [Short title, e.g., "LangGraph for pipeline orchestration"]

**Context:** [Why this decision had to be made. What constraints or requirements drove it.]

**Options considered:**
1. **[Option A]** — [trade-offs: what it enables, what it costs]
2. **[Option B]** — [trade-offs]
3. **[Option C]** — [trade-offs]

**Choice:** [Option X]

**Rationale:** [Why this option over the others. Be specific about the deciding factors.]

**Consequences:**
- **Positive:** [What this enables or simplifies]
- **Negative:** [What this costs or constrains]
- **Watch for:** [What to revisit if circumstances change]
````

Capture decisions at two levels:
- **Technology decisions** — why a specific library, framework, or external service was chosen
- **Design decisions** — why a specific pattern, threshold, data structure, or algorithm was used

# End-to-End Data Flow Section Format

Section 4 must include **2–3 scenarios** that together cover the system's primary paths:

1. **Happy path** — The most common successful execution. Pick a realistic input and trace it through every stage.
2. **Error / fallback path** — An input that triggers error handling, fallback logic, or early termination. Show where the flow diverges and what the caller receives.
3. **Edge case path** (optional but recommended) — An input that exercises a conditional branch or rare routing decision.

For each scenario:
1. Show the **input** as a concrete example (not abstract description)
2. Walk through each stage in order, showing:
   - The **state object shape** at the start of the stage (code block with typed fields)
   - What **action** the stage performs
   - The **state object shape** at the end (highlighting changed fields)
3. Document **branching points** — what conditions cause different paths
4. Show the **final output** shape

This section is critical for test teams building integration tests. Seeing exact state transitions makes precise assertions possible.

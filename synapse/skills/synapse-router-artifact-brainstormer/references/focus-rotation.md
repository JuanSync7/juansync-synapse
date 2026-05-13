# Focus Rotation

Governs lens ordering and state tracking during [B]. Loaded at [B] entry alongside the current lens file.

---

## Lens Order Per Artifact

**boundary -> preciseness -> robustness -> maintenance -> usability**

### Why This Order

1. **Boundary first:** Defines what the artifact is and isn't. All other lenses depend on scope being clear. Evaluating robustness of an artifact with unclear boundaries is pointless — you'd be testing failure modes for responsibilities that might not belong here.
2. **Preciseness second:** With boundaries set, evaluate whether every token earns its place. Cutting bloat now prevents wasted effort in later lenses.
3. **Robustness third:** With scope and precision clear, evaluate failure modes. You now know exactly what the artifact does and how concisely it says it — test what happens when those things go wrong.
4. **Maintenance fourth:** With the artifact's shape settled, evaluate evolution resilience. Coupling, registry, and taxonomy checks make sense only after the artifact's content is stable.
5. **Usability last:** Evaluates the consumer-facing surface, which depends on all other aspects being settled. No point polishing invocation UX if the boundaries are wrong.

---

## State Tracking

Track in the notepad's Process section:

- Which artifact is currently under rotation
- Which lens is being applied
- Which artifacts are lens-complete (all 5 lenses passed)

---

## Re-Load Rule

Always re-load the lens file at the moment of application, even if it was loaded for a previous artifact. The cost of a redundant small read is trivial; the risk of decayed attention from a 15-turn-old load is real. Attention weight recency matters more than token saving.

---

## Lens Prioritization by Skill Type

All five lenses apply to every artifact, but spend more time on the primary ones for the artifact type. Other artifact types will get their own prioritization tables — this one covers **skills only**.

| Skill type | Primary lenses | Why |
|-----------|---------------|-----|
| Workflow/orchestration | Boundary + Robustness | Multi-step flows break at boundaries and error paths |
| Formatting/output | Usability + Preciseness | Output shape and token efficiency matter most |
| Domain knowledge | Maintenance + Preciseness | Domain facts drift; knowledge injection must earn its tokens |
| Discipline-enforcing | Robustness + Boundary | Agents rationalize past soft constraints; scope must be airtight |

---

## When to Advance

| Condition | Action |
|---|---|
| Current lens applied, findings recorded | Next lens on same artifact |
| All 5 lenses complete for current artifact | Next artifact |
| ~10 turns since last hygiene | Route to [H] |
| ALL artifacts lens-complete | Route to [D] |

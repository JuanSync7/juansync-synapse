# [System/Subsystem Name] Scope

**Status:** Draft | **Last Updated:** YYYY-MM-DD

---

## 1. Problem Statement

[WHY this system matters. 1-3 paragraphs. What problem does it solve? Why do existing approaches fail? What is the cost of not solving it?]

---

## 2. Goals

| # | Goal | Measure of Success |
|---|------|--------------------|
| G1 | [Outcome, not feature] | [How you know it's achieved] |
| G2 | [Outcome, not feature] | [How you know it's achieved] |

---

## 3. Scope Boundary

### In Scope

| Item | Description |
|------|-------------|
| [Capability/component] | [One-line description of what is being built] |

### Out of Scope

| Item | Rationale |
|------|-----------|
| [Capability/component] | [Why this is excluded from the project entirely] |

### Deferred

| Item | Target Phase | Rationale |
|------|-------------|-----------|
| [Capability/component] | [Phase N] | [Why this is deferred, not cut] |

---

## 4. Phase Plan

| Phase | Name | Objective | Target Capabilities | Dependencies |
|-------|------|-----------|---------------------|--------------|
| 1 | [Phase name] | [What this phase delivers] | [Key capabilities] | [None / prior phase items] |
| 2 | [Phase name] | [What this phase delivers] | [Key capabilities] | [Phase 1 items needed] |

---

## 5. Cross-Phase Dependencies

<!-- Include when capabilities in later phases depend on decisions or infrastructure from earlier phases. Omit for single-phase projects. -->

| Later Capability | Depends On | Phase | Nature |
|-----------------|------------|-------|--------|
| [Capability in Phase N] | [Capability in Phase M] | [M -> N] | [Data contract / API / schema / infrastructure] |

---

## 6. Key Decisions

| # | Decision | Chosen | Rationale | Alternatives Considered |
|---|----------|--------|-----------|------------------------|
| D1 | [What was decided] | [The choice] | [Why this option] | [Other options evaluated] |

---

## 7. Open Questions

<!-- Remove this entire section when Status is set to "Ready". -->

- [ ] [Question?] (raised YYYY-MM-DD)
- [ ] [Question?] (raised YYYY-MM-DD)

---

## 8. Readiness Checkpoint

| Check | Status |
|-------|--------|
| All open questions resolved or deferred | [ ] |
| Scope boundary reviewed by stakeholders | [ ] |
| Phase 1 objective is actionable | [ ] |
| Key decisions recorded with rationale | [ ] |

**Readiness confirmed:** [Not yet / YYYY-MM-DD]
**Next step:** [Pending / `/write-spec-docs` / `/write-architecture-docs`]

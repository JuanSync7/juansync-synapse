# {SUBSYSTEM} — Architecture

| Field | Value |
|-------|-------|
| Status | Draft / Ready |
| Subsystem | {name} |
| Last updated | {YYYY-MM-DD} |
| Scope doc | {path or "N/A"} |

---

## 1. System Overview

{High-level description: what this system does, who uses it, why it exists. 2-4 sentences.}

```
{ASCII component diagram showing major components and their relationships.
Use box-drawing characters. Show directional data flow with arrows.}
```

---

## 2. Component Boundaries

| Component | Responsibility | Owns | Communicates With |
|-----------|---------------|------|-------------------|
| {name} | {single-sentence responsibility} | {data/resources owned} | {other components} |

---

## 3. Technology Decisions

| Area | Choice | Rationale | Alternatives Considered | Decided |
|------|--------|-----------|------------------------|---------|
| {area} | {technology} | {why this over alternatives} | {what else was evaluated} | {YYYY-MM-DD} |

---

## 4. Data Flow Patterns

### {Pattern Name} (e.g., "Request Processing", "Background Jobs")

```
{ASCII diagram showing the data flow for this pattern}
```

**Key decisions:**
- {Decision and rationale}

---

## 5. Integration Points

| External System | Protocol | Direction | Contract |
|----------------|----------|-----------|----------|
| {system} | {REST/gRPC/WebSocket/etc.} | {Inbound/Outbound/Bidirectional} | {link or description} |

---

## 6. Constraints

- **Infrastructure:** {hosting, cloud provider, region requirements}
- **Scale:** {expected load, concurrency, data volume}
- **Compliance:** {regulatory, security, data residency}

---

## 7. Open Questions

<!-- Active during planning. Removed when Status = Ready. -->

- [ ] {Question}? (raised {YYYY-MM-DD})

---

## 8. Readiness Checkpoint

- **Components defined:** {Yes/No — all major components listed in Section 2}
- **Technology decisions made:** {Yes/No — no TBD entries in Section 3}
- **Data flows documented:** {Yes/No — at least one pattern in Section 4}
- **Open questions:** {count remaining / all resolved}
- **Status:** {Draft / Ready}

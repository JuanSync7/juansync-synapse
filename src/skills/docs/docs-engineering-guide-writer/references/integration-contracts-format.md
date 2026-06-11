# Integration Contracts Section Format (Section 6)

**Section 6 documents the system boundary — how external callers interact with this system.** It is NOT about internal module-to-module contracts (those are covered in each module's Purpose and Error behavior sub-sections in Section 3).

Section 6 must cover:
- **Entry point signature** — the public function or API endpoint callers use
- **Input contract** — required/optional fields, types, constraints, validation rules
- **Output contract** — response shape, which fields are always present vs conditional
- **External dependency contracts** — what the system assumes about services it depends on (databases, LLMs, embedding models, etc.)

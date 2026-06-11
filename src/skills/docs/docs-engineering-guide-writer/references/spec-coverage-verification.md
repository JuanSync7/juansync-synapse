# Spec Requirement Coverage Verification

If a companion spec (Layer 3) exists, verify coverage after writing:

1. List every functional requirement ID from the spec (e.g., REQ-101, FR-201).
2. For each requirement, confirm at least one Module Reference section addresses it.
3. If any requirement is not covered by the guide, either:
   - The module that implements it was missed — add the module section.
   - The requirement was descoped or not implemented — note it in Known Limitations (Section 9).

Include a **Requirement Coverage Summary** at the end of the document:

```markdown
## Appendix: Requirement Coverage

| Spec Requirement | Covered By (Module Section) |
|------------------|-----------------------------|
| REQ-101 | `src/path/module.py` — Module Name |
| REQ-102 | `src/path/other.py` — Other Module |
| REQ-103 | Not implemented — see Known Limitations |
```

If no companion spec exists, omit this appendix and note in the document header: "No formal spec companion — guide is based on implemented behavior."

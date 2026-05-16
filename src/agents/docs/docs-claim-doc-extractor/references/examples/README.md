# Test fixtures — docs-claim-doc-extractor

Smoke-test inputs for the extractor. Each fixture has an expected outcome documented either inline (T2–T4) or in a sibling `.expected.md` file (T1). All claim IDs in expected outputs are deterministically derived: `id = sha256(heading_anchor + claim_text)[:8]` (lowercase hex).

| Fixture | Purpose | Expected `claims` count | Expected `contradictions` | Expected `redundancies` |
|---------|---------|-------------------------|---------------------------|--------------------------|
| [small-claim-doc.md](small-claim-doc.md) | T1 — three headings, six atomic claims, no compound sentences | 6 (see [`small-claim-doc.expected.md`](small-claim-doc.expected.md)) | `[]` | `[]` |
| [compound-sentence.md](compound-sentence.md) | T2 — exercises the atomic-claim splitting rule on `and`, `because`, `but` | 5 (2 from line 1, 1 from line 2, 2 from line 3) | `[]` | `[]` |
| [known-contradiction.md](known-contradiction.md) | T3 — directly contradictory claims under sibling headings | 2 | 1 pair (`f035f4fe` ↔ `492948be`) | `[]` |
| [known-redundancy.md](known-redundancy.md) | T4 — two near-paraphrased claims under one heading | 2 | `[]` | 1 pair (`0adbe21e` ≈ `aaac1f8d`), `similarity ≥ 0.85` |

## How to use

1. Pass the fixture's full content as `file_content` and its repo-relative path as `file_path`.
2. For T1, compare each claim's `(heading_anchor, text, source_lines)` against `small-claim-doc.expected.md`. ID equality is implied — if `(heading_anchor, text)` match exactly, the ID must match because the hash is deterministic.
3. For T2, verify the splitting behavior on each of the three lines against the rule in `EVAL.md` O5.
4. For T3, verify the contradiction list contains the two named claim IDs and a one-line reason.
5. For T4, verify the redundancy list contains the two named claim IDs with `similarity ≥ 0.85`.

## ID determinism check (any fixture)

For any claim emitted by the agent, a reviewer can reproduce the ID with:

```
python3 -c 'import hashlib; print(hashlib.sha256(b"<heading_anchor><claim_text>").hexdigest()[:8])'
```

A mismatch indicates either non-deterministic ID generation (hard FAIL — see EVAL O3) or a normalization difference between the reviewer's anchor/text and the agent's. Both cases require investigation; neither is a soft warning.

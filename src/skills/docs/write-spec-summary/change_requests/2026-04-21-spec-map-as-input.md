# Consider reading _SPEC_MAP.md instead of full spec

write-spec-docs now produces a companion `_SPEC_MAP.md` alongside every spec. This file contains a knowledge graph index: section list, entity index (entity → defined in → referenced by), and REQ index (range → section → tally).

For write-spec-summary, this map may be sufficient to generate the summary without reading the full spec — or at minimum, it can guide which sections to read in detail vs. skim. This could reduce token cost and improve summary accuracy by starting from the structural index rather than parsing the full document.

Source: write-spec-docs brainstorm 2026-04-21

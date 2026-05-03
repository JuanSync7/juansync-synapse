# patch-docs — Evaluation Criteria

## Structural Criteria

(Evaluated by improve-skill's baseline checklist — not duplicated here)

## Output Criteria

- [ ] **EVAL-O01:** Every patched doc traces to the diff
  - **Test:** For each row in the "Patched" summary table, verify that the cited section change corresponds to a specific entity (function, class, config key, endpoint) that appears in the input diff. No patched doc should reference changes not present in the diff.
  - **Fail signal:** A "Patched" row describes a change that cannot be traced to any hunk in the input diff, or the change description is generic ("updated section") without naming the specific entity from the diff.

- [ ] **EVAL-O02:** No affected doc is silently omitted
  - **Test:** Given the input diff and the change-type classification, check whether every doc type that should be affected (per the doc-impact-map rules) appears in the summary — either as "Patched", "Escalated", or "Delegated". Docs correctly determined to be unaffected must appear under "Skipped" with a reason.
  - **Fail signal:** A doc that should have been patched given the change type is absent from all four summary sections, or a doc appears under "Skipped" with no reason provided.

- [ ] **EVAL-O03:** Cosmetic-only diffs produce no doc edits
  - **Test:** When the input diff contains only whitespace changes, comment edits, or formatting adjustments with no behavioral or API impact, verify the output halts with a "no behavioral changes" message and does not modify any documentation file.
  - **Fail signal:** Doc files are modified in response to a cosmetic-only diff, or the skill proceeds through discovery/patching phases instead of exiting at triage.

- [ ] **EVAL-O04:** Patched content matches existing doc conventions
  - **Test:** For each doc that was patched, compare the formatting of newly added content (heading levels, list style, table column order, code snippet format, terminology) against the 3-5 lines immediately surrounding the edit location. The new content must use identical formatting conventions.
  - **Fail signal:** New content uses a different heading level, list style (bullets vs. numbers), table format, backtick convention, or terminology style than the surrounding existing content in the same section.

- [ ] **EVAL-O05:** Edits are surgical — unchanged content is preserved
  - **Test:** Diff the patched doc file against its pre-patch state. Verify that only lines directly related to the code change are modified. Lines outside the targeted section(s) must be byte-identical to the original.
  - **Fail signal:** Lines outside the targeted section are modified, reworded, reformatted, or rewritten. Unchanged content within the targeted section is rephrased or restructured when it did not need to be.

- [ ] **EVAL-O06:** Change-type classification is defensible
  - **Test:** Verify the "Change type" stated in the patch summary (feature/refactor/bugfix/cosmetic/config) is consistent with the diff content. A diff that adds new public functions is a feature, not a refactor. A diff that renames a public method is a refactor, not cosmetic. A diff that fixes a bug in error handling is a bugfix, not a feature.
  - **Fail signal:** The stated change type contradicts the observable diff content (e.g., new API endpoint classified as "refactor", public method rename classified as "cosmetic", whitespace-only change classified as "feature").

- [ ] **EVAL-O07:** Escalation fires when patching is structurally insufficient
  - **Test:** When the input diff introduces changes that would require adding a new top-level (H2) section to an existing doc, verify the skill escalates to the appropriate write-* skill rather than creating a shallow new section. The escalation must appear in the "Escalated" summary section with the target skill named.
  - **Fail signal:** The skill creates a new H2 section in an existing doc instead of escalating, or the escalation row does not name the specific write-* skill to redirect to.

- [ ] **EVAL-O08:** Missing docs trigger delegation, not inline creation
  - **Test:** When discovery finds that a doc type relevant to the diff does not exist (e.g., no engineering guide for the affected module), verify the skill delegates creation to the appropriate write-* skill rather than generating the doc inline. The delegation must appear in the "Delegated" summary section.
  - **Fail signal:** The skill writes a new document from scratch inline instead of delegating to a write-* skill, or a missing doc relevant to the diff is silently ignored (does not appear in any summary section).

- [ ] **EVAL-O09:** Patch summary accounts for all discovered docs
  - **Test:** Count the total number of distinct docs across all four summary sections (Patched + Skipped + Escalated + Delegated). This count must equal or exceed the number of doc types flagged during triage. Every doc discovered during Phase 2 must appear in exactly one summary section.
  - **Fail signal:** A doc discovered during the discovery phase is absent from the summary entirely, or a doc appears in multiple summary sections simultaneously.

- [ ] **EVAL-O10:** Public API renames propagate across all affected docs
  - **Test:** When the diff renames a public function, class, or endpoint, verify that every doc referencing the old name is either patched (old name replaced with new name) or escalated. Search the pre-patch versions of all discovered docs for the old name — every occurrence must be addressed.
  - **Fail signal:** A doc containing the old name of a renamed entity is marked "Skipped" or is absent from the summary, leaving a stale reference in the documentation.

- [ ] **EVAL-O11:** .doc-map.yaml is maintained
  - **Test:** After patching, verify that `.doc-map.yaml` exists and reflects any new doc-code relationships created during this run. If a new doc was created via delegation, it must appear in `.doc-map.yaml` with the correct code path mapping.
  - **Fail signal:** `.doc-map.yaml` does not exist after a run that should have generated it, or a newly created doc is absent from the mapping, or code path mappings are incorrect (doc mapped to wrong source directory).

- [ ] **EVAL-O12:** Headless mode produces no interactive prompts
  - **Test:** When invoked without user arguments in a headless/autonomous context (pipeline stage, CLAUDE.md trigger), verify the skill resolves the diff source automatically (staged or HEAD~1) and completes without prompting the user for input at any point.
  - **Fail signal:** The skill asks the user to choose a diff source, confirm a classification, or approve a patch plan during headless execution.

## Test Prompts

### Naive User: Vague update request

**Prompt:** "i just finished some refactoring, can you update the docs"

**Why this tests the skill:** Tests whether the skill can identify the diff source on its own (no path or ref provided) and determine which docs are affected from a vague request with no specifics about what changed.

### Naive User: Single file mention

**Prompt:** "i changed the config file, make sure the docs match"

**Why this tests the skill:** Tests whether the skill can work with a minimal hint (one file mentioned) and discover all affected documentation — not just the obvious one — when the user doesn't enumerate them.

### Naive User: Post-commit with no context

**Prompt:** "patch docs"

**Why this tests the skill:** Tests the zero-argument invocation path — the skill must figure out what changed, what docs exist, and what needs updating with absolutely no user guidance.

### Experienced User: Multi-file diff with public API rename

**Prompt:** "I just renamed `process_payment` to `execute_transaction` across the payments module and updated the error types. The diff is staged. Patch the eng guide, README, and any specs that reference the old name — but don't touch the test docs, I'll handle those separately."

**Why this tests the skill:** Tests handling of a cross-cutting rename (needs to find all doc references to the old name), respecting explicit user scope constraints (skip test-docs), and working with staged changes as the diff source.

### Experienced User: Bugfix with spec implications

**Prompt:** "Just pushed a fix for the race condition in the connection pool — added a mutex around the checkout path and a new timeout config `pool_checkout_timeout_ms`. This fixes issue #247 which means the spec's acceptance criterion about concurrent connections was actually wrong. Sync everything."

**Why this tests the skill:** Tests whether the skill recognizes that a bugfix can have spec-level implications (missing/wrong requirement), handles a new config parameter (needs .env.example update), and manages the "sync everything" scope without over-engineering.

### Experienced User: Incremental test coverage update

**Prompt:** "I added three new test cases for the auth token refresh flow in tests/test_auth_refresh.py. Update test-coverage.md to reflect the new coverage — the acceptance criteria AC-7 and AC-9 should now show as covered."

**Why this tests the skill:** Tests targeted incremental updates to a specific doc type (test-coverage register) with precise row-level changes, not a full document rewrite.

### Adversarial: Massive diff that should escalate

**Prompt:** "I just added an entirely new payments subsystem — 15 new files across src/payments/, new database models, new API endpoints, new config section. Update all the docs to cover this."

**Why this tests the skill:** Tests whether the skill recognizes that a new subsystem is beyond incremental patching and escalates to the appropriate write-* skills instead of producing shallow, incomplete section additions.

### Adversarial: Cosmetic-only diff

**Prompt:** "I reformatted all the Python files with black and fixed some trailing whitespace. Patch the docs."

**Why this tests the skill:** Tests whether the skill correctly identifies a cosmetic-only diff (no behavioral change) and exits cleanly rather than making unnecessary doc updates.

### Wrong Tool: Wants full doc creation

**Prompt:** "We just started a new microservice and have no documentation yet. Can you patch-docs to create an engineering guide and spec for it?"

**Why this tests the skill:** Tests whether the skill recognizes that creating documentation from scratch is not patching — this needs `/doc-authoring` or the specific write-* skills, not patch-docs.

### Wrong Tool: Wants doc quality review

**Prompt:** "The engineering guide feels outdated and inconsistent — can you go through the whole thing and clean it up? Fix the formatting, update stale references, and improve the writing."

**Why this tests the skill:** Tests whether the skill recognizes that a full document quality pass (not driven by a code diff) is outside its scope — it patches based on diffs, it doesn't audit or improve docs holistically.

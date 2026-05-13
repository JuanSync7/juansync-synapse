<!-- Template for memo-producer subagent. Sections are optional — include only what applies to the artifact. -->

# Decision Memo — <artifact-name>

> Artifact type: <skill|tool|agent|protocol> | Memo type: <creation|change_request> | Design doc: `<path-to-design-doc>`

---

## What I want

<!-- User's description in their own words — what they want the artifact to do.
     For creation: the full artifact purpose and scope.
     For change_request: numbered list of specific changes to an existing artifact. -->

---

## Why Claude needs it

<!-- Concrete failure mode. What does Claude currently produce without this artifact?
     What specifically is wrong with that output?
     Not vague improvement claims — specific examples of baseline failure.
     Source: notepad Resolved sections + Process reasoning. -->

---

## Injection shape

<!-- What type of context injection is this artifact? One or more of:
     - Workflow: phase descriptions, flow graphs, node specs
     - Policy: judgment rules, coaching behavior, decision heuristics
     - Domain knowledge: expertise loaded on-demand (criteria, conventions, patterns) -->

- **Workflow:** <if applicable — phase descriptions>
- **Policy:** <if applicable — judgment/coaching behavior>
- **Domain knowledge:** <if applicable — what domain expertise is loaded>

---

## What it produces

<!-- Output table — every artifact the skill/tool/agent/protocol creates or modifies. -->

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| <artifact> | <count> | <yes/no> | <purpose> |

---

## Flow graph

<!-- Include only for workflow/multi-phase artifacts.
     Copy VERBATIM from the notepad Memo-ready section.
     ASCII art preferred — no Mermaid.
     VERBATIM blocks have been pressure-tested during brainstorming — creators should use them as a strong starting point, not re-derive from scratch. -->

---

## Node specifications

<!-- Include only for flow-graph skills — one paragraph per node.
     Format: [NODE] — Load: <files>. Do: <actions>. Don't: <constraints>. Exit: <transitions>.
     Source: notepad Resolved sections for the artifact. -->

---

## Entry gates

<!-- Include only for flow-graph skills — transition conditions table. -->

| Transition | Gate |
|---|---|
| <from → to> | <conditions> |

---

## Notepad architecture

<!-- Include only if the artifact uses a notepad or structured working memory.
     Describe zones, sections, evolution pattern, and verbatim conventions. -->

---

## Naming conventions

<!-- Include only if naming decisions were made during the brainstorm.
     Pattern, segment breakdown, taxonomy source, examples. -->

---

## Edge cases considered

<!-- Key edge cases and failure modes discussed during lens rotation.
     Source: notepad Resolved sections + Process lens observations. -->

| Edge case | Handling |
|---|---|
| <edge case> | <how it's handled> |

---

## Companion files anticipated

<!-- Categorized inventory with load points.
     Group by: always-loaded, templates, references, agents.
     Each entry: filename, loaded-at node, purpose. -->

---

## Dependencies

<!-- What this artifact consumes from and produces for other artifacts. -->

| Artifact | Direction | Contract |
|---|---|---|
| <artifact> | <consumes/produces for> | <contract description> |

---

## Open questions

<!-- Remaining uncertainties for the creator to focus on.
     "None" if all threads were resolved during the brainstorm.
     Each item here tells the creator "don't re-check everything — focus here." -->

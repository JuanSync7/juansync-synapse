# Change Request — delivery-orchestration-dispatch-contract

> Artifact type: protocol | Target: `src/protocols/delivery/delivery-orchestration-dispatch-contract.md`

Source brainstorm: `.brainstorms/2026-05-31-vertical-slice-planning-stack/` (Artifact 2 — `delivery-execution-coding-contract`, "Dispatch-contract dependency (paired CR)" subsection; Cross-cutting line: "Dispatch-contract needs paired CR: {{worker_protocols}} slot description amended 3→4 bodies; EVAL test updated").

---

## What changes

1. **`{{worker_protocols}}` slot — enumerate four bodies (3 → 4).**

   The current Slot table row (Contract Rule 4) reads:

   > `{{worker_protocols}}` | Bodies of `delivery-execution-slice-contract`, `delivery-execution-tdd-contract`, `delivery-orchestration-closeout-schema` | Missing → subagent doesn't know it owes a closeout, test-first discipline, or iteration cap

   Amend the Content cell to enumerate FOUR bodies, adding the new protocol:

   > Bodies of `delivery-execution-slice-contract`, `delivery-execution-tdd-contract`, `delivery-execution-coding-contract`, `delivery-orchestration-closeout-schema`

   Extend the "Why non-negotiable" cell to cover the new body:

   > Missing → subagent doesn't know it owes a closeout, test-first discipline, an iteration cap, **or the code-quality discipline (YAGNI, neighbors-first, no-dead-code, fail-loudly, green-tree-exit, security-tripwires)**

2. **Update the "`{{worker_protocols}}` — three bodies, not by reference" rationale heading + body.**

   The current Slot Design Rationale subsection is titled and worded for three bodies. Rename to **"`{{worker_protocols}}` — four bodies, not by reference"** and update the body to enumerate four bodies. The "fresh context / inline-not-by-reference" argument remains unchanged in substance.

3. **Pre-flight check — add halt-loud on missing `delivery-execution-coding-contract`.**

   Extend Contract Rule 5 (Pre-dispatch checks). The existing Slot completeness check (#4) verifies all 8 slots are populated. Add an explicit halt-loud sub-clause to that check (mirroring the tdd-contract pattern already implicit in the four-body enumeration):

   > **4. Slot completeness** — all 8 prompt slots are populated. On any missing slot: abort (do not launch a partial brief). **In particular, `{{worker_protocols}}` MUST contain all four protocol bodies; absence of `delivery-execution-coding-contract` in the rendered injection is a halt-loud condition, not a soft warn.**

4. **Pre-flight check — add injection-collision check.**

   Add a fifth pre-dispatch check that fires when more than one coding-discipline variant is present in the rendered `{{worker_protocols}}` slot:

   > **5. Coding-discipline collision check** — exactly one coding-discipline protocol body is present in `{{worker_protocols}}`. If multiple variants are detected (e.g., a vestigial discipline body alongside `delivery-execution-coding-contract`, or two competing coding-contract drafts), halt-loud and escalate to user. Silent acceptance of a collision would let conflicting code-quality rules reach the subagent.

5. **Violation Signatures table — add two rows.**

   Add violation IDs (f) and (g) to the Violation Signatures table:

   | ID | Violation | Response |
   |---|---|---|
   | (f) | `{{worker_protocols}}` rendered without `delivery-execution-coding-contract` body | Halt-loud — never dispatch without code-quality discipline |
   | (g) | Multiple coding-discipline variants present in `{{worker_protocols}}` | Halt-loud + escalate to user |

6. **Version bump.**

   Frontmatter `version: 1` → `version: 2`. Status stays `draft`.

---

## Why

The new protocol `delivery-execution-coding-contract` (created in the same brainstorm) defines subagent code-quality discipline (YAGNI, neighbors-first, no-dead-code, fail-loudly, green-tree-exit, security-tripwires) that complements `delivery-execution-tdd-contract`. It MUST be injected into every dispatch alongside the existing three worker protocols, otherwise:

- The subagent runs without a code-quality envelope. Speculative abstractions, dead code, swallowed exceptions, fabricated lint passes, and secret leaks all become undetectable at closeout time because the contract that defines those violation signatures was never in the brief.
- The closeout-schema's new fields (`lint_result`, `dead_code_violations[]`, `neighbors_consulted[]`, etc. — added by the paired closeout-schema CR) have no producer-side contract telling the subagent to populate them.

Earlier brainstorm prose claimed "no new wiring" was needed in the dispatch-contract. The [B] lens-rotation pass invalidated that claim: the slot description IS load-bearing wiring (it is the canonical enumeration the orchestrator's EVAL.md asserts against), and the four-body inventory is what guarantees the subagent receives the protocol in its prompt context.

The pre-flight halt-loud and collision check exist because silent fallback is the dominant failure mode for injection wiring — an absent or duplicated protocol body produces a dispatch that looks well-formed but behaves as if the contract didn't exist.

---

## Impact on existing consumers

- **`delivery-orchestration-plan-executor` SKILL.md** — the [DISPATCH] node prose that names the loaded worker protocols must update from three to four. The slot-population step in the orchestrator's runbook now renders four bodies into `{{worker_protocols}}`.
- **`delivery-orchestration-plan-executor` EVAL.md** — the slot assertion (per lens-rotation findings: test lines around L69 and L119) currently asserts THREE bodies are present in the rendered prompt. Update both assertion sites to assert FOUR bodies, including `delivery-execution-coding-contract` by slug.
- **Subagent prompt rendering** — automatic. The orchestrator's templating step picks up the additional protocol body via the slot. No subagent-side change required; the subagent simply receives one more inlined contract.
- **`delivery-execution-coding-contract` (new protocol, same PR set)** — depends on this CR to land for its injection pathway to exist. Paired-CR coordination: this amendment and the new protocol must merge together (or this lands first; the new protocol does not function in isolation).
- **`delivery-orchestration-closeout-schema` (paired CR)** — independent change set, but the new closeout fields it adds are populated by the subagent only when the coding-contract is injected. The two paired CRs are mutually reinforcing: closeout-schema adds the fields, dispatch-contract guarantees the producer contract reaches the subagent.

---

## Migration path

**Forward-only — no backward-compatibility shim.**

- Older orchestrator runs that have not been updated to inject `delivery-execution-coding-contract` will hit pre-dispatch check #4 (slot completeness, halt-loud variant) and refuse to dispatch. This is intentional: a silently mis-configured dispatch is worse than a loud refusal, because the subagent would run without code-quality discipline and the missing closeout fields would be indistinguishable from "this run pre-dates the protocol."
- Consumers updating in this order avoid breakage:
  1. Land `delivery-execution-coding-contract` (new protocol).
  2. Land this dispatch-contract amendment (version 2) — wiring becomes mandatory.
  3. Land `delivery-orchestration-plan-executor` SKILL.md + EVAL.md updates (four-body assertion).
  4. Land `delivery-orchestration-closeout-schema` amendment (new fields) — closeout side picks up what the dispatch side now injects.
- No data migration: the change is purely in the orchestrator's prompt-assembly step and the contract enumeration. No persisted artifact (closeout, lessons.md, slice file) carries dispatch-contract state.

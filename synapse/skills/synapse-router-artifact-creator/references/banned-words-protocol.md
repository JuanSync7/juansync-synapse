# Banned Words

Words and phrases that MUST NOT appear in a protocol's Contract or Failure Assertion sections. These give the LLM an escape hatch to skip the instruction.

## Banned List

| Banned | Why | Replace with |
|--------|-----|--------------|
| consider | Hedges — agent can "consider" and decide not to | MUST, BEFORE X do Y |
| may want to | Optional framing — agent can want not to | MUST |
| appropriate | Subjective — agent decides what's "appropriate" | Name the specific condition |
| ideally | Aspirational — agent can fall short of ideals | MUST |
| when possible | Escape hatch — agent can claim "not possible" | BEFORE X, AFTER Y |
| should consider | Double hedge | MUST |
| it's recommended | Passive suggestion | MUST, DO NOT |
| generally | Implies exceptions exist | Always state the exception explicitly if one exists |
| optionally | Marks as skippable | Remove the instruction or make it mandatory |
| could | Permissive — agent is "allowed" but not required | MUST |
| might | Speculative — agent decides probability | State the condition directly |
| perhaps | Uncertain — agent decides | MUST or remove |
| arguably | Debatable — agent can argue otherwise | State the fact directly |

## Banned Phrases

| Phrase | Replace with |
|--------|--------------|
| "when appropriate" | Name the exact trigger moment |
| "as needed" | Name the exact condition that creates the need |
| "if desired" | Remove — protocols are mandatory when injected |
| "best practice" | State the specific rule |
| "try to" | MUST |
| "aim to" | MUST |
| "prefer X over Y" | MUST use X. DO NOT use Y. |

## How to Use

During Phase 3 (Signal-Strength Review), synapse-protocol-signal-reviewer checks every sentence in the Contract and Failure Assertion sections against this list. Any match is a FAIL that must be rewritten before the protocol ships.

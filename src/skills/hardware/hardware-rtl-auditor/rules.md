# RTL Design Guard — Hard Rules

The non-negotiables. Each links to the reference with the full rationale. If RTL
or a testbench violates one of these, fix it before moving on.

## Synthesis & lint (→ references/synthesizable_verilog.md)
1. **Width-match every assignment.** Mask/bit-select any RHS wider than the LHS;
   never rely on implicit truncation (Verilator WIDTHTRUNC/WIDTHEXPAND).
2. **Extend before you operate.** Zero/sign-extend narrow operands to the full
   result width before signed arithmetic; declare `N+1` bits for `N`-bit adds.
3. **One driver per net.** One `always` OR one `assign` — never both, never split.
4. **Verilog-2005 only**, explicit widths, no latches, sync active-low reset,
   no `/` `%` float or tristate, every `reg` resets explicitly.
5. **No valid self-cancellation.** Handshake on the *registered* valid; a 1-cycle
   `ready` pulse retires exactly one token.
6. **Complete every `case`/`if`** with a default to avoid inferred latches.

## Arithmetic correctness (→ references/arithmetic_precision.md)
7. **Derive widths by range analysis, round UP.** Never pick by eye.
8. **Declare one number format per node** (integer / Qm.n / float) and the
   conversion on every mixed edge.
9. **State a saturation policy** per arithmetic register: saturating / wraparound
   / range-guaranteed. Never assume "inputs are small."
10. **Match the golden bit-for-bit** — every cast/shift/clip/rounding mode — then
    optimize. Test sign extremes and near-saturation values.

## Interfaces (→ references/interface_protocols.md)
11. **Freeze payload packing** (total width, ordered [MSB:LSB] field slices,
    signedness, encoding) in a contract both endpoints reference.
12. **Derive ready from internal state only** — never combinationally from valid.
13. **Declare a bootstrap policy** for any closed feedback loop, or it deadlocks
    on the first transaction.

## Verification (→ references/dv_and_failure_patterns.md)
14. **Drive ready before sending**, sample on the correct phase (registered →
    after FallingEdge), never `Timer(0)`, one clock driver, watchdog every wait.
15. **Diagnose testbench-bug vs RTL-bug** from the failure signature before
    touching RTL — read the waveform's first divergence first.
16. **Capture each fixed testbench anti-pattern** into a project `DV_RULES.md`
    so later generations don't repeat it.

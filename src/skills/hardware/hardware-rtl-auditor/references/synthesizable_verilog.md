# Synthesizable Verilog Design Rules

Tool-agnostic rules for writing synthesizable, lint-clean Verilog that passes
Verilator (`-Wall`) and Yosys. Load this when authoring or fixing RTL.

## 1. Verilator Width Safety (WIDTHTRUNC / WIDTHEXPAND)

Verilator with `-Wall` treats width mismatches as errors. Every assignment must
match bit widths exactly on LHS and RHS.

### Integer division / modulo
Division and modulo in `initial` blocks default to 32-bit results. Truncate explicitly:
```verilog
// WRONG: 32-bit RHS truncates implicitly to 4-bit LHS
lut[i] = i / 6;
// CORRECT: size both operands, then mask to target width
lut[i] = (i / 6) & 4'hF;
lut[i] = i[5:0] / 4'd6;     // or sized operands
```

### Shifts
Shift results are wider than the left operand. Bit-select to truncate:
```verilog
// WRONG
assign y = x >> shift_amt;
// CORRECT
assign y = (x >> shift_amt)[15:0];
```

### General rule
Apply an explicit mask `& MASK` or bit-select `[N:0]` to every arithmetic RHS
wider than the LHS. Never rely on implicit truncation.

## 2. Signed Arithmetic Width Matching

When mixing signed/unsigned, extend operands to the full result width **before**
the operation. `$signed()` with partial extension produces insufficient width.
```verilog
// WRONG: $signed({1'b0, unsigned_8b}) is only 9 bits, not 16
assign sum = signed_16b + $signed({1'b0, unsigned_8b});
// CORRECT: extend narrow operand to full width first
wire signed [16:0] pred_ext = {9'b0, unsigned_8b};
assign sum = signed_16b + pred_ext;
```
For `N`-bit + `M`-bit addition, declare the result `max(N,M)+1` bits to capture
the carry. Always explicitly zero/sign-extend narrow operands; never assume
automatic extension.

## 3. Single-Driver Rule & Data-Flow Discipline

Every `reg`/`wire` is driven from **exactly one** source — one `always` block OR
one `assign`. Never split updates to a signal across multiple `always` blocks;
never mix combinational `assign` with sequential `always` for the same signal.
Violations create multi-driven nets and unpredictable behavior.

## 4. Synthesizability Constraints (Verilog-2005 subset)

- **Verilog-2005 only.** No SystemVerilog (`logic`, `var`, etc.).
- **No implicit widths.** Explicit `[N:0]` on every signal.
- **No latches.** Every conditional assignment has an else / default.
- **Synchronous active-low reset** (`rst_n`); no async reset.
- **No floating-point** — fixed-point only.
- **No tristates** — most standard-cell PDKs (e.g. Sky130) have none; use mux-based selection.
- **No `/` or `%`** — use shift- or LUT-based implementations.
- Verify every instantiated cell exists in the target library.

### Latch prevention
```verilog
// WRONG: incomplete case infers a latch
always @(*) case (sel) 2'b00: y=a; 2'b01: y=b; endcase
// CORRECT: default branch (or a leading default assignment `y = 0;`)
always @(*) case (sel) 2'b00: y=a; 2'b01: y=b; default: y=1'b0; endcase
```

## 5. Reset, FSM & Clocking Discipline

- One `clk`; synchronous active-low `rst_n`; every `reg` has an explicit reset value.
- FSM states as `localparam`; register `state <= state_next`.
- Combinational logic in `always @(*)` only; sequential in `always @(posedge clk)`
  only. Compute `_next` combinationally, transfer on the clock edge.

### Valid self-cancellation bug (ready/valid output FSM)
```verilog
// WRONG: valid set and cleared in the same combinational cycle -> never asserts -> deadlock
ST_OUT: begin m_tvalid_next = 1'b1; if (m_tready) m_tvalid_next = 1'b0; end
// CORRECT: handshake on the REGISTERED valid
ST_OUT: begin
  m_tvalid_next = 1'b1;
  if (m_tvalid_reg && m_tready) begin m_tvalid_next = 1'b0; state_next = ST_IDLE; end
end
```
A registered output held valid must retire exactly one token per single-cycle
`ready` pulse and advance state once. Do not require `ready` to stay high
multiple cycles or use a previous cycle's `ready`.

## 6. Common Yosys Synthesis-Failure Fixes

- **Unmapped cells** → rebuild the function from primitives present in the target `.lib`.
- **Multi-driven nets** → mux-based priority selection, single driver.
- **Inferred latches** → complete every `case`/`if` with a default.
- **Memory inference** → single clock, no async ports, simple index arithmetic,
  one `always @(posedge clk)` write path.
- **Combinational loops** → break with a register on at least one path.

## 7. SDC / Timing-Constraint Basics

```sdc
create_clock -name clk -period <period_ns> [get_ports <clk_port>]
set_input_delay  -clock clk <0.2*period> [all_inputs]
set_output_delay -clock clk <0.2*period> [all_outputs]
```
Read the module port list to get the exact clock-port name — do not guess.
Default I/O budget ≈ 20% of the clock period. For purely combinational modules,
create a virtual clock (`create_clock -name vclk -period <p>`) and constrain I/O
against it.

## Appendix — Verilog style for waveform auditability

Keep protocol state in **explicit named wires** (`valid`, `ready`, FSM state,
error flags, counters) rather than buried in packed structs. Register pipeline
sideband metadata with stable `_q`-suffixed names so a VCD audit can correlate
data and metadata across cycles. Document non-obvious bit layouts in comments.

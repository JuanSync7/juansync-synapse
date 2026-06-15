# Design-Verification & Failure-Pattern Reference

Tool-agnostic DV knowledge for cocotb/Verilator testbenches: golden-model
methodology, robust handshake-aware stimulus, and a catalogue of failure
signatures with the correct fix and a testbench-bug-vs-RTL-bug decision rule.

## 1. Golden-Model Methodology

A golden model is a reference implementation (typically Python) run in parallel
with RTL sim: same inputs to both, compare outputs bit-exactly, find which side
diverged first.

- **RTL is correct** if the golden passes across random, known, and corner-case
  vectors and the RTL matches — accounting for pipeline latency (a value written
  on cycle N is readable on cycle N + pipeline_depth).
- **Golden is wrong (testbench bug)** if random/stress vectors pass but specific
  hardcoded expected values fail, or the model reads back a written value on the
  same cycle RTL cannot.
- **Non-blocking-assignment (NBA) semantics**: simulators resolve `<=` *after* the
  RisingEdge callback returns. Reading a registered output right after
  `RisingEdge(clk)` yields the OLD value. Read after settle:
  ```python
  await RisingEdge(dut.clk)
  await FallingEdge(dut.clk)   # let NBA settle
  actual = int(dut.out.value)
  ```

## 2. Robust cocotb Testbenches

### Handshake-aware stimulus (ready/valid)
Deadlock happens when the DUT gates input-ready on output-ready
(`assign s_tready = !m_tvalid || m_tready`) and the receiver never asserts
`m_tready`. **Always drive `m_tready=1` before sending input**, or run sender and
receiver concurrently with `cocotb.start_soon()`.

### Phase-safe send
Drive `tvalid/tdata/tlast` before the rising edge that may accept the beat,
sample `tready` for that *same* rising edge, deassert after if it was high.
Count exactly one accepted transfer per intended beat.
```python
async def send_axis(dut, data, last=0, max_wait=1000):
    await FallingEdge(dut.clk)
    dut.s_axis_tdata.value = int(data); dut.s_axis_tlast.value = int(last)
    dut.s_axis_tvalid.value = 1
    for _ in range(max_wait):
        ready = int(dut.s_axis_tready.value)
        await RisingEdge(dut.clk)
        if ready:
            dut.s_axis_tvalid.value = 0
            await FallingEdge(dut.clk); return
        await FallingEdge(dut.clk)
    raise TimeoutError("s_axis_tready never asserted")
```

### Output sampling protocol
- Registered output (`<=`): sample after `RisingEdge` + `FallingEdge`.
- Combinational output (`=`): sample after `RisingEdge` + `Timer(1,"ns")`.
- FSM-driven: poll with a timeout, never fixed-cycle waits.
- **Never `Timer(0)`** — delta-cycle glitches in Verilator.
- After a handshake, wait ≥2 cycles before checking downstream; after reset,
  wait `pipeline_depth + 2`.

### Gotchas
- **Cast to plain `int`** before assigning to DUT signals — numpy types raise.
- **One live clock driver per clock** — multiple `start_soon(Clock(...))` create
  ps-skewed duplicate edges and race-dependent failures.
- **Wide signals (>~2048 bits)**: `int(dut.wide_bus.value)` can be truncated by
  the VPI string buffer → false mismatches. Compare field-sized debug aliases.
- Add a cycle-count **watchdog** to every `while`-waiting-for-a-signal loop.

## 3. Failure-Pattern Catalogue

| Pattern | Tell-tale | Root cause | Fix |
|---|---|---|---|
| **Width cascade** | WIDTHTRUNC/WIDTHEXPAND on 2+ lines | systemic, not per-line | mask/size ALL arithmetic to target width; emit a broad constraint |
| **Invalid TB format** | `SyntaxError`/markdown headers in test file | generator emitted prose | regenerate "valid Python starting with imports only" |
| **Recurring category** | same category ≥2× in attempt history | inner-loop fix too narrow / spec is the cause | broaden the constraint; suspect the uArch spec |
| **Stress-pass, targeted-fail** | random passes, known-vector fails | golden's hardcoded values wrong | testbench bug → fix golden vectors |
| **Timing off-by-one** | `actual[N]==expected[N-1]` all N; `units=` vs `unit=` warning | sample phase / cocotb API drift | testbench bug → fix sampling / `unit="ns"` |
| **Value divergence** | actual is a bit-manip of expected (sign/trunc/endian) | golden width/signedness/byte-order wrong | testbench bug → fix golden computation |
| **False-positive ports** | prose words ("sequence","order") reported as ports | parser read prose, not the port table | NOT a mismatch; trust the formal port table / interface stub |

## 4. Testbench-Bug vs RTL-Bug Decision

**It's a testbench bug when:** random passes but targeted fails; uniform
one-cycle shift; expected/actual differ only by sign/truncation/endianness;
deprecated-API warning; prose words flagged as ports.

**It's an RTL bug when:** first divergence is in the datapath (specific bit
mismatch, not just timing); same category recurs ≥2×; waveform shows a
logic-level anomaly (glitch, wrong FSM state); known + random both fail at the
same phase.

**Always read the VCD/waveform audit first** — it shows which signal diverged
first. Inside RTL → RTL bug. On a comparison/control signal → dig into the golden.

## 5. Self-Improving DV-Rules Loop (worth copying)

Keep a `DV_RULES.md` anti-pattern catalogue in the project:
1. The TB generator reads it and applies every rule before generating.
2. When a testbench bug is diagnosed, append a new rule (wrong-vs-correct code).
3. Next generation automatically avoids that mistake.

```markdown
## Rule: <short title>
<what went wrong, why, and the correct pattern — with a wrong/correct code pair>
```
The feedback loop closes: bug discovered → rule captured → future runs avoid it.
Durable, tool-agnostic, and compounding across designs.

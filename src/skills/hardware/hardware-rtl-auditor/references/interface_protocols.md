# Block Interface Protocols: AXI-Stream & sRdy/dRdy

Reference for designing point-to-point block interfaces. Covers the two
handshakes you'll use most, the payload-packing discipline that prevents
inter-block contract drift, and the closed-loop bootstrap rule that prevents
first-transaction deadlock.

## AXI-Stream (AMBA AXI4-Stream)

Unidirectional, point-to-point, multi-beat. One master (producer) → one slave
(consumer). Per-beat backpressure via ready/valid.

### Required signals
| Signal | Direction | Purpose |
|---|---|---|
| `<p>_tvalid` | master → slave | master presents data |
| `<p>_tready` | slave → master | slave can accept this beat |
| `<p>_tdata[N-1:0]` | master → slave | payload (N is a design choice) |

A beat transfers iff `tvalid && tready` on the same rising edge. **Critical rule:**
once `tvalid` asserts, hold `tvalid` and `tdata` stable until `tready` is also
high. The master must NOT wait for `tready` before asserting `tvalid`.

### Optional sidebands (use only if needed — redundant sidebands are noise)
`tlast` (last beat of packet) · `tuser[U-1:0]` (per-beat metadata: SOF, parity,
source-id) · `tkeep[N/8-1:0]` (valid bytes) · `tstrb` (position vs null bytes,
rarely used) · `tdest[D-1:0]` (route id for switches) · `tid[I-1:0]` (source id
for aggregation).

## sRdy/dRdy (source-ready / destination-ready)

The same per-cycle handshake stripped of sidebands. `srdy` = source has data;
`drdy` = dest can accept; transfer iff `srdy && drdy` on the same edge.
Functionally equivalent to `tvalid`/`tready` but minimal.

| Signal | Direction | Purpose |
|---|---|---|
| `<p>_srdy` | source → dest | source has data this cycle |
| `<p>_drdy` | dest → source | dest can accept this cycle |
| `<p>_data[N-1:0]` | source → dest | payload |

No `last`/`user`/`keep`/`dest`/`id`. If you need any of those, switch to
AXI-Stream — don't graft sidebands on ad hoc.

### Choosing between them
**Pick sRdy/dRdy** when ALL hold: single field or atomic small record (no packet
boundaries); no per-beat sidebands; tight 1-cycle local handshake inside a
subsystem; you want the smallest interface.
**Pick AXI-Stream** when ANY hold: packet boundaries (`tlast`) or per-beat
metadata (`tuser`); multiple producers with source-ids (`tid`); one producer to
many consumers via a switch (`tdest`); interop with off-the-shelf AXI-Stream IP
(FIFOs, width converters, DMAs); a chip/subsystem boundary.
For address-mapped register access use **AXI4-Lite**, not AXI-Stream.

## Payload packing is a design choice, NOT a standard

This is the #1 source of inter-block contract drift. Neither protocol specifies
how multi-field payloads pack inside the data bus. For any payload with >1 field,
declare and **freeze in the interface contract**, referenced by BOTH endpoints:
1. **Total width** in bits.
2. **Ordered field list**, each with its exact `[MSB:LSB]` slice.
3. **Signedness** per field (unsigned, two's-complement…).
4. **Encoding** per field (binary, gray, one-hot, fixed-point Qm.n, ASCII…).

Neither MSB-first nor LSB-first is universally correct — what matters is that
producer and consumer agree. **Default convention** when there's no reason to
deviate: MSB-first by field-list order, no padding (unless a named `reserved`
field), two's-complement for signed, unsigned for indices/counters/addresses.

```
36-bit example: pixel[8], x[10], y[9], frame_idx[4], qp[2], sof[1], eol[1], frame_last[1]
[35:28] pixel  [27:18] x  [17:9] y  [8:5] frame_idx  [4:3] qp  [2] sof  [1] eol  [0] frame_last
```
Deviating (e.g. LSB-first for wire-compatibility with external IP) is fine — but
declare it explicitly in a `packing_convention` field and reference it from both
endpoints.

## Backpressure correctness (passes lint, fails sim)
1. **`tvalid`/`srdy` deasserts mid-burst before ready fires.** Hold valid+data
   stable until ready.
2. **`tready`/`drdy` depends combinationally on valid.** Creates a `valid && ready`
   cycle that confounds skid buffers. Derive ready from internal state ONLY.
3. **Producer asserts valid before reset deasserts.** Downstream may latch a
   phantom beat. Gate valid on reset-done.

## Closed-loop bootstrap (deadlock prevention)
If block A's input waits on block B's output and B's input waits on A's output (a
feedback loop), the design **must** declare an initial-cycle policy or it
deadlocks on the first transaction. Options:
- **Reset seed** — one endpoint emits a specified default value on cycle 0 after reset.
- **Request-driven** — add a request channel carrying what the consumer needs;
  producer responds with current state.
- **Bypass for the first transaction** — declare which endpoint is primed externally.

A closed loop with no declared bootstrap policy is a guaranteed first-cycle hang.

## Naming convention
Master out: `m_srdy`/`m_data` (`m_axis_*` for AXI-Stream), master in: `m_drdy`.
Slave in: `s_srdy`/`s_data`, slave out: `s_drdy`. For multiple interfaces,
qualify by role: `m_pixel_srdy`, `s_neighbor_drdy`. Keep the RTL prefix matching
the contract's `port_role` field.

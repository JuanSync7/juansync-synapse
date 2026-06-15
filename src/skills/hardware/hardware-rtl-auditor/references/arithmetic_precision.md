# Arithmetic Precision in RTL

When a block does arithmetic — DCT/FFT, matmul, FIR/IIR, accumulators, stats,
divides, fixed-point — its register widths and number formats are part of the
**design contract, not an implementation detail**. Getting this wrong silently
corrupts the algorithm: the design still simulates, lint-passes, and emits bytes
— the bytes are just wrong.

## Why this matters (silent-bug examples)

The most common silent bug in machine-generated RTL is "algorithm right, bit
widths wrong":
- A 4×4 forward DCT on 8-bit residuals saturates a 12-bit signed coefficient
  register → quantizer always outputs ±2047 → flat-grey blocks, PSNR drops 25 dB.
- A 16-bit accumulator overflows after 256 8-bit samples → FIR output goes random.
- Q1.15 × Q1.15 stored back into Q1.15 loses sign-extension or high-order bits.
- "Divide by 16" implemented as `>> 4` on a signed value with a buggy rounding
  rule → off-by-one for every negative coefficient.

None fail lint. None fail isolated block tests with toy stimulus. They surface
only when a real workload exercises the full range — often misclassified as a
non-arithmetic failure, wasting debug iterations.

## When this applies
Any block computing sums/products/dot-products/accumulators, transforms,
quantization/scaling/rounding, saturation/clamping, predictors/residuals,
filters, or log/exp/sqrt/reciprocal approximations. **Skip** pure
handshake/framing/routing blocks that only shuffle bits.

## Rule 1 — Derive each register's width from range analysis
Never pick widths by eye. For every arithmetic stage write down:
1. Input range (min,max) — explicit signed/unsigned and units.
2. The exact operation (sum of N terms, product, transform expansion factor…).
3. Output range from (1)+(2).
4. Width = `ceil(log2(max(|min|, max+1))) + 1` signed; `ceil(log2(max+1))` unsigned.
5. Round **UP** to a standard width (8/9/10/12/16/18/20/24/32). Never round down.

Document this in a "Bit-width derivation" section of the spec so an automated
contract-adherence check can verify it.

**Examples**
- 8-bit unsigned pixel − 8-bit unsigned prediction → diff ∈ [−255,255] → **9-bit
  signed** (8-bit wraps every negative residual → garbage).
- 4×4 integer forward DCT on 9-bit signed residuals → worst-case ≈ 16320 →
  **16-bit signed** for the coefficient output, NOT 12-bit. A quantizer may
  saturate to 12-bit *after* the full coefficient is computed — never store the
  intermediate in 12-bit.
- Accumulator of N B-bit signed samples → `ceil(log2(N)) + B` bits signed.
- Quant step Q a power of two → `(C + Q/2) >> log2(Q)` for round-to-nearest
  signed; do NOT use `/` (synthesizes badly, rounds wrong). Arbitrary Q →
  multiplier + reciprocal LUT. Declare the rounding mode and match the golden.

## Rule 2 — Pick a number format and stick to it
For each port and internal node declare ONE of:
- **Plain integer** (signed/unsigned N-bit) — pixels, counters, addresses, config.
- **Fixed-point `Qm.n`** (m integer + n fractional bits, signed unless `UQ`) —
  e.g. `Q1.15` ∈ [−1,1). Use for coefficients reused at multiple scales.
- **Floating-point** — only for genuine huge dynamic range (~6× the area of
  fixed-point). Default is "don't" for DSP/video/audio.

If you mix formats on an edge, the contract must spell out both formats and the
conversion — e.g. "tdata[31:0] = result, Q8.24 signed two's-complement,
converted from input Q1.15 by signed left-shift of 9 bits".

## Rule 3 — Saturation vs wraparound is a policy decision
Default Verilog `+ - *` **wrap modulo 2^N** — almost never what a DSP block wants,
almost always what a counter/pointer wants. For every arithmetic register
document one of: **wraparound** (mark "expected to wrap"), **saturation** (mark
"saturates to ±MAX" and include the `min/max` clamp logic), or
**range-guaranteed** (upstream contract guarantees the bound; carry an explicit
`max_magnitude` field and check downstream width covers it). Never leave
saturation to "the value won't exceed the width because inputs are small" — that
is exactly what breaks under a real workload.

## Rule 4 — Match the golden bit-for-bit, then optimize
1. Read the golden reference. Note every cast, shift, clip, and rounding mode
   (`math.floor`, `int()` truncate-toward-zero, `np.round` banker's rounding…).
2. Write the spec's "Algorithm mapping" calling out each step with its bit width
   and rounding mode.
3. Drive vectors at both sign extremes AND near the saturation/overflow points
   from Rule 1 — not just zero and small positives.

If the golden uses `int()` (truncate-toward-zero) and the RTL uses arithmetic
right shift (floors negatives), every negative coefficient is off by one —
silent, never lint-fails, breaks the bitstream.

## Rule 5 — Surface arithmetic limits in the interface contract
Per-field edge metadata should include width/signedness/encoding plus:
```json
{ "name":"coefficient","width":20,"signed":true,
  "number_format":"integer",        // or "Q4.12","Q1.15","float32"
  "max_magnitude":524287,
  "saturation_policy":"wraparound", // or "saturating" | "range_guaranteed"
  "rationale":"DCT output before quantizer" }
```
A contract-adherence check can then reject specs where a consumer's input width
is narrower than the producer's `max_magnitude` needs.

## Checklist (paste into spec review)
- [ ] Every arithmetic stage has documented input + output ranges.
- [ ] Every register width derives from Rule 1 (round UP).
- [ ] Every Q-format edge states integer/fractional bits, signedness, conversion.
- [ ] Every truncation/shift/round names its mode and matches the golden.
- [ ] Every saturation point is `saturating` / `wraparound` / `range_guaranteed`.
- [ ] Test vectors hit sign extremes and near-saturation values.
- [ ] If a golden exists, "Algorithm mapping" cites each golden op's bit-precision counterpart.

## Fixing a too-narrow width
1. Widen at the **source** of the saturation, not the consumer.
2. Update the interface contract's width and field list.
3. Cascade through downstream registers — but stop widening at any op that
   genuinely must quantize (quantizer rounding, mantissa truncation).
4. Add a regression test for the value that would have saturated.

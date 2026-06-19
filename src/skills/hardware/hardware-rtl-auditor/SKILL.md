---
name: hardware-rtl-auditor
aliases: [rtl-design-guard]
description: "Apply hard-won synthesizable-Verilog, arithmetic-precision, interface-protocol, and design-verification rules when writing, reviewing, or debugging RTL. Trigger: 'write Verilog', 'review this RTL', 'make this synthesizable', 'fix Verilator lint', 'why does my testbench fail', 'is this width correct', 'design an AXI-Stream interface', 'debug RTL vs golden mismatch'."
domain: hardware
scope: rtl
role: auditor
status: draft
tags: [verilog, rtl, asic, synthesis, verilator, yosys, cocotb, dv, fixed-point, axi-stream]
user-invocable: true
argument-hint: "[paste RTL/testbench to review, or describe the block/interface you're designing]"
---

# RTL Design Guard

Encodes the failure modes that bite machine-generated and hand-written RTL alike:
width bugs that pass lint but corrupt the algorithm, arithmetic that silently
overflows, interface contracts that drift between blocks, and testbenches that
fail for reasons that aren't the RTL's fault. It is a **rules-and-reference
advisor** — it pushes back on unsafe RTL before it reaches synthesis or sim, not
a code generator or an EDA toolchain.

Distilled from the prompt/skill IP of an LLM-driven RTL-to-GDS pipeline (Sky130 +
Verilator + Yosys + cocotb), made tool- and vendor-neutral.

**Scope:** reviewing/authoring synthesizable Verilog-2005, sizing arithmetic
datapaths, specifying block interfaces, and diagnosing simulation failures. It
does NOT run tools, generate a full design from a prompt, do place-and-route, or
manage a PDK.

## Wrong-Tool Detection
- **User wants a graph/workflow designed** → `/framework-workflow-designer`.
- **User wants tests run / a fix loop executed** → `/code-test-runner`.
- **User wants full RTL generated from a natural-language spec end-to-end** → this
  skill guides the rules, but generation itself is the user's flow (e.g. their
  Paperclip pipeline); apply these rules *to* that output.
- **User wants place-and-route / DRC / LVS / timing signoff** → out of scope; this
  is front-end (RTL + DV) only.

## How to use — load the right reference

| The task is about… | Load |
|---|---|
| Verilator/Yosys lint, width safety, latches, reset/FSM, valid self-cancellation, SDC basics | `references/synthesizable_verilog.md` |
| Datapath bit-widths, fixed-point Qm.n, saturation, golden bit-exactness | `references/arithmetic_precision.md` |
| AXI-Stream vs sRdy/dRdy, payload packing, backpressure, closed-loop bootstrap | `references/interface_protocols.md` |
| cocotb testbenches, golden-model method, "why does my sim fail", TB-bug vs RTL-bug | `references/dv_and_failure_patterns.md` |
| A fast pass/fail of any RTL or TB | `rules.md` (the 16 hard rules) |

Start from `rules.md`, then pull the matching reference for depth. Cite the rule
number when flagging an issue.

## Core workflow

**Reviewing RTL:**
1. Run the `rules.md` checklist top-to-bottom against the code.
2. For each violation, name the rule, show the offending line, give the corrected
   pattern from the reference.
3. Prioritize **silent** bugs (width/arithmetic/packing) over lint-visible ones —
   silent bugs pass every cheap gate and only surface under real workloads.

**Designing a datapath block:** do the Rule-1 range analysis first, declare
number formats and saturation policy, *then* write RTL. Document the bit-width
derivation so a reviewer/audit can check it.

**Specifying an interface:** pick the protocol (sRdy/dRdy vs AXI-Stream) by the
decision table, freeze the payload packing in a contract both endpoints
reference, and declare a bootstrap policy if there's any feedback loop.

**Debugging a sim failure:** match the symptom against the failure-pattern
catalogue, decide TB-bug vs RTL-bug from the waveform's first divergence *before*
editing RTL, and append the lesson to a project `DV_RULES.md`.

## Provenance & status
Harvested 2026-05 from the MIT-licensed CoreSmith repo's prompt/skill library and
made vendor-neutral. Core skill (SKILL.md + references + rules) and `EVAL.md` are
complete; a measured eval score and gatekeeper sign-off are pending — run
`/synapse-skill-improver` to score, then `/synapse-router-artifact-gatekeeper` to
promote from `draft` to `stable`.

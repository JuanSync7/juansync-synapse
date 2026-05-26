# Design Document — Plan Execution via Vertical-Slice Subagent Orchestration

> Brainstorm slug: `2026-05-22-plan-execution-vertical-slice-orchestration`
> Status: **complete** | Artifact: multi-artifact (creation) | Target: `delivery/` domain — 1 skill + 5 protocols

---

## 1. Problem Statement

No artifact in the library governed sequential, TDD-disciplined subagent execution of a plan. The gap had three distinct root causes:

1. **`parallel-agents-dispatch` lacked TDD discipline.** It dispatched in waves for throughput, but gave no instruction on how each subagent should approach its work — no test-first requirement, no iteration obligation, no structured output for the main agent to ingest.
2. **No close-loop between subagent output and plan mutation.** When a subagent hit a blocker or discovered drift, there was no protocol governing how that signal flowed back to the main agent or how the plan got updated. Lessons from slice N never reached slice N+1.
3. **No resumable execution trail.** Subagent context compaction could lose mid-run progress. There was no filesystem-native audit trail from which a run could be reconstructed and continued.

**What changes:** a new `delivery` domain introduces a skill and five protocols that together govern the full plan-to-closeout loop — from dispatching one subagent on one slice, through TDD-disciplined execution, through structured closeout, through plan mutation — sequentially, resumably, and with compounding lessons across slices.

---

## 2. Design Principles

### 2.1 Sequential execution is the default; parallelism is a named escape hatch

Sequential dispatch — one subagent at a time, next dispatch waits for the prior closeout — eliminates the entire class of write conflicts, prevents plan divergence between in-flight dispatches, and lets lessons from each slice compound into the next subagent's context. Parallelism is only permissible when all three independence conditions hold (zero `touches` overlap, zero `depends_on` coupling, explicit user authorization). The default and recommended path is sequential.

**Implication:** `delivery-orchestration-dispatch-contract` hard-codes sequential as the invariant and models parallelism as an opt-in exception with named conditions, not a tunable preference.

### 2.2 The dispatch unit is a slice, not an epic or a task

The slice is the only unit that is dispatchable. Epic/story/task/subtask are planning vocabulary used to group and order work; they are not dispatch units. A slice is defined by one validable end-goal, one subagent dispatch, and one closeout. Aligning the dispatch unit with the story/FR boundary (Jira-equivalent) makes the system interoperable with `write-story` output without impedance mismatch.

**Implication:** `delivery-execution-slice-contract` is the normative definition of what a slice must contain. The planning hierarchy above it is advisory. `delivery-orchestration-plan-executor` decomposes work into slices — not into epics or tasks — as the leaf unit before any dispatch occurs.

### 2.3 TDD + Ralph are one facet, not two separate protocols

"TDD" (red-green-refactor per iteration), "Ralph loop" (iterate until outcome is met, do not surrender after one failure), and "validable end-goal" (the acceptance criterion expressed as a test) are three names for facets of the same discipline. They collapse to one protocol because separating them would create a coordination problem — no single protocol would own the exit condition. The validable outcome IS the failing test; Ralph IS the iterate-to-green wrapper; inner TDD IS the per-iteration red-green-refactor discipline.

**Implication:** `delivery-execution-tdd-contract` is the single protocol governing all three facets inside a subagent execution. It is not decomposed further. The iteration cap (default 10) is the only exit door short of green; rational surrender is `blocked`, not silence.

### 2.4 Subagents have minimal write scope; spec is sacred

The spec (slice assignment file, from `write-story` or materialized to `.delivery/plan/wp-N.md`) is read-only to subagents. Subagents write code, tests, and their own closeout file — nothing else. The main agent is the sole writer of plan files, lessons, and slice frontmatter. This separation prevents spec drift under concurrent pressure, makes the audit trail unambiguous, and ensures parallelism (the escape hatch) is safe when it fires.

**Implication:** this boundary is enforced by `delivery-orchestration-closeout-schema` (what the subagent MAY write), `delivery-orchestration-dispatch-contract` (what the main agent bundles and controls), and `delivery-orchestration-replan-contract` (what the main agent MAY mutate). Any subagent write to plan/ or lessons.md is a halt-level violation.

### 2.5 Closeouts are append-only, dual-target, and mandatory

Resumability requires that the execution trail survive context compaction. A closeout that exists only in the subagent response is lost after compaction. A closeout that exists only on the filesystem cannot be ingested inline. Both targets are required: subagent emits inline YAML (for immediate ingestion) AND writes to `.delivery/closeouts/<slice-id>-attempt-N.yaml` (for resume and audit). File write must precede inline emission; file-write failure halts the dispatch.

**Implication:** `delivery-orchestration-closeout-schema` mandates both targets and the write ordering. No retry on malformed YAML more than once — two malformations on the same dispatch escalate to user.

### 2.6 Plan mutations are owned by the main agent and fully audited

The replan loop — triggered by `plan_drift_detected`, `next_moves`, blocked or failed closeouts, or non-empty `lessons_learnt` — is the main agent's exclusive domain. All mutations to plan/ and lessons.md must have a matching CHANGELOG entry in the same tick. Closed-out slice files are never deleted; they are marked superseded. Closeout files are never edited.

**Implication:** `delivery-orchestration-replan-contract` owns the full ingest-to-mutation flow (absorbing closeout-schema's ingestion semantics), defines every allowed and forbidden mutation, and requires a CHANGELOG entry per diff. The M=3 replan-cycle cap per slice is skill-overridable (consistent with the N=10 iteration cap in tdd-contract), not a hard constant.

### 2.7 `delivery-orchestration-closeout-schema` extends, not forks, `synapse-observability-execution-trace`

Delivery-specific fields (slice_id, files_created, tests_added, validable_outcome, lessons_learnt, next_moves) are layered on top of the existing observability protocol. Forking would duplicate structural tracing fields and create divergence to maintain. Cross-referencing keeps the observability surface clean and the delivery surface additive.

**Implication:** the closeout-schema body cites `synapse-observability-execution-trace` as its base and only documents the delta fields. A reader of the full schema must read both.

### 2.8 `auto-research` and `plan-executor` are siblings, not a merged skill

Both orchestrate subagents that do iterative work. They differ in intent: `plan-executor` is build-forward (given a plan, execute it to completion); `auto-research` is optimize-same-target (run experiments against one objective until quality bar is met). Collapsing them into one skill produces a mode-switcher with confused intent and tangled stop conditions. Instead, they share the `delivery-orchestration-dispatch-contract` and `delivery-orchestration-closeout-schema` protocols — the shared shape is extracted, not duplicated.

**Implication:** `delivery-orchestration-plan-executor` is a standalone skill. Its protocols are designed as first-class reusables so `auto-research` can adopt them independently when ready.

---

## 3. Architecture

### 3.1 Flow Graph

```
User triggers /build (or "start building" prompt)
          │
          ▼
┌─────────────────────────────────────────────────┐
│  delivery-orchestration-plan-executor (SKILL)   │
│                                                 │
│  1. Pre-flight checks                           │
│     ├─ .delivery/ writable?                     │
│     ├─ decomposition yields ≥1 slice?           │
│     └─ test framework discoverable?             │
│                                                 │
│  2. Decompose → slice list                      │
│     ├─ write-story tickets present?             │
│     │   YES → use FR-NNN dirs as-is             │
│     │   NO  → decompose from context,           │
│     │         materialize wp-N.md files         │
│     └─ present WP list, await user confirm      │
│                                                 │
│  3. OUTER LOOP (main agent)                     │
│     │                                           │
│     ├─► dispatch-contract: pick next slice      │
│     │    ├─ validate slice (slice-contract)     │
│     │    ├─ check depends_on all green          │
│     │    ├─ bundle 8 prompt slots               │
│     │    └─ dispatch one subagent               │
│     │                                           │
│     │         SUBAGENT (inner loop)             │
│     │         ┌───────────────────────────────┐ │
│     │         │ tdd-contract                  │ │
│     │         │ 1. Read validable outcome     │ │
│     │         │ 2. Write failing test first   │ │
│     │         │ 3. Ralph loop (≤N iterations) │ │
│     │         │    write code → run → adjust  │ │
│     │         │ 4. Exit on: green OR cap hit  │ │
│     │         └───────────────────────────────┘ │
│     │                                           │
│     │         SUBAGENT emits closeout           │
│     │         ┌───────────────────────────────┐ │
│     │         │ closeout-schema               │ │
│     │         │ 1. Write .delivery/closeouts/ │ │
│     │         │    <id>-attempt-N.yaml        │ │
│     │         │ 2. Append inline YAML         │ │
│     │         └───────────────────────────────┘ │
│     │                                           │
│     ├─► ingest + validate closeout              │
│     │                                           │
│     ├─► replan-contract (if triggered)          │
│     │    ├─ update plan/INDEX.md               │
│     │    ├─ append lessons.md                  │
│     │    └─ log to plan/CHANGELOG.md           │
│     │                                           │
│     └─► stop conditions check                  │
│          ├─ all slices green → DONE             │
│          ├─ N=2 consecutive failures → escalate │
│          ├─ M=3 replan cycles on slice → halt   │
│          └─ user interrupt → halt               │
│                                                 │
│  4. Final summary                               │
│     ├─ slice rollup (total/green/blocked/supr.) │
│     ├─ lessons.md tail                          │
│     ├─ pointer to plan/INDEX.md                 │
│     └─ exit reason enum                         │
└─────────────────────────────────────────────────┘
```

### 3.2 Node Specifications

#### Node 1: Pre-flight

Load: none (filesystem check only)

Do:
1. Verify `.delivery/` is writable; create if absent.
2. Attempt decomposition — verify it yields ≥1 slice.
3. Probe for test framework (project conventions, config files).

Don't: proceed silently if any check fails.

Exit: all checks pass → Decompose. Any check fails → halt loud with specific failure reason.

---

#### Node 2: Decompose + Confirm

Load: `write-story` FR-NNN dirs (if present) OR free-form context (chat, doc, rough plan).

Do:
1. If `write-story` tickets are present, treat them as the authoritative WP list.
2. Otherwise, decompose from context into slice-shaped work packages; materialize each as `.delivery/plan/wp-N.md`.
3. Write `.delivery/plan/INDEX.md` with WP list, order, and initial statuses.
4. Present WP list to user; await one confirmation before entering dispatch loop.

Don't: enter dispatch loop without user confirmation. Re-decompose tickets from `write-story` — treat them as-is.

Exit: user confirms → Outer Loop. User rejects → re-decompose with feedback.

---

#### Node 3: Dispatch (dispatch-contract)

Load: `delivery-orchestration-dispatch-contract`, plan/INDEX.md, next slice file, dependency closeouts, prior attempt closeouts, lessons.md.

Do:
1. Pick next undispatched slice from INDEX.md in dependency order.
2. Run slice-contract validation; refuse dispatch if malformed.
3. Verify all `depends_on` slices have pass closeouts.
4. Bundle all 8 required prompt slots.
5. Select model explicitly (default: sonnet; opus only if slice notes flag architectural complexity).
6. Dispatch single subagent.

Don't: dispatch more than one subagent at a time (sequential invariant). Dispatch without explicit model. Dispatch with any of the 8 slots missing. Dispatch on a slice with unresolved dependencies.

Exit: subagent completes and emits closeout → Closeout Ingestion. Sequential invariant broken → halt + escalate.

---

#### Node 4: Subagent — TDD Execution (tdd-contract)

Load: `delivery-execution-tdd-contract` (injected via `{{worker_protocols}}` slot), slice assignment.

Do:
1. Read the slice's validable outcome from the assignment.
2. Write a failing test that encodes that outcome — first file edit is a test file.
3. Ralph loop: `write minimum code → run test → observe → adjust` (≤N=10 iterations, skill-overridable).
4. Apply inner red-green-refactor per iteration for any subordinate assertions.
5. Exit when outcome test is green AND no in-scope tests fail.

Don't: write production code before a test. Surrender before iteration cap. Disable or weaken tests to force green. Dispatch nested subagents (slice too big if this impulse arises).

Exit: outcome test green → Closeout Emission. Iteration cap hit without green → emit `blocked` closeout.

---

#### Node 5: Subagent — Closeout Emission (closeout-schema)

Load: `delivery-orchestration-closeout-schema` (injected via `{{worker_protocols}}` slot).

Do:
1. Write `.delivery/closeouts/<slice-id>-attempt-N.yaml` (file write first, mandatory).
2. Append inline YAML block to response.
3. Populate all required fields: slice_id, attempt_number, validable_outcome (verbatim), validation_result, outcome_test_path (if pass), iterations_used, files_created, files_modified, tests_added, lessons_learnt, next_moves, plan_drift_detected, plan_drift_reason (if drift), blocked_reason (if blocked).

Don't: emit inline YAML before file write succeeds. Omit slice_id, validable_outcome, or validation_result. Report `pass` without outcome_test_path. Write to plan/ or lessons.md.

Exit: closeout emitted → main agent Closeout Ingestion.

---

#### Node 6: Closeout Ingestion + Replan (replan-contract)

Load: `delivery-orchestration-replan-contract`, closeout YAML, plan/INDEX.md, lessons.md.

Do:
1. Parse and validate closeout YAML (all required fields, structural integrity).
2. On `pass`: mark slice complete in plan/INDEX.md; append lessons to lessons.md; evaluate next_moves.
3. On `blocked`/`failed`/`rejected`: route to replan logic.
4. Replan triggers: plan_drift_detected, non-empty next_moves, blocked/failed result, non-empty lessons_learnt.
5. Allowed mutations: add/reorder/block/defer/supersede slices, re-decompose into smaller slices, append lessons, update frontmatter, log to plan/CHANGELOG.md.
6. Every plan/ or lessons.md diff gets a matching CHANGELOG entry in the same tick.
7. Increment replan cycle count per slice; escalate at M=3.

Don't: delete closed-out slice files (mark superseded). Edit or delete closeout files. Apply non-append edits to lessons.md. Allow subagent writes to plan/.

Exit: plan updated, lessons appended → Stop Conditions Check.

---

#### Node 7: Stop Conditions

Do:
1. Check: all slices in INDEX.md are closed-out green → DONE, emit final summary.
2. Check: N=2 consecutive failures on the same slice → escalate to user.
3. Check: M=3 replan cycles on a single slice → halt, signal "plan likely fundamentally misframed".
4. Check: user interrupt received → halt, emit partial summary.
5. Otherwise → return to Dispatch (Node 3) for next slice.

Exit: any stop condition met → Final Summary. None met → Dispatch.

---

### 3.3 Entry Gates

| Transition | Gate conditions |
|---|---|
| Pre-flight → Decompose | `.delivery/` writable; decomposition yields ≥1 slice; test framework discoverable |
| Decompose → Dispatch loop | User confirms WP list |
| Dispatch → Subagent dispatch | Slice-contract validation passes; all `depends_on` slices have pass closeouts; no other subagent in-flight; all 8 prompt slots populated; model explicitly selected |
| Subagent → Emit closeout (pass) | Outcome test green; no in-scope tests failing |
| Subagent → Emit closeout (blocked) | Iteration cap reached without green |
| Closeout Ingestion → Dispatch (next slice) | Closeout YAML well-formed; all required fields present; `pass` ⇒ outcome_test_path populated and appears in tests_added; replan cycle count < M=3 for this slice |
| Parallel dispatch escape hatch | Zero `touches` overlap between concurrent slices; zero `depends_on` coupling between concurrent slices; explicit user authorization for this run |

---

## 4. Naming Conventions

The `delivery` domain is new. All six artifacts follow the four-segment naming pattern used across this library:

```
{domain}-{subdomain}-{subject}-{role/kind}
```

**Domain:** `delivery`
Rationale: plan-execution is a distinct concern from `synapse` (framework-meta). `delivery` is semantically precise, carries no slot collisions, and signals the transport-from-plan-to-code purpose of this artifact family.

**Subdomains:**
- `execution` — worker-side concern; what one subagent does inside a slice. Covers protocols `delivery-execution-slice-contract` and `delivery-execution-tdd-contract`.
- `orchestration` — manager-side concern; how subagents are coordinated, closeouts consumed, plan mutated. Covers skill `delivery-orchestration-plan-executor` and protocols `delivery-orchestration-closeout-schema`, `delivery-orchestration-dispatch-contract`, `delivery-orchestration-replan-contract`.

Each subdomain encodes *which agent role* enforces the protocol — this is not padding; it prevents cross-role confusion in a system where main agent and subagent have strictly different write authorities.

**Artifact name breakdown:**

| Artifact | domain | subdomain | subject | role/kind |
|---|---|---|---|---|
| `delivery-orchestration-plan-executor` | delivery | orchestration | plan | executor |
| `delivery-execution-slice-contract` | delivery | execution | slice | contract |
| `delivery-execution-tdd-contract` | delivery | execution | tdd | contract |
| `delivery-orchestration-closeout-schema` | delivery | orchestration | closeout | schema |
| `delivery-orchestration-dispatch-contract` | delivery | orchestration | dispatch | contract |
| `delivery-orchestration-replan-contract` | delivery | orchestration | replan | contract |

**Taxonomy registration required:** `delivery` must be added to `PROTOCOL_VOCABULARY.md` and `SKILL_VOCABULARY.md`. The `executor` role value must be verified in `SKILL_VOCABULARY.md`; if absent, propose an addition.

---

## 5. Companion Model — `delivery-orchestration-plan-executor` (Skill)

The skill uses a **lite two-tier companion model**: the SKILL.md body carries always-on orchestration policy; one `references/` file carries operationally-detailed heuristics that would bloat the body.

| Tier | File | Load point | Content |
|---|---|---|---|
| Tier 1 (always-on) | `SKILL.md` | Every invocation | Trigger phrases, outer loop policy, stop conditions, protocol reference names (never protocol bodies inline) |
| Tier 2 (decision-point) | `references/slice-decomposition-heuristics.md` | At decomposition step (Node 2) | Guidance for epic-vs-story-vs-task judgment; slice size bounds; when to re-decompose vs. escalate |

**Creator constraint:** SKILL.md MUST reference protocols by name only. Protocol bodies are never restated inline in the skill body. This keeps the skill body token-lean and forces protocol authority to stay in the protocol files.

---

## 6. Filesystem Surfaces

The `.delivery/` directory is the runtime working memory for a single plan-executor run. Its shape is canonical for free-form mode; write-story mode reuses its existing `docs/<initiative>/.../stories/FR-NNN/` structure and adds `.delivery/` for closeouts and lessons only.

<!-- VERBATIM -->
```
.delivery/
├── plan/
│   ├── INDEX.md             # main agent's WP list with status, deps, order
│   └── wp-<id>.md           # per-WP assignment (free-form mode only; ticketed mode uses write-story dirs)
├── closeouts/
│   └── wp-<id>-attempt-N.yaml   # one per subagent dispatch; append-only
└── lessons.md               # curated by main agent from closeouts; injected into future subagent prompts
```

**Two-surface model** — the full runtime picture across both surfaces:

<!-- VERBATIM -->
| Surface | Jira analogue | Lifetime |
|---|---|---|
| `docs/<initiative>/.../stories/FR-NNN/` (from write-story) | Backlog + tickets (spec) | Long-lived archive |
| `.delivery/plan/INDEX.md` | Current sprint board | Per-run, gitignored |
| `.delivery/closeouts/*.yaml` | Work logs / activity stream | Append-only audit trail |
| `.delivery/lessons.md` | Retro notebook | Append-only within run |

When tickets exist, `plan/INDEX.md` references FR-NNN dirs (no copy). Free-form mode: `plan/wp-N.md` takes the ticket role for that run.

**Linkage model (Model C) — ticket ↔ subagent ↔ closeout:**

<!-- VERBATIM -->
| Surface | Writer | Reader | Mutability |
|---|---|---|---|
| Work-package files (`docs/.../FR-NNN/{story,design,impl,test}.md` from write-story, OR `.delivery/plan/wp-<id>.md` for free-form) | Main agent ONLY | Subagent (read-only assignment package) | Frontmatter mutable by main agent (status, pr_url); body mutable only via replan |
| Code + tests | Subagent | Both | Normal source code |
| Closeout files (`.delivery/closeouts/wp-<id>.yaml` and appended to response) | Subagent (one per dispatch attempt) | Main agent | Append-only — each dispatch attempt is a new file `wp-<id>-attempt-N.yaml`. Audit trail. |
| Plan file (the rolling WP list — `.delivery/plan/INDEX.md` or similar) | Main agent ONLY | Both (subagent reads its own WP entry) | Main agent edits after ingesting closeouts |
| Lessons trail (`.delivery/lessons.md` — append-only) | Main agent (curates from closeouts) | Subsequent subagent dispatches | Append-only |

---

## 7. Protocol Field Tables

### 7.1 `delivery-orchestration-closeout-schema` — Required Fields

| Field | Required when | Notes |
|---|---|---|
| `slice_id` | Always | Stable identifier for cross-reference |
| `attempt_number` | Always | Count of prior closeouts for this slice + 1 |
| `validable_outcome` | Always | Verbatim from assignment — must match exactly |
| `validation_result` | Always | `pass` \| `blocked` \| `failed` \| `rejected` |
| `outcome_test_path` | If `pass` | Test file path encoding the outcome |
| `iterations_used` | Always | Count of Ralph-loop iterations |
| `files_created` | Always | List (may be empty) |
| `files_modified` | Always | Must be ⊆ slice's declared `touches` scope |
| `tests_added` | Always | List; if `pass`, outcome_test_path appears here |
| `lessons_learnt` | Always | List (may be empty) |
| `next_moves` | Always | List of `{summary, rationale, suggested_slice_id?}` (may be empty) |
| `plan_drift_detected` | Always | Boolean |
| `plan_drift_reason` | If `plan_drift_detected: true` | Free-form explanation |
| `blocked_reason` | If `blocked` | Free-form explanation |

### 7.2 `delivery-orchestration-dispatch-contract` — Required Prompt Slots

| Slot | Content | Why non-negotiable |
|---|---|---|
| `{{slice_assignment}}` | Full slice file content | Subagent's complete brief |
| `{{slice_id}}` | Stable slice identifier | Closeout cross-reference |
| `{{attempt_number}}` | Prior closeout count + 1 | Retry awareness |
| `{{dependency_closeouts}}` | Closeouts of depends_on slices (distilled: validation_result + tests_added + lessons summary) | Prevents subagent re-inventing pinned contracts |
| `{{prior_attempt_closeouts}}` | Closeouts of prior attempts on this slice | Prevents same approach retried (loop death) |
| `{{lessons_md}}` | Full `.delivery/lessons.md` content | Compounds learning across slices |
| `{{worker_protocols}}` | slice-contract + tdd-contract + closeout-schema bodies | Subagent knows it owes a closeout, must test-first, has an iteration cap |
| `{{model}}` | Explicit model choice | Reproducible runs; no cost surprises |

---

## 8. Accepted Tensions

| Tension | Decision | Revisit when |
|---|---|---|
| Sequential execution vs. throughput | Sequential is the default; parallel is an escape hatch requiring all three independence conditions and explicit user authorization | When benchmarks show sequential is the bottleneck on consistently independent slices |
| Iteration cap default (N=10) is empirical | Accept as default; skill-overridable at dispatch time | After dogfooding — revisit if cap is routinely hit or routinely far from binding |
| Replan cycle cap (M=3) is empirical | Accept as skill-overridable default (consistent with N=10 policy) | After dogfooding — revisit if M=3 triggers false escalations |
| dependency_closeouts passes distilled summaries, not full bodies | Distilled (validation_result + tests_added + lessons summary) to keep prompt budget controlled | When prompt-budget pressure is no longer a constraint or distillation loses material information |
| lessons.md end-of-run compression | Bet: end-of-run hook compresses to a "run summary" while preserving raw as `lessons.raw.md` | Confirm at companion-file design; not load-bearing on protocol correctness |
| auto-research overlap with plan-executor | Build as siblings sharing dispatch and closeout protocols; do not merge | If 3+ adopters report identical usage patterns suggesting the two modes are the same intent |
| `parallel-agents-dispatch` coexistence vs. retirement | Coexist for now (user picks based on risk/coupling); plan-executor is canonical for TDD-disciplined sequential execution | When `parallel-agents-dispatch` has zero active use post-dogfooding; retire with deprecation note |

---

## 9. Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `delivery-execution-slice-contract` | consumed by `delivery-orchestration-plan-executor` | Defines what a valid slice file must contain; main agent validates pre-dispatch |
| `delivery-execution-tdd-contract` | consumed by subagent (injected via dispatch) | Governs subagent's inner TDD + Ralph loop and exit conditions |
| `delivery-orchestration-closeout-schema` | consumed by subagent (injected via dispatch); consumed by `delivery-orchestration-replan-contract` | Defines closeout YAML structure; extends `synapse-observability-execution-trace` |
| `delivery-orchestration-dispatch-contract` | consumed by `delivery-orchestration-plan-executor` | Governs pre-dispatch validation, prompt slot assembly, model selection, and sequential invariant |
| `delivery-orchestration-replan-contract` | consumed by `delivery-orchestration-plan-executor` | Governs all plan/ and lessons.md mutations post-closeout-ingestion; owns the full ingest-to-mutation flow |
| `synapse-observability-execution-trace` | consumed by `delivery-orchestration-closeout-schema` | Base schema that closeout-schema extends (not forks) |
| `synapse-memory-external-memory-contract` | consumed by `delivery-orchestration-replan-contract` | Plan/ and lessons.md are the working memory; replan-contract is the write-rule layer on top |
| `write-story` | consumed by `delivery-orchestration-plan-executor` | When tickets are present, their FR-NNN dirs are the authoritative WP list (read-only input; not re-decomposed) |
| `parallel-agents-dispatch` | sibling (coexists) | User selects between them based on coupling risk; plan-executor is canonical for TDD-disciplined sequential execution |

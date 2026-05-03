# Animation Timing & Sync Reference

**Purpose:** Implementation details for the unified timing system, sequential packet animation, CSS animation resets, and auto-play mode. Read this when writing `runFlowAnimation`, `runTimelineAnimation`, `runTerminalAnimation`, and auto-play logic.

---

## Unified Timing System — Stage-Arrival Sync

All three animated sections (flow graph, timeline, terminal) MUST be driven by the same timing source. The flow graph computes cumulative delays; timeline and terminal use **stage arrival delays** extracted from those.

**Why proportional/even distribution is wrong:** If you spread timeline or terminal items evenly across the total duration, they will drift out of sync with the flow graph. For example, the "DNS Resolve" timeline step would appear while the flow is still at the Client node. Instead, extract the exact moments when each flow stage completes, and use those as anchors.

**Stage arrivals** are flow steps that have NO connector — they represent the moment a node becomes active after a packet arrives. Skip the first step (index 0, which is just the initiating node).

```javascript
// Flow animation returns computed delays for ALL steps
var flowDelays = runFlowAnimation(scenario.flowSequence);
// Pass both the sequence and delays so other sections can extract stage arrivals
runTimelineAnimation(scenario.timeline, scenario.flowSequence, flowDelays);
runTerminalAnimation(scenario.terminalLines, scenario.flowSequence, flowDelays);

// Extract stage arrival delays from flow
function getStageDelays(flowSeq, allDelays) {
  var stageDelays = [];
  flowSeq.forEach(function(step, idx) {
    // Node-only steps after index 0 = stage completions
    if (idx > 0 && !step.connector) {
      stageDelays.push(allDelays[idx]);
    }
  });
  return stageDelays;
}
```

### Timeline Sync

Each timeline step maps 1:1 to a stage arrival. Timeline step `i` fires at `stageDelays[i]`.

```javascript
function runTimelineAnimation(steps, flowSeq, allDelays) {
  var stageDelays = getStageDelays(flowSeq, allDelays);
  steps.forEach(function(step, i) {
    // Use matching stage arrival delay
    var syncedDelay = (i < stageDelays.length)
      ? stageDelays[i]
      : stageDelays[stageDelays.length - 1] + (i - stageDelays.length + 1) * 800;
    // schedule reveal at syncedDelay...
  });
}
```

### Terminal Sync

Terminal lines are spread proportionally across the full duration bounded by stage arrivals, so they progress naturally as the flow advances.

```javascript
function runTerminalAnimation(lines, flowSeq, allDelays) {
  var stageDelays = getStageDelays(flowSeq, allDelays);
  var totalDuration = allDelays[allDelays.length - 1];
  // Build boundaries: [startOffset, stage0, stage1, ..., totalDuration+buffer]
  var boundaries = [200];
  for (var s = 0; s < stageDelays.length; s++) boundaries.push(stageDelays[s]);
  boundaries.push(totalDuration + 200);
  var totalSpan = boundaries[boundaries.length - 1] - boundaries[0];

  lines.forEach(function(line, i) {
    var pos = i / lines.length;
    var syncedDelay = Math.round(boundaries[0] + pos * totalSpan);
    // schedule reveal at syncedDelay...
  });
}
```

**Design the scenario data so this mapping works:** Each scenario's `timeline` array should have one entry per stage arrival in the `flowSequence`. For example, if the flow visits Client → DNS → TLS → Server → Response (4 arrivals after Client), the timeline should have exactly 4 entries.

---

## Sequential Packet Animation

Packets must appear one after another — never overlapping. Use cumulative delay calculation:

```javascript
const PACKET_DURATION = 600; // must match CSS animation duration

function runFlowAnimation(seq) {
  var computedDelays = [];
  var cumulativeDelay = 0;

  seq.forEach(function(step, idx) {
    if (idx === 0) {
      cumulativeDelay = 300;
    } else {
      var prevStep = seq[idx - 1];
      var authoredGap = step.delay - prevStep.delay;
      // Long idle dwell at node after packet arrives, shorter for node-only steps
      var minGap = prevStep.connector ? PACKET_DURATION + 900 : 800;
      cumulativeDelay += Math.max(authoredGap, minGap);
    }
    computedDelays.push(cumulativeDelay);

    // Schedule node activation, packet animation, status update at this delay
    // ... (see implementation details below)
  });
  return computedDelays;
}
```

### Key Timing Values

| Constant | Value | Purpose |
|----------|-------|---------|
| `PACKET_DURATION` | 600ms | CSS travel animation duration |
| Idle dwell | 900ms | Visible pause at each stage after packet arrives |
| Node-only gap | 800ms | Gap for steps without connector animation |
| Trail persistence | Indefinite | Trails reset only in `clearAnimations()` |

---

## CSS Animation Reset Pattern

To restart a CSS animation on the same element, reset the class and force a reflow:

```javascript
element.className = 'packet';
void (element.offsetWidth);  // force reflow — parentheses required
element.classList.add('traveling-right');
```

---

## Auto-Play Mode

- Toggle between auto and manual mode using the slider switch
- Auto mode cycles through scenarios using **dynamic timing**, NOT a fixed interval
- After the last flow step completes, wait **3 seconds** (visible pause at final state) before advancing
- Compute total wait per scenario: `flowDelays[last] + 3000`
- Use chained `setTimeout` (not `setInterval`) so each scenario gets exactly the time it needs
- Show a progress bar on the active scenario button that fills over the computed total wait duration
- Clear all animations, timeouts, and progress bars when switching scenarios

**Why fixed intervals are wrong:** If you use `setInterval(fn, 9500)`, fast scenarios waste time sitting idle while slow scenarios get cut off mid-animation. Instead, compute the actual animation duration from `flowDelays` and add a 3-second pause.

```javascript
/* In selectScenario, after running flow animation: */
if (autoPlaying) {
  clearTimeout(autoTimer);
  var lastDelay = flowDelays[flowDelays.length - 1];
  var totalWait = lastDelay + 3000;
  /* progress bar */
  prog.style.transitionDuration = totalWait + 'ms';
  prog.style.width = '100%';
  /* chain to next */
  autoTimer = setTimeout(function() {
    selectScenario((currentIdx + 1) % scenarios.length);
  }, totalWait);
}
```

---
name: create-animation-page
description: "Creates a single-page interactive animation visualization as one HTML file with embedded CSS and JavaScript. Triggered by: 'create animation page', 'single page animation', 'interactive visualization', 'animated explainer'."
domain: creative
intent: write
tags: [animation, HTML, visualization]
user-invocable: true
argument-hint: "[topic/concept to visualize]"
---

# Create Animation Page

Generates a complete, self-contained single-page interactive animation as one HTML file with embedded CSS and JavaScript. The output visualizes a technical concept or process with animated flow graphs, scenario selectors, and a macOS-style terminal.

## When to Use

- User wants to visualize a technical concept (API flows, data pipelines, auth flows, etc.)
- User asks for an interactive single-page animation or explainer
- User wants an animated demo page for a process or system

## Wrong-Tool Detection

- **User wants a multi-page website** → not this skill; this creates single-page animations only
- **User wants a static diagram or chart** → suggest using Mermaid or a charting library directly
- **User wants a React/Vue component** → not this skill; this produces vanilla HTML/CSS/JS only

## Critical Rule: No TypeScript in Browser Scripts

**NEVER use TypeScript syntax inside `<script>` tags.** Browsers cannot parse TypeScript, and the entire script block will silently fail with zero error output — the page loads but nothing works.

Forbidden patterns (these kill the page silently):
```
interface Foo { ... }           // TS-only construct
const x: string = "hello"      // type annotation
const el = div as HTMLElement   // type cast
el.querySelector('x')!.method  // non-null assertion
function foo(): void { }       // return type annotation
```

Use plain JavaScript equivalents:
```javascript
// No interfaces — use plain objects or JSDoc if needed
const x = "hello"
const el = div
var dot = el.querySelector('x'); if (dot) dot.method()
function foo() { }
```

When forcing a DOM reflow (to restart CSS animations), use parentheses:
```javascript
void (element.offsetWidth);  // correct
// NOT: void element.offsetWidth  — this is a syntax issue in some contexts
```

## Output Structure

Generate a single `index.html` file containing:

```
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Topic] Visualizer</title>
  <style>
    /* All CSS here */
  </style>
</head>
<body>
  <!-- All HTML here -->
  <script>
    // All JavaScript here — PLAIN JS ONLY, NO TYPESCRIPT
  </script>
</body>
</html>
```

## Design System

### Theme
- Dark background with subtle radial gradients for depth
- Use CSS custom properties for all colors
- Default gradient theme: yellow-to-green (customizable per user request)

```css
:root {
  --bg-primary: #0a0a0f;
  --bg-secondary: #12121a;
  --bg-card: #1a1a26;
  --border: #2a2a3a;
  --text-primary: #e8e8f0;
  --text-secondary: #8888a0;
  --accent-start: #e8d44d;
  --accent-end: #34d399;
  --gradient: linear-gradient(135deg, var(--accent-start), var(--accent-end));
}
```

Adjust `--accent-start` and `--accent-end` if the user specifies a different theme color.

### Container Styling
All major containers (flow section, controls, detail panel, terminal) use transparent/dark background with a solid border. Detail cards (key-value pairs) are the exception — they use `--bg-secondary` to reduce visual clutter.

### Typography
- Use `Inter` for UI text, `JetBrains Mono` for code/terminal
- Import from Google Fonts

### Layout
The page has four sections stacked vertically:

1. **Header** — Title with gradient text, subtitle
2. **Flow Graph** — Horizontal node-connector chain showing stages of the process
3. **Scenario Section** — Grid with sidebar selector (left) and detail panel (right)
4. **Terminal** — macOS-framed terminal showing CLI commands

## Required Components

### 1. Flow Graph
A horizontal chain of nodes connected by lines. Each node represents a stage in the process.

- **Nodes**: icon + label, with CSS states for `active`, `error-state`, `success-state`. Active nodes get a gradient border (dark interior preserved) via the `padding-box`/`border-box` CSS trick. Error nodes get red border + shake. Success nodes get green border + pop.
- **Connectors**: thin lines between nodes starting as grey (`var(--border)`), containing animated packets and trails
- **Packets**: small circles that travel along connectors with a comet-tail effect
- **Trails**: gradient color fills that persist at full opacity (`opacity: 1`) after the packet passes, creating a visual breadcrumb. The grey-to-gradient contrast is what makes the animation readable.
- **Error trails**: when `isError: true`, the trail turns red and an "✕" marker appears at the connector center
- **clearAnimations()**: must reset trail inline styles (`style.width = '0%'`, `style.opacity = ''`) because `animation-fill-mode: forwards` persists computed values after class removal
- Status text below the graph updates at each step
- Hover tooltips on each node explaining the stage

> **Read [`references/component-patterns.md`](references/component-patterns.md)** when implementing node borders, error trails, trail resets, and toggle switch CSS.

### 2. Scenario Selector
Left sidebar in a single styled container (solid border, border-radius, padding) grouping the auto-play toggle and all scenario buttons. Each button shows a color-coded status badge (2xx=green, 3xx=blue, 4xx=amber, 5xx=red), short title, and progress bar during auto-play. Buttons use `background: var(--bg-primary)` for consistency with flow nodes. The auto-play toggle is a **slider switch** (track + thumb), not a dot or checkbox.

### 3. Detail Panel
Right side showing: status code badge + title, description paragraph, grid of detail cards (key-value pairs), and timeline of steps with colored dots (success/error/active).

### 4. macOS Terminal
Title bar with red/yellow/green dots. Monospace output area with line-by-line reveal animation. Blinking cursor after final line. Color classes: prompt (green), command (white), dim, success, error, warning, info, highlight.

## Animation Architecture

Three animated sections (flow graph, timeline, terminal) must be driven by the **same timing source** — stage-arrival delays extracted from the flow graph's cumulative delay calculation.

- **Stage arrivals** = flow steps with no connector (after index 0) — the moments each node activates
- **Timeline** maps 1:1 to stage arrivals
- **Terminal** lines spread proportionally across stage-arrival boundaries
- **Packets** animate sequentially (never overlapping) using cumulative delay with idle dwell gaps
- **Auto-play** uses dynamic `setTimeout` chaining (not fixed `setInterval`) with a 3-second post-animation pause before advancing

If you distribute timeline or terminal items evenly across total duration instead of anchoring to stage arrivals, they will drift out of sync with the flow graph.

> **Read [`references/animation-timing.md`](references/animation-timing.md)** when writing `runFlowAnimation`, `runTimelineAnimation`, `runTerminalAnimation`, and auto-play logic. It contains the exact timing system, sync formulas, and code patterns.

## Scenario Data Structure

Each scenario object contains: `code`, `title`, `method`, `endpoint`, `description`, `details` (key-value cards), `timeline` (steps synced to stage arrivals), `terminalLines`, and `flowSequence` (animation steps with `node`, `connector`, `direction`, `status`, `statusClass`, `isError`, `delay`).

**Error scenarios must set `isError: true` on the final/response node** so it gets red error-state styling instead of the default gradient active state.

> **Read [`references/scenario-data.md`](references/scenario-data.md)** when defining the scenario array. It contains a full annotated example and field-by-field documentation.

## Scenarios to Include

Generate at least 6-10 scenarios covering:
- 2-3 success cases (different methods/operations)
- 2-3 client errors (auth, not found, rate limit, etc.)
- 2-3 server errors (500, 503, timeout, etc.)
- 1 redirect or special case

Adapt the specific scenarios to the topic being visualized. For non-HTTP topics, replace status codes with relevant step numbers or states.

## Responsive Design

Include a media query for screens under 800px:
- Stack the scenario section vertically
- Reduce connector widths
- Single-column detail grid

## Checklist Before Delivering

1. Zero TypeScript syntax in `<script>` — scan for `: `, `interface `, `as `, `!.`
2. All CSS animation durations match JS `PACKET_DURATION` constant
3. Timeline steps use stage-arrival delays (1:1 mapping), NOT even distribution
4. Terminal lines spread across stage-arrival boundaries, NOT evenly across total duration
5. Auto-play uses dynamic `setTimeout` chaining (not fixed `setInterval`) with 3s post-animation pause
6. All DOM IDs referenced in JS exist in the HTML
7. Packets animate sequentially, never overlapping
8. `void (expr)` used (with parentheses) for reflow triggers
9. Terminal cursor appears after all lines are revealed
10. Auto-play toggle is a slider switch (track + thumb), not a dot/checkbox
11. Scenario buttons + auto-play enclosed in a single styled container
12. Connector trails persist after packet passes (no fade-out)
13. Error connector steps apply `error-active` class (red trail + ✕ marker); cleared in `clearAnimations()`
14. Connectors start grey (`var(--border)`); trails render at full opacity (`opacity: 1`) and persist until `clearAnimations()` resets them with explicit `style.width = '0%'`
15. Error scenarios set `isError: true` on the final/response node step (not just server/connector steps)

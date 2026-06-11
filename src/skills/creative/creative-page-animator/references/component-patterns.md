# Component CSS & JS Patterns

**Purpose:** Detailed CSS and JavaScript patterns for flow graph components and scenario selector. Read this when implementing flow nodes, connectors, error states, trails, and the toggle switch.

---

## Flow Graph — Error Trails

When a flow step has `isError: true` on a connector, the trail turns red and an "✕" marker appears at the connector center.

```css
/* Error trail — red line with X marker */
.flow-connector.error-active .connector-trail {
  background: linear-gradient(135deg, #ef4444, #dc2626) !important;
}
.flow-connector.error-active::after {
  content: '✕';
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  color: #ef4444;
  font-size: 0.85rem;
  font-weight: 700;
  z-index: 5;
  text-shadow: 0 0 8px rgba(239,68,68,0.6);
}
```

In the flow animation JS, apply the error marker when `isError` is set:
```javascript
if (s.isError && connEl) {
  connEl.classList.add('error-active');
}
```
Remember to clear `error-active` from all connectors in `clearAnimations()`.

---

## Flow Graph — clearAnimations() Trail Reset

Because trails use `animation-fill-mode: forwards`, the final `width: 100%` state persists even after removing CSS classes. You must explicitly reset inline styles:

```javascript
trail.className = 'trail';
trail.style.width = '0%';
trail.style.opacity = '';
void (trail.offsetWidth);
```

---

## Flow Graph — Active Node Gradient Border

Node icons use `var(--bg-primary)` background in their default state. When active, the node gains a gradient border (using `padding-box`/`border-box` trick) while keeping the dark interior:

```css
.flow-node-icon {
  background: var(--bg-primary);
  border: 2px solid var(--border);
}
.flow-node-icon.active {
  border: 2px solid transparent;
  background:
    linear-gradient(var(--bg-primary), var(--bg-primary)) padding-box,
    var(--gradient) border-box;
}
```

Node state animations:
- **Active**: gradient border, pulsing glow, slight scale-up
- **Error**: red border, shake animation, red glow
- **Success**: green border, pop animation, green glow

---

## Scenario Selector — Toggle Switch

The auto-play toggle uses a **toggle switch** (not a dot or checkbox). The switch has a track and thumb that slides right when active, colored with the accent color. Place the label on the left and the switch on the right, separated with `justify-content: space-between`.

```css
.toggle-track {
  width: 38px; height: 20px;
  border-radius: 10px;
  background: var(--border);
  position: relative;
  transition: background 0.3s;
}
.auto-toggle.active .toggle-track { background: var(--accent-end); }
.toggle-thumb {
  width: 16px; height: 16px;
  border-radius: 50%;
  background: var(--text-primary);
  position: absolute; top: 2px; left: 2px;
  transition: transform 0.3s ease;
}
.auto-toggle.active .toggle-thumb { transform: translateX(18px); }
```

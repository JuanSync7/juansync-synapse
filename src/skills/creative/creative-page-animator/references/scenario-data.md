# Scenario Data Structure

**Purpose:** Full schema and annotated example for scenario objects. Read this when defining the scenario array.

---

## Example Scenario Object

```javascript
{
  code: 200,                    // HTTP status or step number
  title: 'OK — Successful GET', // Display title
  method: 'GET',                // Method/action
  endpoint: '/api/v1/resource', // Target
  description: '...',           // Explanation paragraph
  details: [                    // Key-value detail cards
    { label: 'Method', value: 'GET' },
    { label: 'Latency', value: '47ms' },
  ],
  timeline: [                   // Timeline steps (1:1 with stage arrivals)
    { text: '<strong>Step</strong> description', type: 'success' },
  ],
  terminalLines: [              // Terminal output lines
    { content: '<span class="term-prompt">$ </span><span class="term-command">command</span>', delay: 0 },
  ],
  flowSequence: [               // Flow graph animation steps
    { node: 'node-client', status: 'Starting...', statusClass: 'pending', delay: 0 },
    { node: 'node-client', connector: 'conn-1', direction: 'right', status: 'Next...', delay: 300 },
  ],
}
```

## Flow Sequence Step Properties

| Property | Required | Description |
|----------|----------|-------------|
| `node` | Yes | ID of the node to activate |
| `connector` | No | ID of connector to animate packet on |
| `direction` | No | `'right'` or `'left'` for packet travel direction |
| `status` | Yes | Text to show below flow graph |
| `statusClass` | Yes | `'pending'`, `'success'`, `'error'`, `'info'` |
| `isError` | No | Boolean — applies red trail, error packet, error-active connector marker, and error-state on the node |
| `delay` | Yes | Authored delay (used as minimum gap hint) |

## Error Scenario Rule

**Error scenarios must mark the final/response node with `isError: true`** so it gets the red error-state styling (red border, shake, red glow) instead of the default gradient active state. Without this, the response node looks successful even when the scenario is an error.

Example:
```javascript
{ node: 'node-response', status: '✗ 401 Unauthorized', statusClass: 'error', isError: true, delay: 1600 },
```

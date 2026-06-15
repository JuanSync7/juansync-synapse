# web/client

Vite + React 18 + TypeScript + Tailwind CSS v4 client. `src/theme.css` holds the Wet Lab design tokens; `src/App.tsx` is the router shell (left rail + outlet); `src/pages/`, `src/components/`, `src/api/` fill in over slices S4+. Dev server on 5173 proxies `/api` to 8787. Component tests in `test/` (vitest + testing-library + jsdom).

# web

Localhost web interface for browsing and operating this synapse repo — an npm-workspaces monorepo (Express API + Vite/React client). Not a synapse artifact tree; validators ignore it.

## Docs

| Doc | What it covers |
|-----|----------------|
| [`../docs/web/FEATURES.md`](../docs/web/FEATURES.md) | 1:1 capability → feature map (the contract) |
| [`../docs/web/SPEC.md`](../docs/web/SPEC.md) | Functional + non-functional requirements |
| [`../docs/web/DESIGN.md`](../docs/web/DESIGN.md) | Architecture, aesthetic direction, test strategy, slice plan |

## Workspaces

| Directory | What it is |
|-----------|------------|
| [`server/`](server/README.md) | Express + TypeScript API (port 8787) |
| [`client/`](client/README.md) | Vite + React 18 + Tailwind v4 client (port 5173, proxies `/api`) |
| [`shared/`](shared/README.md) | TypeScript types shared by server and client |
| [`e2e/`](e2e/README.md) | Playwright end-to-end specs (placeholder until slice S10) |

## Commands (run from `web/`)

| Command | Does |
|---------|------|
| `npm run dev` | Server (tsx watch) + client (vite) concurrently |
| `npm run build` | Server `tsc` + client `vite build` |
| `npm run lint` | ESLint flat config, zero warnings tolerated |
| `npm test` | Vitest in both workspaces |
| `npm run e2e` | Playwright (no specs yet — passes with no tests) |

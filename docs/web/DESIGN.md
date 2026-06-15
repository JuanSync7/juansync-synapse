# Synapse Web Interface — Design Plan

> Architecture + aesthetic direction for the app specified in [`SPEC.md`](SPEC.md).

## Architecture

```
web/                          (npm workspaces root)
├── package.json              workspaces: ["server", "client"]; scripts: dev/build/lint/test/e2e
├── eslint.config.js          shared typescript-eslint flat config (zero-warning policy)
├── server/                   Express + TS (tsx runtime, vitest + supertest)
│   ├── src/
│   │   ├── index.ts          app bootstrap (port 8787)
│   │   ├── app.ts            express app factory (testable without listen)
│   │   ├── repo.ts           repo-root resolution (SYNAPSE_REPO env → upward search)
│   │   ├── lib/
│   │   │   ├── frontmatter.ts   tolerant YAML-frontmatter parser (skills, memos, tools)
│   │   │   ├── crawler.ts       artifact crawl: synapse/ src/ external/ → ArtifactIndex
│   │   │   ├── evalParse.ts     EVAL.md → criteria groups (EVAL-Exx/Oxx)
│   │   │   ├── mdTable.ts       registry markdown-table parse/serialize + shape guard
│   │   │   ├── memos.ts         memo crawl + executed-flag PATCH (byte-preserving)
│   │   │   ├── scriptsMeta.ts   scripts/@frontmatter + docs/cli pairing
│   │   │   ├── pipeline.ts      SKILLS_REGISTRY.yaml parse
│   │   │   ├── claudeSession.ts spawn/resume claude -p stream-json; event bus
│   │   │   └── safeExec.ts      allow-listed read-only command runner
│   │   └── routes/           artifacts, registry, taxonomy, memos, sessions, runs, scripts, pipeline
│   └── test/                 vitest: unit per lib + integration (supertest, real repo)
├── client/                   Vite + React + TS + Tailwind v4 + React Router
│   ├── src/
│   │   ├── main.tsx, App.tsx (router + shell)
│   │   ├── theme.css         design tokens (CSS variables) + Tailwind
│   │   ├── api/client.ts     typed fetch wrapper (shared types from server via web/shared)
│   │   ├── components/       Markdown, EvalPanel, LayerBadge, StatusChip, DataTable,
│   │   │                     TerminalPane, ChatStream, EditorPane, Card
│   │   └── pages/            Landing, ArtifactList, ArtifactDetail, Registry, Taxonomy,
│   │                         Framework, Memos, Brainstorm, CreatorRun, Scripts
│   └── test/                 vitest + @testing-library/react component tests
├── shared/                   TS types shared by both (Artifact, Memo, RunStatus, …)
└── e2e/                      Playwright specs (one per surface) + fixtures
```

Key decisions:

1. **Crawl-at-request, no database.** The repo *is* the database (registries/taxonomies
   are authoritative files). A 60-second in-memory cache keyed by mtime keeps lists fast
   without staleness risk. This is what makes the app work unchanged for any adopter
   overlay (NFR4).
2. **Headless claude = `claude -p --output-format stream-json`** spawned with
   `execFile`-style arg arrays, cwd = repo root, so skills, memory, and `.brainstorms/`
   behave exactly as a CLI invocation. `--resume <sessionId>` powers multi-turn chat.
   The driver is one module (`claudeSession.ts`) reused by brainstorm chat (FR6) and
   creator runs (FR7); tests inject a fake binary via `CLAUDE_BIN` env.
3. **Writes are scalpel-shaped.** Registry/taxonomy PUT = whole-file with parse guard;
   memo PATCH = frontmatter-only line edit preserving the body byte-for-byte. Both go
   through one `safeWrite()` with the path allow-list (NFR5).
4. **SSE over WebSocket** for streams — one-directional output fits EventSource, no
   extra dependency, trivially proxied by Vite.

## Aesthetic direction — minimalist modern tech (light)

A clean, light, product-grade UI in the Stripe/Linear idiom: white canvas, generous
whitespace, soft borders and shadows, one cool accent. Precise and instrumented, but
unfussy — the artifacts are the content, the chrome stays out of the way.

> The token *names* in `theme.css` are a stable Tailwind contract reused across every
> page (`bg-ink`, `text-synapse`, `font-display`, …); a redesign remaps their *values*
> and shifts the whole look centrally. The names are legacy: `ink` = page canvas,
> `surface` = card, `synapse` = the accent, `signal` = amber, `membrane` = red.

- **Palette** (CSS variables): canvas `ink` `#FFFFFF`; card `surface` `#F7F8FA`; rule
  lines `#E6E8EC`; text `#1A1D21` / muted `#6B7280`. Accent: **violet `#5B5BD6`**
  (`synapse` — active states, slugs, links, primary actions). State only: **amber
  `#B45309`** (`signal` — draft/pending/warning) and **red `#DC2626`** (`membrane` —
  errors). One dark surface, `code` `#14161A`, is kept dark for code blocks and terminal
  panes (docs-style contrast on the light UI).
- **Typography**: **Inter** for everything (display + body), tuned with stylistic-set
  features; `ui-monospace`/**JetBrains Mono** for slugs, frontmatter, tables, and code.
  Slugs are always mono + violet — they are the framework's atoms and read like
  identifiers. (No serif display; the previous Fraunces/Spline stack is retired.)
- **Section divider**: a quiet 1px hairline rule under page titles and between sections.
  (The former animated "dendrite" node-and-pulse motif is stripped per the minimalist
  brief; the `DendriteRule` component remains as the plain-rule API.)
- **Layout**: sticky left rail (sans nav grouped into Library / Catalog / Operate, a
  violet-pill active state, artifact-class counts as small muted numerals, a wordmark with
  a violet "S" mark), content column max-w-5xl, generous vertical rhythm; detail pages use
  an asymmetric two-column split (body 2/3, frontmatter+eval rail 1/3). Landing leads with
  a clean wordmark hero and soft-shadow count tiles.
- **Motion**: staggered fade-rise on list mount (CSS animation-delay) and a subtle
  card lift on hover; nothing gratuitous. Honors `prefers-reduced-motion`.
- **Badges**: layer (`base` = violet outline, `add-on` = amber outline, `external` =
  grey outline), status chips (stable solid / draft hollow), audience badges on
  script cards.

## Test strategy

- **Unit** (server): frontmatter, mdTable shape-guard round-trip, evalParse, memos
  byte-preservation, scriptsMeta, pipeline parse — pure functions, fixture strings.
- **Integration** (server): supertest against the app wired to the *real repo checkout*
  — asserts e.g. `GET /api/artifacts?class=skill` includes `docs-spec-writer`,
  registry PUT round-trips on a temp copy, claude session driver against a fake
  `CLAUDE_BIN` script.
- **Component** (client): EvalPanel parses groups, Registry editor dirty/save flow,
  ChatStream renders SSE chunks (mocked EventSource).
- **E2E/system** (Playwright): real server + built client over the real repo —
  one spec per surface (browse, detail+eval, registry edit (on temp-copied file),
  taxonomy view, framework, memos toggle, scripts panel + validate run, brainstorm
  page with fake CLAUDE_BIN, creator run with fake CLAUDE_BIN).
- **Ralph loop exit bar**: `npm run lint` (0 warnings) + `npm test` + `npm run e2e`
  all green **and** `./cortex validate` still 0/0.

## Slice plan (one subagent per slice)

S2 scaffold → S3 crawler+artifacts API → S4 shell+browse+eval → then S5 registry/
taxonomy, S6 framework+scripts, S7 memos (parallelizable: disjoint files; route
registration conflicts resolved by orchestrator) → S8 claude driver+brainstorm →
S9 creator run → S10 e2e + ralph loop.

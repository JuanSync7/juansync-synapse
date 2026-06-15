# Synapse Web Interface — Specification

> Requirements for the web app defined by [`FEATURES.md`](FEATURES.md). Architecture in
> [`DESIGN.md`](DESIGN.md).

## Functional requirements

### FR1 — Artifact browsing (F1–F5, F18, F20)
- FR1.1 `GET /api/artifacts?class={skill|agent|protocol|tool|pathway}` returns every
  artifact of that class found by crawling `synapse/`, `src/`, `external/` at request
  time (no build-time snapshot). Each item: slug, class, layer (`base|addon|external`),
  frontmatter (verbatim), path, has_eval flag.
- FR1.2 `GET /api/artifacts/:class/:slug` returns the artifact body (raw markdown),
  parsed frontmatter, companion file tree (references/, templates/, schemas, cli),
  EVAL.md raw + parsed criteria, and registry row if present.
- FR1.3 Client routes `/skills`, `/agents`, `/protocols`, `/tools`, `/pathways`:
  filterable/searchable lists (domain, status, layer, free text) + detail pages with
  rendered markdown. Personas appear under `/skills` with an empty-state when none exist.
- FR1.4 Pathway detail resolves `inherits:` and lists the flattened synapse set.

### FR2 — EVAL display (F6)
- FR2.1 Every artifact detail page shows an Eval panel: criteria parsed into
  `EVAL-Exx` / `EVAL-Oxx` checklist groups; raw markdown viewable; artifacts whose
  EVAL.md is missing or a placeholder are flagged visibly.

### FR3 — Registry & taxonomy editing (F7–F9)
- FR3.1 `GET /api/registry` lists registry files; `GET /api/registry/:name` returns
  parsed table rows + raw markdown; `PUT /api/registry/:name` writes the full raw
  markdown back (with a same-shape guard: must still parse as a table with the original
  column set).
- FR3.2 Same trio for `/api/taxonomy/:name` covering `taxonomy/*.md` **and**
  `registry/*_VOCABULARY.md` (vocabularies are taxonomy-class editables).
- FR3.3 Writes are atomic (temp file + rename) and restricted to an allow-listed set of
  paths — the server must never write outside `registry/` and `taxonomy/`(+vocab files)
  for these endpoints.
- FR3.4 Client: `/registry` and `/taxonomy` pages with table view, status chips,
  cross-links to artifact pages, and an edit mode (textarea/markdown editor + save +
  dirty indicator + server-error surfacing).

### FR4 — Framework page (F10–F11)
- FR4.1 `/framework` shows only `synapse/`-layer items grouped by class, with the
  creation-lifecycle order (brainstormer → creator → eval-writer → improver →
  gatekeeper → suite-validator) explained.
- FR4.2 Pipeline section renders `synapse/SKILLS_REGISTRY.yaml`: stages with
  input/output types, `requires_*` edges, and the named presets.
  `GET /api/pipeline` serves the parsed YAML.

### FR5 — Memo system (F13)
- FR5.1 `GET /api/memos` crawls `.brainstorms/**/[*-]memo-*.md` and
  `**/change_requests/*.md`; each memo: id (path-derived), title, session/source,
  artifact type, `executed` boolean (frontmatter `executed:`; absent ⇒ false), created
  date, body.
- FR5.2 `PATCH /api/memos/:id` toggles `executed:` in the memo's frontmatter (adding
  the field if missing), preserving the rest of the file byte-for-byte.
- FR5.3 Client `/memos`: board grouped by brainstorm session / CR directory, executed
  vs pending filters, detail drawer with rendered memo, execute-toggle, and a
  "Run creator with this memo" button (→ FR7).

### FR6 — Headless brainstorm chat (F12)
- FR6.1 `POST /api/sessions` spawns `claude -p` (`--output-format stream-json`,
  `--verbose`, cwd = repo root) with the user's first message prefixed by the skill
  invocation (`/synapse-router-artifact-brainstormer …`). Response: session id.
- FR6.2 `GET /api/sessions/:id/events` streams assistant/tool events via SSE;
  `POST /api/sessions/:id/messages` continues the conversation via
  `claude -p --resume <claude-session-id>`.
- FR6.3 Client `/brainstorm`: chat transcript (streamed), input box, session list
  (resume past sessions), and a live link to memos created during the session
  (memo board refresh).
- FR6.4 Session metadata persisted server-side under `web/.sessions/` (gitignored) so
  the page survives reloads.

### FR7 — Creator end-to-end run (F14–F15)
- FR7.1 `POST /api/runs/creator` body `{memoId}`: spawns a headless claude session
  instructed to run `/synapse-router-artifact-creator` against that memo file and
  proceed end-to-end (artifact + EVAL + registry + READMEs). Streams progress like FR6.
- FR7.2 On completion the server runs `bash scripts/validate.sh` and returns its
  output + exit code; the run page shows a verification panel: validation result,
  detected new/changed artifact paths (git status diff), links to the new artifact page.
- FR7.3 Runs are recorded under `web/.sessions/runs/` with status
  (`running|succeeded|failed`).

### FR8 — Scripts control panel (F16–F17)
- FR8.1 `GET /api/scripts` parses `scripts/*.sh` comment frontmatter (@name,
  @description, @audience, @action, @scope) and pairs each with its `docs/cli/<name>.md`
  doc when present; also lists the cortex python-CLI command groups (pin/drift/doctor/
  clerk/telemetry) from their docs.
- FR8.2 Client `/scripts`: card grid with audience/action badges, usage snippet,
  "where/when to use" prose from docs — never raw source code.
- FR8.3 An allow-listed set of read-only commands is executable from the UI with output
  shown in a terminal-style panel: `validate`, `list`, `available`, `doctor`,
  `pin status`, `pathway list`. Everything else is documentation-only.

### FR9 — Landing (F19)
- FR9.1 `/` explains the framework (base / add-on / external layers), shows live counts
  per artifact class (from the crawler), and links to the GitHub repo and the docs.

## Non-functional requirements

- NFR1 Stack: Vite + React 18 + TypeScript strict + Tailwind CSS v4; backend
  Express + TypeScript on Node ≥20; npm workspaces under `web/`.
- NFR2 ESLint (typescript-eslint flat config) passes with zero warnings
  (`--max-warnings 0`) across client and server.
- NFR3 Tests: Vitest unit + integration (supertest against the real repo checkout);
  Playwright e2e covering each surface; all green in `npm test` / `npm run e2e`.
- NFR4 The server takes the repo root from `SYNAPSE_REPO` env (default: resolved
  upward from `web/`), so the same app serves any adopter checkout.
- NFR5 Safety: filesystem writes restricted to allow-listed paths (FR3.3, FR5.2);
  command execution restricted to the FR8.3 allow-list; child processes killed on
  session abort; no shell-interpolated user input (use execFile/spawn arg arrays).
- NFR6 Localhost single-user; default ports 5173 (client dev) / 8787 (API);
  `npm run dev` runs both with proxy.
- NFR7 Adding `web/` must not break framework validation: `./cortex validate` stays
  0 errors / 0 warnings (web/ is not a synapse artifact tree; ensure validators ignore
  it, and directory README convention is satisfied).

# web/server

Express + TypeScript API serving the repo at runtime (crawl, never hardcode). Entry `src/index.ts` (PORT, default 8787); `src/app.ts` is the testable app factory; `src/repo.ts` resolves the repo root (`SYNAPSE_REPO` env → upward search). `src/lib/` and `src/routes/` are placeholders filled by slices S3+. Tests in `test/` (vitest + supertest).

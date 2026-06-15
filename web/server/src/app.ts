import express from 'express';
import type { Express } from 'express';
import type { ArtifactClass } from '../../shared/types';
import { artifactsRouter } from './routes/artifacts';
import { frameworkRouter } from './routes/framework';
import { memosRouter } from './routes/memos';
import { pipelineRouter } from './routes/pipeline';
import { registryRouter } from './routes/registry';
import { runsRouter } from './routes/runs';
import { scriptsRouter } from './routes/scripts';
import { sessionsRouter } from './routes/sessions';
import { taxonomyRouter } from './routes/taxonomy';

/** Classes the artifact routes (slice S3) will serve. */
export const ARTIFACT_CLASSES: readonly ArtifactClass[] = [
  'skill',
  'agent',
  'protocol',
  'tool',
  'pathway',
];

/**
 * Express app factory — testable without listening (DESIGN.md).
 * Route modules under src/routes/ register here in later slices.
 */
export function createApp(repoRoot: string): Express {
  const app = express();
  app.use(express.json());

  app.get('/api/health', (_req, res) => {
    res.json({ ok: true, repoRoot });
  });

  app.use('/api/artifacts', artifactsRouter(repoRoot));
  app.use('/api/pipeline', pipelineRouter(repoRoot));
  app.use('/api/registry', registryRouter(repoRoot));
  app.use('/api/taxonomy', taxonomyRouter(repoRoot));
  app.use('/api/framework', frameworkRouter(repoRoot));
  app.use('/api/memos', memosRouter(repoRoot));
  app.use('/api/scripts', scriptsRouter(repoRoot));
  app.use('/api/sessions', sessionsRouter(repoRoot));
  app.use('/api/runs', runsRouter(repoRoot));

  return app;
}

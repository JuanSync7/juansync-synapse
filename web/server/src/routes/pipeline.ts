import fs from 'node:fs';
import path from 'node:path';
import { Router } from 'express';
import type { Router as ExpressRouter } from 'express';
import { loadPipeline } from '../lib/pipeline';

/** GET /api/pipeline — parsed synapse/SKILLS_REGISTRY.yaml (FR4.2). */
export function pipelineRouter(repoRoot: string): ExpressRouter {
  const router = Router();

  router.get('/', (_req, res) => {
    const file = path.join(repoRoot, 'synapse', 'SKILLS_REGISTRY.yaml');
    if (!fs.existsSync(file)) {
      res.status(404).json({ error: 'synapse/SKILLS_REGISTRY.yaml not found' });
      return;
    }
    res.json(loadPipeline(file));
  });

  return router;
}

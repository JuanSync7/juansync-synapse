// Scripts control panel API (FR8). GET serves the parsed scripts/*.sh inventory
// plus the cortex python-CLI command groups; POST /run executes ONLY the
// allow-listed read-only commands through safeExec (execFile, no shell, NFR5).
// The allow-list gate lives in safeExec.runAllowed — the route maps a refusal
// to a 400 with a clear message rather than ever spawning a forbidden command.
import { Router } from 'express';
import type { Router as ExpressRouter } from 'express';
import { collectScriptsMeta } from '../lib/scriptsMeta';
import { isAllowed, runAllowed } from '../lib/safeExec';

export function scriptsRouter(repoRoot: string): ExpressRouter {
  const router = Router();

  // GET /api/scripts — { scripts, cliCommands }.
  router.get('/', (_req, res) => {
    res.json(collectScriptsMeta(repoRoot));
  });

  // POST /api/scripts/run — run an allow-listed read-only command.
  router.post('/run', (req, res) => {
    const body = (req.body ?? {}) as { command?: unknown; args?: unknown };
    const command = typeof body.command === 'string' ? body.command : '';
    const args = Array.isArray(body.args) ? body.args.map((a) => String(a)) : [];

    if (!isAllowed(command, args)) {
      res.status(400).json({
        error:
          `Command not allowed: \`${command} ${args.join(' ')}\`. ` +
          'Only read-only cortex commands are runnable: validate, list, available, ' +
          'doctor, pin status, pathway list.',
      });
      return;
    }

    runAllowed(repoRoot, command, args)
      .then((result) => res.json(result))
      .catch((err: unknown) => {
        res.status(400).json({ error: err instanceof Error ? err.message : 'Run failed.' });
      });
  });

  return router;
}

import { createApp } from './app';
import { resolveRepoRoot } from './repo';

const port = Number(process.env.PORT ?? 8787);
const repoRoot = resolveRepoRoot();

createApp(repoRoot).listen(port, () => {
  console.log(`synapse-web server on http://localhost:${port} (repo: ${repoRoot})`);
});

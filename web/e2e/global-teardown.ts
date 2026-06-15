// e2e global teardown — remove the temp-copy sandbox repo built in the config.
import { teardownSandbox } from './lib/sandbox';

export default function globalTeardown(): void {
  const repo = process.env.SYNAPSE_E2E_SANDBOX;
  if (repo) teardownSandbox(repo);
}

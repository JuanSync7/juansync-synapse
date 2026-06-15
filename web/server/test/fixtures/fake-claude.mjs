#!/usr/bin/env node
// Fake `claude` binary for tests (NEVER spawns the real CLI — fast + offline).
// Emits a canned stream-json transcript: a system init line carrying a
// session_id, an assistant text message, a tool_use block, a tool_result, then
// a final result line. Also dumps its own argv to FAKE_CLAUDE_ARGV_OUT (if set)
// so a test can assert spawn args (e.g. that --resume <id> is passed).
import fs from 'node:fs';

const argv = process.argv.slice(2);

const argvOut = process.env.FAKE_CLAUDE_ARGV_OUT;
if (argvOut) {
  fs.writeFileSync(argvOut, JSON.stringify(argv), 'utf8');
}

// Optional behaviour knobs so one fixture covers several scenarios.
const sessionId = process.env.FAKE_CLAUDE_SESSION_ID || 'fake-session-0001';
const isError = process.env.FAKE_CLAUDE_IS_ERROR === '1';
// FAKE_CLAUDE_HANG=1 keeps the process alive so killSession has something to kill.
const hang = process.env.FAKE_CLAUDE_HANG === '1';

// FAKE_CLAUDE_CREATE_FILE=<relpath> makes the fake actually write a file in its
// cwd (the repoRoot), so a creator-run test sees the file appear in `git status
// --porcelain` — exercising the real git-diff verification path without a real
// claude. Path is created relative to cwd; dirs are made as needed.
const createFile = process.env.FAKE_CLAUDE_CREATE_FILE;
if (createFile) {
  const abs = createFile;
  const dir = abs.includes('/') ? abs.slice(0, abs.lastIndexOf('/')) : '';
  if (dir) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(abs, '# created by fake claude\n', 'utf8');
}

const lines = [
  { type: 'system', subtype: 'init', session_id: sessionId, cwd: process.cwd() },
  {
    type: 'assistant',
    message: {
      role: 'assistant',
      content: [{ type: 'text', text: 'Hello from fake claude.' }],
    },
  },
  {
    type: 'assistant',
    message: {
      role: 'assistant',
      content: [
        { type: 'tool_use', id: 'toolu_1', name: 'Read', input: { file_path: '/tmp/x' } },
      ],
    },
  },
  {
    type: 'user',
    message: {
      role: 'user',
      content: [{ type: 'tool_result', tool_use_id: 'toolu_1', content: 'file body' }],
    },
  },
  {
    type: 'result',
    subtype: isError ? 'error' : 'success',
    session_id: sessionId,
    is_error: isError,
    result: 'Done from fake claude.',
  },
];

for (const line of lines) {
  process.stdout.write(`${JSON.stringify(line)}\n`);
}

if (hang) {
  // Stay alive until killed — lets a test exercise killSession / abort.
  setInterval(() => {}, 1000);
} else {
  process.exit(0);
}

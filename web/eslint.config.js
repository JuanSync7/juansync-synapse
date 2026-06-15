// Shared flat config for the synapse-web workspaces (zero-warning policy, NFR2).
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';

export default tseslint.config(
  {
    ignores: [
      '**/dist/**',
      '**/node_modules/**',
      '**/.sessions/**',
      '**/coverage/**',
      // Downloaded Chrome-for-Testing binary + e2e artifacts — not lint source.
      'chrome/**',
      'test-results/**',
      'playwright-report/**',
      'blob-report/**',
      // Runtime test fixture (a fake `claude` binary), not lib source.
      'server/test/fixtures/**',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['client/src/**/*.{ts,tsx}', 'client/test/**/*.{ts,tsx}'],
    plugins: { 'react-hooks': reactHooks },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'error',
    },
  },
);

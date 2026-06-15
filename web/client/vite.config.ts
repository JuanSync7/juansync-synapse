/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8787',
    },
  },
  // `vite preview` (used by the e2e harness) does NOT inherit `server.proxy`,
  // so it needs its own proxy block — both forward /api to the API on 8787.
  preview: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8787',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true, // lets @testing-library/react auto-cleanup between tests
  },
});

import { defineConfig } from 'vitest/config';

// On Windows a shell can spell the drive letter `c:` (VS Code's terminal does) or `C:`.
// Vitest's worker loads its runner from the spelling the command started in, while a
// test file's `import 'vitest'` resolves to `C:`, so a run from `c:` gets two runners
// and every file fails with no test run. Pointing `vitest` at the copy under the working
// directory, which `npm run check` and `npm test` start in, keeps one runner.
// `process` is typed here rather than through @types/node, which the app doesn't need.
const { process: node } = globalThis as unknown as { process: { platform: string; cwd(): string } };
const oneRunner =
  node.platform === 'win32'
    ? [{ find: /^vitest$/, replacement: `${node.cwd()}/node_modules/vitest/dist/index.js` }]
    : [];

export default defineConfig({
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  test: {
    include: ['test/**/*.test.ts'],
    environment: 'node',
    alias: oneRunner,
  },
});

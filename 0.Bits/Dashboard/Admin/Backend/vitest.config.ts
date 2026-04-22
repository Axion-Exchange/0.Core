import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/__tests__/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'text-summary'],
      include: ['src/lib/**', 'src/services/**', 'src/middleware/**'],
      exclude: ['src/**/*.d.ts', 'src/workers/**'],
    },
    testTimeout: 10000,
  },
});

import type { Config } from '@jest/types';
import nextJest from 'next/jest.js';

const createJestConfig = nextJest({
  // Path to Next.js app so Jest can load next.config.js and .env files
  dir: './',
});

const config: Config.InitialProjectOptions = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  testMatch: ['<rootDir>/__tests__/**/*.{test,spec}.{ts,tsx}'],
};

export default createJestConfig(config);

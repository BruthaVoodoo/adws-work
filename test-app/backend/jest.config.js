/** @type {import('jest').Config} */
export default {
  testEnvironment: 'node',
  collectCoverage: false,
  coverageDirectory: 'coverage',
  coverageProvider: 'v8',
  testMatch: ['**/tests/**/*.test.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  transform: {},
  transformIgnorePatterns: [],
};

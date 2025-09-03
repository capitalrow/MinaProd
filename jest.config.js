module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/tests/**/*.test.js'],
  collectCoverage: true,
  coverageDirectory: 'tests/results/coverage',
  collectCoverageFrom: [
    'static/js/**/*.js',
    '!static/js/**/*.min.js',
    '!**/node_modules/**'
  ],
  setupFilesAfterEnv: ['<rootDir>/tests/setup/jest-setup.js'],
  testTimeout: 30000
};
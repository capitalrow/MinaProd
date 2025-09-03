/**
 * Jest Setup Configuration
 * Global test setup for unit and integration tests
 */

// Extend Jest matchers
expect.extend({
  toBeWithinRange(received, floor, ceiling) {
    const pass = received >= floor && received <= ceiling;
    if (pass) {
      return {
        message: () => `expected ${received} not to be within range ${floor} - ${ceiling}`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be within range ${floor} - ${ceiling}`,
        pass: false,
      };
    }
  },
});

// Global test configuration
global.testConfig = {
  timeout: 30000,
  baseURL: 'http://localhost:5000',
  retryCount: 2
};

// Mock console.warn for cleaner test output
const originalWarn = console.warn;
console.warn = (...args) => {
  if (!args[0]?.includes('deprecated') && !args[0]?.includes('ExperimentalWarning')) {
    originalWarn(...args);
  }
};

console.log('🧪 Jest setup completed for MINA E2E tests');
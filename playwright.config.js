// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './tests/e2e',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html', { outputFolder: 'tests/results/html-report' }],
    ['json', { outputFile: 'tests/results/test-results.json' }],
    ['junit', { outputFile: 'tests/results/test-results.xml' }]
  ],
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:5000',
    
    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',
    
    /* Screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Video recording */
    video: 'retain-on-failure',
    
    /* Global timeout for each test */
    timeout: 30000,
    
    /* Global navigation timeout */
    navigationTimeout: 10000,
    
    /* Global action timeout */
    actionTimeout: 5000,
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // Grant microphone permissions for audio testing
        permissions: ['microphone'],
        // Allow insecure contexts for local testing
        ignoreHTTPSErrors: true
      },
    },
    
    {
      name: 'firefox',
      use: { 
        ...devices['Desktop Firefox'],
        permissions: ['microphone'],
        ignoreHTTPSErrors: true
      },
    },

    {
      name: 'webkit',
      use: { 
        ...devices['Desktop Safari'],
        permissions: ['microphone'],
        ignoreHTTPSErrors: true
      },
    },

    /* Mobile Testing */
    {
      name: 'Mobile Chrome',
      use: { 
        ...devices['Pixel 5'],
        permissions: ['microphone'],
        ignoreHTTPSErrors: true
      },
    },
    {
      name: 'Mobile Safari',
      use: { 
        ...devices['iPhone 12'],
        permissions: ['microphone'],
        ignoreHTTPSErrors: true
      },
    },
  ],

  /* Run your local dev server before starting the tests */
  webServer: {
    command: 'python -m gunicorn --bind 0.0.0.0:5000 --reuse-port main:app',
    port: 5000,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },

  /* Global setup and teardown */
  globalSetup: require.resolve('./tests/setup/global-setup.js'),
  globalTeardown: require.resolve('./tests/setup/global-teardown.js'),

  /* Test output directories */
  outputDir: 'tests/results/test-output',
  
  /* Maximum test time */
  timeout: 60000,
  
  /* Global expect timeout */
  expect: {
    timeout: 10000,
  },
});
// Playwright Configuration for E2E Testing
module.exports = {
  testDir: '../e2e',
  timeout: 60000, // 60 seconds per test
  expect: { timeout: 10000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 2,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }]
  ],
  use: {
    baseURL: 'http://localhost:5000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // Audio/video permissions
    permissions: ['microphone', 'camera'],
    // Mobile simulation for Pixel 9 Pro
    ...require('playwright/lib/deviceDescriptors')['Pixel 5'],
  },
  projects: [
    {
      name: 'chromium-desktop',
      use: { ...require('playwright/lib/deviceDescriptors')['Desktop Chrome'] },
    },
    {
      name: 'chromium-mobile',
      use: { 
        ...require('playwright/lib/deviceDescriptors')['Pixel 5'],
        // Custom Pixel 9 Pro simulation
        viewport: { width: 1344, height: 2992 },
        userAgent: 'Mozilla/5.0 (Linux; Android 16; Pixel 9 Pro) AppleWebKit/537.36'
      },
    },
    {
      name: 'firefox',
      use: { ...require('playwright/lib/deviceDescriptors')['Desktop Firefox'] },
    },
  ],
  webServer: {
    command: 'cd .. && python -m flask run --host=0.0.0.0 --port=5000',
    port: 5000,
    timeout: 30000,
    reuseExistingServer: !process.env.CI,
  },
};
// @ts-check
const { defineConfig, devices } = require('@playwright/test')

module.exports = defineConfig({
  testDir: '.',
  timeout: 30000,
  retries: 1,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    cwd: '../../client',
    port: 5173,
    reuseExistingServer: true,
    timeout: 60000,
  },
})

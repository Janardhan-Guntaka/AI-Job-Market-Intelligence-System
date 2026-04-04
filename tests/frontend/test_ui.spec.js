const { test, expect } = require('@playwright/test')

test.describe('AI Job Market Intelligence System', () => {
  test('dashboard page loads and shows KPI cards', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveTitle(/AI Job Market Intelligence/)
    // Sidebar present
    await expect(page.locator('#sidebar')).toBeVisible()
    // Navbar present
    await expect(page.locator('#navbar')).toBeVisible()
    // KPI cards
    await expect(page.locator('#kpi-total-jobs')).toBeVisible({ timeout: 15000 })
    await expect(page.locator('#kpi-avg-salary')).toBeVisible()
    await expect(page.locator('#kpi-remote-jobs')).toBeVisible()
    await expect(page.locator('#kpi-categories')).toBeVisible()
  })

  test('sidebar navigation links are visible', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page.locator('#nav-dashboard')).toBeVisible()
    await expect(page.locator('#nav-job-explorer')).toBeVisible()
    await expect(page.locator('#nav-analytics')).toBeVisible()
  })

  test('navigates to Job Explorer page', async ({ page }) => {
    await page.goto('/dashboard')
    await page.click('#nav-job-explorer')
    await expect(page).toHaveURL(/\/jobs/)
    await expect(page.locator('#job-explorer')).toBeVisible()
    await expect(page.locator('#job-search')).toBeVisible()
  })

  test('job cards render on Job Explorer', async ({ page }) => {
    await page.goto('/jobs')
    // Wait for loading to finish
    await expect(page.locator('#jobs-loading')).not.toBeVisible({ timeout: 15000 })
    const cards = page.locator('[data-testid="job-card"]')
    await expect(cards.first()).toBeVisible({ timeout: 15000 })
    const count = await cards.count()
    expect(count).toBeGreaterThan(0)
  })

  test('job search filters results', async ({ page }) => {
    await page.goto('/jobs')
    await expect(page.locator('#jobs-loading')).not.toBeVisible({ timeout: 15000 })
    await page.fill('#job-search', 'Engineer')
    await page.waitForTimeout(800)
    // Should still have results or empty state (no error)
    const errorEl = page.locator('text=Error')
    await expect(errorEl).not.toBeVisible()
  })

  test('filter panel toggles open', async ({ page }) => {
    await page.goto('/jobs')
    await page.click('#toggle-filters')
    await expect(page.locator('#filter-category')).toBeVisible()
    await expect(page.locator('#filter-remote')).toBeVisible()
    await expect(page.locator('#filter-experience')).toBeVisible()
  })

  test('navigates to Analytics page', async ({ page }) => {
    await page.goto('/dashboard')
    await page.click('#nav-analytics')
    await expect(page).toHaveURL(/\/analytics/)
    await expect(page.locator('#analytics')).toBeVisible()
  })

  test('analytics charts render', async ({ page }) => {
    await page.goto('/analytics')
    await expect(page.locator('#analytics-loading')).not.toBeVisible({ timeout: 15000 })
    await expect(page.locator('#analytics')).toBeVisible()
    await expect(page.locator('#skills-table')).toBeVisible({ timeout: 15000 })
  })

  test('pagination works on job explorer', async ({ page }) => {
    await page.goto('/jobs')
    await expect(page.locator('#jobs-loading')).not.toBeVisible({ timeout: 15000 })
    const pagination = page.locator('#pagination')
    await expect(pagination).toBeVisible()
    const nextBtn = page.locator('#next-page')
    if (await nextBtn.isEnabled()) {
      await nextBtn.click()
      await page.waitForTimeout(500)
      const prevBtn = page.locator('#prev-page')
      await expect(prevBtn).toBeEnabled()
    }
  })

  test('root redirects to dashboard', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL(/\/dashboard/)
  })
})

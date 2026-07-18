import { test, expect } from '@playwright/test'
import { mockTrip, setupApiMocks } from './mocks'

const trips = Array.from({ length: 10 }, (_, index) => ({
  ...mockTrip,
  id: `trip-${index + 1}`,
  title: `目的地 ${index + 1} · 经典初访覆盖线`,
  destination_name: `目的地 ${index + 1}`,
  updated_at: `2026-03-${String(10 - index).padStart(2, '0')}T00:00:00.000Z`,
}))

test('首页展示最近 8 个行程，并可从账户进入所有行程与详情', async ({ page }) => {
  await setupApiMocks(page, { trips })

  await page.goto('/login')
  await page.getByPlaceholder('you@example.com').fill('test@lv.com')
  await page.getByPlaceholder('请输入密码').fill('password123')
  await page.locator('button[type="submit"]').click()
  await page.waitForURL((url) => new URL(url).pathname === '/')

  await expect(page.locator('.home-trips-section .trip-card')).toHaveCount(8)
  await page.getByRole('button', { name: '打开账户菜单' }).click()
  await page.getByRole('button', { name: '所有行程' }).click()
  await page.waitForURL((url) => new URL(url).pathname === '/trips')

  await expect(page.getByRole('heading', { name: '所有行程' })).toBeVisible()
  await expect(page.locator('.all-trips-grid .trip-card')).toHaveCount(10)
  const targetTrip = page.locator('.all-trips-grid .trip-card').filter({ hasText: '目的地 10' })
  await expect(targetTrip).toHaveCount(1)
  await targetTrip.click()
  await page.waitForURL((url) => new URL(url).pathname === '/trips/trip-10')
})

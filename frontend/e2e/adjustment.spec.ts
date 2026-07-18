import { test, expect } from '@playwright/test'
import { setupApiMocks } from './mocks'

async function loginAndOpenTrip(page: Parameters<typeof setupApiMocks>[0]) {
  await page.goto('/login')
  await page.getByPlaceholder('you@example.com').fill('test@lv.com')
  await page.getByPlaceholder('请输入密码').fill('password123')
  await page.locator('button[type="submit"]').click()
  await page.waitForURL((url) => new URL(url).pathname === '/')
  await page.goto('/trips/trip-1')
  await expect(page.getByText('厦门 · 文艺海岸 3 日游')).toBeVisible()
}

test('AI 修改期间展示进度弹窗，成功后清空输入', async ({ page }) => {
  await setupApiMocks(page)
  await loginAndOpenTrip(page)

  const input = page.getByPlaceholder('想调整行程？直接告诉我，比如「把第二天下午改轻松一点」「加一个拍照点」…')
  await input.fill('把第一天下午安排得轻松一点')
  await page.getByRole('button', { name: '提交 AI 行程修改' }).click()

  await expect(page.getByRole('dialog', { name: '正在修改行程' })).toBeVisible()
  await expect(page.getByRole('progressbar', { name: 'AI 修改行程进度' })).toBeVisible()
  await expect(page.getByRole('dialog', { name: '正在修改行程' })).toBeHidden()
  await expect(input).toHaveValue('')
})

test('AI 修改失败时关闭进度弹窗并保留用户输入', async ({ page }) => {
  await setupApiMocks(page, { adjustmentFailure: true })
  await loginAndOpenTrip(page)

  const instruction = '把第一天下午安排得轻松一点'
  const input = page.getByPlaceholder('想调整行程？直接告诉我，比如「把第二天下午改轻松一点」「加一个拍照点」…')
  await input.fill(instruction)
  await page.getByRole('button', { name: '提交 AI 行程修改' }).click()

  await expect(page.getByRole('dialog', { name: '正在修改行程' })).toBeVisible()
  await expect(page.getByRole('dialog', { name: '正在修改行程' })).toBeHidden()
  await expect(input).toHaveValue(instruction)
})

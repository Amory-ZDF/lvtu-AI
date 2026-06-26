/**
 * 6 阶段用户主路径 E2E 测试
 * 灵感 → 决策 → 规划 → 准备 → 执行 → 分享
 *
 * 全部 API 请求被 mock，无需后端即可运行。
 * 前置：通过登录 UI 完成鉴权（设置 user 状态，后续阶段依赖登录态）。
 */
import { test, expect } from '@playwright/test'
import { setupApiMocks } from './mocks'

test.describe('6 阶段用户主路径', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
  })

  test('灵感 → 决策 → 规划 → 准备 → 执行 → 分享 完整旅程', async ({ page }) => {
    // ── 前置：登录（设置鉴权状态，阶段 3+ 依赖） ──
    await page.goto('/login')
    await page.getByPlaceholder('you@example.com').fill('test@lv.com')
    await page.getByPlaceholder('请输入密码').fill('password123')
    await page.locator('button[type="submit"]').click()
    await page.waitForURL((url) => new URL(url).pathname === '/')

    // ── 阶段 1：灵感（首页 → 开始规划） ──
    await test.step('阶段 1：灵感', async () => {
      await expect(page.locator('.home-hero h1')).toContainText('想去旅行')
      await expect(page.getByRole('button', { name: '开始你的行程' })).toBeVisible()
      await page.getByRole('button', { name: '开始你的行程' }).click()
      await page.waitForURL((url) => new URL(url).pathname === '/start')
    })

    // ── 阶段 2：决策（偏好输入 → 目的地推荐） ──
    await test.step('阶段 2：决策', async () => {
      // 验证偏好表单存在
      await expect(page.locator('label', { hasText: '出发地' })).toBeVisible()
      await expect(page.locator('label', { hasText: '预算' })).toBeVisible()
      await expect(page.locator('label', { hasText: '风格偏好' })).toBeVisible()

      // 填写表单
      await page.getByPlaceholder('城市名称').fill('北京')
      await page.locator('select').selectOption({ label: '1000-3000 元' })

      // 提交推荐
      await page.getByRole('button', { name: '为我推荐目的地' }).click()

      // 验证生成进度显示（百分比文案仅在生成态出现）
      await expect(page.getByText(/\d+%/)).toBeVisible({ timeout: 5000 })

      // 等待跳转到目的地推荐页
      await page.waitForURL((url) => new URL(url).pathname === '/destinations', { timeout: 15000 })

      // 验证目的地推荐卡片显示
      await expect(page.getByText('厦门', { exact: true })).toBeVisible()
      await expect(page.getByRole('button', { name: '查看方案对比' }).first()).toBeVisible()
    })

    // ── 阶段 3：规划（目的地选择 → 方案对比 → 生成行程） ──
    await test.step('阶段 3：规划', async () => {
      // 验证目的地卡片存在
      await expect(page.getByText('厦门', { exact: true })).toBeVisible()

      // 点击"查看方案对比"跳转 /comparison
      await page.getByRole('button', { name: '查看方案对比' }).first().click()
      await page.waitForURL((url) => new URL(url).pathname === '/comparison')

      // 验证方案卡片存在
      await expect(page.getByText('文艺海岸慢游')).toBeVisible()
      await expect(page.getByText('打卡精华快线')).toBeVisible()

      // 选择方案 B（点击第二张方案卡片）
      await page.locator('.compare-card').nth(1).click()

      // 点击"选择此方案"生成行程
      await page.getByRole('button', { name: '选择此方案' }).click()
      await page.waitForURL((url) => /\/trips\/trip-1$/.test(new URL(url).pathname), {
        timeout: 15000,
      })
    })

    // ── 阶段 4：准备（行程工作台 → 打包清单） ──
    await test.step('阶段 4：准备', async () => {
      // 等待行程详情加载完成
      await expect(page.getByText('厦门 · 文艺海岸 3 日游')).toBeVisible({ timeout: 10000 })

      // 验证 4 个子 Tab 存在
      await expect(page.locator('.sub-tabs .sub-tab', { hasText: '行程' })).toBeVisible()
      await expect(page.locator('.sub-tabs .sub-tab', { hasText: '穿搭' })).toBeVisible()
      await expect(page.locator('.sub-tabs .sub-tab', { hasText: '机位' })).toBeVisible()
      await expect(page.locator('.sub-tabs .sub-tab', { hasText: '打包' })).toBeVisible()

      // 切换到"打包"Tab
      await page.locator('.sub-tabs .sub-tab', { hasText: '打包' }).click()
      await expect(page.getByText('🎒 打包清单')).toBeVisible()

      // 验证打包清单显示
      await expect(page.getByText('护照', { exact: true })).toBeVisible()

      // 测试添加打包项
      await page.locator('.pack-input').first().fill('充电宝')
      await page.locator('.pack-category .add-btn').first().click()
      await expect(page.getByText('充电宝', { exact: true })).toBeVisible({ timeout: 5000 })

      // 测试勾选打包项
      await page.locator('.pack-item').first().click()
      await expect(page.locator('.pack-item.packed')).toBeVisible({ timeout: 5000 })
    })

    // ── 阶段 5：执行（行程查看 → 行程点操作） ──
    await test.step('阶段 5：执行', async () => {
      // 切换回"行程"Tab
      await page.locator('.sub-tabs .sub-tab', { hasText: '行程' }).click()

      // 验证行程天显示（标题为文本节点）
      await expect(page.getByText('抵达厦门', { exact: true })).toBeVisible()

      // 验证行程点显示（名称渲染在 input 的 value 中，用 toHaveValue 校验）
      const day1 = page.locator('.day-panel').first()
      const firstStopName = day1.locator('.stop-card').first().locator('input[type="text"]').first()
      await expect(firstStopName).toHaveValue('环岛路骑行')

      // 测试添加行程点
      await page.getByRole('button', { name: '添加行程点' }).first().click()
      await expect(
        day1.locator('.stop-card').last().locator('input[type="text"]').first(),
      ).toHaveValue('新行程点', { timeout: 5000 })

      // 测试删除行程点（带确认弹窗）
      await page.locator('.stop-card .stop-act.del').first().click()
      await expect(page.getByText('确定要删除这个行程点吗？')).toBeVisible()
      await page.locator('.detail-panel').getByRole('button', { name: '删除' }).click()
      // 删除首个行程点后，第 1 天仅剩 1 个行程点
      await expect(day1.locator('.stop-card')).toHaveCount(1, { timeout: 5000 })
    })
  })
})

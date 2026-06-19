/**
 * 鉴权流程 E2E 测试
 * - 登录表单 / 注册表单切换
 * - 空表单提交校验提示
 *
 * 校验在前端完成（不触发 API），全部 API 仍被 mock 兜底。
 */
import { test, expect } from '@playwright/test'
import { setupApiMocks } from './mocks'

test.describe('鉴权流程', () => {
  test.beforeEach(async ({ page }) => {
    await setupApiMocks(page)
  })

  test('登录表单存在并可切换到注册表单', async ({ page }) => {
    await page.goto('/login')

    // 验证登录表单存在
    await expect(page.getByPlaceholder('you@example.com')).toBeVisible()
    await expect(page.getByPlaceholder('请输入密码')).toBeVisible()
    await expect(page.locator('.login-tabs .login-tab', { hasText: '登录' })).toBeVisible()

    // 切换到注册 Tab
    await page.locator('.login-tabs .login-tab', { hasText: '注册' }).click()

    // 验证注册表单存在（用户名 + 昵称为注册独有字段）
    await expect(page.getByPlaceholder('字母/数字组合')).toBeVisible()
    await expect(page.getByPlaceholder('展示给其他用户的名字')).toBeVisible()
    // 注册模式下密码占位符变化
    await expect(page.getByPlaceholder('至少 8 位')).toBeVisible()
  })

  test('登录模式空表单提交显示校验提示', async ({ page }) => {
    await page.goto('/login')

    // 不填写任何内容直接提交
    await page.locator('button[type="submit"]').click()

    // 邮箱与密码校验提示
    await expect(page.getByText('请输入有效的邮箱地址')).toBeVisible()
    await expect(page.getByText('密码至少 8 位')).toBeVisible()
  })

  test('注册模式空表单提交显示全部校验提示', async ({ page }) => {
    await page.goto('/login')

    // 切换到注册 Tab
    await page.locator('.login-tabs .login-tab', { hasText: '注册' }).click()

    // 空表单提交
    await page.locator('button[type="submit"]').click()

    // 注册模式额外校验用户名与昵称
    await expect(page.getByText('请输入有效的邮箱地址')).toBeVisible()
    await expect(page.getByText('密码至少 8 位')).toBeVisible()
    await expect(page.getByText('请输入用户名')).toBeVisible()
    await expect(page.getByText('请输入昵称')).toBeVisible()
  })
})

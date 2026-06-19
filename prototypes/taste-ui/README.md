# 旅图 Taste Prototype

## 目标

- 覆盖 Task1 / Task2 要求的双原型工程骨架
- 提供统一目录规范、页面路由、mock 数据、弹窗与状态基线
- 保持与另一套原型相同的信息架构，便于后续继续推进完整页面实现

## 目录

- `src/pages`: 页面路由与页面编排
- `src/components`: 可复用页面片段
- `src/modals`: 统一弹窗容器
- `src/data`: 路由、页面基线、mock 数据、弹窗与状态注册表
- `src/hooks`: 本地演示态管理
- `src/styles`: 主题 token 与全局布局

## 命令

```bash
npm install
npm run dev
npm run lint
npm run format:check
npm run build
```

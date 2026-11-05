# Readlog 读书打卡 — 开发规划输入 Planner brief

> 由 design-to-dev 生成（收尾模式 B）。下一步：“用 planner 按 PLANNER_BRIEF.md 规划 Readlog 的开发”。

## 产品与用户 Product and users

- 一句话：一个很轻的读书打卡工具，记录每天读到第几页，看到进度和连续天数。
- 目标用户：想养成阅读习惯的上班族，睡前在手机上记录。
- 设备：手机优先；桌面端可用。

## 已有成果 What already exists

- 可交互原型：`prototype/`（3 个页面，假数据，无后端）
- 设计规范：`design-tokens/tokens.css`、`design-tokens/tokens.json`（77 项）
- 交接文档：`HANDOFF.md`（页面、流程、组件、交互、6 个待定问题）

## 核心流程 Core flow

1. 添加一本书（书名、总页数、封面颜色）。
2. 在书的详情页记录今天读到第几页。
3. 看到进度、阅读记录和连续天数；读完后进入“读完”分栏。

## 已决定 Decisions (from the designer)

- 品牌色 Moss / Amber / Ink / Paper，标题用 Noto Serif SC 粗体，正文系统字体。
- 主按钮手机通栏；语气温和鼓励。
- 页码校验：必须大于上次、不超过总页数；保存失败保留输入并提示。
- 三个页面的结构和书卡片、进度、分栏样式按原型还原（HANDOFF 中的【确定】项）。

## 约束 Constraints

- 视觉遵循 tokens；【确定】项按原型还原。
- 第一阶段只做个人使用，不做社交。
- 设计师非开发背景，需要能在手机上直接打开试用（建议 PWA 或移动端 Web）。

## 需要规划阶段决定 For planning to decide

| # | 事项 Item | 来自 From | 建议 Suggestion |
| --- | --- | --- | --- |
| 1 | 技术栈：移动端 Web/PWA、小程序还是原生 | 原型为纯 HTML/CSS/JS | 先做 PWA，复用 tokens 与页面结构 |
| 2 | 数据存储：只存本机还是账号同步 | `data.js` 假数据 | M1 本机存储，M2 再加账号同步 |
| 3 | 连续天数规则 | HANDOFF 待定问题 1 | 本地自然日，漏一天清零 |
| 4 | 排序、总页数上限、编辑删除、自动重试、字体加载 | HANDOFF 待定问题 2–6 | 见 HANDOFF 建议列 |

## 数据草图 Data sketch

| 实体 Entity | 字段 Fields | 说明 Notes |
| --- | --- | --- |
| Book | id, title, author?, totalPages, currentPage, cover, createdAt | `cover` 为色板名，后续可换真实封面 |
| ReadingLog | bookId, date, page | 每天每本书一条；页码单调递增 |
| UserStats | streakDays, lastLogDate | 可由 ReadingLog 计算，不必单独存 |

## 建议的第一个里程碑 Suggested first milestone

用真实的本机存储跑通“添加书 → 记录页码 → 书架显示进度”，视觉按 tokens 还原，三个页面的 loading / empty / error 状态保留。

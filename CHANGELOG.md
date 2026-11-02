# Changelog

## 1.0.0 — 2026-11-02

- 首个版本。六步工作流：理解意图（一轮最多五个问题 + 理解卡）→ 提取 design tokens（CSS 变量 + W3C JSON，每项带等级与来源）→ 搭建可交互原型（纯 HTML/CSS/JS，双击打开，假数据，默认/空/加载/报错状态，模拟请求失败）→ 标注【确定】【示意】【待定】（Shift+A 显示）→ 输出 HANDOFF.md → 两种收尾模式（A 交给开发，B 生成 PLANNER_BRIEF.md 衔接 planner）。
- 自带脚本：`tokens_json.py` 从 tokens.css 生成 tokens.json；`check_output.py` 交付前校验产出（两份 tokens 一致、页面与文档一致、标注合法、无原始色值、无远程脚本等）。
- 完整示例 `examples/readlog/`。
- 发布：Agent Skills 标准格式、Claude Code 插件市场清单、WorkBuddy 上传包 `design-to-dev.zip`；`scripts/build.py` 校验三个平台的规则，CI 拦截未更新的上传包。

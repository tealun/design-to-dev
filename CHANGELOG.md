# Changelog

## 1.1.1 — 2026-11-02

修复发布前审计（`docs/99_audits/99_01_release_audit_v1.1.0.md`）的 4 个 P1，每项附回归测试，测试进入 CI：

- F-01 proto-kit：`Proto.go()` 跳到当前地址时也会重新渲染（此前第二次登录失败会让按钮一直停在“登录中”）。
- F-02 `tokens_json.py` / `check_output.py`：出现多个 `:root` 块（如深色模式）或非小写的 token 名时明确报错，不再静默丢弃。
- F-03 `check_output.py` 从 HANDOFF 的“交接对象”读取模式，模式 B 缺少 PLANNER_BRIEF.md 即报错；SKILL.md 第 6 步改为先写 brief 再检查。
- F-04 proto-kit：本地保存的数据带上 `data.js` 指纹，改了假数据后刷新即生效，不再被旧数据覆盖。
- 新增 `tests/`：脚本单元测试与 proto-kit 浏览器测试；CI 运行两者。

## 1.1.0 — 2026-11-02

用一张真实的公开登录页截图实测后迭代（记录见 `docs/02_field-test.md`）：

- 新增 `scripts/palette.py`：从 PNG 截图读取精确色板、指定点颜色和倍率（如 780 px = 390pt 手机 2 倍图），并计算 WCAG 对比度。取色与对比度不再靠目测和心算。
- 流程边界：流程终点没有设计时做一个标【待定】的桩页面；超范围链接加 `data-out`，proto-kit 统一提示“不在本原型范围”。
- 素材：标志、图标、图片未提供文件时用占位并标【待定】，HANDOFF 第 3 节新增素材清单；参考他人产品时不复刻其品牌名与标志。
- 登录、支付类流程只用虚构演示账号，写在 HANDOFF 第 0 节，原型不向网络发送任何输入。
- 从图片测量的字重、字号、间距在元素标注里也只能是【示意】；复制模板后要按设计调整基础组件，并把原型截图与原图并排对比。

## 1.0.0 — 2026-11-02

- 首个版本。六步工作流：理解意图（一轮最多五个问题 + 理解卡）→ 提取 design tokens（CSS 变量 + W3C JSON，每项带等级与来源）→ 搭建可交互原型（纯 HTML/CSS/JS，双击打开，假数据，默认/空/加载/报错状态，模拟请求失败）→ 标注【确定】【示意】【待定】（Shift+A 显示）→ 输出 HANDOFF.md → 两种收尾模式（A 交给开发，B 生成 PLANNER_BRIEF.md 衔接 planner）。
- 自带脚本：`tokens_json.py` 从 tokens.css 生成 tokens.json；`check_output.py` 交付前校验产出（两份 tokens 一致、页面与文档一致、标注合法、无原始色值、无远程脚本等）。
- 完整示例 `examples/readlog/`。
- 发布：Agent Skills 标准格式、Claude Code 插件市场清单、WorkBuddy 上传包 `design-to-dev.zip`；`scripts/build.py` 校验三个平台的规则，CI 拦截未更新的上传包。

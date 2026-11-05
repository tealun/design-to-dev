# Changelog

## design-to-dev 1.4.0 — 2026-11-05

发布方式照搬 tealun-dev-pdca（规划见 `docs/06_release-pipeline-plan.md`）：

- `.claude-plugin/plugin.json` 成为唯一的版本来源；SKILL.md、`workbuddy.yaml` 不再写版本，WorkBuddy 包打包时注入。
- 删除仓库内的 `marketplace.json` 和提交的 `design-to-dev.zip`。插件改由 tealun 市场（`tealun/tealun-plugins`）提供，市场跟踪只由 CI 写入的 `plugin` 分支。
- 新增 `scripts/build_plugin.py`（插件清单、技能、README、仓库导出一致性、发布审计门禁、升版本检查、打包）、`scripts/build_suite.py`（WorkBuddy 全部已知规则与打包）、`scripts/publish_plugin_branch.sh`、`scripts/check_ledger.py`；新增 `release.yml`、`plugin-branch.yml`，`check.yml` 每次推送都校验。
- 新增 `docs/claude-directory-rules.md`、`docs/workbuddy-rules.md`：两个平台的全部已知规则，每条对应本地检查或写明不检查的原因。
- `.gitattributes` 设为 `* -text`；新增 `PRIVACY.md`、图标、`docs/98_evolution/compliance-log.md`。
- 技能：运行 `fetch_fonts.py` 前要先告诉设计师它会把原型用字的集合发给 Google Fonts，同意后才运行；不同意就用系统字体并记为【待定】。
- README 去掉下载后直接执行的命令，安装改为 tealun 市场或从 Release 下载。

按新 agent 试跑（只给 SKILL.md 路径，Linear 登录页截图）的 17 条反馈核实后修改：

- 模板：`.app` 的最大宽度不再把两侧留白算进 `--layout-content-width`，token 就是内容宽度（模板与 Readlog 改为 440px，视觉不变）；忙碌中的主按钮、次按钮保持原色，不再变灰。
- `check_output.py`：区分系统字体与常见网页字体（Inter、Roboto 等）；字体 token 注释写 `fidelity` 时不再警告；字体未打包时给出警告（此前只在有 `fonts.css` 时检查）。
- `palette.py`：新增 `--cols y0-y1` 测水平位置和宽度；`--contrast … --fix` 给出满足 AA 的最近色。
- `tokens_json.py`：注释第三段 `level · source · description` 写成 `$description`。
- 规则补充：他人产品截图即使被称为“我的设计”也按参考处理（布局还原，颜色【示意】，品牌色【待定】）；还原模式下设计稿的字体和字号优先；流程中段未设计的步骤和第三方登录怎么模拟；无数据页面只需默认和报错状态；字体打包的同意放进第一轮提问且不占五个问题；对比截图按原图 1× 尺寸和缩放倍数；标注数量按源码计；HANDOFF 标题可单语；brief 指定的核心流程顺序为【确定】；字体未打包时写明截图用的字体。

## design-to-dev 1.3.1 — 2026-11-03

修复发布前审计 `99_03` 的全部问题（每项先写回归测试，修复前失败、修复后通过）：

- `fetch_fonts.py`：先下载到临时目录，全部成功才替换（P1 F1，没有网络时保留原有字体）；字重先校验（F2）；字体名或字重写错时如实报错（F3）；找不到 tokens.css 链接时下载前就报错（F4）；收集用字按原型内相对路径判断，并包含 CSS（F5）。
- `check_output.py` 视觉检查：间距只查 margin/padding/gap（V1）；支持负值、rem、`grid-gap`、`font:` 简写和 token 解析（V2）；字重解析回退值和关键字（V3）；豁免注释只作用于紧挨着的那条声明（V4）；展示字体解析 token 别名（V5）；检查页面代码里的内联样式（V6）；`https://` 不再让同一行的颜色漏检（N-01）。
- `palette.py`：参数错误给出用法提示而不是异常（N-02、F-07）；半透明颜色需要 `--over` 指定底色并先合成（F-07，此前会误报通过）；按行保存像素，2880×4000 图峰值内存低于 400MB（F-08）。
- proto-kit：URL 中非法的 % 编码显示“页面不存在”，不再白屏（F-05）。
- 文档与数值：token 参考表头（R-8）、动效时长与缓动的分工（C1）、阴影预设（C2）、Readlog 标题 32px（C5）、方向措辞（C6）、触发描述不再匹配“在现有代码库里实现设计”（F-16）。
- Readlog 的基础样式此前没有同步模板，HANDOFF 写的入场序列实际不存在：已同步，并新增测试要求示例与模板一致、浏览器中入场动画确实运行。

## design-to-dev 1.3.0 — 2026-11-03

融合 frontend-design 技能（作者 zxh）的设计方法（规划见 `docs/05_frontend-design-fusion.md`）：

- 视觉方向参考改写：分“还原模式 / 定向模式”；写 CSS 前先做“设计方向说明”（用途、调性、展示与正文字体、主色与强调色、记忆点，用具体的美术指导语言写）；9 种方向菜单（3 种快速选项）；四大支柱（字体、色彩、动效、构图）；离线可用的氛围做法；去 AI 味清单；基准数值。HANDOFF 新增“设计方向”一节。
- 新增 `scripts/fetch_fonts.py`：按原型实际用字从 Google Fonts 下载字体子集打包进 `prototype/fonts/`，原型仍可离线运行（Readlog 中文两套字体共 168KB）。
- 视觉自查分两部分：A 由 `check_output.py` 客观检查（12px 以下字号、非 4px 刻度间距、字重过多、动效没处理减少动效、展示字体为系统默认字体、字体文件缺失），B 写截图观察而不打分，审美定稿留给设计师（审计 R-6 的根因）。
- proto-kit：路由切换时加 `.pk-enter`，模板提供 80ms 间隔的入场序列；刷新（保存后）不重播。
- 模板：头像改用中性色（R-2）、三级文字加深到在凹陷底色上也达标（R-12）、状态文字与标题平衡换行。
- Readlog 按新方法重做：打包 Noto Serif SC / Noto Sans SC，细线代替卡片，书本式封面，页边式 64px 天数，纸张颗粒，入场序列；同时修正审计 R-4、R-5、R-7、R-9、R-10、R-11。
- 实测登录页打包原稿字体 Geist 后，各区块与原稿误差 0–2px。

## design-to-dev 1.2.0 — 2026-11-03

视觉质量（用户反馈：示例与模板“太丑、没有美感”；规划见 `docs/03_visual-quality-plan.md`）：

- 第 1 步必问视觉：索取 VI 规范和 2–3 个视觉参考；都没有时由设计师在“现代精致极简（默认）/ 编辑杂志感 / 温暖手作感”中选择，理解卡写明视觉方向与来源。
- 新增 `references/visual-direction.md`：可检查的审美原则（层级、字体、颜色克制、间距、表面、圆角、控件、列表、占位、状态、图标、动效）、三个方向的 token 预设、12 项视觉自查清单；第 6 步截图后必须逐项自查并在收尾报告结果。
- 默认模板按“现代精致极简”重做：中性灰阶加一个强调色、细边框与轻阴影、紧凑字号阶梯与收紧字距、40px 控件、线性图标、设计过的空/加载/报错状态；token 改名为 `--color-page`（页面）与 `--color-surface`（卡片与输入框）；`{{LANG}}` 统一页面语言。
- Readlog 示例按新方向重做（品牌色、标题宋体、通栏主按钮保持【确定】），新增示例浏览器测试并加入 CI。
- 用 Vercel 公开登录页实测（`docs/04_field-test-2.md`）：`palette.py --rows` 测量区块位置，与原稿并排比对误差 ≤4px；原稿本身对比度不达标时用最近的达标色并列为待定问题。
- `check_output.py` 不再把注释、规格说明、锚点和选择器里的 `#abc` 当成颜色（审计 F-06）；token 参考表与模板命名对齐（F-09）、模板补齐状态色（F-10）、`{{LANG}}`（F-11）、“标注”复选框措辞（F-12）、HANDOFF 对比度与视觉自查位置（F-13）、定义 `<skill-dir>`（F-14）、只复制 5 个原型文件（F-15）。
- README 增加示例预览图。

## design-to-dev 1.1.1 — 2026-11-02

修复发布前审计（`docs/99_audits/99_01_release_audit_v1.1.0.md`）的 4 个 P1，每项附回归测试，测试进入 CI：

- F-01 proto-kit：`Proto.go()` 跳到当前地址时也会重新渲染（此前第二次登录失败会让按钮一直停在“登录中”）。
- F-02 `tokens_json.py` / `check_output.py`：出现多个 `:root` 块（如深色模式）或非小写的 token 名时明确报错，不再静默丢弃。
- F-03 `check_output.py` 从 HANDOFF 的“交接对象”读取模式，模式 B 缺少 PLANNER_BRIEF.md 即报错；SKILL.md 第 6 步改为先写 brief 再检查。
- F-04 proto-kit：本地保存的数据带上 `data.js` 指纹，改了假数据后刷新即生效，不再被旧数据覆盖。
- 新增 `tests/`：脚本单元测试与 proto-kit 浏览器测试；CI 运行两者。

## design-to-dev 1.1.0 — 2026-11-02

用一张真实的公开登录页截图实测后迭代（记录见 `docs/02_field-test.md`）：

- 新增 `scripts/palette.py`：从 PNG 截图读取精确色板、指定点颜色和倍率（如 780 px = 390pt 手机 2 倍图），并计算 WCAG 对比度。取色与对比度不再靠目测和心算。
- 流程边界：流程终点没有设计时做一个标【待定】的桩页面；超范围链接加 `data-out`，proto-kit 统一提示“不在本原型范围”。
- 素材：标志、图标、图片未提供文件时用占位并标【待定】，HANDOFF 第 3 节新增素材清单；参考他人产品时不复刻其品牌名与标志。
- 登录、支付类流程只用虚构演示账号，写在 HANDOFF 第 0 节，原型不向网络发送任何输入。
- 从图片测量的字重、字号、间距在元素标注里也只能是【示意】；复制模板后要按设计调整基础组件，并把原型截图与原图并排对比。

## design-to-dev 1.0.0 — 2026-11-02

- 首个版本。六步工作流：理解意图（一轮最多五个问题 + 理解卡）→ 提取 design tokens（CSS 变量 + W3C JSON，每项带等级与来源）→ 搭建可交互原型（纯 HTML/CSS/JS，双击打开，假数据，默认/空/加载/报错状态，模拟请求失败）→ 标注【确定】【示意】【待定】（Shift+A 显示）→ 输出 HANDOFF.md → 两种收尾模式（A 交给开发，B 生成 PLANNER_BRIEF.md 衔接 planner）。
- 自带脚本：`tokens_json.py` 从 tokens.css 生成 tokens.json；`check_output.py` 交付前校验产出（两份 tokens 一致、页面与文档一致、标注合法、无原始色值、无远程脚本等）。
- 完整示例 `examples/readlog/`。
- 发布：Agent Skills 标准格式、Claude Code 插件市场清单、WorkBuddy 上传包 `design-to-dev.zip`；`scripts/build.py` 校验三个平台的规则，CI 拦截未更新的上传包。

# design-to-dev 1.1.0 发布前审计

## Scope

- Baseline: `claude/bold-mendel-7zvnkp@cad68be`（与 `main` 相同）；工作区干净；观察时间 2026-11-02T15:53Z。
- Included: 整个仓库——`skills/design-to-dev/`（SKILL.md、references、templates、scripts）、`scripts/build.py`、`.claude-plugin/marketplace.json`、`workbuddy.yaml`、`.github/workflows/check.yml`、`examples/readlog/`、README。
- Depth and reason: deep。用户要求完整审计；之前没有审计锚点，因此做全量基线审计。
- Delegation: 指令一致性（SKILL.md / references / templates / 触发描述）交给一名独立审阅者，只给文件、不给结论，以降低作者本人的锚定偏差；它报告的 12 条线索均由主审计在本基线上逐条复核后才接受。
- Evidence limits: 无法安装 `skills-ref`、`npx skills`（会话权限拦截）；未上传 WorkBuddy；未用 Style Dictionary / Tokens Studio 实际导入 tokens.json。

## Verdict

- P0: 0 | P1: 4 | P2: 12
- Main risk: 原型运行时与 token 流水线各有一个“看起来正常、实际错误”的缺陷（重复导航不刷新、token 被静默丢弃且检查仍通过），模式 B 的交付物在流程上从未被检查。

## Critical Paths

- 设计师输入 → 按 SKILL.md 产出 → check_output → 交接：**At risk**。模式 B 的 PLANNER_BRIEF 在检查之后才写、检查命令也不带 `--mode B`（F-03）；参考文档与模板的 token 命名不一致（F-09、F-10）；脚本路径写法不统一（F-14）。
- 原型运行时（file:// → 路由 → 渲染 → 模拟请求 → 本地存储 → 标注层）：**At risk**。F-01、F-04、F-05。
- Token 流水线（tokens.css → tokens_json.py → tokens.json → check_output 一致性）：**At risk**。F-02。
- 发布（源码 → build.py 校验 → zip → 三平台；CI）：**Healthy**，但有验证缺口（见下）。

## Confirmed Strengths

- `build.py` 构建可复现，`--check` 逐字节比对；三平台规则写成本地校验，7 类故障注入均能拦截（见 `docs/01_plan.md`、提交 24ba455 记录）。
- 所有脚本仅用标准库；原型无构建步骤、无外部依赖，在 file:// 下运行。
- `check_output.py` 能发现未定义的 token 引用、未填占位符、页面与文档不一致、标注取值非法（本次实测再次触发并拦住了 `var(--radius-full, 50%)`）。
- 原型渲染用户或数据文本前统一 `Proto.esc()`；proto-kit 自身的样式与设计 token 隔离（`pk-` 前缀，运行时注入）。
- `palette.py` 的取色、倍率与 PIL 结果一致，对比度计算与独立计算一致（不含透明度的情况）。

## Findings

| ID | Severity | Type / Confidence | Status | Finding | Path / Dimension | Evidence | Remediation |
|---|---|---|---|---|---|---|---|
| F-01 | P1 | Confirmed / High | Fixed (1.1.1) | `Proto.go()` 跳转到当前地址时不会重新渲染，页面停在中间状态 | `templates/proto-kit.js:84-87`、`:136`；运行时 / 5 | 实测登录原型：第二次输错密码，地址仍为 `#/?state=error`，按钮停在 “Signing in…” 且 `disabled=true`（`audit/repro.js` 输出） | `go()` 中新地址与当前相同时直接调用 `render()`；示例同步复制 |
| F-02 | P1 | Confirmed / High | Fixed (1.1.1) | token 解析静默丢弃：只读第一个 `:root`（如深色模式块被忽略），只接受小写名（`--colorPrimary` 被忽略）；两边都丢，所以检查仍 PASS | `scripts/tokens_json.py:33`、`:46`；`scripts/check_output.py:57`；数据 / 7 | 在示例 tokens.css 追加 `@media (prefers-color-scheme: dark) { :root {…} }` 后，tokens.json 中 `night` 计数 0，check_output PASS；`--colorPrimary` 生成 0 个 token | 解析所有 `:root` 块（或在出现第二个块时报错），对不符合命名规则的 `--` 声明报错而不是跳过 |
| F-03 | P1 | Confirmed / High | Fixed (1.1.1) | 模式 B 的 PLANNER_BRIEF 从未被检查：第 6 步的命令不带 `--mode B`，且 brief 在检查之后才写；`--mode` 在 SKILL.md 与 references 中都没出现 | `SKILL.md:90`、`:96-98`；`check_output.py:223`；UX / 9 | `grep -rn -- "--mode" SKILL.md references/` 无结果 | 第 6 步先写 brief 再检查，命令写明 `--mode B`；或由 HANDOFF 的“交接对象”自动判断 |
| F-04 | P1 | Confirmed / Medium | Fixed (1.1.1) | localStorage 里的旧数据会盖住 `data.js` 的修改；设计师或 Agent 改了假数据后刷新，看到的还是旧内容 | `templates/proto-kit.js:65-71`；数据 / 7、UX / 9 | 记录一次页码后把 data.js 的书名改为“改过的书名”，刷新后首卡仍显示“慢慢来的散步” | 保存时带上 `window.MOCK` 的指纹，指纹变化时丢弃旧数据 |
| F-05 | P2 | Confirmed / High | Open | 路由参数含非法 `%` 编码时整页空白 | `templates/proto-kit.js:165`；运行时 / 5、8 | `#/book/%E0` → pageerror `URI malformed`，`#app` 为空 | `decodeURIComponent` 包 try/catch，失败时显示“页面不存在” |
| F-06 | P2 | Confirmed / High | Fixed (1.2.0) | 原始色检查把 `#add`、`#bad`、`#face` 这类锚点或 id 当成颜色 | `scripts/check_output.py:31`；测试 / 11 | 在 pages.js 加 `querySelector('#bad')` → `raw colors ['#bad']` FAIL | JS 里只在样式上下文（`style=`、`color:` 等）中查找，或排除 `href="#…"`/选择器 |
| F-07 | P2 | Confirmed / High | Open | `--contrast` 忽略透明度；命名颜色直接崩溃 | `scripts/palette.py:91-92`；数据 / 7、8 | `#ffffff` vs `#2f6f4f66` → 5.99:1 AA pass（与不透明相同）；`white` → ValueError | 带 alpha 时要求给出底色并先合成，或明确报错；非十六进制输入给出可读错误 |
| F-08 | P2 | Exposure / Medium | Open | 大图内存与耗时过高 | `scripts/palette.py:49`、`:83`；效率 / 4 | 2880×6000 白底图：13.7 s，子进程峰值 1269 MB | 只保留计数器、按行累计；或按步长采样并说明 |
| F-09 | P2 | Confirmed / High | Fixed (1.2.0) | token 参考文档的命名与模板不一致：参考写 `content-max-width`、行高按档位，模板用 `--layout-content-width`、`--line-height-base`；参考未列出模板必需的 `--size-touch-target` | `references/design-tokens.md:9`、`:14`；`templates/styles.css:13`、`:22`、`:36`；规范 / 10 | 按参考改名后 check_output 报 `var(--line-height-base)…not defined` | 参考表与模板 tokens.css 对齐，列出模板依赖的全部 token |
| F-10 | P2 | Confirmed / High | Fixed (1.2.0) | SKILL.md 与参考要求的状态色（primary-active、disabled-bg/text、success、warning、info）模板里都没有，禁用态改用 `opacity: 0.5` | `SKILL.md:62`、`references/design-tokens.md:7`、`templates/tokens.css`、`templates/styles.css:46`；规范 / 10 | grep 模板 tokens.css 无上述名称 | 模板补齐这些 token 并在 styles.css 使用，或把要求改为“设计中出现时才提取” |
| F-11 | P2 | Confirmed / High | Fixed (1.2.0) | 模板语言自相矛盾：`index.html` 为 `lang="zh-CN"`，`pages.js` 用 `lang: 'en'` | `templates/index.html:2`、`templates/pages.js:49`；UX / 9 | 见行内容 | 统一为占位 `{{LANG}}`，参考里写明两处需一致 |
| F-12 | P2 | Confirmed / High | Fixed (1.2.0) | 收尾话术说“Spec button”，实际是工具面板里的复选框 | `SKILL.md:100`；`templates/proto-kit.js:209`；UX / 9 | 见行内容 | 改为“原型工具里的‘标注’复选框，或 Shift+A” |
| F-13 | P2 | Confirmed / High | Fixed (1.2.0) | 参考要求把对比度写进 HANDOFF 第 5 节，模板第 5 节没有对应位置 | `references/prototype.md:45`；`templates/HANDOFF.md` 第 5 节；规范 / 10 | 模板第 5 节无 contrast/对比 字样 | 模板加“对比度 Contrast”一行 |
| F-14 | P2 | Confirmed / High | Fixed (1.2.0) | 脚本路径三种写法，`<skill-dir>` 没有定义 | `SKILL.md:90`、`references/design-tokens.md:62`、`references/intake.md:7`、`references/annotation-and-handoff.md:46`；规范 / 10 | grep 结果 | SKILL.md 开头定义 `<skill-dir>` = 本 SKILL.md 所在目录，全文统一写法 |
| F-15 | P2 | Likely / Medium | Fixed (1.2.0) | “Copy the templates into `prototype/`” 有歧义：templates 里还有 tokens 与文档模板 | `SKILL.md:66`；`references/prototype.md:7-13`；规范 / 10 | 见行内容 | 写明只复制 5 个原型文件 |
| F-16 | P2 | Likely / Medium | Open | 触发描述含 “design to code”“extract design tokens”，可能被开发者“在现有代码库里把 Figma 实现成 React”或“只要 tokens”的请求误触发；技能只产出一次性原型，没有只出 tokens 的路径 | `SKILL.md:3`；平台 / 2 | 描述原文；技能禁止生产代码（`annotation-and-handoff.md:42`） | 描述里限定“clickable prototype for designers”，并写明不用于在现有代码库中实现设计 |

## Fix Log

- 1.1.1：F-01–F-04 已修复。回归测试 `tests/test_scripts.py`（F-02、F-03）与 `tests/kit.test.js`（F-01、F-04）在修复前失败、修复后通过，CI 运行两者；审计时的原始复现（C3、C4）在修复后的 kit 上不再出现。

- 1.2.0：F-06、F-09–F-15 已修复；复核见 `99_02_release_audit_v1.2.0.md`（F-06 的修复引入 N-01）。F-05、F-07、F-08、F-16 仍为 Open。

## Verification Gaps

- 严格的 Agent Skills 校验器（`skills-ref validate`）与 `npx skills add tealun/design-to-dev` 未运行：需要维护者本机执行（`docs/01_plan.md` V1、V5）。
- WorkBuddy 是否接受包内 `.js` / `.html` / `.css` 与 `category: design`：需首次上传结果（V6）。
- tokens.json 与 DTCG 稳定版（尺寸/时长为对象值、shadow 为复合对象）的兼容性，以及 Style Dictionary / Tokens Studio 实际导入：未测试。当前 `shadow` 写成 CSS 字符串，严格导入器可能拒绝。
- CI 只跑构建校验与示例检查；proto-kit 的浏览器行为（F-01、F-04、F-05 这类问题）没有自动化测试。

## Coverage

- 1 Architecture: 健康。技能本体、示例、构建与文档分层清楚；proto-kit 与设计样式隔离。
- 2 Platform integration: 三平台规则有本地校验，`claude plugin validate` 通过；F-16；其余见验证缺口。
- 3 Security: 原型对数据文本统一转义，不发网络请求；登录类流程要求虚构账号。拒绝的候选见证据日志。
- 4 Code efficiency: F-08。
- 5 Runtime smoothness: F-01、F-05。
- 6 Information isolation: N/A——没有多用户或租户。注：Chromium 中所有 file:// 页面共享同一存储源，存储键按产品名区分，同名原型会互相覆盖（低风险，未列为发现）。
- 7 Data accuracy: F-02、F-04、F-07。
- 8 Parameter passing: CLI 参数与路由参数——F-05、F-07。
- 9 User experience: F-03、F-11、F-12；示例的空/加载/报错状态与键盘焦点正常（此前 Playwright 走查）。
- 10 Coding standards: F-09、F-10、F-13、F-14、F-15。
- 11 Testing: 构建与示例检查在 CI；脚本与 kit 无单元或浏览器测试（验证缺口）；F-06 为检查器误报。
- 12 Deploy and operations: CI 校验上传包一致；版本号四处一致（SKILL.md、workbuddy.yaml、marketplace.json、CHANGELOG 均为 1.1.0）。

## Evidence Log

- 运行：`python3 scripts/build.py --check` → ok（18 files, 1.1.0）；`claude plugin validate .` → Validation passed；`check_output.py examples/readlog/output --mode B` → PASS。
- 浏览器复现（Playwright，持久化上下文）：F-01、F-04、F-05，见 Findings 证据列。
- 脚本探测：F-02（深色块、驼峰名）、F-06（`#bad`）、F-07（alpha、命名色）、F-08（2880×6000 大图）。
- 独立审阅者的 12 条线索：#1→F-09，#2→F-10，#3→F-03，#4→F-07，#5→F-06，#6→F-11，#7→F-12，#8→F-15，#9→F-14，#10→F-13，#11→并入 F-02，#12→F-16；均已复核。
- Rejected: proto-kit 的 `innerHTML` XSS——渲染内容来自页面模板，数据文本经 `Proto.esc()`，无外部输入；`palette.py` 解压炸弹——输入是使用者自己的本地文件；CI actions 用主版本标签而非 SHA——与 Tealun-Skills 惯例一致，本仓库 CI 无密钥与写权限，不构成可利用风险。
- 审计过程未修改仓库文件（仅新增本报告）；复现均在会话临时目录的副本上进行。

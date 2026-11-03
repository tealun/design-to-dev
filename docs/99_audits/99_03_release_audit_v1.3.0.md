# design-to-dev 1.3.0 发布前审计

## Scope

- Baseline: `claude/bold-mendel-7zvnkp@94ae4aa`；工作区干净；观察时间 2026-11-03T09:26Z。
- Anchor: `99_02_release_audit_v1.2.0.md`（基线 5502e30）。变更范围 `5502e30..94ae4aa`：2 个提交，34 个文件。
- Depth and reason: standard。新增了一个联网下载并写入用户文件夹的脚本（fetch_fonts.py）、新的检查逻辑和大段指令改写；不涉及认证、支付或生产环境。
- Delegation: fetch_fonts.py、check_output 的视觉检查、视觉参考的一致性交给一名独立审阅者（只给文件）；它的 14 条线索均已在本基线上复核。99_02 各项状态由主审计逐项复现。
- Evidence limits: 同前（skills-ref、npx skills、WorkBuddy 上传、DTCG 导入未验证）。

## Verdict

- P0: 0 | P1: 1 | P2: 20（新 13，延续 7）
- Main risk: 没有网络时，fetch_fonts.py 先删掉旧字体再下载，失败后原型引用不存在的字体文件；这正是 SKILL.md 承诺的“没有网络就回退”场景。

## Prior Findings (99_02)

| ID | Status now | Evidence |
| --- | --- | --- |
| R-1、R-2、R-3 | Fixed (1.3.0) | 规则允许颜色与阴影的状态过渡；模板头像为中性色；占位规则统一 |
| R-4、R-5 | Fixed (1.3.0) | Readlog 圆角 6/8/12/16；分段控件外 8、内边距 2、内 6 |
| R-6、R-7 | Fixed (1.3.0) | `check_output.py` 对 Readlog 0 条警告；HANDOFF 不再打分，写“待设计师评审” |
| R-9、R-10、R-11 | Fixed (1.3.0) | 内容宽度标【示意】；琥珀用途改写；字体写明已打包子集、字族【确定】 |
| R-12 | Fixed (1.3.0) | `#6b6b73` 在 `#f4f4f5` 上 4.81:1 |
| R-8 | Open | `design-tokens.md:7` 表头仍为“Tokens the template uses” |
| N-01 | Open | 追加含 `https://` 与内联颜色的一行后仍 PASS |
| N-02 | Open | `--rows abc` 仍抛 ValueError |
| F-05、F-07、F-08、F-16 | Open | 见 99_01；F-07 仍可复现（alpha、命名色） |

## Critical Paths

- 选定字体 → fetch_fonts → 离线原型：**At risk**（F1、F2、F3、F5）。
- 检查器视觉检查：**At risk**（V1–V6：有误报、有漏报，豁免范围过宽）。
- 方向说明 → 模板 → 视觉自查：**Healthy**，有 4 处数值与模板不一致（C1、C2、C5、C6）。
- 发布：**Healthy**（CI run 41605123729 success，build --check、plugin validate 通过）。

## Findings

| ID | Severity | Type / Confidence | Status | Finding | Location | Evidence | Remediation |
|---|---|---|---|---|---|---|---|
| F1 | P1 | Confirmed / High | Open | 先删除全部旧 woff2，再下载；下载失败时旧 fonts.css 仍引用已删除的文件，原型字体丢失、检查器报错 | `scripts/fetch_fonts.py:95-96` | 静态：删除在 try 之前；审阅者用不可达代理复现，`fonts/` 只剩 fonts.css | 下载到临时目录，全部成功后再替换 |
| F2 | P2 | Confirmed / High | Open | 非数字字重（`bold`）抛异常，且发生在删除旧字体之后 | `fetch_fonts.py:59` | `"Noto Serif SC:bold"` → ValueError | 解析参数时先校验 |
| F3 | P2 | Confirmed / High | Open | 字体名或字重写错（HTTP 400）被报告成“连不上 Google Fonts” | `fetch_fonts.py:103` | `"Nonexistent Fam:400"` → “cannot reach” | 区分 HTTPError 400 与网络错误 |
| F4 | P2 | Confirmed / High | Open | index.html 没有 tokens.css 链接时，仍提示“已加入 fonts.css” | `fetch_fonts.py:109-113` | 注入后 `grep -c fonts.css` 为 0 | 没注入成功就报错并说明手动加法 |
| F5 | P2 | Confirmed / High | Open | 原型路径上任何一级目录叫 `fonts` 时，收集字符时把所有文件都排除，中文全部丢出子集；也不收集 CSS `content:` 文字 | `fetch_fonts.py:51` | `fonts/inner/proto` 只收集到 95 个字符 | 用相对路径判断；把 .css 纳入 |
| V1 | P2 | Confirmed / High | Open | 定位属性（top/left/inset）被当作间距检查，产生误报 | `check_output.py`（`SPACING_PROPS`） | `top: 7px` 报警 | 只检查 margin/padding/gap |
| V2 | P2 | Confirmed / High | Open | 漏报：负值、rem/em、`grid-gap`、`font:` 简写、通过 token 设为 10px 的字号 | 同上 | 各夹具均无警告 | 解析 token 值；支持 rem（按 16px）与简写；负值取绝对值 |
| V3 | P2 | Confirmed / High | Open | 字重计数把 `var(--x, 700)` 截断、把 `bold` 与 `700` 计为两种 | 同上 | 夹具输出 6 种 | 解析带回退的 var；把关键字映射为数字 |
| V4 | P2 | Confirmed / High | Open | 一个豁免注释让整行所有属性都免检 | 同上 | `padding: 6px; font-size: 9px; /* decorative */` 无警告 | 豁免只作用于注释所在的声明，或要求注明豁免哪一项 |
| V5 | P2 | Confirmed / Medium | Open | 展示字体是 `var(--font-family-base)` 别名时不解析，系统字体检查漏报 | 同上 | 夹具无警告 | 解析一层 var 别名 |
| V6 | P2 | Confirmed / Medium | Open | pages.js 的内联样式不参与视觉检查 | 同上 | `pages.js:44` 的 `border-radius:2px` 等未检查 | 对内联 `style="…"` 也做同样检查 |
| C1 | P2 | Confirmed / High | Open | 动效基准写“微交互 150–200ms、常规 300–400ms”，模板为 120/180/640ms，没有常规档，状态过渡未用规定的缓动 | `visual-direction.md`（Motion）；`templates/tokens.css` | 见行 | 统一数值（规则或模板二选一） |
| C2 | P2 | Confirmed / High | Open | 预设阴影写“Y 2 / 8 / 24px”，模板为 Y 1 / 1 / 8 | 同上 | 见行 | 统一 |
| C4 | P2 | Confirmed / Low | Open | Readlog 的 `.avatar` 用了强调色（继承自 1.2 模板）；Readlog 没有页面用到它，属于不符合规则的死代码 | `examples/readlog/output/prototype/styles.css:106` | `grep -c avatar pages.js` 为 0 | 与模板同步为中性色 |
| C5 | P2 | Likely / Medium | Open | Readlog 页标题用展示字体 30px，低于“手机展示字 ≥ 32px” | `styles.css`（`.title`） | 见行 | 改为 32px，或调整规则措辞 |
| C6 | P2 | Likely / Low | Open | intake 示例把 Readlog 写成“精致极简预设”，实际是该方向加品牌约束（宋体、自有文字色） | `references/intake.md` | 见行 | 措辞改为“精致极简方向 + 品牌约束” |
| R-8、N-01、N-02、F-05、F-07、F-08、F-16 | P2 | 见前次报告 | Open | — | — | — | — |

Rejected: C3（模板展示字为系统字体）——模板是中性起点，检查器对它报警正是为了提醒为每个产品选字体；在参考中写明这一点即可，不算缺陷。

## Verification Gaps

- fetch_fonts.py 依赖网络，CI 中没有测试；失败路径（F1–F4）此前没有自动化覆盖。
- 视觉检查（check_visual）的测试只覆盖了正向的典型情况，没有覆盖 V1–V6 这类边界。

## Coverage

- 1 Architecture: 健康；字体获取、视觉检查、参考文档各自独立。
- 2 Platform integration: Google Fonts CSS2 API 的 `text=` 子集已实际验证；错误分类见 F3。
- 3 Security: fetch_fonts 的文件名来自参数与 URL 哈希，不由远端数据决定，不会写到目标目录之外；下载内容校验 woff2 文件头。
- 4 Code efficiency: F-08 未变。
- 5 Runtime smoothness: 入场序列只在切换页面时播放（浏览器测试覆盖）；F-05 未变。
- 6 Information isolation: N/A。
- 7 Data accuracy: F1、F5；C1、C2、C6（文档数值）。
- 8 Parameter passing: F2、F3、N-02、F-07。
- 9 User experience: C5；视觉评审已由用户认可（“可以”）。
- 10 Coding standards: R-8、C4。
- 11 Testing: 验证缺口两项。
- 12 Deploy and operations: 版本一致（1.3.0），CI 通过。

## Evidence Log

- 运行：`build.py --check` ok；`claude plugin validate .` 通过；单元测试 15 项、kit 与示例浏览器测试通过；CI run 41605123729 success。
- 复现：99_02 每项逐一复现（结果见上表）；F1 由静态代码证明并经审阅者复现；V4 的豁免逻辑为逐行判断（`excused` 按行计算）。
- 独立审阅者线索：F1–F5、V1–V6、C1–C6；C3 驳回，其余接受，C4 降级为 Low。
- 审计未修改仓库文件（新增本报告，更新 99_02 状态列）。

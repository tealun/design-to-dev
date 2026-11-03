# design-to-dev 1.2.0 发布前审计

## Scope

- Baseline: `claude/bold-mendel-7zvnkp@5502e30`；工作区干净；观察时间 2026-11-03T08:13Z。
- Anchor: `99_01_release_audit_v1.1.0.md`（基线 cad68be）。变更范围 `cad68be..5502e30`，4 个提交，40 个文件。
- Depth and reason: standard。改动跨越指令文本、CSS、浏览器 JS 和 Python 命令行脚本，不涉及认证、支付或生产环境。
- Delegation: 视觉方向参考、模板与 Readlog 的一致性交给一名独立审阅者，只给文件、不给结论（本轮内容仍由同一作者编写）；它的 11 条线索均已在本基线上逐条复核。
- Evidence limits: 与 99_01 相同（未运行 `skills-ref`、`npx skills`，未上传 WorkBuddy，未做 DTCG 导入测试）；第 12 项视觉自查（“设计负责人是否接受”）只能由用户判断。

## Verdict

- P0: 0 | P1: 1 | P2: 15
- Main risk: 1.2.0 的核心承诺是“视觉自查”，但示例的自查结论是作者自评的，写成了 12/12，实际至少 4 项不符合规则；自查清单缺少可执行的客观检查。

## Prior Findings (99_01)

| ID | Status now | Evidence |
| --- | --- | --- |
| F-01–F-04 | Fixed (1.1.1) | `tests/kit.test.js`、`tests/test_scripts.py` 通过；CI run 41601663396 通过 |
| F-05 | Open | `templates/proto-kit.js:178` 仍直接调用 `decodeURIComponent` |
| F-06 | Fixed (1.2.0)，但引入 N-01 | `RawColorCheck` 测试通过 |
| F-07 | Open | `--contrast "#ffffff" "#2f6f4f66"` 仍为 5.99:1；`white` 仍抛 ValueError |
| F-08 | Open | 未改动；`--rows` 复用同一解码路径 |
| F-09 | Fixed，残留 R-8 | 参考表已改为模板实际使用的名称 |
| F-10 | Fixed | 模板 tokens.css 含 success/warning/info/disabled |
| F-11 | Fixed | `{{LANG}}` 用于 index.html 与 pages.js |
| F-12 | Fixed | SKILL.md 不再出现 “Spec button” |
| F-13 | Fixed | HANDOFF 模板第 5 节含视觉方向、视觉自查与对比度 |
| F-14 | Fixed | SKILL.md 定义 `<skill-dir>`；引用均为 `python3 <skill-dir>/scripts/…` |
| F-15 | Fixed | SKILL.md 第 3 步列出 5 个原型文件 |
| F-16 | Open | 触发描述未改 |

## Critical Paths

- 无视觉稿 → 选方向 → 模板 → 视觉自查 → 交付：**At risk**（R-6：自查结论没有客观依据；R-1、R-2、R-3：规则与模板自相矛盾，Agent 照模板做就会违反规则）。
- 有原稿 → 取色、测量 → 还原：**Healthy**（实测登录页各区块误差 0–3px）。
- 检查器守门：**At risk**（N-01：F-06 的修复让一类原始色值漏检）。
- 发布：**Healthy**（build --check、plugin validate、CI 全部通过）。

## Findings

| ID | Severity | Type / Confidence | Status | Finding | Location | Evidence | Remediation |
|---|---|---|---|---|---|---|---|
| R-6 | P1 | Confirmed / High | Open | Readlog 写“视觉自查 12/12”，实际不符合第 3 项（4 种字重：400/500/600/700；第 4 种文字颜色：苔绿用于“+15 页”数据）、第 5 项（6px 间距、6/5/9px 内边距）、原则中“标签最小 12px”（封面字 7/8/11px）与嵌套圆角规则（R-5）。`docs/04_field-test-2.md` 的自查表同样写了通过。 | `examples/readlog/output/HANDOFF.md:102`；`prototype/styles.css:145,164,170,288` | 本节逐项 grep 结果；字重统计 bold 3、medium 9、semibold 5 处 | 修正示例；让 check_output 自动检查可客观判断的自查项（字重种数、字号下限、非刻度间距、强调色用途），自评项只能写“待用户确认” |
| N-01 | P2 | Confirmed / High | Open | 原始色检查把 `https://` 后的整行当成注释删掉，同一行后面的内联颜色漏检 | `skills/design-to-dev/scripts/check_output.py`（`strip_non_color_hashes`） | 追加 `<a href="https://example.com" style="color:#ff0000">` 后检查 PASS | 只删除行首或语句外的 `//` 注释；补回归测试 |
| R-1 | P2 | Confirmed / High | Open | 规则写“动效只用 opacity 和 transform”，模板与示例对背景色、边框色、阴影做过渡 | `visual-direction.md:33`；`templates/styles.css:56,81,96` | 见行 | 规则改为“颜色与阴影的状态过渡也可以；位移类动效只用 transform/opacity” |
| R-2 | P2 | Confirmed / High | Open | 模板列表头像使用强调色，违反“强调色只用于主操作、选中、进度、链接” | `templates/styles.css`（`.avatar`） | 见行 | 头像改用中性色 |
| R-3 | P2 | Confirmed / High | Open | 占位图规则互相矛盾：prototype 参考推荐“灰框写素材名”，视觉参考禁止“灰框写 image” | `references/prototype.md:51`；`visual-direction.md:30` | 见行 | 统一为视觉参考的写法 |
| R-4 | P2 | Likely / Medium | Open | Readlog 圆角 10/14 与预设 6/8/12/16 不同；规划文档写 6/10/14，与参考不一致，且没有记录为品牌例外 | `examples/readlog/output/design-tokens/tokens.css:76-77`；`docs/03_visual-quality-plan.md` | 见行 | 记录为品牌“柔和圆角”的例外，或改回预设 |
| R-5 | P2 | Confirmed / High | Open | 分段切换内外圆角不符合“内 = 外 − 内边距” | `examples/readlog/output/prototype/styles.css`（`.segmented`、`.segmented__item`） | 外 10、内边距 2、内 6 | 内圆角改为 8 |
| R-7 | P2 | Confirmed / High | Open | 示例间距与字号不在刻度上（见 R-6 证据） | 同 R-6 | 同 R-6 | 改用刻度值；封面书名视为装饰时在规则中写明例外 |
| R-8 | P2 | Confirmed / Medium | Open | token 参考表标题写“模板使用的 token”，其中十余项模板并未使用 | `references/design-tokens.md` | 声明与使用的名称做差集 | 标题改为“模板提供的 token” |
| R-9 | P2 | Confirmed / High | Open | HANDOFF 把“内容最宽 480px”标为【确定】，tokens 中为【示意】 | `examples/readlog/output/HANDOFF.md:100`；`tokens.css:94` | 见行 | 两处统一 |
| R-10 | P2 | Confirmed / High | Open | HANDOFF 写“琥珀只用于连续阅读”，琥珀封面也用了品牌琥珀 | `HANDOFF.md:58,95`；`tokens.css:35` | 见行 | 改写说明，或封面改用其他颜色 |
| R-11 | P2 | Confirmed / High | Open | 品牌字体在 tokens 中为【确定】，HANDOFF 素材清单为【待定】，SKILL.md 规定字体不可用时记为【待定】 | `tokens.css:44`；`HANDOFF.md` 第 3 节 | 见行 | 字族【确定】、字体文件加载【待定】，两处写清 |
| R-12 | P2 | Exposure / Medium | Open | 模板三级文字在凹陷底色上 4.40:1，不达标；目前没有文字放在这一组合上 | `templates/tokens.css` | `palette.py --contrast "#71717a" "#f4f4f5"` | 三级文字加深一档，或在参考中注明禁止该组合 |
| N-02 | P2 | Confirmed / High | Open | `--rows` 参数格式错误时抛出原始异常 | `scripts/palette.py` | `--rows abc` → ValueError | 给出可读的用法提示（可与 F-07 一并处理） |
| F-05, F-07, F-08, F-16 | P2 | 见 99_01 | Open | 见上表 | — | — | — |

## Verification Gaps

- 第 12 项视觉自查（设计负责人是否接受）只能由用户评审：Readlog 新旧对比图已交给用户。
- 视觉自查中可客观判断的项目目前没有自动检查（R-6 的根因）。

## Coverage

- 1 Architecture: 健康。视觉方向独立成参考，模板与规则分层。
- 2 Platform integration: 发布校验通过；F-16 未变。
- 3 Security: 新增代码没有网络或外部输入；原型的数据文本仍经 `Proto.esc()` 转义。
- 4 Code efficiency: F-08 未变。
- 5 Runtime smoothness: F-05 未变；浏览器测试无控制台报错。
- 6 Information isolation: N/A。
- 7 Data accuracy: R-9、R-10、R-11（文档与 token 不一致）；R-6（自查结论不实）。
- 8 Parameter passing: N-02、F-07。
- 9 User experience: R-1–R-7、R-12；视觉评审待用户。
- 10 Coding standards: R-3、R-8。
- 11 Testing: 新增示例浏览器测试与原始色回归测试；N-01 说明回归测试只覆盖了误报，没有覆盖漏报。
- 12 Deploy and operations: 版本四处一致（1.2.0），CI 通过。

## Evidence Log

- 运行：`build.py --check` ok（19 files，1.2.0）；`claude plugin validate .` 通过；单元测试 7 项、kit 浏览器测试、示例浏览器测试均通过；CI run 41601663396 success。
- 复现：N-01（追加含 URL 与内联颜色的一行后 PASS）、N-02（`--rows abc`）、F-05/F-07 仍可复现。
- 独立审阅者线索：#1→R-1、#2→R-2、#3→R-3、#4→R-4、#5→R-5、#6→R-6、#7→R-7、#8→R-8、#9→R-9、#10→R-10、#11→R-11、模板对比度→R-12；均已复核。
- 审计过程未改动仓库文件（新增本报告，并更新 99_01 的状态列）。

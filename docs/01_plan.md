# design-to-dev 规划

状态：M0 规划（待 auditor 审计后进入实现）
日期：2026-11-02

## 1. 理解卡

- **是什么**：一个独立发布的 Agent 技能。设计师给出设计稿或产品意图，Agent 产出一个能跑起来的原型、两份 design tokens 和一份交接文档 `HANDOFF.md`。
- **目标用户**：懂设计、不太懂代码的人（UI/UX 设计师、产品设计师、独立创作者）。次要读者：接手的前端开发者。
- **输入**：设计截图、Figma 链接、品牌规范、Claude Design 产出、纯文字产品意图，可混合。
- **产出**：`prototype/`、`design-tokens/`、`HANDOFF.md`。
- **非目标**：不做后端、不接真实接口、不做生产级工程化（构建链、测试框架、状态管理库）、不替代设计评审、不生成 Figma 文件。
- **与 Tealun Skills 的关系**：独立仓库 `tealun/design-to-dev`，单独安装、单独发布，不改动 Tealun-Skills 仓库；收尾模式 B 生成可直接交给 `planner` 的需求输入。

## 2. 规划契约

- `done_definition`：技能包（SKILL.md + references + templates + 自检脚本）、中英 README、完整示例、三平台本地校验与打包、一次真实稿件实测及据此迭代的 SKILL.md。
- `validation_method`：`python3 scripts/build.py --check`（规范与平台校验 + 成品一致性）；`claude plugin validate .`；示例产物用技能自带的 `check_output.py` 校验；原型用 Playwright 打开并点通核心流程、截图各状态。
- `fail_condition`：任一平台规则无法同时满足且无法用打包时注入解决；原型在 `file://` 下无法运行；实测暴露的问题无法在技能文本内修正。

## 3. 决策（Decisions）

| ID | 决策 | 理由 |
|---|---|---|
| D1 | 独立仓库 `tealun/design-to-dev`：仓库根放 README、示例、文档、构建脚本、插件市场清单；技能本体在 `skills/design-to-dev/`。 | 用户已建专门仓库（2026-11-02 纠正：不得放进 Tealun-Skills）。`skills/<name>/SKILL.md` 是 Claude 插件默认扫描位置，`npx skills add tealun/design-to-dev` 也能发现；技能目录只放运行时需要的文件。 |
| D2 | 源码 SKILL.md 的 frontmatter 只用 Agent Skills 规范字段：`name`、`description`、`license`、`compatibility`、`metadata`（`version`、`author`）。 | 规范是三个平台的公共底座；规范外字段可能被严格校验器拒绝（见 V1）。 |
| D3 | WorkBuddy 展示字段（`display_name`、`display_name_en`、`description_zh`、`description_en`、`examples_zh/en`、`author`、`category`、`version`）存放在仓库根 `workbuddy.yaml`，打包 WorkBuddy zip 时注入 frontmatter。 | 同一份源码兼容严格规范与 WorkBuddy 必填字段。 |
| D4 | 技能包目录最多一层子目录：`references/`、`templates/`、`scripts/` 内全部是平铺文件。 | WorkBuddy 只接受 根/二级/文件（EV-20261102-001）；规范也要求引用只深一层。 |
| D5 | 默认原型技术栈：纯 HTML + CSS + 原生 JS，无构建步骤，hash 路由，假数据写在 `data.js`（不用 `fetch` JSON）。双击 `index.html` 即可在 `file://` 下运行。 | 设计师不需要装 Node；开发者无框架负担、可平移到任意框架。用户明确要求时可换 Vite + React，技能给出切换条件。 |
| D6 | Tokens 两份：`design-tokens/tokens.css`（CSS 自定义属性）与 `design-tokens/tokens.json`（W3C Design Tokens 格式，`$value`/`$type`），两份名字一一对应，由 `check_output.py` 校验。 | 用户要求两份；DTCG 格式便于导入 Style Dictionary / Tokens Studio。 |
| D7 | 三级标注：【确定】Fixed / 【示意】Indicative / 【待定】TBD。原型里用 `data-spec="fixed|indicative|tbd"` + `data-spec-note` 标在元素上，按 `Shift+A` 显示标注层；`HANDOFF.md` 汇总成表。tokens 每项也带等级。 | 标注跟着元素走，开发者在原型里直接看到；文档里可检索。 |
| D8 | 关键状态用状态切换条呈现：每页支持 `?state=default|empty|loading|error`（hash 参数），原型角落有切换控件；hover/focus/disabled 写在 CSS。 | 不用真实网络也能演示所有状态，评审可复现。 |
| D9 | 两种收尾：A 交给开发者（HANDOFF 侧重说明与待定问题）；B 自己继续开发（另生成 `PLANNER_BRIEF.md`，按 planner 的输入要求组织：目标用户、核心流程、已决定事项、约束、待验证项）。 | 用户要求；衔接 planner 的 `argument-hint`。 |
| D10 | 自检脚本 `scripts/check_output.py`（Python 3 标准库）：检查产出结构、tokens 两份一致、HANDOFF 必要章节、原型页面与 HANDOFF 页面清单一致、标注存在且取值合法、原型没有外链运行时依赖。 | tasker 惯例：完成要有可执行检查；设计师也能一条命令看结果。 |
| D11 | 构建脚本 `scripts/build.py`：校验 Agent Skills 规范、插件清单与 WorkBuddy 限制，生成仓库根 `design-to-dev.zip`（WorkBuddy，含注入字段与 LICENSE）并支持 `--check`；CI `.github/workflows/check.yml` 运行它。 | 发布前把平台规则写成本地校验（Tealun-Skills EV-20261102-001 的教训）。 |
| D12 | Claude Code 插件市场：本仓库自建 `.claude-plugin/marketplace.json`（市场名 `design-to-dev`），一个插件条目 `design-to-dev`，`source: ./`，`skills: ["./skills/design-to-dev"]`。Tealun-Skills 的市场不列出它。 | 用户选择完全独立；安装命令 `/plugin marketplace add tealun/design-to-dev` + `/plugin install design-to-dev@design-to-dev`。 |
| D13 | 完整示例放 `examples/readlog/`（读书打卡小产品，文字意图 + 品牌规范输入），不进技能包。 | 示例目录较深，放包外不受层级限制；README 链接即可。 |
| D14 | 实测稿件：选一个公开可获取的真实产品界面截图，测试记录写入 `docs/02_field-test.md`，注明来源；第三方图片不提交入库。 | 用户选择“自选公开稿件”；避免版权问题。 |

## 4. 假设（Assumptions）

- A1 目标 Agent 具备读图能力（截图输入）；没有时退回文字描述并在 HANDOFF 标明。
- A2 Figma 链接通过 Figma MCP（`get_design_context` / `get_variable_defs` / `get_screenshot`）读取；不可用时请设计师导出截图与样式表。
- A3 “Claude Design 产出”按 HTML/截图/文字三种之一处理，不依赖特定格式。
- A4 版本从 `1.0.0` 起，记录在 `metadata.version`、`workbuddy.yaml`、`CHANGELOG.md` 三处，构建脚本校验三处一致。

## 5. 待验证（To Verify）

| ID | 事项 | 证据形式 | 归属 |
|---|---|---|---|
| V1 | 严格校验器（skills-ref）是否拒绝规范外 frontmatter 字段 | 本会话安装 skills-ref 被权限拦截；按“会拒绝”保守处理（D2/D3），发布前由维护者本机运行 `skills-ref validate` 确认 | M0，维护者 |
| V2 | WorkBuddy 对单技能包的字段要求与套件包一致 | 沿用 EV-20261102-001 已知规则（第三方整理，待官方证实）；首次上传结果记入台账 | 发布时 |
| V3 | `claude plugin validate .` 接受本仓库的市场与插件清单 | 命令输出 | M1 |
| V4 | 原型在 `file://` 下完整可用（路由、状态切换、标注层） | Playwright 截图与点击脚本输出 | M1 |

## 6. 阶段门槛

- **M0（本文档）**：规则汇总、目录与格式决策、审计通过。失败条件：auditor 报出阻断实现的 P0。
- **M1 技能骨架 + 示例跑通**：SKILL.md、references、templates、check_output.py；示例 `readlog` 全流程产物；`check_output.py` 与 Playwright 点击通过；build.py `--check` 与 `claude plugin validate` 通过。
- **M2 发布就绪**：中英 README、CHANGELOG、LICENSE、CI；auditor 发布前审计。
- **M3 实测迭代**：真实稿件跑一遍，记录问题，修改 SKILL.md（版本 1.0.x/1.1.0），重新构建与校验；evolver 记台账。

## 7. 平台规则汇总（写入 build.py）

**Agent Skills 规范**（agentskills.io/specification）
- 必填 `name`、`description`；可选 `license`、`compatibility`（≤500）、`metadata`（字符串→字符串）、`allowed-tools`。
- `name`：1–64 字符，仅 `a-z0-9-`，不以 `-` 开头/结尾，不含 `--`，等于父目录名。
- `description`：1–1024 字符，写清做什么、何时用、含检索关键词。
- SKILL.md 建议 < 500 行；引用相对技能根、只深一层。

**Claude Code 插件市场**
- 条目必填 `name`、`source`；`source` 相对路径以 `./` 开头、不含 `..`、相对市场根；`skills` 路径以 `./` 开头、位于插件根内且存在。

**WorkBuddy（EV-20261102-001，第三方整理，待官方证实）**
- 目录最多 根/二级/文件；必填 `display_name`、`display_name_en`、`description_zh`、`description_en`、`examples_zh`、`examples_en`；`name` 匹配 `^[a-z0-9][a-z0-9-]{0,39}$`；`display_name_en` ≤ 60、`description_zh` ≤ 500、`description_en` ≤ 1000；示例每种语言 1–3 条。

## 8. 审计记录（auditor，quick，基于 Tealun-Skills 8ef6107 时的方案）

结论：无 P0/P1。迁到独立仓库后：

- P2-1、P2-2（Tealun-Skills 的 AGENTS.md 与 marketplace 描述）已不适用：不再改动 Tealun-Skills。
- P2-3 安装路径：README 给出插件市场、`npx skills add`、手动复制三种方式。
- P2-4 标注快捷键须在输入框聚焦时失效；WorkBuddy 包附带 LICENSE → M1 实现。

## 9. 变更记录

- 2026-11-02 用户纠正：技能不得放进 Tealun-Skills，改为独立仓库 `tealun/design-to-dev`。已把未提交的 10 个文件迁入本仓库并清理 Tealun-Skills 工作区；D1、D3、D11、D12、D13 随之更新。

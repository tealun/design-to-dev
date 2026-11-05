# 1.4.0 规划：照搬 tealun-dev-pdca 的发布规范

状态：规划 · 日期：2026-11-05
参照：`tealun/tealun-dev-pdca @ c78834a`（只读，不修改）、`tealun/tealun-plugins @ be76c9a`

## 1. 理解卡

- **目标**：design-to-dev 采用和 dev-pdca 相同的发布方式：
  - 本地先校验平台规则；
  - 插件目录跟踪只由 CI 写入的 `plugin` 分支；
  - 推送 `v<版本>` tag 后，由 CI 构建并发布 Release；
  - 上架 tealun 市场，为提交 Claude 插件目录做好准备。
- **现状**：
  - 仓库根有 `marketplace.json`（会和 tealun 市场重名冲突）；
  - 提交了 `design-to-dev.zip`；
  - `.gitattributes` 没有设置；
  - 版本分散在 SKILL.md、workbuddy.yaml、marketplace.json、CHANGELOG 四处；
  - README 里有 `npx skills add`、`git clone`；
  - 只有一个 CI 工作流 `check.yml`；
  - 没有 PRIVACY.md 和图标。
- **差异**：dev-pdca 有 6 个技能，以根目录作插件；design-to-dev 只有一个技能，放在 `skills/design-to-dev/`。另外，design-to-dev 的技能包里有 4 个 Python 脚本，其中 `fetch_fonts.py` 会访问网络（Google Fonts）。

## 2. 规划契约

- `done_definition`：
  - 本仓库有 AGENTS.md、`docs/claude-directory-rules.md`、`docs/workbuddy-rules.md`、`scripts/build_plugin.py`、`scripts/build_suite.py`、`scripts/publish_plugin_branch.sh`；
  - `release.yml`、`plugin-branch.yml`、`check.yml` 三个工作流；
  - `.gitattributes`、PRIVACY.md、图标，以及以 `plugin.json` 为唯一来源的版本；
  - 不再提交 zip；README 里没有下载即执行的命令；
  - 新 agent 试跑过并据此迭代；
  - auditor 报告写好；tealun-plugins 的上架 PR 已开。
- `validation_method`：
  - `build_plugin.py --check` 与 `build_suite.py --check` 通过，单元测试通过；
  - 每条平台规则在对照表里都有“检查函数”或“不检查的理由”；
  - 对打包产物运行 `claude plugin validate`；
  - 在本地临时远端上演练 `publish_plugin_branch.sh`；
  - CI 通过。
- `fail_condition`：
  - 某条平台规则既写不成本地检查，又说不清不检查的理由；
  - 打包产物不能通过 `claude plugin validate`；
  - 隐私说明和脚本的实际行为不一致。

## 3. 决策

| ID | 决策 | 依据 |
|---|---|---|
| P-D1 | `.claude-plugin/plugin.json` 是版本的唯一来源。删除 SKILL.md 的 `metadata.version`、workbuddy.yaml 的 `version`；WorkBuddy 包里的 `version` 打包时从 plugin.json 注入；CHANGELOG 小节写成 `## design-to-dev <版本>`，按 plugin.json 校验。 | 用户第 6 条 |
| P-D2 | 删除仓库内的 `.claude-plugin/marketplace.json`。在 tealun/tealun-plugins 的 `marketplace.json` 加一条，source 为 `{"source":"github","repo":"tealun/design-to-dev","ref":"plugin"}`，README 插件表加一行；改动走 PR。 | 用户第 10 条 |
| P-D3 | `scripts/build.py` 拆成两个脚本。`build_plugin.py` 负责插件清单、目录规则、导出一致性、`.gitattributes`、README 词数与下载即执行检查、文件大小与类型、`--tag`、`--since`、`--notes`、打包。`build_suite.py` 负责 WorkBuddy 包：全部字段与结构规则、只能有一个 SKILL.md、不能有 BOM、目录层级。产物只写到 `dist/`。 | 用户第 1、7 条；台账 dev-pdca EV-20261102-001/003 |
| P-D4 | 发布审计门禁（本仓库 EV-20261103-001）并入 `build_plugin.py --check`：每个 MAJOR.MINOR 版本都要有 `docs/99_audits/*release_audit_vX.Y*.md`。 | 本仓库台账 |
| P-D5 | 打包内容：`.claude-plugin/plugin.json`、`skills/design-to-dev/**`、README.md、LICENSE、PRIVACY.md、图标、README 引用的示例预览图。打包不含 CI、scripts/、tests/、docs/（预览图除外）、examples/、CLAUDE.md、AGENTS.md。README 里的仓库内链接一律写成 GitHub 绝对地址，这样在 plugin 分支和上架页上也能打开。 | dev-pdca EV-20261105-003；用户第 3 条 |
| P-D6 | `.gitattributes` 为 `* -text`；`build_plugin.py --check` 包含 `content_rewriting_attributes()` 和 `export_mismatches()`。 | 用户第 2 条；dev-pdca EV-20261105-002 |
| P-D7 | 工作流：`check.yml` 每次推送都校验，并排除 plugin 分支；`release.yml` 由 v* tag 触发，附 `.plugin`、`.zip` 和 WorkBuddy 包；`plugin-branch.yml` 由 v* tag 或在 main 上手动触发；它与 `release.yml` 用同一组门（`--check --tag`、单元测试），手动触发时只发布当前版本已有的 tag（审计 99_04 A-01、A-02）。两个发布工作流都用固定版本的 Claude Code CLI 运行 `plugin validate`。保留 `check.yml` 的文件名，作用对应 dev-pdca 的 `suite-package.yml`。 | 用户第 6 条 |
| P-D8 | **联网披露**：`fetch_fonts.py` 只在 Agent 运行它时访问 `fonts.googleapis.com`、`fonts.gstatic.com`，会把原型里用到的字符作为 `text=` 参数发出去。默认做法是：保留这个脚本；SKILL.md 要求运行前先告诉设计师会发送什么，并给出跳过或 `--latin` 的选择；PRIVACY.md 与 README 写明。数据问卷：个人数据 No，外发数据 Yes（仅限上述字体请求，由用户触发），数据保留 Not retained，面向未成年人 No。 | 用户第 11、12 条；脚本源码 |
| P-D9 | 插件只含技能（不含 MCP、hooks、bin/）。技能里的 4 个脚本在 PRIVACY.md 逐个说明用途和网络行为；目录规则表登记“有可执行脚本，审核会更严”。 | 用户第 12 条 |
| P-D10 | 新增 512×512 PNG 图标 `assets/design-to-dev-icon.png`，由 `scripts/make_icon.py` 生成。 | 目录图标规格 |
| P-D11 | 版本 1.4.0（minor：发布方式和披露行为有变，技能内容有改动）。发布前按 P-D4 要写 1.4 的 auditor 报告。 | AGENTS 升版规则 |
| P-D12 | 照搬演进台账的配套机制：`docs/98_evolution/compliance-log.md`（5 道 Gate）和 `scripts/check_ledger.py`，CI 运行。 | dev-pdca AGENTS.md evolver 规则 |
| P-D13 | 新 agent 试跑：只给 `skills/design-to-dev/SKILL.md` 的路径和一份真实任务（Linear 公开登录页截图加一句产品意图），产出写到 scratchpad；它列出的问题核实后再改。 | 用户第 8 条 |

## 4. 假设

- A1：CI 的 `GITHUB_TOKEN` 有 contents: write 权限，可以推送 plugin 分支（dev-pdca 已验证可行）。
- A2：插件名 `design-to-dev` 符合目录命名规则，与 tealun 市场中已有的条目不重名。

## 5. 待验证

| ID | 事项 | 证据 | 归属 |
|---|---|---|---|
| P-V1 | plugin 分支由 CI 写出，只含打包产物 | 合并并推送 tag 后，plugin 分支的文件列表 | 发布时（需用户合并、推 tag） |
| P-V2 | 插件目录 Validate 和安全扫描通过；有可执行脚本、会联网时的审核结果 | 门户结果，登记进规则表 | 提交时（用户在门户操作） |
| P-V3 | WorkBuddy 能否接受 `.js`、`.css`、`.html` 模板和 `category: design` | 上传结果 | 上传时（用户） |
| P-V4 | 检查脚本的测试是否成对（本仓库 EV-20261103-005，Guarded） | 新测试按“必须报出 / 必须放过”成对编写 | 本周期 M1 |
| P-V5 | 从 tealun 市场安装能用 | `/plugin install design-to-dev@tealun` | plugin 分支生成后（用户） |

## 6. 阶段

- **M1**：规则表、脚本、工作流、`.gitattributes`、plugin.json、PRIVACY.md、README、图标、AGENTS.md、测试；`claude plugin validate` 和 publish 演练通过。
- **M2**：新 agent 试跑，按结果迭代。
- **M3**：auditor 写 1.4 报告；evolver 记台账和 compliance log；在 tealun-plugins 开上架 PR；更新 PR #1。合并、推 tag、门户提交和 webhook 配置由用户决定和操作。

## 7. 消费的台账条目

- 本仓库 EV-20261103-001：并入 build_plugin 的发布门禁（P-D4）。
- 本仓库 EV-20261103-005：写成待验证 P-V4。
- 本仓库 EV-20261102-001：参照仓库只读，不修改（本规划的约束）。
- dev-pdca EV-20261102-001、EV-20261102-003、EV-20261105-002、EV-20261105-003：分别落到 P-D3、P-D3、P-D6、P-D5 与 P-D7。
- 其余条目：none relevant。

# design-to-dev 1.4.0 发布前审计

## Scope

- Baseline: `claude/bold-mendel-7zvnkp@8242ab9`；工作区干净；观察时间 2026-11-05T05:50Z。
- Anchor: `99_03_release_audit_v1.3.0.md`，状态在 1.3.1（`7a87ad3`）全部关闭。变更范围 `7a87ad3..8242ab9`：4 个提交，45 个文件（+1793 / −394）。
- Included: 照搬 tealun-dev-pdca 的发布规范（`plugin.json` 唯一版本源；`build_plugin.py`、`build_suite.py`、`publish_plugin_branch.sh`、`check_ledger.py`；`check.yml`、`release.yml`、`plugin-branch.yml`；两份平台规则对照表；PRIVACY.md 与数据问卷；README 安装方式；AGENTS.md），以及新 agent 试跑反馈的修复（模板、`check_output.py`、`palette.py`、`tokens_json.py`、SKILL.md 与 references）。
- Depth and reason: standard。改动触及发布与部署（tag 触发的 Release、CI 写分支、`contents: write` 权限），属于供应链和运维面；技能本身没有认证、支付或用户数据。
- Delegation: 无。范围集中在 3 个工作流、4 个脚本和文档，主审计直接逐文件检查；dev-pdca 的对应文件作为对照（只读，`/home/user/tealun/tealun-dev-pdca@c78834a`）。
- Evidence limits: 没有真实推过 tag，plugin 分支和 Release 只在本地裸仓库演练过；插件目录门户审核、WorkBuddy 实际上传、tealun 市场安装都没有验证（P-V1、P-V2、P-V3、P-V5）。`8242ab9` 的 CI 在观察时仍在运行。

## Verdict

- P0: 0 | P1: 1 | P2: 2
- Main risk: 推 tag 时 `plugin-branch.yml` 与 `release.yml` 并行而且各自校验，前者缺少 tag 与版本一致、CHANGELOG、单元测试这几道门；Release 失败时 plugin 分支照样更新，市场用户会装到一个没有 Release 的版本。

## Prior Findings (99_03)

| ID | Status now | Evidence |
| --- | --- | --- |
| F1–F5、V1–V6、N-01、N-02、F-05、F-07、F-08、F-16、R-8、C1、C2、C5、C6 | Fixed (1.3.1)，未回退 | 对应回归测试仍在 `tests/test_scripts.py`、`tests/kit.test.js`，本基线 65 个单元测试与两组浏览器测试全部通过 |

## Critical Paths

- 推 tag → Release 附件：**Healthy**。`release.yml` 依次跑 WorkBuddy 校验、台账、单元测试、`--check --tag --since`、构建、固定版本 CLI 的 `plugin validate`、CHANGELOG 生成说明；附件文件名与本地构建产物一致（`dist/design-to-dev-1.4.0.plugin`、`.zip`、`design-to-dev-workbuddy-1.4.0.zip`、`-flat.zip`）。
- 推 tag 或手动触发 → plugin 分支：**At risk**（A-01、A-02）。只写打包产物、只追加不改写历史已在本地裸仓库演练（首推建分支、内容不变不提交、内容变化追加一个提交）。
- 每次推送 → 校验：**Healthy**。`check.yml` 排除 plugin 分支；`179499a` run 41974753385 success。
- 设计输入 → 原型 → 检查器：**Healthy**。试跑反馈 17 条中可在代码里核实的 6 条（#2、#5、#7、#10、#13、#17）都先写了修复前失败的测试，修复后通过；其余为文档条目，已逐条落到 SKILL.md 或 references。

## Confirmed Strengths

- 版本只来自 `plugin.json`；`check_skill` 拒绝 `metadata.version`，`workbuddy_fields` 拒绝 `version`，打包时注入（`tests/test_build.py` 有成对测试）。
- `* -text` 与导出一致性检查、提交的 zip/`.plugin`、README 下载即执行命令、仓库内 `marketplace.json` 都由 `build_plugin.py --check` 拦截，且各有“必须报出 / 必须放过”测试。
- PRIVACY.md、README、SKILL.md 与 `docs/claude-directory-rules.md` 的数据问卷答案一致：唯一联网是 `fetch_fonts.py`，发送去重字符集合，`--latin` 不发送原型文字，运行前征得同意。
- 发布审计门只在发布路径（`--tag`、`--release`）生效，开发期 CI 不会因还没有报告而长期红。

## Findings

| ID | Severity | Type / Confidence | Status | Finding | Location | Evidence | Remediation |
|---|---|---|---|---|---|---|---|
| A-01 | P1 | Confirmed (static) / High | Fixed (1.4.0) | 推 tag 时 plugin 分支的门禁比 Release 少：不校验 tag 等于 `v<plugin.json 版本>`、不要求 CHANGELOG 小节、不跑单元测试和 WorkBuddy 校验。两个工作流由同一事件并行触发，互不依赖，所以 `release.yml` 因这些门失败时，`plugin-branch.yml` 仍会把内容推上 plugin 分支。 | `.github/workflows/plugin-branch.yml:35-42`；对照 `release.yml:30-38` | `plugin-branch.yml` 只运行 `build_plugin.py --check --release`；`check()` 只在 `tag is not None` 时比对 tag 与版本、检查 CHANGELOG（`scripts/build_plugin.py:171-175`）。例：`plugin.json` 为 1.4.0 时推 `v1.4.1`，Release 报 “tag v1.4.1 does not match”，plugin 分支照样得到 1.4.0。dev-pdca 的同名工作流也是这样（只跑 `--check`），属于照搬时一并带入。 | tag 触发时与 Release 用同一组门：`--check --tag "$GITHUB_REF_NAME"`，并运行单元测试。 |
| A-02 | P2 | Confirmed (static) / High | Fixed (1.4.0) | 手动触发只限 main，但不要求当前版本已经发布：main 上合入了未打 tag 的新版本时，手动触发会把未发布的内容写进 plugin 分支，违反 tealun-plugins 的“用户只会装到已发布的版本”。 | `.github/workflows/plugin-branch.yml:22-23` | `if:` 只判断 `refs/heads/main` 或 `refs/tags/v*`；手动路径的 `--release` 只要求审计报告存在，不要求 tag `v<版本>` 存在。 | 手动触发时检出 `v<plugin.json 版本>` 这个 tag 再构建；tag 不存在就失败。 |
| A-03 | P2 | Verification gap / Medium | Partly fixed (1.4.0) | `release.yml` 不跑示例检查和浏览器测试，依赖同一提交在分支推送时已由 `check.yml` 跑过。tag 打在没有推过分支的提交上时，这两项不会运行。 | `.github/workflows/release.yml` | 对照 `check.yml:34-46`。正常流程（合并到 main 后在 main 上打 tag）不受影响。 | 发布说明写明 tag 只打在 main 的提交上；或在 release.yml 补跑 `check_output.py` 示例检查（浏览器测试耗时，可不补）。 |

## Rejected Candidates

- `.app { max-width: calc(token + 2 × space-5) }` 遇到百分比 token 会溢出：模板与参考都用 px，参考写明 token 是内容宽度，不成立。
- 新的“字体未打包”警告在设计师拒绝下载字体时必然出现：这是预期的（试跑 #16、#17），SKILL.md 要求在收尾里解释警告并写明截图用的字体。
- `check.yml` 只设 `branches-ignore`，推 tag 不会触发：符合设计，tag 由 release.yml 负责。

## 12-Dimension Coverage

| Dimension | Result |
| --- | --- |
| Architecture | 发布产物、plugin 分支、市场条目三者分离，与 dev-pdca 一致 |
| Platform integration | 插件目录与 WorkBuddy 规则表齐全；门户、上传、安装未实测（P-V2、P-V3、P-V5） |
| Security | `contents: write` 只给两个发布工作流；未用第三方 action 之外的脚本来源；CLI 固定版本 |
| Code efficiency | `palette.py --cols` 按 2 像素行采样，2880 宽图在可接受范围 |
| Runtime smoothness | 忙碌按钮保持原色（kit 测试） |
| Information isolation | N/A：技能不处理用户账户数据；联网范围见 PRIVACY |
| Data accuracy | `tokens_json.py` 的 `$description` 不继承（测试） |
| Parameter passing | `palette.py` 新参数错误时返回 2（测试） |
| User experience | 试跑 17 条已落地；审美定稿仍待设计师评审 |
| Coding standards | 检查脚本每处改动有成对测试 |
| Testing | 65 个单元测试、kit 与示例浏览器测试本地通过 |
| Deploy and operations | A-01、A-02、A-03 |

## Checks Run

- `python3 -m unittest discover -s tests`：Ran 65 tests, OK。
- `node tests/kit.test.js`、`node tests/example.test.js`：all passed。
- `python3 skills/design-to-dev/scripts/check_output.py examples/readlog/output`：PASS, 0 errors, 0 warnings。
- `python3 scripts/build_plugin.py --check`：ok；`python3 scripts/build_suite.py --check`：ok（57 KB，20 个文件）；`python3 scripts/check_ledger.py`：ok。
- `python3 scripts/build_plugin.py && python3 scripts/build_suite.py`：产物名与 `release.yml` 附件一致。
- 上一轮已验证：构建出的 `dist/design-to-dev` 通过 `claude plugin validate`（2.1.318）；plugin 分支发布在本地裸仓库演练三种情形。

## Fix Verification (same day)

- A-01：`plugin-branch.yml` 改为 `--check --tag "$RELEASE_TAG" --since <上一个 tag>`，并跑 WorkBuddy 校验、台账、示例检查和单元测试，与 `release.yml` 同一组门。本地按工作流原文执行该步骤：`RELEASE_TAG=v1.4.1` 时报 “tag v1.4.1 does not match plugin.json version 1.4.0”，退出码 1；`--tag v1.4.0` 时 ok。
- A-02：手动触发先找 `v<plugin.json 版本>` 这个 tag 并检出它再构建。本地临时克隆中执行该步骤：没有 tag 时报 “v1.4.0 is not released yet”，退出码 1；打 tag 后退出码 0，`HEAD detached at v1.4.0`。
- A-03：`release.yml` 补跑示例的 `check_output.py`；浏览器测试仍只在 `check.yml` 跑，tag 应打在已推到 main 的提交上。
- 工作流 YAML 解析通过；真实的 tag 推送仍待 P-V1。

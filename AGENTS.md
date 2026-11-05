# design-to-dev 仓库的 Agent 指令

本仓库开发 design-to-dev：一个独立发布的技能，以 Claude 插件形式发布到 tealun 市场和 Claude 插件目录，同时打成 WorkBuddy 包。技能源码在 `skills/design-to-dev/`；`examples/readlog/` 是完整示例；`.claude-plugin/plugin.json` 是插件清单和唯一的版本来源。

## 配套技能：要调用，不要只“照着精神做”

本仓库用 Tealun Dev PDCA 套件（`tealun/tealun-dev-pdca`）的技能工作。触发条件满足时，通过技能工具调用对应技能；技能工具里看不到时，读取该套件对应技能的 `SKILL.md` 并按步骤执行。只按“大意”去做不算调用。每个会话的第一条回复，先说明这六个技能里哪些可用；缺哪个就直说。

- **planner：任何规划意图，不论大小。** 新功能、技能结构调整、发布方式、文档体系或流程。在改文件之前调用，先把决定写进 `docs/` 下对应的规划文档。
- **tasker：任何对文件或状态的改动，包括看起来很小的修补。** 动手前写清完成定义和一个可执行的检查；收尾时给出证据（命令输出、读回结果），不要只给描述。只读的问答不需要。
- **bugfixer：用户说有问题或“还是不对”、某个检查失败、CI 失败、外部平台（插件目录、WorkBuddy、市场）上传或审核被拒时。** 先复现或直接观察，证明原因，只修这个原因，再验证最初的症状已经消失，并补一条修复前会失败的回归测试。
- **auditor：推送影响发布包、工作流、共享规则的改动之前，发布之前，以及任何审计请求。** “做过审计”只指正式调用 auditor 并把报告写进 `docs/99_audits/`。
- **evolver：用户报告的问题修好并验证之后、同一周期内第二次被纠正之后、以及每个工作周期结束时。** 把经验和对应的防线记到 `docs/98_evolution/evolution-ledger.md`；同时在 `docs/98_evolution/compliance-log.md` 按 5 道 Gate 各记一行，写明是否遵守和证据。
- **explainer：用户想看懂某块代码、某个功能流程、某次改动或改动影响时。** 只读。

## 本仓库的硬规则

- **本仓库是公开的。** 文件和提交信息里不写内部决策、会话编号、私有仓库名和商业安排，只写对使用者和贡献者有用的内容；遵守率记录只写周期名称，不写会话编号。提交信息末尾只写 `Co-Authored-By`，不写 `Claude-Session` 行；PR 描述也不写会话链接（2026-11-05 起，已有提交不改写）。`build_plugin.py --check` 拦截已跟踪文件里的会话链接和会话编号。
- **本仓库是独立发布的技能。** 不要把它的文件写进 tealun-dev-pdca 或其他仓库。唯一的例外是上架：在 `tealun/tealun-plugins` 的 `marketplace.json` 加或改本插件那一条，README 插件表同步一行，改动走 PR。
- **发布到任何平台之前，先查清它的全部规则。** 规则逐条登记到对照表（Claude 插件目录见 `docs/claude-directory-rules.md`，WorkBuddy 见 `docs/workbuddy-rules.md`），每条要么写进本地检查（`scripts/build_plugin.py --check`、`scripts/build_suite.py --check`），要么写明不检查的原因；本地通过后再上传。不要用平台的报错来逐条试规则，也不要只挑带数字的规则做检查。平台新报出的问题，先登记进对照表再修。
- **版本只写在 `.claude-plugin/plugin.json`。** SKILL.md、`workbuddy.yaml` 不写版本，打包时注入。改了 `skills/` 下任何文件，就升版本，并在 `CHANGELOG.md` 加一节 `## design-to-dev <版本> — <日期>`。升法：删技能或改变已有输出格式（目录结构、HANDOFF 章节、token 命名）升 major；新增行为、改变触发描述或工作流程升 minor；其余（修复、措辞、文档）升 patch。CI 用 `build_plugin.py --check --since <上一个 tag>` 拦截没升版本的改动。
- **发布只靠推送 `v<版本>` tag。** 两种推法：命令行 `git push origin v<版本>`；或在 GitHub 网页 Releases → Draft a new release，新建 tag `v<版本>`、目标 main，直接发布，附件和说明由 `release.yml` 自动补上。 `.github/workflows/release.yml` 构建 `.plugin`、`.zip` 和 WorkBuddy 包，并附到 Release 上。不手动上传 Release 附件，也不把 zip、`.plugin` 提交进仓库（`--check` 会拦截）。每个 MAJOR.MINOR 版本发布前，要有 `docs/99_audits/*release_audit_vX.Y*.md`（发布工作流里的 `--check --tag`/`--release` 会拦截）。
- **`plugin` 分支只由 `.github/workflows/plugin-branch.yml` 写入。** 插件目录和 tealun 市场跟踪这个分支。它只包含打包好的插件，不要手动往里提交，也不要把开发文件（CI、脚本、测试、文档）放进去。
- **本仓库不放 `marketplace.json`。** 市场条目在 `tealun/tealun-plugins`，source 写 `{"source":"github","repo":"tealun/design-to-dev","ref":"plugin"}`。
- **`.gitattributes` 保持 `* -text`。** 任何会改写导出内容的属性都会让插件目录的 Validate 失败（`--check` 会拦截）。
- **README 不写下载后直接执行的命令**（`curl | sh`、`git clone` 后运行脚本、`npx` 等）。安装方式写成：市场安装命令，或从 Release 下载后上传或手动放置（`--check` 会拦截）。
- **插件只含技能。** 不加 MCP、hooks、`bin/` 或命令；技能脚本的网络行为必须在 `PRIVACY.md`、README 和 `SKILL.md` 里写明，与插件目录数据问卷的答案一致（`docs/claude-directory-rules.md` 的“数据问卷答案”）。
- **插件目录提交由用户在门户完成。** 每个插件单独提交一次；第一个版本要经 Anthropic 审核员批准；提交后配置 GitHub push webhook，secret 只显示一次，要当场保存。
- **新增或大改技能的工作流之后、发布之前，** 派一个只拿到 `skills/design-to-dev/SKILL.md` 路径的全新 agent，在真实输入上按技能执行一次，要求它列出指令不清、矛盾或缺失之处；核验它的产出后按反馈迭代。样本只读，产出写到会话 scratchpad，不写进本仓库或样本仓库。
- **改了模板 `proto-kit.js` 或模板基础样式，** 同步到 `examples/readlog/output/prototype/`（`ExampleInSync` 测试拦截）；改了 Readlog 的文案或页面，运行 `python3 skills/design-to-dev/scripts/fetch_fonts.py examples/readlog/output/prototype "Noto Serif SC:700" "Noto Sans SC:400,500"` 重新生成字体子集。
- **视觉自查不自评打分。** 客观项以 `check_output.py` 的警告为准，审美定稿由用户评审；示例里写的任何效果都要有测试或检查证明它真的存在。
- **修改检查脚本**（`build_plugin.py`、`build_suite.py`、`check_output.py`、`palette.py`、`fetch_fonts.py`）**时，每处改动同时写一条“必须报出”和一条“必须放过”的测试。**

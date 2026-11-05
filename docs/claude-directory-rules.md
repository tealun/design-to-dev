# Claude 插件目录规则对照表

提交 Claude 插件目录、上架 tealun 市场之前要满足的已知规则，以及每条规则由什么检查。新增规则时，先在这里加一行，再补校验；能写成本地检查的就写进 `scripts/build_plugin.py --check`，写不了的要注明原因。

插件目录跟踪 `plugin` 分支。这个分支只由 `.github/workflows/plugin-branch.yml` 写入，内容就是 `build_plugin.py` 打出的包（`dist/design-to-dev/`）：`.claude-plugin/plugin.json`、`skills/design-to-dev/`、README.md、LICENSE、PRIVACY.md、图标、README 用到的预览图。仓库的 CI、脚本、测试、文档和示例都不在包里。

**来源**：规则逐条照搬自 `tealun/tealun-dev-pdca` 的 `docs/claude-directory-rules.md`（@ c78834a，2026-11-05 读取），那份表的来源是：
- **提交**：[Submit a plugin](https://claude.com/docs/plugins/submit)
- **清单**：[Pre-submission checklist](https://claude.com/docs/plugins/pre-submission-checklist.md)
- **构建**：[Build a plugin](https://claude.com/docs/plugins/build.md)
- **参考**：[Plugins reference](https://code.claude.com/docs/en/plugins-reference)
- **门户**：tealun-dev-pdca 提交时门户的实际报错与提示

另外两类来源：
- **规范**：[Agent Skills specification](https://agentskills.io/specification)
- **本仓库**：本仓库的规划和台账

**检查级别**：
- **阻断**：`--check` 报错，CI 失败；
- **提示**：`--check` 打印 warning，不阻断，因为目录对这类问题的处理是转人工审核。

## 提交与托管

| 规则 | 来源 | 本地检查 |
| --- | --- | --- |
| 目录只从 github.com 上的仓库读取插件 | 提交 | 不校验：仓库托管在 GitHub 上是既定事实 |
| 提交和验证期间仓库可以是私有的，上架前必须公开 | 提交 | 不校验：`tealun/design-to-dev` 已公开；属于 GitHub 设置 |
| 每个插件文件夹单独提交一次；同一组织对同一仓库加文件夹只能有一个提交 | 提交 | 不校验：本仓库只有一个插件，插件路径留空（plugin 分支根目录） |
| 每个组织 24 小时内最多创建 10 个提交，草稿和撤回的也计入 | 提交 | 不校验：属于门户操作次数 |
| 首次提交后，目录跟踪的分支一有新提交就扫描、检查、发布；本仓库跟踪 `plugin` 分支 | 提交 | 不校验：在门户里设置 |
| 第一个版本必须由 Anthropic 审核员批准才能上线；Auto-publish 只对之后的版本生效 | 门户 | 不校验：门户流程 |
| 已有提交（含草稿）时再新建会报 `SUBMISSION_EXISTS`；继续草稿时仓库、文件夹和分支都不能改 | 门户 | 不校验：门户操作。首次创建时 Source 就选 `plugin` 分支 |
| 目录约每 6 小时检查一次跟踪的分支；配置 GitHub push webhook 后几分钟内拾取。webhook 的 secret 只显示一次 | 门户 | 不校验：仓库设置。提交后由用户配置并保存 secret |
| 提交时要回答数据处理问卷，并勾选 4 项合规声明；答案要和 `PRIVACY.md` 一致 | 门户 | 部分校验：`check()` 要求 `PRIVACY.md` 存在。问卷答案本身不能本地校验，按下文“数据问卷答案”填写 |
| 每次扫描都会重新校验目录规则，并做安全扫描（未披露的外发数据、隐藏代码、修改权限设置）；首次提交没通过安全扫描直接被拒；另有政策审核 | 提交 | 部分校验：`claude plugin validate` 只覆盖一部分；外发数据在 PRIVACY.md、README、SKILL.md 和 `fetch_fonts.py` 文档字符串里披露 |
| 插件含 MCP、hooks 或可执行脚本时审核更严，且这些组件只能在 Claude Code 里用；只有技能的插件哪里都能用 | 用户经验 | 不校验：本插件只有技能，没有 MCP、hooks、`bin/`。技能里有 4 个 Python 脚本（由 Claude 在会话里按需运行），其中 `fetch_fonts.py` 会联网，预期审核更严；结果待提交后登记（规划 P-V2） |

## 数据问卷答案（与 PRIVACY.md 一致）

| 问题 | 答案 | 依据 |
| --- | --- | --- |
| 是否处理个人数据 | No | 技能不读取或保存个人数据；示例数据都是虚构的 |
| 是否向外发送数据 | Yes：仅 `fetch_fonts.py`，由用户同意后触发，请求 fonts.googleapis.com / fonts.gstatic.com，内容为原型用字的去重集合（`--latin` 时不发送） | `skills/design-to-dev/scripts/fetch_fonts.py` 源码；其余 3 个脚本没有网络访问 |
| 数据保留 | Not retained | 插件没有服务器，不保存任何数据 |
| 是否面向未成年人 | No | 面向设计师与开发者 |

## 清单（plugin.json）

| 规则 | 来源 | 本地检查 |
| --- | --- | --- |
| 清单位于 `.claude-plugin/plugin.json`，`name` 必填 | 参考 | 阻断：`check()` 读取清单，缺 `name` 报错 |
| 应设置 `description`、`author`、`version` | 清单 | 阻断：`check()` 要求都有 |
| 名称只能用小写字母、数字、连字符，最长 64，首尾为字母或数字；不能是保留名；不能以 `claude-`、`anthropic-`、`anthropics-`、`cc-plugin-` 开头 | 清单 | 阻断：`NAME_PATTERN`、`RESERVED_NAMES`、`RESERVED_PREFIXES` |
| 设了 `version` 就要在每次发布时升高；Claude Code 固定使用这个版本直到它改变 | 提交、参考 | 阻断：`--since <上一个 tag>`，技能有改动但版本没升高时报错 |
| `plugin.json` 是唯一的版本来源（SKILL.md、workbuddy.yaml 不得另写版本） | 本仓库 | 阻断：`check_skill()` 拒绝 `metadata.version`；`workbuddy_fields()` 拒绝 `version` |
| `skills` 是以 `./` 开头、位于插件内的目录路径 | 参考 | 阻断：`check()` 检查前缀和 `..`，并要求与 `skills/*/SKILL.md` 一致 |
| 插件仓库里不放自己的 `marketplace.json`（会和 tealun 市场重名冲突） | 本仓库 | 阻断：存在 `.claude-plugin/marketplace.json` 即报错 |
| `icon` 是插件内图片文件的路径；目录在提交时读取 | 参考 | 阻断：`icon` 指向的文件必须存在 |
| 图标规格：512–2048 px 正方形、小于 2 MB、不接受 SVG/WebP | dev-pdca 转述 | 不校验：官方页面没找到原文。本仓库图标为 512×512 PNG（13 KB），由 `scripts/make_icon.py` 生成 |
| 上架页文字取自 `plugin.json` 和 README | 提交 | 不校验：属于文案 |
| `documentationUrl`、`privacyPolicyUrl`、`supportUrl`、`icon` 会被报为 UNKNOWN_KEY 提示，门户写明不需处理 | 门户（dev-pdca） | 不校验：合法字段的提示 |

## 技能文件（Agent Skills 规范）

| 规则 | 来源 | 本地检查 |
| --- | --- | --- |
| `SKILL.md` 有 YAML frontmatter，必填 `name`、`description` | 规范 | 阻断：`build_suite.check_skill()` |
| `name` 1–64 字符，只含 `a-z0-9` 和单个连字符，等于文件夹名 | 规范 | 阻断：同上 |
| `description` 1–1024 字符；`compatibility` 1–500 字符 | 规范 | 阻断：同上 |
| 只允许规范字段（name、description、license、compatibility、metadata、allowed-tools） | 规范 | 阻断：同上 |
| `SKILL.md` 少于 500 行 | 规范 | 阻断：同上 |
| 文件引用相对技能根目录且存在 | 规范 | 阻断：`check_skill()` 检查 Markdown 链接；`check()` 检查 `references/`、`scripts/`、`templates/` 的引用 |

## 文件与内容

| 规则 | 来源 | 本地检查 |
| --- | --- | --- |
| 插件里要有 README，代码块之外至少 40 个单词 | 清单 | 阻断：`check()` 统计 README.md |
| README 不能有下载后直接执行的安装步骤（curl \| sh、git clone 后运行、npx 等） | 门户（dev-pdca）、用户经验 | 阻断：`DOWNLOAD_AND_RUN` 检查 README.md 与 README.en.md |
| 要有 `LICENSE` 或在 `plugin.json` 设 `license` | 清单 | 阻断：两者都没有时报错 |
| 单个文件超过 5 MiB，校验会停止 | 清单 | 阻断：对包内每个文件检查 |
| 不能有符号链接 | 清单 | 阻断：对包内每个文件检查 |
| 不能有子模块和 LFS 指针 | 清单 | 不校验：仓库没有 `.gitmodules`，没有用 LFS |
| 仓库导出内容必须和存储内容一致：`.gitattributes` 不能有 `export-ignore`、`filter`、会改动换行的 `eol`/`text` 规则 | 门户（dev-pdca EV-20261105-002） | 阻断：`content_rewriting_attributes()` 要求 `* -text`、拒绝改写内容的属性；`export_mismatches()` 导出索引后逐个比对 |
| 文件名不能含冒号或反斜杠、不能以点或空格结尾、不能是 Windows 设备名、不能有只差大小写的同名文件 | 门户（dev-pdca） | 不校验：目前没有命中；包内文件名由本仓库控制 |
| 不提交 zip 或 `.plugin`（`.zip` 等二进制会转人工审核） | 清单、用户经验 | 阻断：被跟踪的 `.zip`、`.plugin` 报错；提示：包内其他二进制由 `directory_warnings()` 报出 |
| 图片和字体以外的文件超过 256 KiB，转人工审核 | 清单 | 提示：`directory_warnings()` |
| 文件超过 512 个，转人工审核 | 清单 | 提示：`directory_warnings()` |
| 删掉 `.DS_Store`、`Thumbs.db`、`desktop.ini`、`__MACOSX` | 清单 | 提示：`directory_warnings()`；打包时也排除 |
| 包启动器要固定版本，不能用 `@latest` | 清单 | 不校验：插件本身不调用启动器；工作流里的 `npx @anthropic-ai/claude-code@2.1.318` 已固定版本 |
| 凭据不能写死在代码里 | 清单 | 不校验：插件不需要凭据 |
| 顶层有 `bin/` 时 claude.ai 和 Cowork 无法安装 | 清单 | 不校验：包里没有 `bin/` |
| 安全扫描读不懂的编译或压缩代码转人工审核 | 清单 | 不校验：包里只有 Markdown、Python、JS、CSS、HTML 源码和图片 |
| 插件文件夹里的开发工具也会被扫描（CI 凭据、脚本、测试、CLAUDE.md 等曾导致 policy hold） | 门户（dev-pdca EV-20261105-003） | 结构上避免：目录跟踪的 `plugin` 分支只含打包产物，由 `plugin-branch.yml` 写入 |

## 安装包

| 规则 | 来源 | 本地检查 |
| --- | --- | --- |
| claude.ai 上传 zip（Customize > Plugins > Add > Upload plugin），zip 根目录要有 `.claude-plugin/plugin.json` | 构建 | 阻断：单元测试检查包结构；发布流程用固定版本的 CLI 校验解包后的 `dist/design-to-dev/` |
| `.plugin` 后缀 | dev-pdca 转述 | 不校验：官方页面没有说明。Release 同时附内容相同的 `.zip` 和 `.plugin`，README 指导上传 `.zip` |
| 每个 MAJOR.MINOR 版本发布前要有 auditor 报告 | 本仓库 EV-20261103-001 | 阻断（只在发布路径）：`release_audit()`，`--tag` 或 `--release` 时运行；`release.yml` 与 `plugin-branch.yml` 都会触发。开发中的推送不要求，避免整个开发期 CI 都红 |

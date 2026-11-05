# Privacy Policy

Last updated: 2026-11-05

design-to-dev is a skill for Claude: written instructions, templates and four small Python scripts that Claude may run in your project. It adds no MCP servers, hooks or commands, and has no server of its own.

- **We collect nothing.** The plugin does not collect, store, sell or send to its author any personal data, usage data or content.
- **Your conversations stay between you and Claude.** How Anthropic handles your conversations is governed by Anthropic's own privacy policy, not by this plugin.
- **Files stay in your project.** The skill writes the prototype, design tokens and handoff documents into the output folder you work in.
- **One optional network request: fonts.** `scripts/fetch_fonts.py` downloads open-licence fonts from Google Fonts (fonts.googleapis.com, fonts.gstatic.com) so the prototype shows real typography offline. To keep the download small, the request includes the set of characters used in your prototype (deduplicated and sorted, not your copy in order); with `--latin` it sends no prototype text. Claude asks you before running it; if you decline, the prototype uses system fonts. Google's handling of these requests is governed by Google's privacy policy.
- **The other scripts work offline.** `check_output.py`, `palette.py` and `tokens_json.py` only read and write files in your project.

Questions: open an issue at https://github.com/tealun/design-to-dev/issues.

---

# 隐私政策

最后更新：2026-11-05

design-to-dev 是一个给 Claude 用的技能：一份文字说明、几套模板，以及 4 个可能在你的项目里运行的 Python 小脚本。它不添加 MCP 服务器、hooks 或命令，也没有自己的服务器。

- **不收集任何数据。** 插件不收集、存储、出售任何个人数据、使用数据或内容，也不把它们发给作者。
- **对话只在你和 Claude 之间。** Anthropic 如何处理你的对话，适用 Anthropic 自己的隐私政策，与本插件无关。
- **文件留在你的项目里。** 原型、design tokens 和交接文档都写在你工作的输出文件夹里。
- **唯一可选的联网：下载字体。** `scripts/fetch_fonts.py` 从 Google Fonts（fonts.googleapis.com、fonts.gstatic.com）下载开源字体，让原型离线也能显示真实字体。为了让字体包更小，请求里会带上原型里用到的字符集合（去重并排序，不是按顺序的文案）；加 `--latin` 时不发送任何原型文字。Claude 运行它之前会先问你；你不同意时，原型用系统字体。Google 如何处理这些请求，适用 Google 的隐私政策。
- **其他脚本都在本地运行。** `check_output.py`、`palette.py`、`tokens_json.py` 只读写你项目里的文件。

有问题请在 https://github.com/tealun/design-to-dev/issues 提 issue。

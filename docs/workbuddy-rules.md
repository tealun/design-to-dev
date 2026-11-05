# WorkBuddy 上架规则对照表

`design-to-dev-workbuddy-<版本>.zip`（由 `scripts/build_suite.py` 生成到 `dist/`，发版时附在 Release 上）上传 WorkBuddy 前要满足的全部已知规则，以及每条规则由谁检查。新增规则时，先在这里加一行，再补校验；能校验的必须写进 `build_suite.py`，不能校验的写明原因。不要用平台的报错来逐条试规则，也不要只挑带数字的规则做校验（tealun-dev-pdca EV-20261102-001、EV-20261102-003）。

来源：
- **实测**：tealun-dev-pdca 上传或审核时实际报错过，见其 `docs/workbuddy-rules.md`（@ c78834a）；
- **第三方**：[wb-skill-converter 的 workbuddy-schema.md](https://github.com/starve001/wb-skill-converter/blob/main/references/workbuddy-schema.md)，非官方文档。

| 规则 | 来源 | 本地检查 |
| --- | --- | --- |
| 目录最多三层：根目录 / 二级目录 / 文件 | 实测 | `validate_package()`：超过即报错 |
| 包内只能有一个 `SKILL.md`（多个会被判为多 skill 包、资产无效） | 实测 + 第三方 | `validate_package()`：只允许根目录一个。本技能本来就只有一个，无需改名 |
| 其他 `.md` 不能带技能 frontmatter | 推断（避免被识别为第二个技能） | `validate_package()`：带 `name:` 的 frontmatter 即报错 |
| 必填 `display_name`、`display_name_en`、`description_zh`、`description_en` | 实测 | `workbuddy_fields()`，字段来自 `workbuddy.yaml` |
| 必填 `examples_zh`、`examples_en`，各 1–3 条 | 实测 | `workbuddy_fields()` |
| 必填 `name`、`description`、`version` | 第三方 | `name`、`description` 由 `check_skill()` 检查；`version` 打包时从 `.claude-plugin/plugin.json` 注入，`check()` 要求为 x.y.z |
| `name` 符合 `^[a-z0-9][a-z0-9-]{0,39}$` | 第三方 | `workbuddy_fields()` |
| `display_name_en` ≤ 60 字符 | 第三方 | `workbuddy_fields()` |
| `description_zh` ≤ 500 字符 | 第三方 | `workbuddy_fields()` |
| `description_en` ≤ 1000 字符 | 实测 | `workbuddy_fields()` |
| frontmatter 必须是合法 YAML（值里有 `: ` 要加引号） | 第三方 | 字段值统一加引号；单元测试用 YAML 解析打包后的 `SKILL.md` |
| 编码 UTF-8 无 BOM | 第三方 | `validate_package()` |
| 排除 `__pycache__`、`.DS_Store`、`*.pyc` 等 | 第三方 | `EXCLUDE_PATTERNS` |
| 压缩包根目录直接放 `SKILL.md`，不要多套一层目录 | 第三方 | 不校验：tealun-dev-pdca 实测内含一层文件夹的包能解析通过；被拒时改传 `-flat.zip` |
| `name` 全平台唯一 | 第三方 | 不能本地校验：只有上传时平台才能判断 |
| `category` 建议填写 | 第三方 | 已填 `design`，不强制校验；该取值是否被接受待首次上传确认（规划 P-V3） |
| 包里的非 Markdown 文件（`.js`、`.css`、`.html` 模板，`.py` 脚本）能否被接受 | 待验证 | 不能本地校验：tealun-dev-pdca 的包只含 `.md` 和 `.py`，没有先例；首次上传结果登记到本表（规划 P-V3） |

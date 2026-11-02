# design-to-dev 仓库的 Agent 指令

技能源码在 `skills/design-to-dev/`；`examples/readlog/` 是完整示例；`scripts/build.py` 校验平台规则并打包。

## 配套技能

本仓库按 Tealun Skills 的惯例工作：规划用 planner，任何改动用 tasker（先写完成定义和可执行检查，收尾给证据），检查失败或用户说“不对”用 bugfixer，发布前用 auditor，问题修好或周期结束用 evolver（台账：`docs/98_evolution/evolution-ledger.md`）。

## 硬规则

- 本仓库是独立发布的技能，不要把它的文件写进 Tealun-Skills 或其他仓库。
- 改了 `skills/design-to-dev/` 或 `workbuddy.yaml`：运行 `python3 scripts/build.py` 重新生成 `design-to-dev.zip` 并一起提交；CI 用 `--check` 拦截。
- 改了技能行为或触发描述：同步更新 `SKILL.md` 的 `metadata.version`、`workbuddy.yaml` 的 `version`、`.claude-plugin/marketplace.json` 的 `version` 和 `CHANGELOG.md`（build.py 校验它们一致）。
- 改了模板 `proto-kit.js`：同步复制到 `examples/readlog/output/prototype/`，并运行 `python3 skills/design-to-dev/scripts/check_output.py examples/readlog/output --mode B`。
- 发布到新平台之前，先把它的全部规则写进 `scripts/build.py`，本地通过后再上传。

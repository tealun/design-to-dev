# 示例：Readlog 读书打卡

用一个很小的产品把 design-to-dev 的全流程跑一遍。输入只有一段文字意图和一页品牌规范，没有视觉稿。

## 输入

- [`input/brief.md`](input/brief.md)：设计师写的产品意图。
- [`input/brand.md`](input/brand.md)：品牌规范节选（4 个颜色、字体、语气）。

设计师对 Agent 说：

```text
用 design-to-dev 把 input/ 里的 Readlog 做成可交互原型，输出到 output/。
```

## 第 1 步：理解意图（Agent 提问）

```text
我读了产品意图和品牌规范，开始之前确认 4 件事（回复“ok”就按我的建议）：
1. 页面：书架、书的详情、添加一本书，就这 3 个？（建议：是）
2. 必须走通的流程：添加一本书 → 在详情页记录今天读到第几页 → 书架看到进度？
3. 主要在手机上用？（建议：手机优先，桌面端居中显示）
4. 你说“先按自己继续开发准备”，那我用模式 B：除了交接文档，再生成一份给 planner 的规划输入？
5. 视觉：品牌规范我已读到。有没有 2–3 个你喜欢的 App 或截图作为视觉参考？
   没有的话选一个方向：现代精致极简（建议，安静精确，类似 Linear、Things）、编辑杂志感、温暖手作感。
```

设计师回复：“ok，没有参考，选现代精致极简；品牌色和标题字体必须按规范，其他你来定。”

理解卡：

```text
产品：Readlog 读书打卡 | 用户：想养成阅读习惯的上班族 | 设备：手机优先
页面：书架、书的详情、添加 | 核心流程：添加书 → 记录页码 → 看进度
模式：B（设计师继续开发）
视觉：现代精致极简预设 + brand.md 的品牌色与标题字体（无视觉参考）
假设：没有视觉稿，版式按品牌规范推导，全部标为【示意】；连续天数规则等标为【待定】
```

## 第 2–5 步：产出

| 产出 | 说明 |
| --- | --- |
| [`output/design-tokens/tokens.css`](output/design-tokens/tokens.css) | 77 个 CSS 变量，每行注释写明等级和来源 |
| [`output/design-tokens/tokens.json`](output/design-tokens/tokens.json) | 同名 W3C 格式，由 `scripts/tokens_json.py` 从 CSS 生成 |
| [`output/prototype/`](output/prototype/) | 双击 `index.html` 打开；3 个页面，书架有默认/空/加载/报错 4 种状态 |
| [`output/HANDOFF.md`](output/HANDOFF.md) | 页面、流程图、11 个组件与素材清单、交互、对比度、6 个待定问题 |
| [`output/PLANNER_BRIEF.md`](output/PLANNER_BRIEF.md) | 模式 B：交给 planner 的规划输入 |

原型里能试的：

- 书架 → 点第一本书 → 输入“50”点记录，看校验提示；输入“120”点记录，看进度更新。
- 右下角“原型工具”勾选“下次请求失败”，再记录一次，看失败提示且输入保留。
- 按 Shift+A 查看【确定】【示意】【待定】标注，悬停编号看说明。
- “添加一本书”直接点保存看校验，填好后保存会跳到新书详情。

## 第 6 步：检查

```bash
python3 skills/design-to-dev/scripts/check_output.py examples/readlog/output --mode B
```

```text
info  tokens: 77 (fixed 10, indicative 67, tbd 0)
info  pages: 3 (/, /book/:id, /add)
info  spec marks: fixed 9, indicative 5, tbd 5
info  open questions: 6
info  mode: B
PASS: 0 errors, 0 warnings
```

浏览器实测（Playwright，390×844）：三条流程点通、各状态截图、标注层开关、输入框内 Shift+A 不触发，无控制台报错。实测中发现并修正了两处：提示条遮住原型工具面板（改到顶部），琥珀色封面上的白字对比度只有 2.2:1（改用墨色字，并把对比度检查写进技能）。

1.2.0 按“现代精致极简”方向重做了全部页面：一个列表面板代替一书一卡片、渐变封面显示真实书名、连续阅读改为本周 7 天打点、数据组用等宽数字；交付前按 `references/visual-direction.md` 的视觉自查清单 12 项逐项核对。

# Spec levels, HANDOFF.md and closing

## Deciding the level

| Signal | Level |
| --- | --- |
| The designer said it must match; it is in the brand guide; it is a Figma variable or component the team owns | Fixed 【确定】 |
| Visible in the design but measured, approximated, or a reasonable variant you derived | Indicative 【示意】 |
| You had to invent behavior, copy or data rules; inputs conflict; the font or asset is unavailable; the design does not cover it | TBD 【待定】 |

Ask the designer to confirm only the items that would change a lot of work if wrong (core layout, brand color, main flow). Everything else follows the table.

## Marking the prototype

```html
<button class="btn btn--primary" data-spec="fixed" data-spec-note="Primary action, brand color, full width on phone">Add book</button>
<p class="hint" data-spec="tbd" data-spec-note="Daily goal rule not decided: pages or minutes?">…</p>
```

- Mark components and regions, not every text node: aim for 5–15 marks per page.
- Notes are one sentence a developer can act on.
- Every `tbd` note becomes a row in HANDOFF section 8 with a suggested answer and an owner.
- Shift+A or the Spec checkbox shows the marks as dashed boxes with numbered tags; hover a tag to read its note.

## Writing HANDOFF.md

Start from [../templates/HANDOFF.md](../templates/HANDOFF.md) and replace every `{{…}}`. Keep the numbered section headings; the checker looks for them.

- Pages: one row per `Proto.page()`, with its route in backticks and the states it supports.
- Flow: a Mermaid `flowchart` of the core flow and important branches (error, empty), plus numbered steps.
- Components: each reusable piece, its variants and states.
- Interactions: triggers and results, including validation, loading, error and retry.
- Tokens: a short summary; the files hold the details.
- Open questions: every TBD, each with a suggested answer and an owner.

Write in the designer's language. Avoid code in sections 0–6 except file names and routes.

## Closing modes

**Mode A — hand to a developer.** The developer will read HANDOFF.md first, then open the prototype. Make section 7 accurate (what is scaffolding, where real APIs go). In the summary to the designer, list the open questions they should answer before sending, and tell them to send the whole output folder (zip it).

**Mode B — continue development.** Also fill [../templates/PLANNER_BRIEF.md](../templates/PLANNER_BRIEF.md): the product, users, existing artifacts, core flow, decisions (Fixed items), constraints, items for planning to decide (stack, data, open questions) and a data sketch from `data.js`. Tell the designer the next step: start a planning skill such as planner with this file. Do not start building production code inside this skill.

## Checker

`scripts/check_output.py <output>` verifies the folder structure, that both token files list the same names with valid levels, that HANDOFF.md has its sections, a Mermaid flow and open questions, that every page in `pages.js` is listed in HANDOFF and vice versa, that spec marks use valid levels, that every TBD mark has open questions, that styles and pages use no raw colors, and that the prototype loads no remote scripts. Errors must be fixed; warnings must be read and either fixed or explained in the close.

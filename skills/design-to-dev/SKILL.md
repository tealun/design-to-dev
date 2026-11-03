---
name: design-to-dev
description: "Turn a designer's mockups or product intent into a runnable, clickable prototype plus design tokens and a developer handoff. For designers who know design but not much code. Inputs: screenshots, Figma links, brand guidelines, Claude Design output, or a plain-text product idea. Outputs: prototype/ (plain HTML/CSS/JS, opens by double-click, fake data, hover/empty/loading/error states), design-tokens/ (CSS variables + W3C JSON), and HANDOFF.md (pages, flow diagram, components, interactions, open questions), with every item marked Fixed, Indicative or TBD. Ends by handing off to a developer or by writing a brief for the planner skill. Use for: design to prototype, mockup or Figma to clickable prototype, a distinctive prototype from a product idea, design tokens and handoff for a prototype, design spec for developers. Not for building production features inside an existing codebase. 设计稿转原型、设计转代码、截图/Figma 做成可点击原型、提取设计规范/design tokens、设计交接文档、给开发的交付说明。"
license: MIT
compatibility: "Needs file read/write. Reading images needs a vision-capable model; Figma links need a Figma MCP server or exported screenshots. The prototype needs only a browser; check_output.py needs Python 3."
metadata:
  author: Tealun
  version: "1.3.1"
---

# design-to-dev

Help a designer turn designs or an idea into something that runs: a clickable prototype, the design rules behind it as tokens, and a handoff document a developer can build from. The designer may not read code. Talk in design language, keep code out of the conversation unless asked, and let the running prototype do the explaining.

## Outputs

Write everything into one output folder (default `./design-to-dev-output/`, or the folder the user names):

```text
<output>/
  prototype/        index.html, styles.css, proto-kit.js, data.js, pages.js
  design-tokens/    tokens.css, tokens.json
  HANDOFF.md
  PLANNER_BRIEF.md  only in mode B
```

The three spec levels used everywhere:

| Level | Mark | Meaning for the developer |
| --- | --- | --- |
| Fixed | 【确定】 `fixed` | Must match the design exactly. |
| Indicative | 【示意】 `indicative` | Shows intent; adjust freely within the tokens. |
| TBD | 【待定】 `tbd` | Not decided; the developer or team must decide. Always becomes an open question. |

## Conditional References

Load the reference for the step you are on:

- [references/intake.md](references/intake.md) — reading each input type, the question list, the understanding card.
- [references/visual-direction.md](references/visual-direction.md) — fidelity vs direction mode, the direction lock, direction menu, four pillars (type, color, motion, composition), atmosphere, anti-slop list, the quality bar and the two-part visual QA; adapted in part from the frontend-design skill by zxh. Read it before building styles.
- [references/design-tokens.md](references/design-tokens.md) — extracting tokens, naming, levels, the two file formats.
- [references/prototype.md](references/prototype.md) — default stack, proto-kit API, pages, states, fake data, when to use another stack.
- [references/annotation-and-handoff.md](references/annotation-and-handoff.md) — marking levels, HANDOFF.md, the two closing modes.

Templates in [templates/](templates/) are starting points to copy into the output folder, not files to edit in place. In commands below, `<skill-dir>` is the folder that contains this SKILL.md, and `<output>` is the output folder.

## Workflow

### 1. Understand the intent

Read every input first (see intake reference). Then ask one round of at most five questions, each with a suggested default, covering only what the inputs do not answer:

1. Which pages are in scope, and which one flow must work end to end?
2. Who uses it, and on what device (phone, desktop, both)?
3. Who gets the result: a developer (mode A) or the designer continuing development (mode B)?
4. The look: please share your VI / brand guide (colors, fonts, logo) and 2–3 visual references you like (products, screenshots, or a few mood words). Without them, pick a direction: refined minimal (default), editorial, or warm handmade.
5. Anything that must look exactly like the design, and anything that is just a sketch?

Always ask question 4 unless a VI and mockups are already provided. The look is the designer's call, never yours to guess.

If the user says “you decide” or skips a question, take the default and record it as an assumption. Then show a short understanding card (product, users, device, pages, core flow, mode, visual sources, assumptions) and, in direction mode, the direction lock from the visual direction reference: tone, display and body faces, dominant and accent colors, and the one memorable thing, written as concrete art direction and continue unless the user corrects it. Do not ask a second round unless an answer contradicts the inputs.

### 2. Extract the design rules

Build tokens for color, typography (family, size scale, weight, line height), spacing, radius, shadow, and motion if visible; add component state colors (hover, active, focus, disabled, error, success). Write `design-tokens/tokens.css` with a `level · source` comment on each token, then generate the matching `tokens.json` with `python3 <skill-dir>/scripts/tokens_json.py <output>/design-tokens/tokens.css`. Every token has a level and a source. For PNG screenshots, run `python3 <skill-dir>/scripts/palette.py <image>` first: it gives the exact colors and the scale factor (a 780 px wide phone shot is 2×, so divide measured sizes by 2). Exact colors sampled from the designer's own final design may be Fixed; sizes measured from an image are Indicative, snapped to a consistent scale.

### 3. Build the clickable prototype

Copy the five prototype templates (`index.html`, `styles.css`, `proto-kit.js`, `data.js`, `pages.js`) into `prototype/`. They are a neutral, refined-minimal starting point, not the look: restyle `styles.css` for the VI, mockups or the locked direction (faces, weights, radius, borders, density, atmosphere, page-load sequence), so no two products come out looking the same. Write `data.js` (fake data) and `pages.js` (one entry per page). When the copy is final, bundle the chosen faces with `python3 <skill-dir>/scripts/fetch_fonts.py <output>/prototype "Display Face:700" "Body Face:400,500"` (all families in one call; re-run after copy changes). Without network, keep the system fallback and record the fonts as TBD. Requirements:

- Every page in scope exists and every step of the core flow is clickable from the first page. If the flow ends on a page that was not designed (after sign-in, after checkout), add a minimal stub page marked TBD instead of inventing a design.
- Links to pages outside the scope get `data-out`: the kit shows a “not in this prototype” toast. List them as open questions.
- Logos, icons, photos and illustrations that are not supplied as files become labelled placeholders marked TBD and go in the HANDOFF asset list.
- Styles use token variables: no raw colors anywhere outside tokens, and sizes from tokens wherever the design defines them.
- Text meets WCAG AA contrast against its real background (4.5:1, or 3:1 for large text); check text on brand and accent colors with `palette.py --contrast <text> <background>`, never by estimate.
- Every page that shows data supports the `default`, `empty`, `loading` and `error` states; forms show validation errors; buttons and links have hover, focus and disabled styles.
- Saving uses `Proto.fake()` so the loading and error paths can be demonstrated; no backend, no network calls.
- It runs by double-clicking `index.html`: no build step, no server, no CDN script.

### 4. Mark what is fixed, indicative and TBD

Put `data-spec` and `data-spec-note` on the elements that matter: key layouts, components, copy, and anything uncertain. Behavior you had to invent (sorting, limits, validation rules, what happens after an error) is TBD unless the user confirmed it. A visual property you measured from an image (weight, size, spacing) is Indicative, not Fixed, unless a spec or the designer confirms it. Every TBD item must reappear in the HANDOFF open questions.

### 5. Write HANDOFF.md

Fill [templates/HANDOFF.md](templates/HANDOFF.md): how to open the prototype, page list with routes and states, a Mermaid flow diagram, component list, interaction details, the token summary, the spec-level table, and open questions with an owner and a suggested answer. Write it in the user's language.

### 6. Check and close

In mode B, write `PLANNER_BRIEF.md` first (see the closing modes below). Then run the checker and fix every error it reports before closing. It reads the mode from the HANDOFF “Handoff to” row, so in mode B it also checks the brief:

```bash
python3 <skill-dir>/scripts/check_output.py <output>
```

If you can drive a browser, open `prototype/index.html` at the design's width, walk the core flow and each state, and put each screenshot side by side with its source design. Fix visible differences in anything marked Fixed (color, weight, size, order); a page that renders blank or unstyled is a failure even when the checker passes. Then run the two-part visual QA in the visual direction reference: part A comes from the checker's warnings (fix or explain each), part B is answered from the screenshots with what you saw, never as a score. When there is a source design, measure both screenshots with `palette.py --rows` instead of judging by eye. Without a browser, say the visual check was not seen. The final aesthetic call belongs to the designer: report it as awaiting their review.

Then close in the chosen mode:

- **Mode A, hand to a developer:** make HANDOFF.md self-explanatory, put open questions first in the summary, and tell the designer what to send (the whole output folder).
- **Mode B, continue development:** also write `PLANNER_BRIEF.md` from [templates/PLANNER_BRIEF.md](templates/PLANNER_BRIEF.md) and tell the designer to start the next stage with it, for example “use planner with PLANNER_BRIEF.md”.

Close with plain-language results for the designer: how to open the prototype, what to click to see the core flow and the states, how to show the spec marks (the Spec checkbox under “Prototype tools”, or Shift+A), the open questions that need their decision, the direction lock, the visual QA notes (part A warnings and part B observations), and the checker result.

## Rules

- Do not invent brand facts. If a color, font or rule is not in the inputs, choose a sensible value, mark it Indicative or TBD, and list it.
- Never ship a page the designer has not asked for just to look complete; list suggested extra pages as open questions instead.
- Keep real or personal data out of fake data; use obviously fictional names. For sign-in or payment flows, use a fictional demo account, write it in HANDOFF section 0, and never send any input over the network.
- If the input is someone else's product (a reference, a competitor, a public site), do not reproduce its name or logo: use placeholders and say so in HANDOFF.
- Fonts: use the brand font if it is a free web font or installed system font; otherwise use a system stack and record the real font as TBD.
- If the designer asks for React, Vue or another stack, read the prototype reference first; keep the same tokens, levels and HANDOFF.

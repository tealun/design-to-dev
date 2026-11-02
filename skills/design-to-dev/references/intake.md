# Intake: reading inputs and asking questions

## Read each input type

| Input | How to read it | What to extract |
| --- | --- | --- |
| Screenshot or exported image | Look at it at full size. Note the canvas width (390 suggests phone, 1440 desktop). Zoom mentally into buttons, cards, inputs. | Pages, regions, components, copy, colors, type sizes, spacing rhythm, icons, which states are shown. |
| Figma link | With a Figma MCP server: `get_metadata` for the frame list, `get_screenshot` per frame, `get_variable_defs` for variables and styles, `get_design_context` for exact values of a frame. Without one: ask for exported PNGs of each frame plus a screenshot of the local styles panel. | Same as screenshots, plus exact values and existing variable names. Reuse the file's variable names when they are sensible. |
| Brand guidelines (PDF, doc, page) | Read the color, typography, logo, voice and do/don't sections. | Fixed values: brand colors, fonts, logo rules, tone of voice. These are usually Fixed. |
| Claude Design or other generated output | HTML: read the CSS for values and the DOM for structure. Image or text: treat as screenshot or intent. | Structure and values; treat generated choices the designer did not confirm as Indicative. |
| Plain-text intent | Read for users, jobs, pages, flow, tone. | Pages and flow; every visual decision you make is Indicative. |

When inputs disagree (a screenshot uses a color not in the brand guide), prefer the more authoritative source (brand guide > Figma variables > screenshot > intent), note the conflict, and add it to open questions.

Record what each input contributed. This becomes the “Sources” section of HANDOFF.md.

## The question round

Ask once, at most five questions, each answerable in a few words and each with a default the designer can accept by saying “ok”. Skip any question the inputs already answer. Write for a designer: no words like route, component tree, state machine, API.

Example wording:

```text
I've read the 3 screens. Before I build, 4 quick questions (reply "ok" to take my suggestion):
1. Pages: Home, Book detail, Add book. Anything else? (suggested: these 3)
2. Must-work flow: add a book, then log today's reading from its page. Right?
3. Mainly used on a phone? (suggested: phone first, also fine on desktop)
4. Who gets this next: a developer (A), or you'll keep building it yourself (B)? (suggested: A)
```

Then the understanding card:

```text
Product: … | Users: … | Device: …
Pages: … | Core flow: …
Mode: A (developer handoff)
Assumptions: … (I'll mark these as Indicative/TBD)
```

## Defaults when the designer doesn't decide

- Device: phone first at 390px wide, centered on desktop.
- Pages: exactly those shown or named; nothing extra.
- Core flow: the main create-or-act action in the design.
- Mode: A.
- Language of UI copy: the language used in the design.

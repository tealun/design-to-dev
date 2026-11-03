# Intake: reading inputs and asking questions

## Read each input type

| Input | How to read it | What to extract |
| --- | --- | --- |
| Screenshot or exported image | Look at it at full size. For PNG run `scripts/palette.py <image>`: exact colors by share, plus the likely scale (780 px wide = 2× of a 390pt phone; divide every measured size by the scale). Use `--at x,y` to read one element's color. | Pages, regions, components, copy, exact colors, type sizes, spacing rhythm, icons, which states are shown, and links that lead to pages not in the material. |
| Figma link | With a Figma MCP server: `get_metadata` for the frame list, `get_screenshot` per frame, `get_variable_defs` for variables and styles, `get_design_context` for exact values of a frame. Without one: ask for exported PNGs of each frame plus a screenshot of the local styles panel. | Same as screenshots, plus exact values and existing variable names. Reuse the file's variable names when they are sensible. |
| Brand guidelines (PDF, doc, page) | Read the color, typography, logo, voice and do/don't sections. | Fixed values: brand colors, fonts, logo rules, tone of voice. These are usually Fixed. |
| Claude Design or other generated output | HTML: read the CSS for values and the DOM for structure. Image or text: treat as screenshot or intent. | Structure and values; treat generated choices the designer did not confirm as Indicative. |
| Plain-text intent | Read for users, jobs, pages, flow, tone. | Pages and flow; every visual decision you make is Indicative. |

Material that is not yours to copy: when the screenshot is another company's product used as reference, keep its layout and interaction ideas but replace its name, logo and distinctive brand assets with placeholders.

Assets: list every logo, icon, photo and illustration you see. Only files the designer supplies are used as-is; everything else becomes a placeholder marked TBD.

When inputs disagree (a screenshot uses a color not in the brand guide), prefer the more authoritative source (brand guide > Figma variables > screenshot > intent), note the conflict, and add it to open questions.

Record what each input contributed. This becomes the “Sources” section of HANDOFF.md.

## The question round

If links in the design lead to pages you were not given (forgot password, sign up, settings), name them in question 1 and suggest leaving them out of scope.

Ask once, at most five questions, each answerable in a few words and each with a default the designer can accept by saying “ok”. Skip any question the inputs already answer. Write for a designer: no words like route, component tree, state machine, API.

Always include the look question unless a VI and mockups are already in the material. Ask for the VI / brand guide and 2–3 visual references (screenshots or product names they like, or a few mood words); if they have none, offer the three presets from the visual direction reference with refined minimal as the default. References are for type, density, radius and color restraint, never for copying another brand.

Example wording:

```text
I've read the brief. Before I build, 4 quick questions (reply "ok" to take my suggestion):
1. Pages: Shelf, Book detail, Add book; the flow that must work is "add a book, then log today's reading". Right?
2. Mainly used on a phone? (suggested: phone first, also fine on desktop)
3. Who gets this next: a developer (A), or you'll keep building it yourself (B)? (suggested: A)
4. The look: do you have a VI / brand guide and 2–3 apps or screenshots whose feel you like?
   If not, pick one: refined minimal (calm, precise, like Linear or Things; suggested), editorial (magazine-like, serif titles), warm handmade (soft, rounded, notebook-like).
```

Then the understanding card:

```text
Product: … | Users: … | Device: …
Pages: … | Core flow: …
Mode: A (developer handoff)
Look: refined minimal preset + brand colors from brand.md (references: none)
Assumptions: … (I'll mark these as Indicative/TBD)
```

## Defaults when the designer doesn't decide

- Device: phone first at 390px wide, centered on desktop.
- Pages: exactly those shown or named; nothing extra.
- Core flow: the main create-or-act action in the design.
- Mode: A.
- Look: the brand guide if given, otherwise the refined minimal preset, stated in the understanding card and marked Indicative.
- Language of UI copy: the language used in the design.

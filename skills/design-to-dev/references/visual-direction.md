# Visual direction and quality bar

A prototype that works but looks like an unstyled admin panel fails the designer. Read this before building styles, and run the checklist at the end before closing.

## Where the look comes from

In priority order:

1. **The designer's VI / brand guide**: colors, fonts, logo rules, tone. Its values are Fixed.
2. **The designer's own mockups** (screenshots, Figma): match them; sampled colors may be Fixed, measured sizes are Indicative.
3. **Visual references** the designer likes (2–3 products, screenshots, mood words): borrow their type scale, density, radius, color restraint, never their brand names, logos or illustrations.
4. **A direction preset** below, chosen by the designer when 1–3 are missing. Default: Refined minimal.

Ask for 1 and 3 in the question round (see intake). Never invent a brand personality silently: if you choose, say which preset you used and mark its values Indicative.

## Principles (checkable)

| Area | Rule |
| --- | --- |
| Hierarchy | Build it with size, weight and color, not with boxes. One focal point per screen: the main content or the primary action. |
| Type | One sans family (plus at most one display family from the brand). 2–3 weights (400/500/600). Body 14–16px, line height 1.5. Titles 24–32px, line height 1.2–1.25, letter spacing −0.01 to −0.02em. Labels and meta 12–13px. Numbers use `font-variant-numeric: tabular-nums`. |
| Text color | At most three: primary, secondary, tertiary. Never pure black on pure white for large areas of text; use near-black (#18181b-like). |
| Color | Neutrals do 90% of the work. One accent, used only for the primary action, selection, progress and links. No large saturated fills except the one primary button. |
| Spacing | 4px base. Items inside a group 8–12px apart, groups 24–32px apart, page edges 16–24px (phone) or 32px+ (desktop). Section spacing is always larger than item spacing. |
| Surfaces | One elevation level per region. 1px hairline borders first, very soft shadows second, never a heavy border and a heavy shadow together. No card inside a card: inside a card use dividers or spacing. |
| Radius | One family: controls 6–8px, cards 10–12px, sheets/dialogs 14–16px, pills full. Nested radius = outer radius − padding. |
| Controls | Buttons and inputs in the same row share height (36–40px desktop, 44px+ phone) and radius. Primary, secondary and ghost buttons only. Visible soft focus ring. No unstyled browser controls. |
| Lists | Prefer one surface with dividers over a stack of separate cards. Leading visual (icon, avatar, cover) aligned on a fixed column; meta right-aligned and tertiary. |
| Placeholders | Must look intentional: tinted gradient covers with real text, initials in a soft circle, a quiet line icon. Never a single letter in a flat saturated square or a grey box labelled “image”. |
| Empty / loading / error | Designed as carefully as the default state: a line icon in a soft circle, one short sentence, one action. Skeletons match the real layout's shapes. |
| Icons | One set style: 16–20px, 1.5px stroke line icons drawn inline as SVG with `stroke="currentColor"`. |
| Motion | 120–200ms, ease-out, opacity and transform only, disabled under `prefers-reduced-motion`. |
| Text layout | Long text left-aligned, 45–75 characters per line. Truncate with ellipsis, never overflow. |

## Direction presets

Starting tokens for each direction; adapt to the product. All three keep the principles above.

| Token | Refined minimal (default) | Editorial | Warm handmade |
| --- | --- | --- | --- |
| Feel | Linear / Things: precise, quiet, dense but airy | Independent magazine: typographic, generous, rules and serif display | Notebook: soft, friendly, rounded, tactile |
| Background / surface | `#ffffff` / `#fafafa`, sunken `#f4f4f5` | `#faf9f6` / `#ffffff` | `#fbf7f0` / `#fffdf8` |
| Border | `#e4e4e7` hairline | `#e7e2d9`, 1px rules between sections | `#ece3d3`, softer |
| Text 1 / 2 / 3 | `#18181b` / `#52525b` / `#71717a` | `#1c1b19` / `#55524c` / `#7a766e` | `#2b2722` / `#6b6459` / `#857d70` |
| Accent | one cool accent, e.g. `#4f46e5`; primary button near-black `#18181b` | one deep accent, e.g. `#9f1d20` | one warm accent, e.g. `#c2643d` |
| Type | system sans; titles 600, −0.02em | serif display for titles (system serif stack), sans body | rounded-feeling system sans; titles 600 |
| Radius | 6 / 8 / 12 / 16 | 2 / 4 / 6 (nearly square) | 10 / 14 / 20 |
| Shadow | `0 1px 2px rgba(24,24,27,.05)`; popovers `0 8px 24px rgba(24,24,27,.08)` | none; use rules | `0 2px 8px rgba(43,39,34,.06)` |
| Density | controls 36–40px, compact lists | spacious, large titles 32–40px | controls 44px, generous padding |

The template files implement Refined minimal. For another preset, change tokens first, then only the component rules that the table says differ.

## Visual QA checklist

Run on the screenshots of every page and state, at the design's width, before closing. Fix every “no”, then list the results in the close (for example “Visual QA 12/12”).

1. Squint test: one clear focal point per screen.
2. One accent color, used only for primary action, selection, progress and links.
3. At most three text colors and three weights on any screen.
4. No card inside a card; no element with both a heavy border and a heavy shadow.
5. All spacing from the scale; sibling gaps equal; section gaps larger than item gaps.
6. Controls in a row share height and radius; focus ring visible.
7. Placeholders and empty, loading and error states look designed, not default.
8. Titles have tightened letter spacing; numbers are tabular; nothing overflows.
9. Icons share size and stroke; no emoji used as icons.
10. Nothing looks like an unstyled browser default.
11. Against the VI, mockups or references (when given): palette, type, radius and density match side by side.
12. Would a design lead accept this as a first-pass prototype without saying “it looks like a template”? If not, name what breaks it and fix that.

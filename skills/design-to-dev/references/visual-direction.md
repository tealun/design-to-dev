# Visual direction and quality bar

A prototype that works but looks like an unstyled admin panel or “AI-generated template” fails the designer. Read this before building styles. Parts of the method (direction lock, direction menu, four pillars, atmosphere, orchestrated motion, anti-slop list, benchmarks) are adapted from the frontend-design skill by zxh.

The template files are a neutral refined-minimal starting point. Their system display face is deliberate: the checker warns about it until you choose a face for the product.

Two modes:

- **Fidelity mode** — the designer gave mockups or a VI. Match them; their values win. Use this reference only for parts the design does not cover (states, placeholders, motion, gaps).
- **Direction mode** — there is only an idea, a brief or loose references. Lock a direction (below) and design with intent.

## 1. Where the look comes from

In priority order: (1) the designer's VI / brand guide, values Fixed; (2) their own mockups, sampled colors may be Fixed, measured sizes Indicative; (3) visual references they like, borrow type scale, density, radius and color restraint, never names, logos or illustrations; (4) a direction from the menu, chosen by the designer. Never pick a personality silently: if you choose, say so and mark it Indicative.

## 2. Direction lock (write it before any CSS)

Write one short paragraph in the understanding card, and later in HANDOFF section “Design direction”:

```text
Purpose: what the product does, for whom, in what moment of their day.
Tone: one direction from the menu, in one sentence of concrete art direction.
Type: display face + body face (names, weights, sizes), and why they fit.
Color: dominant color, supporting neutrals, one sharp accent, with hex values.
Memorable thing: the one detail someone remembers after closing the prototype.
```

Write it as art direction, never as adjectives: “Noto Serif SC Bold 40px, −0.02em, ink on warm paper, moss as the only accent; the shelf shows real-looking spines” — not “modern, clean and elegant”.

## 3. Direction menu

Offer the three quick picks first; show the full menu when the designer wants more choice. Pick one and stay inside it; do not blend three into mush.

| Direction | Keywords | Fits | Quick pick |
| --- | --- | --- | --- |
| Refined minimal | precise spacing, generous air, one accent, hairlines | tools, productivity, professional services | ✓ default |
| Editorial / magazine | serif display, grid and rules, large type contrast | content, reading, media | ✓ |
| Warm handmade / organic | soft curves, earth tones, paper texture | wellness, food, lifestyle, journaling | ✓ |
| Luxury / refined | serif titles, restrained metallic accent, wide margins | premium consumer, hospitality | |
| Playful / toy-like | rounded shapes, bright blocks, springy motion | kids, social, casual consumer apps | |
| Brutalist / raw | exposed borders, mono type, thick black rules | studios, indie products | |
| Retro-futuristic | mono fonts, neon on dark, scanlines | developer tools, hardware | |
| Industrial / utilitarian | dense data, tabular numbers, instrument feel | ops, monitoring, B2B consoles | |
| Maximalist | layering, clashing colors, high density | campaigns, entertainment, events | |

Starting tokens for the three quick picks:

| Token | Refined minimal | Editorial | Warm handmade |
| --- | --- | --- | --- |
| Page / surface | `#fafafa` / `#ffffff` | `#faf9f6` / `#ffffff` | `#fbf7f0` / `#fffdf9` |
| Border | `#e4e4e7` hairline | `#e7e2d9`, 1px rules | `#ece3d3` |
| Text 1 / 2 / 3 | `#18181b` / `#52525b` / `#6b6b73` | `#1c1b19` / `#55524c` / `#6f6b64` | `#2b2722` / `#5f584e` / `#74695c` |
| Accent | one cool accent; primary button near-black | one deep accent, e.g. `#9f1d20` | one warm accent, e.g. `#c2643d` |
| Display / body face (Google Fonts) | Geist or Inter Tight display, Geist body; Chinese: Noto Sans SC | Fraunces or Instrument Serif display, Source Serif 4 body; Chinese: Noto Serif SC | Bricolage Grotesque or Fraunces soft display, Nunito Sans body; Chinese: LXGW WenKai / Noto Serif SC |
| Radius | 6 / 8 / 12 / 16 | 2 / 4 / 6 | 10 / 14 / 20 |
| Shadow | 3 levels (`--shadow-xs/sm/md`: Y 1 / 1 / 8, 2–24px blur), low opacity; one dramatic shadow allowed on the memorable element | none; use rules | soft, warm-tinted |

## 4. The four pillars

| Pillar | Rule |
| --- | --- |
| Typography | The fastest differentiator. Pair a distinctive display face with a refined body face and bundle both with `fetch_fonts.py` (subset to the characters used, so it stays small and offline). A system font or Inter/Roboto/Arial is never the display face unless the VI says so. Display ≥ 32px on phone, ≥ 48px on desktop heroes, tracking −0.02 to −0.04em, line height 1.0–1.15. Body 14–17px, line height 1.5–1.7, 45–75 characters per line (Chinese 28–40). Text weights: three at most, plus one display weight. Tabular numbers for data. |
| Color & theme | Dominant color about 60%, supporting neutrals about 30%, one sharp accent about 10%, all as CSS variables. The accent marks the primary action, selection, progress and links only — never decoration or data. Choose light or dark base on purpose. |
| Motion | One orchestrated page-load sequence beats scattered micro-interactions: 3–6 groups revealed with 60–120ms stagger (proto-kit adds `.pk-enter` on navigation; see templates/styles.css). Durations: micro 150–200ms (`--duration-fast`, `--duration-base`, state changes with `--easing-standard`), standard 300–400ms (sheets, toasts), scene 600–800ms (`--duration-scene`, the page-load sequence with `--easing-out` = `cubic-bezier(0.16, 1, 0.3, 1)`). Movement uses transform and opacity; color and shadow transitions are fine for states. Everything stops under `prefers-reduced-motion`. |
| Composition | Decide air or density, then commit. In app screens keep lists and forms regular and scannable; spend boldness on the header, the hero number, empty states and the one memorable moment (asymmetry, overlap, a dramatic type scale). |

## 5. Atmosphere, not flat color

Pick one or two treatments that match the direction; all must work offline:

- Grain / paper: an inline SVG `feTurbulence` noise as a `data:` URI on `body::before`, opacity 0.03–0.08 (example in the Readlog styles).
- Gradient mesh: two or three large `radial-gradient`s in the page background, low saturation.
- Rules and frames: 1px rules, section numbers, a deliberate border frame for editorial directions.
- Depth: one dramatic shadow on the memorable element only.

Never stack effects to look busy. Restraint is also a direction.

## 6. Anti-slop list (fix every hit)

- System or Inter/Roboto/Arial as the display face; no bundled fonts.
- Purple-to-blue gradient on white; evenly distributed rainbow palette; accent used everywhere.
- The predictable layout: centered hero + three equal cards; every block a white card with the same shadow; card inside card.
- Emoji as icons; mixed icon styles; grey boxes labelled “image”; a single letter in a flat saturated square as a placeholder.
- Default browser controls (number spinners, unstyled selects), default blue links in a styled UI.
- Everything the same size and weight; no type contrast; centered long text.
- Motion that is either absent or scattered on every element; no reduced-motion handling.
- Looking like the previous prototype you made: every product gets its own direction.

## 7. Principles (checkable)

| Area | Rule |
| --- | --- |
| Hierarchy | Built with size, weight and color, not boxes. One focal point per screen. |
| Text color | Three at most (primary, secondary, tertiary); near-black, not pure black, for large areas. |
| Contrast | WCAG AA for all text (`palette.py --contrast`). When the source design fails, use the nearest passing shade, keep the original in the token comment, add an open question. |
| Spacing | 4px scale (1px and 2px allowed for hairline offsets). Section gaps larger than item gaps. |
| Surfaces | One elevation per region; hairline first, soft shadow second; no card inside a card. |
| Radius | One family; nested radius = outer radius − padding. |
| Controls | Same height and radius in a row (36–40px desktop, 44px+ touch); primary / secondary / ghost only; visible focus ring. |
| Placeholders | Intentional: tinted covers with real text, initials in a soft neutral circle, a quiet line icon labelled with what belongs there. |
| States | Empty, loading, error designed with the same care as the default. Skeletons match real shapes. |
| Icons | One style: 16–20px line icons, 1.5px stroke, inline SVG with `currentColor`. |
| Minimum size | Readable text ≥ 12px. Decorative text (cover texture) may be smaller if marked `/* decorative: … */` and `aria-hidden`. |

## 8. Visual QA

Two parts. Do not self-grade the first part: the script grades it.

**A. Objective, run by `check_output.py`** (warnings must be fixed or explained in the close): text below 12px, spacing off the 4px scale, more than 3 text weights + 1 display weight, animation without reduced-motion handling, a system/default display face, missing bundled font files. Contrast comes from `palette.py --contrast`; positions against a source come from `palette.py --rows` (blocks within 4px).

**B. Judgement, from the screenshots of every page and state** — answer each with what you saw, not “pass”:

1. Squint test: is there one focal point per screen? Name it.
2. Which element is the memorable thing from the direction lock, and is it visible on the first screen?
3. Is the accent only on action, selection, progress and links? List where it appears.
4. Any anti-slop hit (section 6)? List or say none.
5. Do placeholders and empty, loading, error states look designed?
6. Does the page-load sequence feel orchestrated (one sequence, not everything at once)?
7. Fidelity mode: palette, type, radius and density match the source side by side.
8. Would a design lead say “it looks like a template”? Name what breaks it, fix it, and leave the final call to the designer: report “awaiting designer review”, never a score.

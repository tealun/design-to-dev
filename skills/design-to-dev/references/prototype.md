# Building the prototype

## Default stack and why

Plain HTML + CSS + JavaScript, no build step, no dependencies. The designer opens it by double-clicking `index.html`; a developer can read every line and port it to any framework. Copy these templates into `<output>/prototype/`:

| File | Role | Edit? |
| --- | --- | --- |
| `index.html` | Loads tokens, styles, data, kit, pages in that order | Set the title and `lang` |
| `styles.css` | Base components on token variables | Yes, add page styles at the end |
| `proto-kit.js` | Routing, state switcher, fake requests, spec layer, toast | No |
| `data.js` | `window.MOCK` fake data | Yes |
| `pages.js` | One `Proto.page()` per screen | Yes |

Data goes in `data.js` as a script, never in a JSON file loaded with `fetch`: browsers block `fetch` from `file://`.

## proto-kit API

```js
Proto.page('/book/:id', {
  title: 'Book',                 // shown in the toolbar page list
  sample: '/book/1',             // where the toolbar goes for a page with parameters
  states: ['default', 'loading', 'error'],
  render: function (ctx) { return '<h1>…</h1>'; },   // ctx.params, ctx.query, ctx.state, ctx.store
  mount: function (root, ctx) { /* add event listeners */ }
});
Proto.go('/book/1');            // navigate; Proto.go('/', { state: 'empty' })
Proto.store                      // copy of window.MOCK; change it, then Proto.save() and Proto.refresh()
Proto.fake(result, 700)          // Promise; rejects once when "Fail next request" is ticked
Proto.toast('Saved') / Proto.toast('Failed', 'error')
Proto.esc(text)                  // escape before putting user text into HTML
Proto.start({ name: 'Readlog', home: '/', lang: 'zh' })   // last line of pages.js; lang 'zh' or 'en'
```

## Page checklist

For every page:

- Data pages declare `states: ['default', 'empty', 'loading', 'error']` and render each one. Detail pages without a list may skip `empty`.
- Forms: required fields, inline error under the field, submit button disabled or busy while saving, error toast and preserved input when `Proto.fake()` rejects, success feedback and navigation when it resolves.
- Every link and button leads somewhere real in the prototype or is marked TBD with a note (“Share: not in scope”).
- Escape any text that came from the user or the store with `Proto.esc()`.
- Use semantic elements: `button` for actions, `a href="#/…"` for navigation, `label` for inputs.
- No raw colors in `styles.css` or `pages.js`; read them from tokens. Prefer tokens for sizes too.
- Text contrast at least 4.5:1 (3:1 for text 24px+ or 19px+ bold) against its actual background, including text on brand or accent colors. Compute it with `python3 <skill-dir>/scripts/palette.py --contrast <text> <background>` and copy the printed ratios into HANDOFF section 5; estimates were wrong in testing. A white label on a light brand color (yellow, amber, light green) usually fails.

## Flow edges, assets and demo accounts

- **Flow ends outside the design:** add one stub page (for example `/signed-in`) that says the flow ended, mark it `data-spec="tbd"`, and list it in the HANDOFF page table with level TBD. Do not design it.
- **Links to pages not in scope:** `<a href="#" data-out>Forgot password?</a>`. proto-kit shows a “not in this prototype” toast. Each becomes an open question.
- **Assets not supplied:** a neutral placeholder (initial in a circle, grey box with the asset name), marked TBD, listed in HANDOFF section 3 under Assets.
- **Sign-in, payment and other sensitive forms:** accept only a fictional demo account from `data.js` (e.g. demo / demo1234), state it in HANDOFF section 0, and never send input anywhere.

## Fake data

Use 3–8 believable, clearly fictional records, including one long title, one with a missing optional field, and one edge value (0%, 100%, zero items) so layouts are tested. Dates as ISO strings.

## Another stack on request

If the designer asks for React/Vue/Svelte or the handoff team requires one, use Vite with that framework, keep `design-tokens/` unchanged and imported globally, keep the same pages, states and `data-spec` marks, and add “npm install && npm run dev” to HANDOFF section 0. Tell the designer it now needs Node.js to run. Run check_output.py with `--prototype-entry` pointing at the source folder.

## Verify in a browser

If a browser tool is available (Playwright, Chrome), open `prototype/index.html` at the design's width, walk the core flow, switch every state, toggle the spec layer, and capture screenshots. Put each screenshot beside its source design and compare color, font weight, sizes, order and spacing; template defaults (bold buttons, radius) often override the design unnoticed. Also check: no console errors, no unstyled page (tokens path wrong), no dead link, text not overflowing.

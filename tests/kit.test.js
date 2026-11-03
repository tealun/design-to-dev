/*
 * Browser regression tests for templates/proto-kit.js. Run: node tests/kit.test.js
 * Builds a throwaway prototype from the templates in a temp folder and drives it with Playwright.
 */
const { chromium } = require('playwright');
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const T = path.join(__dirname, '..', 'skills', 'design-to-dev', 'templates');

function buildFixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pk-'));
  fs.mkdirSync(path.join(root, 'prototype'));
  fs.mkdirSync(path.join(root, 'design-tokens'));
  fs.copyFileSync(path.join(T, 'tokens.css'), path.join(root, 'design-tokens', 'tokens.css'));
  for (const f of ['proto-kit.js', 'styles.css']) fs.copyFileSync(path.join(T, f), path.join(root, 'prototype', f));
  fs.writeFileSync(path.join(root, 'prototype', 'index.html'),
    fs.readFileSync(path.join(T, 'index.html'), 'utf8').replace(/{{PRODUCT_NAME}}/g, 'Kit test'));
  writeData(root, 'First title');
  // One page; "Retry" navigates to the URL it is already on, like a repeated failed sign-in.
  fs.writeFileSync(path.join(root, 'prototype', 'pages.js'), `
    var renders = 0;
    Proto.page('/', {
      states: ['default', 'error'],
      render: function (ctx) {
        renders += 1;
        return '<h1 id="title">' + Proto.esc(ctx.store.items[0].title) + '</h1>' +
          '<p id="renders">' + renders + '</p><button id="retry">Retry</button><button id="save">Save</button>';
      },
      mount: function (root, ctx) {
        root.querySelector('#retry').addEventListener('click', function () { Proto.go('/', { state: 'error' }); });
        root.querySelector('#save').addEventListener('click', function () { ctx.store.items[0].title = 'Edited in prototype'; Proto.save(); Proto.refresh(); });
      }
    });
    Proto.page('/other', { render: function () { return '<p id="other">Other</p>'; } });
    Proto.start({ name: 'kit-test', home: '/', lang: 'en' });`);
  return root;
}

function writeData(root, title) {
  fs.writeFileSync(path.join(root, 'prototype', 'data.js'), `window.MOCK = { items: [ { id: '1', title: '${title}' } ] };`);
}

(async () => {
  const root = buildFixture();
  const url = 'file://' + path.join(root, 'prototype', 'index.html');
  const context = await chromium.launchPersistentContext(path.join(root, 'profile'), { viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  let failed = 0;
  async function test(name, fn) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed += 1; console.log('FAIL ' + name + '\n     ' + e.message); }
  }

  await test('F-01 navigating to the current URL renders again', async () => {
    await page.goto(url + '#/');
    await page.click('#retry');
    await page.waitForTimeout(100);
    const first = Number(await page.textContent('#renders'));
    await page.click('#retry'); // same URL: #/?state=error
    await page.waitForTimeout(100);
    const second = Number(await page.textContent('#renders'));
    assert.ok(second > first, `render count stayed at ${first} after Proto.go to the current URL`);
  });

  await test('F-04 editing data.js replaces data saved by an older version', async () => {
    await page.goto(url + '#/');
    await page.click('#save');
    assert.strictEqual(await page.textContent('#title'), 'Edited in prototype');
    await page.reload();
    assert.strictEqual(await page.textContent('#title'), 'Edited in prototype', 'changes made in the prototype should survive a reload');
    writeData(root, 'Second title'); // the designer or the agent edits the fake data
    await page.reload();
    assert.strictEqual(await page.textContent('#title'), 'Second title', 'stale saved data hid the data.js edit');
  });

  await test('page-load sequence plays on navigation, not on refresh', async () => {
    await page.goto(url + '#/other');
    await page.goto(url + '#/');
    assert.ok(await page.evaluate(() => document.getElementById('app').classList.contains('pk-enter')), 'navigation should add pk-enter');
    await page.click('#save'); // Proto.refresh()
    assert.ok(!(await page.evaluate(() => document.getElementById('app').classList.contains('pk-enter'))), 'refresh must not replay the entrance');
  });

  await test('no page errors', async () => {
    assert.deepStrictEqual(errors, []);
  });

  await context.close();
  fs.rmSync(root, { recursive: true, force: true });
  console.log(failed ? `${failed} failed` : 'all passed');
  process.exit(failed ? 1 : 0);
})();

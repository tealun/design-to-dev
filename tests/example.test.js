/*
 * Browser test of the Readlog example's core flows. Run: node tests/example.test.js
 * Covers: shelf states, logging a page (validation, success, simulated failure), adding a book, finishing a book.
 */
const { chromium } = require('playwright');
const assert = require('assert');
const path = require('path');

const URL = 'file://' + path.join(__dirname, '..', 'examples', 'readlog', 'output', 'prototype', 'index.html');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  let failed = 0;
  async function test(name, fn) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed += 1; console.log('FAIL ' + name + '\n     ' + e.message); }
  }
  async function open(hash) {
    await page.goto(URL + '#' + hash);
    await page.evaluate(() => localStorage.clear());
    await page.reload();
  }

  await test('shelf lists books and every state renders', async () => {
    await open('/');
    assert.strictEqual(await page.locator('.book-row').count(), 3);
    for (const [state, selector] of [['empty', '.state'], ['loading', '[aria-busy="true"]'], ['error', '.state--error']]) {
      await page.goto(URL + '#/?state=' + state);
      assert.ok(await page.locator(selector).count() > 0, state + ' state missing');
    }
  });

  await test('log today\'s page: validation, success, simulated failure', async () => {
    await open('/book/1');
    await page.fill('#page', '50');
    await page.click('.log-form button');
    assert.match(await page.textContent('#page-error'), /96/);
    await page.fill('#page', '51');
    assert.strictEqual(await page.isHidden('#page-error'), true, 'error should clear while typing');
    await page.fill('#page', '120');
    await page.click('.log-form button');
    await page.waitForSelector('.pk-toast');
    assert.match(await page.textContent('.stats'), /120/);
    await page.click('.pk-bar__toggle');
    await page.check('[data-pk="fail"]');
    await page.fill('#page', '130');
    await page.click('.log-form button');
    await page.waitForSelector('.pk-toast--error');
    assert.strictEqual(await page.inputValue('#page'), '130', 'input should be kept after a failed save');
  });

  await test('add a book and land on its page', async () => {
    await open('/add');
    await page.click('button[type=submit]');
    assert.strictEqual(await page.locator('.field--error').count(), 2);
    await page.fill('#title', '夜航西飞');
    assert.strictEqual(await page.textContent('[data-live-title]'), '夜航西飞', 'cover preview shows the title');
    await page.fill('#total', '200');
    await page.click('.cover-option >> nth=2');
    await page.click('button[type=submit]');
    await page.waitForSelector('.book-hero__title');
    assert.strictEqual(await page.textContent('.book-hero__title'), '夜航西飞');
  });

  await test('finishing a book shows the done panel', async () => {
    await open('/book/3');
    await page.fill('#page', '180');
    await page.click('.log-form button');
    await page.waitForSelector('.done-panel');
  });

  await test('page-load sequence runs on the shelf', async () => {
    await page.goto(URL + '#/book/1');
    await page.goto(URL + '#/');
    const names = await page.evaluate(() => Array.from(document.querySelectorAll('#app > *')).slice(0, 3).map((el) => getComputedStyle(el).animationName));
    assert.ok(names.every((n) => n === 'enter'), 'entrance animation missing: ' + names.join(','));
  });

  await test('no page errors', async () => { assert.deepStrictEqual(errors, []); });

  await browser.close();
  console.log(failed ? `${failed} failed` : 'all passed');
  process.exit(failed ? 1 : 0);
})();

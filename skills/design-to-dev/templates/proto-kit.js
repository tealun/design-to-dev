/*
 * proto-kit.js — tiny runtime for design-to-dev prototypes. No dependencies, works from file://.
 *
 * Developers: this file is prototype scaffolding, not production code. It gives you
 *   - hash routing:      Proto.page('/book/:id', { title, states, render(ctx), mount(root, ctx) })
 *   - demo states:       ctx.state is 'default' | 'empty' | 'loading' | 'error' (switch in the toolbar or ?state=)
 *   - fake requests:     await Proto.fake(result, ms) resolves after a delay, or rejects when "Fail next request" is on
 *   - fake data store:   Proto.store (deep copy of window.MOCK, kept in localStorage, "Reset data" restores it)
 *   - spec marks:        elements with data-spec="fixed|indicative|tbd" and data-spec-note="…", shown with Shift+A
 *   - toast:             Proto.toast('Saved')
 *   - out of scope:      <a href="#" data-out> shows a "not in this prototype" toast instead of navigating
 * Replace routing, store and fake() with your real stack; keep the tokens and the page structure.
 */
(function () {
  'use strict';

  var LABELS = {
    zh: { page: '页面', state: '状态', spec: '标注', fail: '下次请求失败', reset: '重置数据', hide: '收起', show: '原型工具',
          fixed: '确定', indicative: '示意', tbd: '待定', failed: '请求失败（模拟）', notFound: '页面不存在',
          outOfScope: '不在本原型范围，见交接文档的待定问题' },
    en: { page: 'Page', state: 'State', spec: 'Spec', fail: 'Fail next request', reset: 'Reset data', hide: 'Hide', show: 'Prototype tools',
          fixed: 'Fixed', indicative: 'Indicative', tbd: 'TBD', failed: 'Request failed (simulated)', notFound: 'Page not found',
          outOfScope: 'Not in this prototype; see HANDOFF open questions' }
  };

  /* Kit chrome uses its own fixed styles so it never depends on, or leaks into, the design tokens. */
  var KIT_CSS = [
    '.pk-bar{position:fixed;right:12px;bottom:12px;z-index:9998;font:12px/1.4 system-ui,sans-serif;color:#1d1d1f;}',
    '.pk-bar__toggle{background:#1d1d1f;color:#fff;border:0;border-radius:999px;padding:8px 12px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.25);font:inherit;}',
    '.pk-bar__body{display:none;flex-direction:column;gap:8px;margin-bottom:8px;padding:12px;background:#fff;border:1px solid #d0d0d5;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.18);min-width:220px;}',
    '.pk-bar--open{display:flex;flex-direction:column-reverse;align-items:flex-end;}',
    '.pk-bar--open .pk-bar__body{display:flex;}',
    '.pk-bar label{display:flex;justify-content:space-between;align-items:center;gap:8px;}',
    '.pk-bar select,.pk-bar button[data-pk="reset"]{font:inherit;padding:4px 6px;border:1px solid #c7c7cc;border-radius:6px;background:#fff;color:inherit;}',
    '.pk-bar .pk-check{justify-content:flex-start;}',
    '.pk-bar kbd{margin-left:auto;font:11px ui-monospace,monospace;color:#6e6e73;}',
    '.pk-legend{margin:0;color:#6e6e73;display:flex;align-items:center;gap:4px;flex-wrap:wrap;}',
    '.pk-dot{display:inline-block;width:8px;height:8px;border-radius:50%;}',
    '.pk-dot--fixed,.pk-spec--fixed .pk-spec__tag{background:#d92d20;}',
    '.pk-dot--indicative,.pk-spec--indicative .pk-spec__tag{background:#2563eb;}',
    '.pk-dot--tbd,.pk-spec--tbd .pk-spec__tag{background:#b45309;}',
    '.pk-spec-layer{position:fixed;inset:0;pointer-events:none;z-index:9997;}',
    '.pk-spec{position:fixed;border:1.5px dashed;box-sizing:border-box;}',
    '.pk-spec--fixed{border-color:#d92d20;}.pk-spec--indicative{border-color:#2563eb;}.pk-spec--tbd{border-color:#b45309;}',
    '.pk-spec__tag{position:absolute;top:-1px;left:-1px;color:#fff;font:600 10px/1 system-ui,sans-serif;padding:3px 5px;border-radius:0 0 4px 0;pointer-events:auto;cursor:help;white-space:nowrap;}',
    '.pk-spec__note{display:none;position:absolute;top:16px;left:-1px;max-width:260px;background:#1d1d1f;color:#fff;font:11px/1.4 system-ui,sans-serif;padding:6px 8px;border-radius:6px;z-index:1;}',
    '.pk-spec__tag:hover+.pk-spec__note{display:block;}',
    '.pk-toast{position:fixed;left:50%;top:16px;max-width:calc(100vw - 32px);transform:translateX(-50%);z-index:9999;background:#1d1d1f;color:#fff;padding:10px 16px;border-radius:999px;font:14px/1.4 system-ui,sans-serif;transition:opacity .3s;}',
    '.pk-toast--error{background:#b42318;}.pk-toast--out{opacity:0;}',
    '.pk-missing{padding:24px;font:14px system-ui,sans-serif;}'
  ].join('\n');

  var routes = [];
  var options = { name: 'prototype', home: '/', lang: 'zh' };
  var failNext = false;
  var specOn = false;
  var current = null;

  function t(key) { return (LABELS[options.lang] || LABELS.en)[key]; }

  function clone(value) { return value === undefined ? {} : JSON.parse(JSON.stringify(value)); }

  function storageKey() { return 'proto:' + options.name; }

  function loadStore() {
    try {
      var saved = localStorage.getItem(storageKey());
      if (saved) return JSON.parse(saved);
    } catch (e) { /* storage unavailable: fall back to fresh mock data */ }
    return clone(window.MOCK);
  }

  var Proto = {
    store: null,

    /** Register a page. pattern like '/book/:id'. def: { title, states, render(ctx) -> html, mount(root, ctx) } */
    page: function (pattern, def) {
      var keys = [];
      var re = new RegExp('^' + pattern.replace(/\/:([\w]+)/g, function (_, k) { keys.push(k); return '/([^/]+)'; }) + '$');
      routes.push({ pattern: pattern, re: re, keys: keys, def: def });
    },

    /** Navigate. Proto.go('/book/2') or Proto.go('/', { state: 'empty' }) */
    go: function (path, query) {
      var qs = query ? '?' + new URLSearchParams(query).toString() : '';
      location.hash = '#' + path + qs;
    },

    /** Persist the fake data store after you change it. */
    save: function () {
      try { localStorage.setItem(storageKey(), JSON.stringify(Proto.store)); } catch (e) { /* ignore */ }
    },

    /** Simulated request: resolves with result after ms, or rejects once if "Fail next request" is on. */
    fake: function (result, ms) {
      return new Promise(function (resolve, reject) {
        setTimeout(function () {
          if (failNext) {
            failNext = false;
            syncToolbar();
            reject(new Error(t('failed')));
          } else {
            resolve(result);
          }
        }, ms === undefined ? 700 : ms);
      });
    },

    toast: function (message, kind) {
      var el = document.createElement('div');
      el.className = 'pk-toast' + (kind ? ' pk-toast--' + kind : '');
      el.setAttribute('role', 'status');
      el.textContent = message;
      document.body.appendChild(el);
      setTimeout(function () { el.classList.add('pk-toast--out'); }, 2200);
      setTimeout(function () { el.remove(); }, 2600);
    },

    /** Escape text before putting it into HTML strings. */
    esc: function (value) {
      return String(value === undefined || value === null ? '' : value).replace(/[&<>"']/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
      });
    },

    /** Re-render the current page (after changing Proto.store). */
    refresh: function () { render(); },

    start: function (opts) {
      for (var k in opts) options[k] = opts[k];
      var style = document.createElement('style');
      style.textContent = KIT_CSS;
      document.head.appendChild(style);
      Proto.store = loadStore();
      buildToolbar();
      window.addEventListener('hashchange', render);
      // Links to pages that were not designed: explain instead of navigating to a dead end.
      document.addEventListener('click', function (e) {
        var out = e.target.closest && e.target.closest('#app [data-out]');
        if (out) { e.preventDefault(); Proto.toast(t('outOfScope')); }
      });
      window.addEventListener('resize', drawSpecs);
      document.addEventListener('scroll', drawSpecs, true);
      document.addEventListener('keydown', function (e) {
        var tag = (e.target && e.target.tagName) || '';
        if (/INPUT|TEXTAREA|SELECT/.test(tag) || (e.target && e.target.isContentEditable)) return;
        if (e.shiftKey && (e.key === 'A' || e.key === 'a')) { toggleSpec(); }
      });
      if (!location.hash) location.hash = '#' + options.home;
      else render();
    }
  };

  function parseHash() {
    var raw = location.hash.replace(/^#/, '') || options.home;
    var parts = raw.split('?');
    return { path: parts[0] || '/', query: new URLSearchParams(parts[1] || '') };
  }

  function match(path) {
    for (var i = 0; i < routes.length; i++) {
      var m = routes[i].re.exec(path);
      if (m) {
        var params = {};
        routes[i].keys.forEach(function (k, j) { params[k] = decodeURIComponent(m[j + 1]); });
        return { route: routes[i], params: params };
      }
    }
    return null;
  }

  function render() {
    var root = document.getElementById('app');
    var loc = parseHash();
    var found = match(loc.path);
    if (!found) {
      root.innerHTML = '<p class="pk-missing">' + t('notFound') + ': ' + Proto.esc(loc.path) + '</p>';
      current = null;
      syncToolbar();
      return;
    }
    var def = found.route.def;
    var states = def.states || ['default'];
    var state = loc.query.get('state') || 'default';
    if (states.indexOf(state) === -1) state = 'default';
    var ctx = { params: found.params, query: loc.query, state: state, store: Proto.store, go: Proto.go };
    current = { route: found.route, ctx: ctx, path: loc.path };
    document.title = (def.title ? def.title + ' · ' : '') + options.name;
    root.innerHTML = def.render(ctx);
    if (def.mount) def.mount(root, ctx);
    window.scrollTo(0, 0);
    syncToolbar();
    drawSpecs();
  }

  /* ---------- toolbar ---------- */

  var bar;

  function buildToolbar() {
    bar = document.createElement('aside');
    bar.className = 'pk-bar';
    bar.setAttribute('aria-label', t('show'));
    bar.innerHTML =
      '<button type="button" class="pk-bar__toggle" data-pk="toggle">' + t('show') + '</button>' +
      '<div class="pk-bar__body">' +
      '<label>' + t('page') + ' <select data-pk="page"></select></label>' +
      '<label>' + t('state') + ' <select data-pk="state"></select></label>' +
      '<label class="pk-check"><input type="checkbox" data-pk="spec"> ' + t('spec') + ' <kbd>Shift+A</kbd></label>' +
      '<label class="pk-check"><input type="checkbox" data-pk="fail"> ' + t('fail') + '</label>' +
      '<button type="button" data-pk="reset">' + t('reset') + '</button>' +
      '<p class="pk-legend"><span class="pk-dot pk-dot--fixed"></span>' + t('fixed') +
      ' <span class="pk-dot pk-dot--indicative"></span>' + t('indicative') +
      ' <span class="pk-dot pk-dot--tbd"></span>' + t('tbd') + '</p>' +
      '</div>';
    document.body.appendChild(bar);

    var pageSelect = bar.querySelector('[data-pk="page"]');
    routes.forEach(function (r) {
      var opt = document.createElement('option');
      opt.value = r.pattern;
      opt.textContent = (r.def.title || r.pattern) + '  ' + r.pattern;
      pageSelect.appendChild(opt);
    });
    pageSelect.addEventListener('change', function () {
      var r = routes.filter(function (x) { return x.pattern === pageSelect.value; })[0];
      var sample = r.def.sample || r.pattern.replace(/:[\w]+/g, '1');
      Proto.go(sample);
    });
    bar.querySelector('[data-pk="state"]').addEventListener('change', function (e) {
      Proto.go(current ? current.path : options.home, e.target.value === 'default' ? null : { state: e.target.value });
    });
    bar.querySelector('[data-pk="spec"]').addEventListener('change', toggleSpec);
    bar.querySelector('[data-pk="fail"]').addEventListener('change', function (e) { failNext = e.target.checked; });
    bar.querySelector('[data-pk="reset"]').addEventListener('click', function () {
      try { localStorage.removeItem(storageKey()); } catch (e) { /* ignore */ }
      Proto.store = clone(window.MOCK);
      render();
    });
    bar.querySelector('[data-pk="toggle"]').addEventListener('click', function () {
      bar.classList.toggle('pk-bar--open');
    });
  }

  function syncToolbar() {
    if (!bar) return;
    var stateSelect = bar.querySelector('[data-pk="state"]');
    stateSelect.innerHTML = '';
    var states = current ? (current.route.def.states || ['default']) : ['default'];
    states.forEach(function (s) {
      var opt = document.createElement('option');
      opt.value = s;
      opt.textContent = s;
      stateSelect.appendChild(opt);
    });
    if (current) {
      stateSelect.value = current.ctx.state;
      bar.querySelector('[data-pk="page"]').value = current.route.pattern;
    }
    bar.querySelector('[data-pk="fail"]').checked = failNext;
    bar.querySelector('[data-pk="spec"]').checked = specOn;
  }

  /* ---------- spec marks ---------- */

  var layer;

  function toggleSpec() {
    specOn = !specOn;
    document.body.classList.toggle('pk-spec-on', specOn);
    syncToolbar();
    drawSpecs();
  }

  function drawSpecs() {
    if (!layer) {
      layer = document.createElement('div');
      layer.className = 'pk-spec-layer';
      document.body.appendChild(layer);
    }
    layer.innerHTML = '';
    if (!specOn) return;
    var nodes = document.querySelectorAll('#app [data-spec]');
    Array.prototype.forEach.call(nodes, function (node, i) {
      var level = node.getAttribute('data-spec');
      var rect = node.getBoundingClientRect();
      if (!rect.width && !rect.height) return;
      var box = document.createElement('div');
      box.className = 'pk-spec pk-spec--' + level;
      box.style.left = rect.left + 'px';
      box.style.top = rect.top + 'px';
      box.style.width = rect.width + 'px';
      box.style.height = rect.height + 'px';
      var tag = document.createElement('span');
      tag.className = 'pk-spec__tag';
      tag.textContent = (i + 1) + ' ' + (t(level) || level);
      tag.title = node.getAttribute('data-spec-note') || '';
      var note = document.createElement('span');
      note.className = 'pk-spec__note';
      note.textContent = node.getAttribute('data-spec-note') || '';
      box.appendChild(tag);
      box.appendChild(note);
      layer.appendChild(box);
    });
  }

  window.Proto = Proto;
})();

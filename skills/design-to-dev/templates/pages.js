/* pages.js — one Proto.page() per screen. Each render(ctx) returns HTML; mount(root, ctx) wires events.
 * ctx.state is 'default' | 'empty' | 'loading' | 'error', chosen in the prototype toolbar.
 * Visual rules: see references/visual-direction.md (one accent, hairline surfaces, designed states). */
(function () {
  var esc = Proto.esc;

  /* Line icons: 16px, 1.5px stroke, currentColor. Add paths as needed. */
  var ICONS = {
    plus: '<path d="M8 3.5v9M3.5 8h9"/>',
    back: '<path d="M10 3.5 5.5 8l4.5 4.5"/>',
    inbox: '<path d="M2.5 9.5 4 4h8l1.5 5.5M2.5 9.5v3h11v-3M2.5 9.5h3l1 1.5h3l1-1.5h3"/>',
    alert: '<path d="M8 5v3.5M8 11h.01"/><circle cx="8" cy="8" r="5.5"/>',
    chevron: '<path d="m6 3.5 4.5 4.5L6 12.5"/>'
  };
  function icon(name) {
    return '<svg class="icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + ICONS[name] + '</svg>';
  }

  /* Shared state views: designed as carefully as the default state. */
  function loadingView(rows) {
    var row = '<div class="skeleton-row"><div class="skeleton" style="width:32px;height:32px;border-radius:999px"></div>' +
      '<div style="flex:1;display:grid;gap:8px"><div class="skeleton" style="width:60%"></div><div class="skeleton" style="width:35%;height:12px"></div></div></div>';
    return '<div class="surface" aria-busy="true" data-spec="indicative" data-spec-note="Skeleton mirrors the list layout so nothing jumps when data arrives">' +
      new Array(rows || 3).fill(row).join('') + '</div>';
  }
  function errorView(retryHref) {
    return '<div class="state state--error" role="alert" data-spec="tbd" data-spec-note="Error copy and retry behavior to be decided">' +
      '<span class="state__icon">' + icon('alert') + '</span>' +
      '<p class="state__title">Couldn\'t load this page</p><p class="state__text">Check your connection and try again.</p>' +
      '<a class="btn btn--secondary" href="' + retryHref + '">Try again</a></div>';
  }
  function emptyView(title, text, actionHtml) {
    return '<div class="state" data-spec="fixed" data-spec-note="Empty state keeps the main action visible">' +
      '<span class="state__icon">' + icon('inbox') + '</span>' +
      '<p class="state__title">' + esc(title) + '</p><p class="state__text">' + esc(text) + '</p>' + (actionHtml || '') + '</div>';
  }

  Proto.page('/', {
    title: 'Home',
    states: ['default', 'empty', 'loading', 'error'],
    render: function (ctx) {
      var add = '<a class="btn btn--primary" href="#" data-out data-spec="fixed" data-spec-note="Primary action, top right">' + icon('plus') + 'New item</a>';
      var head = '<header class="page-header"><div class="page-header__text"><p class="eyebrow">Workspace</p>' +
        '<h1 class="title">Home</h1></div>' + add + '</header>';
      if (ctx.state === 'loading') return head + loadingView();
      if (ctx.state === 'error') return head + errorView('#/');
      var items = ctx.state === 'empty' ? [] : ctx.store.items;
      if (!items.length) return head + emptyView('Nothing here yet', 'Items you create will show up here.', add);
      return head + '<ul class="surface list">' + items.map(function (it) {
        return '<li><a class="list__item" href="#/item/' + esc(it.id) + '">' +
          '<span class="avatar">' + esc(it.title.charAt(0)) + '</span>' +
          '<span class="list__main"><span class="list__title">' + esc(it.title) + '</span><span class="list__meta">' + esc(it.note) + '</span></span>' +
          '<span class="list__trail">' + icon('chevron') + '</span></a></li>';
      }).join('') + '</ul>';
    }
  });

  Proto.page('/item/:id', {
    title: 'Item',
    sample: '/item/1',
    states: ['default', 'loading', 'error'],
    render: function (ctx) {
      var back = '<a class="back-link" href="#/">' + icon('back') + 'Home</a>';
      var it = ctx.store.items.filter(function (x) { return x.id === ctx.params.id; })[0];
      if (ctx.state === 'loading') return back + loadingView(1);
      if (ctx.state === 'error' || !it) return back + errorView('#/item/' + esc(ctx.params.id));
      return back + '<header class="page-header"><div class="page-header__text"><h1 class="title">' + esc(it.title) + '</h1>' +
        '<p class="secondary">' + esc(it.note) + '</p></div></header>';
    }
  });

  Proto.start({ name: '{{PRODUCT_NAME}}', home: '/', lang: '{{LANG}}' });
})();

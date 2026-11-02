/* pages.js — one Proto.page() per screen. Each render(ctx) returns HTML; mount(root, ctx) wires events.
 * ctx.state is 'default' | 'empty' | 'loading' | 'error', chosen in the prototype toolbar. */
(function () {
  var esc = Proto.esc;

  /* Shared state views. Mark them so developers know which parts are fixed. */
  function loadingView() {
    return '<div class="state state--loading" aria-busy="true" data-spec="indicative" data-spec-note="Skeleton while loading; any loading pattern that keeps layout stable is fine">' +
      '<div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div></div>';
  }
  function errorView(retryHref) {
    return '<div class="state state--error" role="alert" data-spec="tbd" data-spec-note="Error copy and retry behavior to be decided">' +
      '<p class="state__title">Couldn\'t load</p><p class="state__text">Check your connection and try again.</p>' +
      '<a class="btn btn--secondary" href="' + retryHref + '">Try again</a></div>';
  }
  function emptyView(text, actionHtml) {
    return '<div class="state state--empty" data-spec="fixed" data-spec-note="Empty state must keep the main action visible">' +
      '<p class="state__title">' + esc(text) + '</p>' + (actionHtml || '') + '</div>';
  }

  Proto.page('/', {
    title: 'Home',
    states: ['default', 'empty', 'loading', 'error'],
    render: function (ctx) {
      var head = '<header class="topbar"><h1 class="topbar__title">Home</h1></header>';
      if (ctx.state === 'loading') return head + loadingView();
      if (ctx.state === 'error') return head + errorView('#/');
      var items = ctx.state === 'empty' ? [] : ctx.store.items;
      if (!items.length) return head + emptyView('Nothing here yet');
      return head + '<ul class="list">' + items.map(function (it) {
        return '<li><a class="card" href="#/item/' + esc(it.id) + '">' + esc(it.title) + '</a></li>';
      }).join('') + '</ul>';
    }
  });

  Proto.page('/item/:id', {
    title: 'Item',
    sample: '/item/1',
    states: ['default', 'loading', 'error'],
    render: function (ctx) {
      var it = ctx.store.items.filter(function (x) { return x.id === ctx.params.id; })[0];
      if (ctx.state === 'loading') return loadingView();
      if (ctx.state === 'error' || !it) return errorView('#/item/' + esc(ctx.params.id));
      return '<header class="topbar"><a class="topbar__back" href="#/">Back</a><h1 class="topbar__title">' + esc(it.title) + '</h1></header>' +
        '<p>' + esc(it.note) + '</p>';
    }
  });

  Proto.start({ name: '{{PRODUCT_NAME}}', home: '/', lang: 'en' });
})();

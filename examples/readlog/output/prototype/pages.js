/* pages.js — Readlog pages: Shelf (/), Book (/book/:id), Add book (/add).
 * Each render(ctx) returns HTML; mount(root, ctx) wires events. ctx.state comes from the prototype toolbar. */
(function () {
  var esc = Proto.esc;

  function percent(book) {
    return book.totalPages ? Math.round((book.currentPage / book.totalPages) * 100) : 0;
  }
  function isDone(book) { return book.currentPage >= book.totalPages; }
  function today() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function findBook(store, id) { return store.books.filter(function (b) { return b.id === id; })[0]; }

  function cover(book, large) {
    return '<span class="cover cover--' + esc(book.cover) + (large ? ' cover--large' : '') + '" aria-hidden="true">' +
      esc(book.title.charAt(0)) + '</span>';
  }
  function progressBar(book) {
    return '<div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + percent(book) + '">' +
      '<span class="progress__fill" style="width:' + percent(book) + '%"></span></div>';
  }

  /* Shared state views */
  function loadingView() {
    return '<div class="state state--loading" aria-busy="true" data-spec="indicative" data-spec-note="加载时用骨架屏占位，保持布局不跳动；具体样式可调整">' +
      '<div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div></div>';
  }
  function errorView(retryHref) {
    return '<div class="state state--error" role="alert" data-spec="tbd" data-spec-note="加载失败的文案与重试策略（自动重试几次？）待定">' +
      '<p class="state__title">没加载出来</p><p class="state__text">网络好像不太好，稍后再试一次。</p>' +
      '<a class="btn btn--secondary" href="' + retryHref + '">重新加载</a></div>';
  }

  /* ---------- Shelf ---------- */
  Proto.page('/', {
    title: '书架',
    states: ['default', 'empty', 'loading', 'error'],
    render: function (ctx) {
      var tab = ctx.query.get('tab') === 'done' ? 'done' : 'reading';
      var head = '<header class="topbar"><h1 class="topbar__title display" data-spec="fixed" data-spec-note="标题用品牌宋体粗体（Noto Serif SC Bold）">我的书架</h1></header>';
      if (ctx.state === 'loading') return head + loadingView();
      if (ctx.state === 'error') return head + errorView('#/');

      var books = ctx.state === 'empty' ? [] : ctx.store.books;
      var addButton = '<div class="bottom-bar"><a class="btn btn--primary btn--block" href="#/add" data-spec="fixed" data-spec-note="主按钮：苔绿底，手机上通栏，固定在底部">添加一本书</a></div>';
      if (!books.length) {
        return head + '<div class="state state--empty" data-spec="fixed" data-spec-note="空书架：插图位 + 一句鼓励 + 主按钮，必须引导添加第一本书">' +
          '<span class="empty-art" aria-hidden="true"></span>' +
          '<p class="state__title display">书架还空着</p><p class="state__text">放上第一本在读的书，从今天开始记录。</p>' +
          '<a class="btn btn--primary" href="#/add">添加第一本书</a></div>';
      }

      var reading = books.filter(function (b) { return !isDone(b); });
      var done = books.filter(isDone);
      var shown = tab === 'done' ? done : reading;
      var streak = '<section class="streak" data-spec="indicative" data-spec-note="连续打卡卡片：琥珀色强调；文案语气温和鼓励，可调整">' +
        '<span class="streak__num">' + esc(ctx.store.streakDays) + '</span>' +
        '<div><p class="streak__title">已连续阅读 ' + esc(ctx.store.streakDays) + ' 天</p>' +
        '<p class="streak__text">今天也读了一点，很好。</p></div>' +
        '<span class="spec-anchor" data-spec="tbd" data-spec-note="“连续天数”的规则待定：按自然日还是 24 小时？漏记一天是否清零？"></span></section>';
      var tabs = '<nav class="tabs" aria-label="书架分类" data-spec="fixed" data-spec-note="在读 / 读完 两个分类，数字为本数">' +
        '<a class="tabs__item' + (tab === 'reading' ? ' is-active' : '') + '" href="#/">在读 ' + reading.length + '</a>' +
        '<a class="tabs__item' + (tab === 'done' ? ' is-active' : '') + '" href="#/?tab=done">读完 ' + done.length + '</a></nav>';
      var list = shown.length
        ? '<ul class="list">' + shown.map(function (b, i) {
            return '<li><a class="card book-card" href="#/book/' + esc(b.id) + '"' +
              (i === 0 ? ' data-spec="fixed" data-spec-note="书卡片：封面色块 + 书名（最多两行）+ 作者 + 进度条与页数"' : '') + '>' +
              cover(b) +
              '<span class="book-card__body"><span class="book-card__title">' + esc(b.title) + '</span>' +
              '<span class="book-card__author">' + (b.author ? esc(b.author) : '作者未填写') + '</span>' +
              progressBar(b) +
              '<span class="book-card__meta">' + esc(b.currentPage) + ' / ' + esc(b.totalPages) + ' 页 · ' + percent(b) + '%</span></span></a></li>';
          }).join('') + '</ul>'
        : '<div class="state state--empty"><p class="state__text">' + (tab === 'done' ? '还没有读完的书，慢慢来。' : '在读的书都读完了，添加下一本吧。') + '</p></div>';
      var sortNote = '<p class="hint" data-spec="tbd" data-spec-note="书架排序规则待定：目前按添加时间（新的在前），是否改为最近记录在前？">按添加时间排列</p>';
      return head + streak + tabs + sortNote + list + addButton;
    }
  });

  /* ---------- Book detail + log today's page ---------- */
  Proto.page('/book/:id', {
    title: '书的详情',
    sample: '/book/1',
    states: ['default', 'loading', 'error'],
    render: function (ctx) {
      var back = '<header class="topbar"><a class="topbar__back" href="#/">‹ 书架</a></header>';
      if (ctx.state === 'loading') return back + loadingView();
      var book = findBook(ctx.store, ctx.params.id);
      if (ctx.state === 'error' || !book) return back + errorView('#/book/' + esc(ctx.params.id));

      var hero = '<section class="book-hero">' + cover(book, true) +
        '<div><h1 class="book-hero__title display">' + esc(book.title) + '</h1>' +
        '<p class="book-card__author">' + (book.author ? esc(book.author) : '作者未填写') + '</p></div></section>';
      var progress = '<section class="progress-panel" data-spec="fixed" data-spec-note="进度：大号百分比 + 进度条 + 当前页/总页数">' +
        '<p class="progress-panel__pct display">' + percent(book) + '<small>%</small></p>' + progressBar(book) +
        '<p class="book-card__meta">第 ' + esc(book.currentPage) + ' / ' + esc(book.totalPages) + ' 页</p></section>';

      var form = isDone(book)
        ? '<section class="done-panel" data-spec="indicative" data-spec-note="读完后的庆祝面板，文案与样式可调整"><p class="state__title display">读完了！</p>' +
          '<p class="state__text">一共 ' + esc(book.totalPages) + ' 页，记得给自己一点奖励。</p></section>'
        : '<form class="log-form" novalidate data-spec="fixed" data-spec-note="核心操作：输入今天读到的页码并记录；校验：必须大于上次页码、不超过总页数">' +
          '<div class="field"><label class="field__label" for="page">今天读到第几页？</label>' +
          '<input class="field__input" id="page" name="page" type="number" inputmode="numeric" min="' + (book.currentPage + 1) + '" max="' + book.totalPages + '" placeholder="比如 ' + Math.min(book.currentPage + 20, book.totalPages) + '">' +
          '<p class="field__error" id="page-error" hidden></p></div>' +
          '<button class="btn btn--primary btn--block" type="submit">记录</button></form>';

      var logs = book.logs.slice().reverse();
      var history = '<section class="history"><h2 class="section-title">阅读记录</h2>' +
        (logs.length
          ? '<ul class="history__list" data-spec="indicative" data-spec-note="记录列表：日期 + 读到第几页 + 当天读了多少页">' + logs.map(function (log, i) {
              var prev = logs[i + 1] ? logs[i + 1].page : 0;
              return '<li><span>' + esc(log.date) + '</span><span>读到第 ' + esc(log.page) + ' 页 <em>+' + (log.page - prev) + '</em></span></li>';
            }).join('') + '</ul>'
          : '<p class="state__text">还没有记录，读完今天的部分就来记一下吧。</p>') + '</section>';
      var manage = '<p class="hint"><span data-spec="tbd" data-spec-note="编辑书籍信息、删除书籍不在本期原型范围，是否需要、放在哪里待定">编辑 · 删除（待定）</span></p>';
      return back + hero + progress + form + history + manage;
    },
    mount: function (root, ctx) {
      var form = root.querySelector('.log-form');
      if (!form) return;
      var book = findBook(ctx.store, ctx.params.id);
      var input = form.querySelector('#page');
      var error = form.querySelector('#page-error');
      var button = form.querySelector('button');

      function showError(message) {
        error.textContent = message;
        error.hidden = !message;
        form.querySelector('.field').classList.toggle('field--error', !!message);
        input.setAttribute('aria-invalid', message ? 'true' : 'false');
      }

      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var value = input.value.trim();
        var page = Number(value);
        if (!value) return showError('请输入今天读到的页码');
        if (!Number.isInteger(page)) return showError('页码需要是整数');
        if (page <= book.currentPage) return showError('要比上次的第 ' + book.currentPage + ' 页更大');
        if (page > book.totalPages) return showError('这本书只有 ' + book.totalPages + ' 页');
        showError('');
        button.disabled = true;
        button.setAttribute('aria-busy', 'true');
        button.textContent = '记录中…';
        Proto.fake({ page: page }).then(function () {
          var date = today();
          var last = book.logs[book.logs.length - 1];
          if (!last || last.date !== date) ctx.store.streakDays += 1;
          book.currentPage = page;
          book.logs.push({ date: date, page: page });
          Proto.save();
          Proto.refresh();
          Proto.toast(isDone(book) ? '读完了！恭喜你' : '记好了，今天也读了一点，很好');
        }).catch(function () {
          button.disabled = false;
          button.removeAttribute('aria-busy');
          button.textContent = '记录';
          Proto.toast('没记上，网络好像不太好，再试一次', 'error');
        });
      });
    }
  });

  /* ---------- Add book ---------- */
  var COVERS = [['moss', '苔绿'], ['amber', '琥珀'], ['clay', '陶土'], ['slate', '石板']];

  Proto.page('/add', {
    title: '添加一本书',
    states: ['default'],
    render: function () {
      return '<header class="topbar"><a class="topbar__back" href="#/">取消</a><h1 class="topbar__title display">添加一本书</h1></header>' +
        '<form class="add-form" novalidate>' +
        '<div class="field" data-spec="fixed" data-spec-note="书名必填"><label class="field__label" for="title">书名</label>' +
        '<input class="field__input" id="title" name="title" autocomplete="off" placeholder="比如《慢慢来的散步》"><p class="field__error" hidden></p></div>' +
        '<div class="field"><label class="field__label" for="author">作者 <span class="optional">选填</span></label>' +
        '<input class="field__input" id="author" name="author" autocomplete="off"><p class="field__error" hidden></p></div>' +
        '<div class="field" data-spec="tbd" data-spec-note="总页数上限暂定 5000，电子书没有页数时怎么办待定"><label class="field__label" for="total">总页数</label>' +
        '<input class="field__input" id="total" name="total" type="number" inputmode="numeric" min="1" max="5000" placeholder="比如 240"><p class="field__error" hidden></p></div>' +
        '<fieldset class="field swatches" data-spec="indicative" data-spec-note="没有真实封面时用色块代替；颜色取自品牌色板，可调整"><legend class="field__label">封面颜色</legend>' +
        COVERS.map(function (c, i) {
          return '<label class="swatch"><input type="radio" name="cover" value="' + c[0] + '"' + (i === 0 ? ' checked' : '') + '>' +
            '<span class="swatch__dot cover--' + c[0] + '"></span><span class="swatch__name">' + c[1] + '</span></label>';
        }).join('') + '</fieldset>' +
        '<div class="bottom-bar"><button class="btn btn--primary btn--block" type="submit" data-spec="fixed" data-spec-note="保存后跳到这本书的详情页">放上书架</button></div>' +
        '</form>';
    },
    mount: function (root, ctx) {
      var form = root.querySelector('.add-form');
      var button = form.querySelector('button[type="submit"]');

      function setError(name, message) {
        var field = form.querySelector('#' + name).closest('.field');
        var error = field.querySelector('.field__error');
        error.textContent = message;
        error.hidden = !message;
        field.classList.toggle('field--error', !!message);
        return !message;
      }

      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var title = form.title.value.trim();
        var author = form.author.value.trim();
        var total = Number(form.total.value);
        var ok = setError('title', title ? (title.length > 60 ? '书名最多 60 个字' : '') : '请填写书名');
        ok = setError('total', !form.total.value ? '请填写总页数'
          : (!Number.isInteger(total) || total < 1 || total > 5000) ? '请输入 1 到 5000 之间的整数' : '') && ok;
        if (!ok) { form.querySelector('.field--error .field__input').focus(); return; }

        button.disabled = true;
        button.setAttribute('aria-busy', 'true');
        button.textContent = '保存中…';
        var book = { id: String(Date.now()), title: title, author: author, totalPages: total, currentPage: 0,
          cover: form.querySelector('input[name="cover"]:checked').value, logs: [] };
        Proto.fake(book).then(function () {
          ctx.store.books.unshift(book);
          Proto.save();
          Proto.go('/book/' + book.id);
          Proto.toast('已放上书架');
        }).catch(function () {
          button.disabled = false;
          button.removeAttribute('aria-busy');
          button.textContent = '放上书架';
          Proto.toast('没保存上，网络好像不太好，再试一次', 'error');
        });
      });
    }
  });

  Proto.start({ name: 'Readlog', home: '/', lang: 'zh' });
})();

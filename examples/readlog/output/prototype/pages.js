/* pages.js — Readlog pages: Shelf (/), Book (/book/:id), Add book (/add).
 * Direction: refined minimal with brand.md constraints. Each render(ctx) returns HTML; mount(root, ctx) wires events. */
(function () {
  var esc = Proto.esc;
  var WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日'];

  /* Line icons: 16px, 1.5px stroke, currentColor. */
  var ICONS = {
    plus: '<path d="M8 3.5v9M3.5 8h9"/>',
    back: '<path d="M10 3.5 5.5 8l4.5 4.5"/>',
    book: '<path d="M3 3.5c1.6-.6 3.3-.6 5 .5v9c-1.7-1.1-3.4-1.1-5-.5zM13 3.5c-1.6-.6-3.3-.6-5 .5v9c1.7-1.1 3.4-1.1 5-.5z"/>',
    alert: '<circle cx="8" cy="8" r="5.5"/><path d="M8 5v3.5M8 11h.01"/>',
    check: '<path d="m3.5 8.5 3 3 6-6.5"/>',
    more: '<path d="M4 8h.01M8 8h.01M12 8h.01"/>'
  };
  function icon(name) {
    return '<svg class="icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + ICONS[name] + '</svg>';
  }

  function percent(book) { return book.totalPages ? Math.round((book.currentPage / book.totalPages) * 100) : 0; }
  function isDone(book) { return book.currentPage >= book.totalPages; }
  function today() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function todayIndex() { return (new Date().getDay() + 6) % 7; } // Monday = 0
  function eyebrowDate() { var d = new Date(); return (d.getMonth() + 1) + '月' + d.getDate() + '日 · 周' + WEEKDAYS[todayIndex()]; }
  function findBook(store, id) { return store.books.filter(function (b) { return b.id === id; })[0]; }

  /* A placeholder cover that looks like a book: gradient, spine shadow, a band, and the title in the
     brand serif. Small covers show the first character as decoration; large ones show the title. */
  function cover(book, size) {
    var text = size === 'sm' ? book.title.charAt(0) : book.title;
    return '<span class="cover cover--' + esc(book.cover) + ' cover--' + size + '" aria-hidden="true">' +
      '<span class="cover__band"></span><span class="cover__title">' + esc(text) + '</span></span>';
  }
  function progress(book, thick) {
    return '<span class="progress' + (thick ? ' progress--thick' : '') + '" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + percent(book) + '">' +
      '<span class="progress__fill" style="width:' + percent(book) + '%"></span></span>';
  }

  /* Shared state views */
  function loadingView() {
    var row = '<div class="skeleton-row"><div class="skeleton" style="width:44px;height:62px;border-radius:2px"></div>' +
      '<div style="flex:1;display:grid;gap:8px"><div class="skeleton" style="width:65%"></div><div class="skeleton" style="width:30%;height:12px"></div><div class="skeleton" style="height:4px"></div></div></div>';
    return '<div class="list" aria-busy="true" data-spec="indicative" data-spec-note="骨架屏与列表同形，数据到达时布局不跳动">' + row + row + row + '</div>';
  }
  function errorView(retryHref) {
    return '<div class="state state--error" role="alert" data-spec="tbd" data-spec-note="加载失败的文案与重试策略（自动重试几次？）待定">' +
      '<span class="state__icon">' + icon('alert') + '</span>' +
      '<p class="state__title">没加载出来</p><p class="state__text">网络好像不太好，稍后再试一次。</p>' +
      '<a class="btn btn--secondary" href="' + retryHref + '">重新加载</a></div>';
  }

  /* ---------- Shelf ---------- */
  Proto.page('/', {
    title: '书架',
    states: ['default', 'empty', 'loading', 'error'],
    render: function (ctx) {
      var tab = ctx.query.get('tab') === 'done' ? 'done' : 'reading';
      var head = '<header class="page-header"><div class="page-header__text"><p class="eyebrow">' + eyebrowDate() + '</p>' +
        '<h1 class="title" data-spec="fixed" data-spec-note="标题用品牌宋体粗体（Noto Serif SC Bold），字距略收">我的书架</h1></div></header>';
      var addButton = '<div class="bottom-bar"><a class="btn btn--primary btn--block btn--large" href="#/add" data-spec="fixed" data-spec-note="主按钮：苔绿底，手机上通栏，固定在底部">' + icon('plus') + '添加一本书</a></div>';
      if (ctx.state === 'loading') return head + loadingView();
      if (ctx.state === 'error') return head + errorView('#/');

      var books = ctx.state === 'empty' ? [] : ctx.store.books;
      if (!books.length) {
        return head + '<div class="state" data-spec="fixed" data-spec-note="空书架：一个安静的图标 + 一句鼓励 + 主按钮">' +
          '<span class="state__icon state__icon--accent">' + icon('book') + '</span>' +
          '<p class="state__title">书架还空着</p><p class="state__text">放上第一本在读的书，从今天开始记录。</p>' +
          '<a class="btn btn--primary" href="#/add">' + icon('plus') + '添加第一本书</a></div>';
      }

      var reading = books.filter(function (b) { return !isDone(b); });
      var done = books.filter(isDone);
      var shown = tab === 'done' ? done : reading;
      var week = ctx.store.week.map(function (read, i) {
        return '<span class="week__day' + (read ? ' is-read' : '') + (i === todayIndex() ? ' is-today' : '') + '">' +
          '<span class="week__dot"></span><span class="week__label">' + WEEKDAYS[i] + '</span></span>';
      }).join('');
      var streak = '<section class="streak" data-spec="indicative" data-spec-note="连续阅读：像笔记本页边的大号宋体天数 + 本周 7 天打点；琥珀只用于已读的日子">' +
        '<p class="streak__num">' + esc(ctx.store.streakDays) + '<span class="streak__unit">天</span></p>' +
        '<div class="streak__text"><p class="streak__label">连续阅读</p><p class="tertiary">今天也读了一点，很好。</p></div>' +
        '<div class="week" aria-label="本周阅读情况">' + week + '</div>' +
        '<span class="spec-anchor" data-spec="tbd" data-spec-note="“连续天数”的规则待定：按自然日还是 24 小时？漏记一天是否清零？"></span></section>';
      var tabs = '<div class="shelf-bar"><nav class="segmented" aria-label="书架分类" data-spec="fixed" data-spec-note="在读 / 读完 两个分类，数字为本数">' +
        '<a class="segmented__item' + (tab === 'reading' ? ' is-active' : '') + '" href="#/">在读 <span class="num">' + reading.length + '</span></a>' +
        '<a class="segmented__item' + (tab === 'done' ? ' is-active' : '') + '" href="#/?tab=done">读完 <span class="num">' + done.length + '</span></a></nav>' +
        '<span class="tertiary" data-spec="tbd" data-spec-note="书架排序规则待定：目前按添加时间（新的在前），是否改为最近记录在前？">按添加时间</span></div>';
      var list = shown.length
        ? '<ul class="list book-list">' + shown.map(function (b, i) {
            return '<li><a class="list__item book-row" href="#/book/' + esc(b.id) + '"' +
              (i === 0 ? ' data-spec="fixed" data-spec-note="书目行：书本式封面 + 书名（单行省略）+ 作者 + 细进度条与百分比，行间用细线分隔"' : '') + '>' +
              cover(b, 'sm') +
              '<span class="list__main"><span class="list__title">' + esc(b.title) + '</span>' +
              '<span class="list__meta">' + (b.author ? esc(b.author) : '作者未填写') + '</span>' +
              '<span class="book-row__progress">' + progress(b) + '<span class="num tertiary">' + percent(b) + '%</span></span></span></a></li>';
          }).join('') + '</ul>'
        : '<div class="state state--compact"><p class="state__text">' + (tab === 'done' ? '还没有读完的书，慢慢来。' : '在读的书都读完了，添加下一本吧。') + '</p></div>';
      return head + streak + tabs + list + addButton;
    }
  });

  /* ---------- Book detail + log today's page ---------- */
  Proto.page('/book/:id', {
    title: '书的详情',
    sample: '/book/1',
    states: ['default', 'loading', 'error'],
    render: function (ctx) {
      var back = '<a class="back-link" href="#/">' + icon('back') + '书架</a>';
      if (ctx.state === 'loading') return back + loadingView();
      var book = findBook(ctx.store, ctx.params.id);
      if (ctx.state === 'error' || !book) return back + errorView('#/book/' + esc(ctx.params.id));

      var hero = '<section class="book-hero">' + cover(book, 'lg') +
        '<div class="book-hero__text"><span class="badge' + (isDone(book) ? ' badge--done' : '') + '">' + (isDone(book) ? '已读完' : '在读') + '</span>' +
        '<h1 class="title book-hero__title">' + esc(book.title) + '</h1>' +
        '<p class="secondary">' + (book.author ? esc(book.author) : '作者未填写') + '</p></div></section>';
      var stats = '<section class="stats" data-spec="fixed" data-spec-note="进度：三项数字（等宽数字）以细线分隔 + 进度条">' +
        '<div class="stats__row">' +
        '<div><p class="tertiary">进度</p><p class="stats__value num">' + percent(book) + '<small>%</small></p></div>' +
        '<div><p class="tertiary">已读</p><p class="stats__value num">' + esc(book.currentPage) + '<small>页</small></p></div>' +
        '<div><p class="tertiary">剩余</p><p class="stats__value num">' + esc(book.totalPages - book.currentPage) + '<small>页</small></p></div></div>' +
        progress(book, true) + '</section>';

      var form = isDone(book)
        ? '<section class="done-panel" data-spec="indicative" data-spec-note="读完后的庆祝面板，文案与样式可调整">' +
          '<span class="state__icon state__icon--accent">' + icon('check') + '</span>' +
          '<div><p class="done-panel__title">读完了</p><p class="secondary">一共 ' + esc(book.totalPages) + ' 页，记得给自己一点奖励。</p></div></section>'
        : '<section class="section"><h2 class="section__title">今天的进度</h2>' +
          '<form class="log-form" novalidate data-spec="fixed" data-spec-note="核心操作：输入今天读到的页码并记录；校验：必须大于上次页码、不超过总页数">' +
          '<div class="field"><label class="field__label" for="page">今天读到第几页？</label>' +
          '<div class="inline-field"><input class="field__input num" id="page" name="page" type="number" inputmode="numeric" min="' + (book.currentPage + 1) + '" max="' + book.totalPages + '" placeholder="比如 ' + Math.min(book.currentPage + 20, book.totalPages) + '">' +
          '<button class="btn btn--primary" type="submit">记录</button></div>' +
          '<p class="field__hint">上次读到第 ' + esc(book.currentPage) + ' 页，共 ' + esc(book.totalPages) + ' 页</p>' +
          '<p class="field__error" id="page-error" hidden></p></div></form></section>';

      var logs = book.logs.slice().reverse();
      var history = '<section class="section"><h2 class="section__title">阅读记录</h2>' +
        (logs.length
          ? '<ul class="list history" data-spec="indicative" data-spec-note="记录列表：日期 + 读到第几页 + 当天读了多少页（不用强调色）">' + logs.map(function (log, i) {
              var prev = logs[i + 1] ? logs[i + 1].page : 0;
              return '<li class="list__item"><span class="list__main"><span class="list__title num">' + esc(log.date) + '</span>' +
                '<span class="list__meta">读到第 ' + esc(log.page) + ' 页</span></span><span class="history__gain num">+' + (log.page - prev) + ' 页</span></li>';
            }).join('') + '</ul>'
          : '<p class="tertiary">还没有记录，读完今天的部分就来记一下吧。</p>') + '</section>';
      var manage = '<div class="manage"><a href="#" class="btn btn--ghost" data-out data-spec="tbd" data-spec-note="编辑书籍信息、删除书籍不在本期原型范围，是否需要、放在哪里待定">' + icon('more') + '编辑或删除</a></div>';
      return back + hero + stats + form + history + manage;
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

      input.addEventListener('input', function () { if (!error.hidden) showError(''); });

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
          ctx.store.week[todayIndex()] = true;
          book.currentPage = page;
          book.logs.push({ date: date, page: page });
          Proto.save();
          Proto.refresh();
          Proto.toast(isDone(book) ? '读完了，恭喜你' : '记好了，今天也读了一点，很好');
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
      return '<a class="back-link" href="#/">' + icon('back') + '取消</a>' +
        '<header class="page-header"><div class="page-header__text"><h1 class="title">添加一本书</h1>' +
        '<p class="secondary">放上书架后，就可以每天记录进度。</p></div></header>' +
        '<form class="add-form" novalidate>' +
        '<div class="field" data-spec="fixed" data-spec-note="书名必填，最多 60 字"><label class="field__label" for="title">书名</label>' +
        '<input class="field__input" id="title" name="title" autocomplete="off" placeholder="比如《慢慢来的散步》"><p class="field__error" hidden></p></div>' +
        '<div class="field"><label class="field__label" for="author">作者 <span class="tertiary">选填</span></label>' +
        '<input class="field__input" id="author" name="author" autocomplete="off"><p class="field__error" hidden></p></div>' +
        '<div class="field" data-spec="tbd" data-spec-note="总页数上限暂定 5000，电子书没有页数时怎么办待定"><label class="field__label" for="total">总页数</label>' +
        '<input class="field__input num" id="total" name="total" type="number" inputmode="numeric" min="1" max="5000" placeholder="比如 240"><p class="field__error" hidden></p></div>' +
        '<fieldset class="field cover-picker" data-spec="indicative" data-spec-note="没有真实封面时用书名生成的色彩封面；颜色取自品牌色板，可调整"><legend class="field__label">封面</legend>' +
        '<div class="cover-picker__options">' + COVERS.map(function (c, i) {
          return '<label class="cover-option"><input type="radio" name="cover" value="' + c[0] + '"' + (i === 0 ? ' checked' : '') + '>' +
            '<span class="cover cover--' + c[0] + ' cover--md"><span class="cover__title" data-live-title>书名</span></span>' +
            '<span class="cover-option__name">' + c[1] + '</span></label>';
        }).join('') + '</div></fieldset>' +
        '<div class="bottom-bar"><button class="btn btn--primary btn--block btn--large" type="submit" data-spec="fixed" data-spec-note="保存后跳到这本书的详情页">放上书架</button></div>' +
        '</form>';
    },
    mount: function (root, ctx) {
      var form = root.querySelector('.add-form');
      var button = form.querySelector('button[type="submit"]');
      // Cover previews show the title as it is typed.
      form.title.addEventListener('input', function () {
        Array.prototype.forEach.call(form.querySelectorAll('[data-live-title]'), function (el) { el.textContent = form.title.value.trim() || '书名'; });
      });

      // An error clears as soon as the field is edited.
      ['title', 'total'].forEach(function (name) {
        form[name].addEventListener('input', function () { setError(name, ''); });
      });

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

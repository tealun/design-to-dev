/* data.js — Readlog fake data. Fictional books and authors; replace with real API data in development. */
window.MOCK = {
  streakDays: 5,
  week: [true, true, false, true, true, true, false], // Monday to Sunday: read on that day
  books: [
    { id: '1', title: '慢慢来的散步', author: '林小鹿', totalPages: 240, currentPage: 96, cover: 'moss',
      logs: [ { date: '2026-10-30', page: 60 }, { date: '2026-10-31', page: 81 }, { date: '2026-11-01', page: 96 } ] },
    { id: '2', title: '一个关于海边灯塔、旧书店和一只总在下午三点出现的猫的很长很长的故事', author: '周未', totalPages: 512, currentPage: 12, cover: 'clay',
      logs: [ { date: '2026-11-01', page: 12 } ] },
    { id: '3', title: '城市观察笔记', author: '', totalPages: 180, currentPage: 0, cover: 'slate', logs: [] },
    { id: '4', title: '冬天的厨房', author: '何夕', totalPages: 160, currentPage: 160, cover: 'amber',
      logs: [ { date: '2026-10-20', page: 120 }, { date: '2026-10-22', page: 160 } ] }
  ]
};

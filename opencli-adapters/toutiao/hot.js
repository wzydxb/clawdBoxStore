import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'toutiao',
  name: 'hot',
  description: '今日头条热榜，返回排名、标题、热度',
  domain: 'www.toutiao.com',
  args: [
    { name: 'limit', type: 'int', default: 20, help: '返回条数（最多50）' },
  ],
  columns: ['rank', 'title', 'hot'],
  pipeline: [
    { navigate: 'https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc' },
    { wait: 5 },
    { evaluate: `(() => {
  const results = [];
  const items = document.querySelectorAll('.hot-board-item, [class*="hot-board"] li, [class*="HotBoard"] li');
  let rank = 1;
  for (const el of items) {
    const titleEl = el.querySelector('[class*="title"], a, h3');
    const title = titleEl?.innerText?.trim() || '';
    const hotEl = el.querySelector('[class*="hot"], [class*="count"]');
    const hot = hotEl?.innerText?.trim() || '';
    if (title && title.length > 2) {
      results.push({ rank: String(rank), title, hot });
      rank++;
    }
    if (rank > 50) break;
  }
  return results;
})()` },
    { map: { rank: '${{ item.rank }}', title: '${{ item.title }}', hot: '${{ item.hot }}' } },
    { limit: '${{ args.limit }}' },
  ],
});

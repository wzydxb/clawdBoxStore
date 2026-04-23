import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'zhihu',
  name: 'hot',
  description: '知乎热榜，返回排名、标题、热度',
  domain: 'www.zhihu.com',
  args: [
    { name: 'limit', type: 'int', default: 20, help: '返回条数（最多50）' },
  ],
  columns: ['rank', 'title', 'hot'],
  pipeline: [
    { navigate: 'https://www.zhihu.com/hot' },
    { wait: 5 },
    { evaluate: `(() => {
  const results = [];
  // Try multiple selectors for zhihu hot list
  const items = document.querySelectorAll('.HotItem, [class*="HotItem-content"], .css-1bnkhe8');
  let rank = 1;
  for (const el of items) {
    const titleEl = el.querySelector('h2, [class*="HotItem-title"], .css-1bnkhe8');
    const title = titleEl?.innerText?.trim() || el.querySelector('a')?.innerText?.trim() || '';
    const hotEl = el.querySelector('[class*="HotItem-metrics"], [class*="metrics"]');
    const hot = hotEl?.innerText?.trim() || '';
    if (title && title.length > 2) {
      results.push({ rank: String(rank), title, hot });
      rank++;
    }
    if (rank > 50) break;
  }
  // Fallback: try section list items
  if (results.length === 0) {
    const sections = document.querySelectorAll('section');
    for (const s of sections) {
      const a = s.querySelector('a[href*="/question/"]');
      if (!a) continue;
      const title = a.innerText?.trim() || '';
      const hot = s.querySelector('[class*="metric"]')?.innerText?.trim() || '';
      if (title) results.push({ rank: String(rank), title, hot });
      rank++;
      if (rank > 50) break;
    }
  }
  return results;
})()` },
    { map: { rank: '${{ item.rank }}', title: '${{ item.title }}', hot: '${{ item.hot }}' } },
    { limit: '${{ args.limit }}' },
  ],
});

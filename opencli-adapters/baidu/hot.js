import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'baidu',
  name: 'hot',
  description: '百度热搜榜，返回排名、关键词、热度',
  domain: 'www.baidu.com',
  args: [
    { name: 'limit', type: 'int', default: 20, help: '返回条数（最多50）' },
  ],
  columns: ['rank', 'keyword', 'hot'],
  pipeline: [
    { navigate: 'https://top.baidu.com/board?tab=realtime' },
    { wait: 4 },
    { evaluate: `(() => {
  const results = [];
  const items = document.querySelectorAll('.c-single-text-ellipsis, [class*="content_1YWBm"]');
  let rank = 1;
  for (const el of items) {
    const keyword = el.innerText?.trim() || '';
    if (keyword && keyword.length > 1 && keyword.length < 60) {
      results.push({ rank: String(rank), keyword, hot: '' });
      rank++;
    }
    if (rank > 50) break;
  }
  // Fallback: try card items
  if (results.length === 0) {
    const cards = document.querySelectorAll('[class*="item_"]');
    for (const card of cards) {
      const titleEl = card.querySelector('[class*="title_"]');
      const hotEl = card.querySelector('[class*="hot_"]');
      const keyword = titleEl?.innerText?.trim() || '';
      const hot = hotEl?.innerText?.trim() || '';
      if (keyword && keyword.length > 1) {
        results.push({ rank: String(rank), keyword, hot });
        rank++;
      }
      if (rank > 50) break;
    }
  }
  return results;
})()` },
    { map: { rank: '${{ item.rank }}', keyword: '${{ item.keyword }}', hot: '${{ item.hot }}' } },
    { limit: '${{ args.limit }}' },
  ],
});

import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'weibo',
  name: 'hot',
  description: '微博热搜榜，返回排名、关键词、热度值',
  domain: 's.weibo.com',
  args: [
    { name: 'limit', type: 'int', default: 20, help: '返回条数（最多50）' },
  ],
  columns: ['rank', 'keyword', 'hot'],
  pipeline: [
    { navigate: 'https://s.weibo.com/top/summary?cate=realtimehot' },
    { wait: 4 },
    { evaluate: `(() => {
  const results = [];
  // Main hot list table
  const rows = document.querySelectorAll('#pl_top_realtimehot table tbody tr');
  for (const row of rows) {
    const rankEl = row.querySelector('td.td-01');
    const rank = rankEl?.innerText?.trim() || '';
    const keywordEl = row.querySelector('td.td-02 a');
    const keyword = keywordEl?.innerText?.trim() || '';
    const hotEl = row.querySelector('td.td-02 span');
    const hot = hotEl?.innerText?.trim() || '';
    if (keyword && keyword.length > 1) {
      results.push({ rank, keyword, hot });
    }
  }
  return results;
})()` },
    { map: { rank: '${{ item.rank }}', keyword: '${{ item.keyword }}', hot: '${{ item.hot }}' } },
    { limit: '${{ args.limit }}' },
  ],
});

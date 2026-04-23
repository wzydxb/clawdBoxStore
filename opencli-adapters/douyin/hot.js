import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'douyin',
  name: 'hot',
  description: '抖音热点榜，返回排名、话题、热度',
  domain: 'www.douyin.com',
  args: [
    { name: 'limit', type: 'int', default: 20, help: '返回条数（最多50）' },
  ],
  columns: ['rank', 'topic', 'hot'],
  pipeline: [
    { navigate: 'https://www.douyin.com/hot' },
    { wait: 5 },
    { evaluate: `(() => {
  const results = [];
  // Douyin hot list items
  const items = document.querySelectorAll('[class*="hot-list"] li, [class*="hotList"] li, [class*="HotList"] li');
  let rank = 1;
  for (const el of items) {
    const topicEl = el.querySelector('[class*="title"], [class*="name"], a');
    const topic = topicEl?.innerText?.trim() || '';
    const hotEl = el.querySelector('[class*="hot"], [class*="count"], [class*="num"]');
    const hot = hotEl?.innerText?.trim() || '';
    if (topic && topic.length > 1) {
      results.push({ rank: String(rank), topic, hot });
      rank++;
    }
    if (rank > 50) break;
  }
  // Fallback: try generic list
  if (results.length === 0) {
    const links = document.querySelectorAll('a[href*="hashtag"], a[href*="search"]');
    for (const a of links) {
      const topic = a.innerText?.trim() || '';
      if (topic && topic.length > 2 && topic.length < 50) {
        results.push({ rank: String(rank), topic, hot: '' });
        rank++;
      }
      if (rank > 50) break;
    }
  }
  return results;
})()` },
    { map: { rank: '${{ item.rank }}', topic: '${{ item.topic }}', hot: '${{ item.hot }}' } },
    { limit: '${{ args.limit }}' },
  ],
});

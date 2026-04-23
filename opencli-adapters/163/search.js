import { cli } from '@jackwener/opencli/registry';
cli({
  site: '163',
  name: 'search',
  description: '网易新闻搜索，返回标题、链接、来源、时间',
  domain: 'news.163.com',
  args: [
    { name: 'keyword', positional: true, type: 'string', required: true, help: '搜索关键词' },
    { name: 'limit', type: 'int', default: 10, help: '返回结果数量' },
  ],
  columns: ['title', 'url', 'source', 'time'],
  pipeline: [
    { navigate: 'https://news.163.com/search/?keyword=${{ args.keyword | urlencode }}' },
    { wait: 5 },
    { evaluate: `(() => {
  const results = [];
  const seen = new Set();
  // 163 search redirects to homepage — grab h3 news links as fallback
  const h3links = document.querySelectorAll('h3 a[href*="163.com"]');
  for (const a of h3links) {
    const title = a.innerText?.trim() || '';
    const url = a.href || '';
    if (title.length > 5 && title.length < 100 && !seen.has(url)) {
      seen.add(url);
      const parent = a.closest('li, div, article') || a.parentElement;
      const source = parent?.querySelector('[class*="source"], [class*="media"]')?.innerText?.trim() || '';
      const time = parent?.querySelector('[class*="time"], time')?.innerText?.trim() || '';
      results.push({ title, url, source, time });
    }
    if (results.length >= 20) break;
  }
  return results;
})()` },
    { map: { title: '${{ item.title }}', url: '${{ item.url }}', source: '${{ item.source }}', time: '${{ item.time }}' } },
    { limit: '${{ args.limit }}' },
  ],
});

import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'so',
  name: 'search',
  description: '搜索360搜索，返回标题、链接、摘要',
  domain: 'www.so.com',
  args: [
    { name: 'keyword', positional: true, type: 'string', required: true, help: '搜索关键词' },
    { name: 'limit', type: 'int', default: 10, help: '返回结果数量' },
  ],
  columns: ['title', 'url', 'snippet'],
  pipeline: [
    { navigate: 'https://www.so.com/s?q=${{ args.keyword | urlencode }}' },
    { wait: 2 },
    { evaluate: `(() => {
  const results = [];
  const items = document.querySelectorAll('#results .res-list');
  for (const el of items) {
    const h3 = el.querySelector('h3');
    const a = h3?.querySelector('a') || el.querySelector('a');
    const title = h3?.innerText?.trim();
    const url = a?.href || '';
    const snippet = el.querySelector('.res-desc, .res-summary')?.innerText?.trim() || '';
    if (title && url && !url.startsWith('javascript')) {
      results.push({ title, url, snippet: snippet.slice(0, 300) });
    }
    if (results.length >= 20) break;
  }
  return results;
})()` },
    { map: { title: '${{ item.title }}', url: '${{ item.url }}', snippet: '${{ item.snippet }}' } },
    { limit: '${{ args.limit }}' },
  ],
});

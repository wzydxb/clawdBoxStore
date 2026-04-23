import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'sohu',
  name: 'search',
  description: '搜索搜狐，返回标题、链接、摘要',
  domain: 'www.sohu.com',
  args: [
    { name: 'keyword', positional: true, type: 'string', required: true, help: '搜索关键词' },
    { name: 'limit', type: 'int', default: 10, help: '返回结果数量' },
  ],
  columns: ['title', 'url', 'snippet'],
  pipeline: [
    { navigate: 'https://www.sohu.com/a/search?keyword=${{ args.keyword | urlencode }}' },
    { wait: 2 },
    { evaluate: `(() => {
  const results = [];
  const items = document.querySelectorAll('.search-result-item, .article-item');
  for (const el of items) {
    const a = el.querySelector('a[href*="sohu.com"]') || el.querySelector('a');
    const title = a?.innerText?.trim() || el.querySelector('h3,h2')?.innerText?.trim();
    const url = a?.href || '';
    const snippet = el.querySelector('.summary, .desc, p')?.innerText?.trim() || '';
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

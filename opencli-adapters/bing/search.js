import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'bing',
  name: 'search',
  description: '搜索必应，返回标题、链接、摘要',
  domain: 'www.bing.com',
  args: [
    { name: 'keyword', positional: true, type: 'string', required: true, help: '搜索关键词' },
    { name: 'limit', type: 'int', default: 10, help: '返回结果数量' },
  ],
  columns: ['title', 'url', 'snippet'],
  pipeline: [
    { navigate: 'https://www.bing.com/search?q=${{ args.keyword | urlencode }}' },
    { wait: 2 },
    { evaluate: `(() => {
  const results = [];
  const items = document.querySelectorAll('#b_results .b_algo');
  for (const el of items) {
    const h2 = el.querySelector('h2');
    const a = h2?.querySelector('a');
    const title = a?.innerText?.trim();
    const url = a?.href || '';
    const snippet = el.querySelector('.b_caption p')?.innerText?.trim() || '';
    if (title && url) results.push({ title, url, snippet: snippet.slice(0, 300) });
    if (results.length >= 20) break;
  }
  return results;
})()` },
    { map: { title: '${{ item.title }}', url: '${{ item.url }}', snippet: '${{ item.snippet }}' } },
    { limit: '${{ args.limit }}' },
  ],
});

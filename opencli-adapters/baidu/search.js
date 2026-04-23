import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'baidu',
  name: 'search',
  description: '搜索百度，返回标题、链接、摘要（使用真实浏览器，无需代理）',
  domain: 'www.baidu.com',
  args: [
    { name: 'keyword', positional: true, type: 'string', required: true, help: '搜索关键词' },
    { name: 'limit', type: 'int', default: 10, help: '返回结果数量（最多 20）' },
  ],
  columns: ['title', 'url', 'snippet'],
  pipeline: [
    { navigate: 'https://www.baidu.com/s?wd=${{ args.keyword | urlencode }}&rn=${{ args.limit }}' },
    { wait: 2 },
    { evaluate: `(() => {
  const results = [];
  const containers = document.querySelectorAll('#content_left .result.c-container, #content_left .result-op.c-container');
  for (const el of containers) {
    const h3 = el.querySelector('h3');
    if (!h3) continue;
    const a = h3.querySelector('a') || el.querySelector('a');
    const title = h3.innerText?.trim();
    const url = a?.href || '';
    const snippet =
      el.querySelector('.content-right_8Zs40')?.innerText?.trim() ||
      el.querySelector('.c-abstract')?.innerText?.trim() ||
      el.querySelector('[class*="content"]')?.innerText?.trim() ||
      '';
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

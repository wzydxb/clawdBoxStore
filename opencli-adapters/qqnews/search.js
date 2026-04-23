import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'qqnews',
  name: 'search',
  description: '腾讯新闻搜索，返回标题、链接、来源、时间、摘要（intercept API）',
  domain: 'new.qq.com',
  args: [
    { name: 'keyword', positional: true, type: 'string', required: true, help: '搜索关键词' },
    { name: 'limit', type: 'int', default: 10, help: '返回结果数量' },
  ],
  columns: ['title', 'url', 'source', 'time', 'abstract'],
  pipeline: [
    { navigate: 'https://new.qq.com/search?query=${{ args.keyword | urlencode }}' },
    { wait: 6 },
    { evaluate: `(() => {
  // QQ news renders via API — extract from page state or DOM
  const results = [];
  // Try to find rendered article cards
  const cards = document.querySelectorAll('[class*="article"], [class*="news-item"], [class*="search-result"]');
  for (const card of cards) {
    const a = card.querySelector('a[href*="inews.qq.com"], a[href*="new.qq.com"]');
    const title = card.querySelector('[class*="title"], h3, h2')?.innerText?.trim() || a?.innerText?.trim() || '';
    const url = a?.href || '';
    const source = card.querySelector('[class*="source"], [class*="media"]')?.innerText?.trim() || '';
    const time = card.querySelector('[class*="time"], time')?.innerText?.trim() || '';
    const abstract = card.querySelector('[class*="abstract"], [class*="desc"], p')?.innerText?.trim() || '';
    if (title && title.length > 5) {
      results.push({ title, url, source, time, abstract: abstract.slice(0, 150) });
    }
    if (results.length >= 20) break;
  }
  // Fallback: grab all inews links
  if (results.length === 0) {
    const links = document.querySelectorAll('a[href*="inews.qq.com/a/"], a[href*="view.inews.qq.com"]');
    for (const a of links) {
      const title = a.innerText?.trim() || a.title || '';
      if (title.length > 5) {
        results.push({ title, url: a.href, source: '', time: '', abstract: '' });
      }
      if (results.length >= 20) break;
    }
  }
  return results;
})()` },
    { map: { title: '${{ item.title }}', url: '${{ item.url }}', source: '${{ item.source }}', time: '${{ item.time }}', abstract: '${{ item.abstract }}' } },
    { limit: '${{ args.limit }}' },
  ],
});

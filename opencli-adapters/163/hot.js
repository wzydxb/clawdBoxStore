import { cli } from '@jackwener/opencli/registry';
cli({
  site: '163',
  name: 'hot',
  description: '网易新闻热点，返回标题、链接、来源、时间（首页实时热点）',
  domain: 'news.163.com',
  args: [
    { name: 'limit', type: 'int', default: 20, help: '返回条数' },
  ],
  columns: ['title', 'url', 'source', 'time'],
  pipeline: [
    { navigate: 'https://news.163.com/' },
    { wait: 4 },
    { evaluate: `(() => {
  const results = [];
  const seen = new Set();
  const h3links = document.querySelectorAll('h3 a[href*="163.com"]');
  for (const a of h3links) {
    const title = a.innerText?.trim() || '';
    const url = a.href || '';
    // Only news articles, exclude open.163.com video and mail
    if (title.length > 5 && title.length < 100 && !seen.has(url)
        && !url.includes('open.163.com') && !url.includes('mail.163.com')
        && (url.includes('news.163.com') || url.includes('163.com/dy/') || url.includes('www.163.com/'))) {
      seen.add(url);
      const parent = a.closest('li, div, article') || a.parentElement;
      const source = parent?.querySelector('[class*="source"], [class*="media"]')?.innerText?.trim() || '';
      const time = parent?.querySelector('[class*="time"], time')?.innerText?.trim() || '';
      results.push({ title, url, source, time });
    }
    if (results.length >= 50) break;
  }
  return results;
})()` },
    { map: { title: '${{ item.title }}', url: '${{ item.url }}', source: '${{ item.source }}', time: '${{ item.time }}' } },
    { limit: '${{ args.limit }}' },
  ],
});

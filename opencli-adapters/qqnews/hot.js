import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'qqnews',
  name: 'hot',
  description: '腾讯新闻热点榜，返回标题、链接、来源、时间',
  domain: 'new.qq.com',
  args: [
    { name: 'limit', type: 'int', default: 20, help: '返回条数' },
  ],
  columns: ['title', 'url', 'source', 'time'],
  pipeline: [
    { navigate: 'https://new.qq.com/' },
    { wait: 5 },
    { evaluate: `(() => {
  const results = [];
  // QQ news homepage hot articles
  const cards = document.querySelectorAll('[class*="article"], [class*="news-item"], [class*="feed-item"], [class*="item_"]');
  for (const card of cards) {
    const a = card.querySelector('a[href*="qq.com"]');
    const titleEl = card.querySelector('[class*="title"], h3, h2, [class*="head"]');
    const title = titleEl?.innerText?.trim() || a?.innerText?.trim() || '';
    const url = a?.href || '';
    const source = card.querySelector('[class*="source"], [class*="media"], [class*="author"]')?.innerText?.trim() || '';
    const time = card.querySelector('[class*="time"], time, [class*="date"]')?.innerText?.trim() || '';
    if (title && title.length > 5 && title.length < 100 && url) {
      results.push({ title, url, source, time });
    }
    if (results.length >= 50) break;
  }
  // Fallback: grab inews links from page
  if (results.length === 0) {
    const links = document.querySelectorAll('a[href*="inews.qq.com"], a[href*="view.inews.qq.com"]');
    for (const a of links) {
      const title = a.innerText?.trim() || '';
      if (title.length > 5 && title.length < 100) {
        results.push({ title, url: a.href, source: '', time: '' });
      }
      if (results.length >= 50) break;
    }
  }
  return results;
})()` },
    { map: { title: '${{ item.title }}', url: '${{ item.url }}', source: '${{ item.source }}', time: '${{ item.time }}' } },
    { limit: '${{ args.limit }}' },
  ],
});

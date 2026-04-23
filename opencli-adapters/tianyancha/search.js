import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'tianyancha', name: 'search',
  description: '天眼查企业搜索，返回企业名称、法人、注册资本、成立日期、状态',
  domain: 'www.tianyancha.com',
  args: [
    { name: 'company', positional: true, type: 'string', required: true, help: '企业名称或关键词' },
    { name: 'limit', type: 'int', default: 5, help: '返回结果数量' },
  ],
  columns: ['name', 'status', 'legal_person', 'capital', 'established'],
  pipeline: [
    { navigate: 'https://www.tianyancha.com/search?key=${{ args.company | urlencode }}' },
    { wait: 5 },
    { evaluate: `(() => {
  const results = [];
  // search-item__ is the per-company card container (class has hash suffix, use prefix match)
  const items = document.querySelectorAll('[class*="search-item__"]');
  for (const el of items) {
    const text = el.innerText || '';
    if (!text.includes('法定代表人')) continue;

    // Company name: first non-empty line before status tags
    const lines = text.split('\\n').map(s => s.trim()).filter(Boolean);
    const name = lines[0] || '';

    // Status: 存续/注销/吊销 etc — appears right after name
    const status = lines[1] && lines[1].length < 10 ? lines[1] : '';

    // Info row: 法定代表人/注册资本/成立日期
    const infoEl = el.querySelector('[class*="info-row__"]');
    const info = infoEl?.innerText || '';
    const legal = (info.match(/法定代表人[：:](.*?)(?:\\n|注册|$)/) || [])[1]?.trim() || '';
    const capital = (info.match(/注册资本[：:](.*?)(?:\\n|成立|$)/) || [])[1]?.trim() || '';
    const established = (info.match(/成立日期[：:](.*?)(?:\\n|统一|$)/) || [])[1]?.trim() || '';

    if (name) results.push({ name, status, legal_person: legal, capital, established });
    if (results.length >= 10) break;
  }
  return results;
})()` },
    { map: { name: '${{ item.name }}', status: '${{ item.status }}', legal_person: '${{ item.legal_person }}', capital: '${{ item.capital }}', established: '${{ item.established }}' } },
    { limit: '${{ args.limit }}' },
  ],
});

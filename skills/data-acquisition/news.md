---
name: data-acquisition/news
description: 新闻资讯获取。网易163、腾讯新闻、36氪、新浪财经、BBC/Bloomberg RSS、行业协会报告。覆盖国内外主流媒体。
---

# 新闻资讯数据

## 工具地图

| 来源 | 命令/方式 | 特点 |
|------|-----------|------|
| 网易新闻 | `opencli 163 hot/search` | 综合新闻，覆盖广 |
| 腾讯新闻 | `opencli qqnews hot/search` | 综合新闻，时效强 |
| 36氪 | `opencli 36kr hot/news/search` | 科技/创投/商业 |
| 新浪财经 | `opencli sinafinance news` | 财经快讯，实时 |
| BBC | `opencli bbc news` | 国际新闻（英文） |
| Bloomberg | `opencli bloomberg markets/tech` | 金融/科技（英文） |
| 虎扑 | `opencli hupu hot` | 体育/生活 |
| 行业协会 | playwright headless | 深度行业报告 |

## 国内新闻

```bash
# 网易新闻热点（综合）
opencli 163 hot --limit 20

# 网易新闻搜索
opencli 163 search '关键词' --limit 10

# 腾讯新闻热点
opencli qqnews hot --limit 20

# 腾讯新闻搜索
opencli qqnews search '关键词' --limit 10

# 36氪热榜（科技/商业）
opencli 36kr hot --limit 20

# 36氪最新资讯
opencli 36kr news --limit 20

# 36氪搜索
opencli 36kr search '关键词' --limit 10

# 新浪财经快讯（实时）
opencli sinafinance news --limit 30
```

## 国际新闻（RSS，无需登录）

```bash
# BBC新闻
opencli bbc news --limit 20

# Bloomberg各频道
opencli bloomberg main --limit 20      # 头条
opencli bloomberg markets --limit 20   # 市场
opencli bloomberg tech --limit 20      # 科技
opencli bloomberg economics --limit 20 # 经济

# Google新闻
opencli google news --limit 20

# Reuters路透社
opencli reuters search '关键词' --limit 10
```

## 行业协会报告（playwright抓取）

```python
from playwright.sync_api import sync_playwright

# 常用协会网站
ASSOCIATIONS = {
    '互联网': 'https://www.cnnic.cn/hlwfzyj/',
    '制造业': 'https://www.mei.net.cn/news/',
    '零售': 'https://www.ccfa.org.cn/portal/cn/view/1/1.html',
    '物流': 'https://www.chinawuliu.com.cn/lhhzq/',
    '金融': 'https://www.china-cba.net/Index/index.html',
}

def fetch_association_news(url, limit=10):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        page.goto(url, timeout=15000)
        page.wait_for_timeout(3000)
        items = page.evaluate(f'''() => {{
            const links = document.querySelectorAll('a');
            const results = [];
            for (const a of links) {{
                const title = a.innerText?.trim() || '';
                const href = a.href || '';
                if (title.length > 8 && title.length < 80 && href.startsWith('http')) {{
                    results.push({{title, url: href}});
                }}
                if (results.length >= {limit}) break;
            }}
            return results;
        }}''')
        browser.close()
        return items
```

## RSS 批量订阅（免费，无反爬）

```python
import urllib.request
import xml.etree.ElementTree as ET

RSS_FEEDS = {
    '36氪': 'https://36kr.com/feed',                          # ✅ 验证可用
    '少数派': 'https://sspai.com/feed',                        # ✅ 验证可用
    '爱范儿': 'https://www.ifanr.com/feed',                    # ✅ 验证可用
    '极客公园': 'https://www.geekpark.net/rss',
    'BBC中文': 'https://feeds.bbci.co.uk/zhongwen/simp/rss.xml', # ✅ 验证可用
    # 路透中文RSS已停止免费服务，改用Google News聚合
    '路透中文(Google)': 'https://news.google.com/rss/search?q=reuters+china&hl=zh-CN&gl=CN&ceid=CN:zh-Hans',
}

def fetch_rss(feed_url, limit=10):
    try:
        req = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
        content = urllib.request.urlopen(req, timeout=10).read()
        root = ET.fromstring(content)
        items = []
        for item in root.findall('.//item')[:limit]:
            title = item.findtext('title', '').strip()
            link = item.findtext('link', '').strip()
            pub_date = item.findtext('pubDate', '').strip()
            desc = item.findtext('description', '').strip()[:150]
            if title:
                items.append({'title': title, 'url': link, 'date': pub_date, 'desc': desc})
        return items
    except Exception as e:
        return [{'error': str(e)}]

# 批量拉取多个RSS源
all_news = {}
for name, url in RSS_FEEDS.items():
    all_news[name] = fetch_rss(url, limit=5)
```

## 虎嗅（RSS超时，改用playwright）

```python
def fetch_huxiu_news(limit=20):
    """虎嗅最新文章（RSS不稳定，用playwright直接抓）"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.huxiu.com/", timeout=20000)
        page.wait_for_timeout(3000)
        items = page.evaluate(f"""() => {{
            const cards = document.querySelectorAll('.article-item, .mod-b-info, .feed-item');
            return [...cards].slice(0, {limit}).map(c => ({{
                title: c.querySelector('.article-title a, .title a, h2 a')?.innerText?.trim() || '',
                url: c.querySelector('.article-title a, .title a, h2 a')?.href || '',
                summary: c.querySelector('.article-summary, .summary, .desc')?.innerText?.trim() || '',
                time: c.querySelector('.article-time, .time, .date')?.innerText?.trim() || '',
            }})).filter(i => i.title);
        }}""")
        browser.close()
        return items
```

```bash
# 任意网页转Markdown（opencli内置）
opencli web read --url 'https://example.com/article'

# 微信公众号文章
opencli weixin download --url 'https://mp.weixin.qq.com/s/xxx'
```

## 新闻搜索工作流

```
1. 确定关键词和时间范围
2. 并行搜索多个来源：
   - opencli 163 search / qqnews search（国内综合）
   - opencli 36kr search（科技商业）
   - opencli google search 'site:reuters.com OR site:bloomberg.com'（国际）
3. 去重、按时间排序
4. 对重要文章用 opencli web read 抓全文
5. 整理成 brief 格式输出
```

## 行业报告搜索

```bash
# 搜索行业报告PDF
opencli baidu search 'XX行业 年度报告 2024 filetype:pdf' --limit 10
opencli bing search 'XX行业 白皮书 2024' --limit 10

# 找到PDF后下载并解析
# wget -O /tmp/report.pdf <url>
# python3 -c "import pymupdf; doc=pymupdf.open('/tmp/report.pdf'); print('\n'.join([p.get_text() for p in doc[:5]]))"
```

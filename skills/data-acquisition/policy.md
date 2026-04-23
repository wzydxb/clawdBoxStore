---
name: data-acquisition/policy
description: 政策法规、招标公告、政府统计数据获取。gov.cn、国家统计局API、中国政府采购网、法律法规数据库。免费官方数据源。
---

# 政策法规与政府数据

## 数据源地图

| 类型 | 来源 | 获取方式 |
|------|------|----------|
| 国务院政策文件 | gov.cn | `opencli gov-policy search/recent` |
| 法律法规 | 国家法律法规数据库 | `opencli gov-law search/recent` |
| 宏观统计数据 | 国家统计局 | NBSC API / AKShare |
| 政府采购 | ccgp.gov.cn | playwright headless |
| 招投标 | ctbpsp.com | playwright headless |
| 证监会文件 | csrc.gov.cn | playwright headless |
| 央行数据 | pbc.gov.cn | AKShare |

## opencli 内置政府数据命令

```bash
# 国务院最新政策文件（直连gov.cn，免费）
opencli gov-policy recent --limit 20

# 搜索政策文件
opencli gov-policy search '数字经济' --limit 10

# 法律法规搜索（国家法律法规数据库）
opencli gov-law search '个人信息保护' --limit 10

# 最新法规
opencli gov-law recent --limit 20
```

## 国家统计局 API（NBSC，官方免费）

```python
# 安装：pip3 install nbsc --break-system-packages
# 注意：data.stats.gov.cn 接口需要浏览器环境（防爬），用 nbsc 包封装好的接口
try:
    import nbsc
    USE_NBSC = True
except ImportError:
    USE_NBSC = False

def get_national_stats(indicator_code, start_year=2020, end_year=2024):
    """获取国家统计局数据，nbsc包优先，playwright备选"""
    if USE_NBSC:
        return nbsc.get_data(indicator_code=indicator_code, start_year=start_year, end_year=end_year)
    # playwright 备选（直接访问 data.stats.gov.cn 网页）
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://data.stats.gov.cn/index.htm", timeout=20000)
        page.wait_for_timeout(2000)
        # 通过 fetch 调用接口（浏览器环境下不会403）
        result = page.evaluate(f"""async () => {{
            const r = await fetch('/easyquery.htm?m=QueryData&dbcode=hgnd&rowcode=zb&colcode=sj&wds=[]&dfwds=[{{"wdcode":"zb","valuecode":"{indicator_code}"}}]', {{
                headers: {{'X-Requested-With': 'XMLHttpRequest', 'Referer': 'https://data.stats.gov.cn/index.htm'}}
            }});
            return await r.json();
        }}""")
        browser.close()
        return result

# 常用指标代码
INDICATORS = {
    'GDP总量': 'A010101',
    '居民消费价格指数CPI': 'A010301',
    '工业生产者价格指数PPI': 'A010401',
    '固定资产投资': 'A020101',
    '社会消费品零售总额': 'A020401',
    '进出口总额': 'A060101',
    '城镇居民人均可支配收入': 'A030201',
    '城镇登记失业率': 'A040201',
}
```

## 政府采购/招标平台

```python
from playwright.sync_api import sync_playwright

def fetch_government_bids(keyword, limit=20):
    """中国政府采购网"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        url = f'https://www.ccgp.gov.cn/cggg/zygg/?searchWord={keyword}'
        page.goto(url, timeout=15000)
        page.wait_for_timeout(4000)
        items = page.evaluate(f'''() => {{
            const rows = document.querySelectorAll('ul.notice-list li, .list li, tr');
            const results = [];
            for (const row of rows) {{
                const a = row.querySelector('a');
                const title = a?.innerText?.trim() || '';
                const url = a?.href || '';
                const date = row.querySelector('.date, .time, td:last-child')?.innerText?.trim() || '';
                const dept = row.querySelector('.dept, .unit, td:nth-child(2)')?.innerText?.trim() || '';
                if (title.length > 5) results.push({{title, url, date, dept}});
                if (results.length >= {limit}) break;
            }}
            return results;
        }}''')
        browser.close()
        return items

def fetch_ctbpsp_bids(keyword, limit=20):
    """中国招标投标公共服务平台"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f'https://www.ctbpsp.com/front/search?keyword={keyword}', timeout=15000)
        page.wait_for_timeout(4000)
        items = page.evaluate(f'''() => {{
            const rows = document.querySelectorAll('.list-item, .result-item, tr');
            const results = [];
            for (const row of rows) {{
                const a = row.querySelector('a');
                const title = a?.innerText?.trim() || '';
                const url = a?.href || '';
                const date = row.querySelector('.date, .time')?.innerText?.trim() || '';
                const budget = row.querySelector('.budget, .amount, .money')?.innerText?.trim() || '';
                if (title.length > 5) results.push({{title, url, date, budget}});
                if (results.length >= {limit}) break;
            }}
            return results;
        }}''')
        browser.close()
        return items
```

## 省级地方政府数据

```bash
# 搜索地方政策（百度限定gov.cn）
opencli baidu search 'XX省 产业政策 2024 site:gov.cn' --limit 10
opencli baidu search 'XX市 营商环境 补贴 site:gov.cn' --limit 10

# 搜索到具体页面后抓全文
opencli web read --url 'https://www.xxx.gov.cn/...'
```

## 监管机构数据

```python
# 证监会公告
browser_navigate("http://www.csrc.gov.cn/csrc/c100028/zfxxgk_zdgk.shtml")
browser_snapshot()

# 银保监会
browser_navigate("https://www.cbirc.gov.cn/cn/view/pages/ItemList.html?itemPId=928")
browser_snapshot()

# 央行货币政策报告
browser_navigate("http://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125440/index.html")
browser_snapshot()

# 工信部政策
browser_navigate("https://www.miit.gov.cn/zwgk/zcwj/index.html")
browser_snapshot()
```

## 政策研究工作流

```
1. opencli gov-policy search '<行业/关键词>' --limit 10
2. 筛选最相关的2-3个文件
3. opencli web read --url <政策页面URL>
4. 整理要点：
   - 发文机关 + 文号
   - 核心条款（支持/限制/要求）
   - 适用范围
   - 执行时间
   - 补贴/申报条件（如有）
5. 输出 brief 格式
```

## 招标情报工作流

```
1. 确定：行业关键词 + 地区 + 预算范围
2. 并行搜索：ccgp.gov.cn + ctbpsp.com + 地方公共资源交易中心
3. 过滤：按预算金额/截止日期/采购方类型
4. 输出：项目名 | 采购方 | 预算 | 截止日期 | 联系方式
```

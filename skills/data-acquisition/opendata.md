---
name: data-acquisition/opendata
description: 政府开放数据平台。国家数据、各省开放数据、世界银行、联合国统计、学术数据库(知网/arXiv)、专业统计数据库。数据分析师首选。
---

# 政府开放数据 & 学术数据库

## 数据源地图

| 平台 | 覆盖范围 | 获取方式 |
|------|---------|--------|
| 国家数据（data.stats.gov.cn） | 国家统计局全量数据 | HTTP API（需 Referer） |
| 国家政务数据开放平台 | 各部委开放数据集 | playwright headless |
| 各省开放数据平台 | 省级政府数据集 | playwright headless |
| 世界银行 | 全球宏观/发展指标 | 免费 REST API |
| 联合国统计 | 全球统计数据 | 免费 REST API |
| 知网/万方 | 学术论文（摘要免费） | playwright headless |
| arXiv | AI/ML/物理等论文 | 免费 API |
| Our World in Data | 全球长期趋势数据 | 免费 CSV/API |

---

## 国家统计局（data.stats.gov.cn）

```python
import urllib.request, json
from playwright.sync_api import sync_playwright

def nbsc_query(indicator_code, region_code="000000", start_year=2020, end_year=2024):
    """
    国家统计局数据接口（需 playwright — 直接 HTTP 会被 403）
    常用指标代码：
      A010101 = 国内生产总值(亿元)
      A010201 = 人均国内生产总值(元)
      A020101 = 居民消费价格指数(上年=100)
      A030101 = 工业增加值增长速度(%)
      A040101 = 固定资产投资(亿元)
      A050101 = 社会消费品零售总额(亿元)
      A060101 = 货物进出口总额(亿美元)
      A070101 = 城镇居民人均可支配收入(元)
      A080101 = 城镇调查失业率(%)
    region_code: 000000=全国, 110000=北京, 310000=上海, 440000=广东
    """
    import json as _json
    from urllib.parse import quote
    dfwds = _json.dumps([
        {"wdcode": "zb", "valuecode": indicator_code},
        {"wdcode": "reg", "valuecode": region_code},
    ])
    api_url = (
        f"https://data.stats.gov.cn/easyquery.htm"
        f"?m=QueryData&dbcode=hgnd&rowcode=zb&colcode=sj"
        f"&wds=%5B%5D&dfwds={quote(dfwds)}&k1={start_year}"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://data.stats.gov.cn/easyquery.htm", timeout=20000)
        page.wait_for_timeout(2000)
        resp = page.evaluate("""async (url) => {
            const r = await fetch(url, {
                headers: {
                    'Referer': 'https://data.stats.gov.cn/easyquery.htm',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                }
            });
            return await r.json();
        }""", api_url)
        browser.close()
    nodes = resp.get("returndata", {}).get("datanodes", [])
    return [{"period": n["wds"][0]["valuecode"], "value": n["data"]["strdata"]} for n in nodes]

# 批量查询多个指标
def nbsc_batch(indicators: dict, region_code="000000", years=5):
    """
    indicators: {"GDP": "A010101", "CPI": "A020101", ...}
    """
    import concurrent.futures
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(nbsc_query, code, region_code, 2024-years, 2024): name
                   for name, code in indicators.items()}
        for f in concurrent.futures.as_completed(futures):
            results[futures[f]] = f.result()
    return results

# 省级数据
PROVINCE_CODES = {
    "北京": "110000", "天津": "120000", "河北": "130000", "山西": "140000",
    "内蒙古": "150000", "辽宁": "210000", "吉林": "220000", "黑龙江": "230000",
    "上海": "310000", "江苏": "320000", "浙江": "330000", "安徽": "340000",
    "福建": "350000", "江西": "360000", "山东": "370000", "河南": "410000",
    "湖北": "420000", "湖南": "430000", "广东": "440000", "广西": "450000",
    "海南": "460000", "重庆": "500000", "四川": "510000", "贵州": "520000",
    "云南": "530000", "西藏": "540000", "陕西": "610000", "甘肃": "620000",
    "青海": "630000", "宁夏": "640000", "新疆": "650000",
}
```

---

## 国家政务数据开放平台（data.gov.cn）

```python
from playwright.sync_api import sync_playwright

def search_govdata(keyword, limit=20):
    """国家政务数据开放平台 — 搜索开放数据集"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        from urllib.parse import quote
        page.goto(f"https://data.gov.cn/search#?searchWord={quote(keyword)}", timeout=20000)
        page.wait_for_timeout(4000)
        datasets = page.evaluate(f"""() => {{
            const items = document.querySelectorAll('.dataset-item, .search-result-item, .list-item');
            return [...items].slice(0, {limit}).map(item => ({{
                title: item.querySelector('.title a, h3 a, .name')?.innerText?.trim() || '',
                url: item.querySelector('.title a, h3 a')?.href || '',
                dept: item.querySelector('.dept, .source, .provider')?.innerText?.trim() || '',
                update: item.querySelector('.update-time, .date')?.innerText?.trim() || '',
                format: item.querySelector('.format, .file-type')?.innerText?.trim() || '',
            }})).filter(i => i.title);
        }}""")
        browser.close()
        return datasets

def download_govdata_api(dataset_id):
    """下载政务数据集（部分有直接API）"""
    url = f"https://data.gov.cn/api/dataset/{dataset_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=15).read())
    except Exception as e:
        return {"error": str(e)}
```

---

## 各省开放数据平台

```python
# 主要省市开放数据平台（已验证可访问）
OPEN_DATA_PLATFORMS = {
    "上海": "https://data.sh.gov.cn",
    "北京": "https://data.beijing.gov.cn",
    "广东": "https://gddata.gd.gov.cn",
    "浙江": "https://data.zjzwfw.gov.cn",
    "江苏": "https://data.jiangsu.gov.cn",
    "四川": "https://data.sc.gov.cn",
    "贵州": "https://data.guizhou.gov.cn",   # 贵州最早建设，数据最全
    "深圳": "https://opendata.sz.gov.cn",
    "成都": "https://data.chengdu.gov.cn",
    "杭州": "https://data.hangzhou.gov.cn",
    "武汉": "https://data.wuhan.gov.cn",
}

def search_provincial_opendata(province, keyword, limit=15):
    """搜索省级开放数据平台"""
    base_url = OPEN_DATA_PLATFORMS.get(province)
    if not base_url:
        # 降级到百度搜索
        import subprocess
        result = subprocess.run(
            ['opencli', 'baidu', 'search',
             f'{province} 政府开放数据 {keyword} site:gov.cn',
             '--limit', str(limit), '-f', 'json'],
            capture_output=True, text=True, timeout=30
        )
        try:
            return json.loads(result.stdout) or []
        except:
            return []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        from urllib.parse import quote
        page.goto(f"{base_url}/search?q={quote(keyword)}", timeout=20000)
        page.wait_for_timeout(3000)
        items = page.evaluate(f"""() => {{
            const links = document.querySelectorAll('a');
            return [...links].filter(a => {{
                const t = a.innerText?.trim() || '';
                return t.length > 5 && t.length < 100;
            }}).slice(0, {limit}).map(a => ({{
                title: a.innerText.trim(),
                url: a.href,
            }}));
        }}""")
        browser.close()
        return items
```

---

## 世界银行（World Bank API）

```python
def worldbank_query(indicator, country="CN", start=2010, end=2024):
    """
    世界银行免费API（无需注册）
    常用指标：
      NY.GDP.MKTP.CD = GDP（美元）
      NY.GDP.PCAP.CD = 人均GDP
      SP.POP.TOTL = 总人口
      FP.CPI.TOTL.ZG = 通货膨胀率
      SL.UEM.TOTL.ZS = 失业率
      NE.EXP.GNFS.ZS = 出口占GDP比
      IT.NET.USER.ZS = 互联网用户占比
      SE.ADT.LITR.ZS = 成人识字率
    country: CN=中国, US=美国, JP=日本, DE=德国, IN=印度
    """
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json&date={start}:{end}&per_page=100"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        if len(data) < 2:
            return []
        return [{"year": d["date"], "value": d["value"], "country": d["country"]["value"]}
                for d in data[1] if d["value"] is not None]
    except Exception as e:
        return [{"error": str(e)}]

def worldbank_compare(indicator, countries=["CN", "US", "JP", "DE", "IN"], years=10):
    """多国对比"""
    import concurrent.futures
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(worldbank_query, indicator, c, 2024-years, 2024): c
                   for c in countries}
        for f in concurrent.futures.as_completed(futures):
            results[futures[f]] = f.result()
    return results
```

---

## 联合国统计（UN Data）

```python
def un_data_query(series_code, area_code="156", start=2015, end=2024):
    """
    联合国统计数据（免费API）
    area_code: 156=中国, 840=美国, 392=日本
    常用 series_code（需查 https://data.un.org/）
    """
    url = f"https://data.un.org/ws/rest/data/DF_UNData_UNFCC/{series_code}/.{area_code}/?startPeriod={start}&endPeriod={end}&format=jsondata"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return data
    except Exception as e:
        return {"error": str(e)}
```

---

## arXiv 论文（AI/ML/经济学）

```python
def arxiv_search(query, category="cs.AI", max_results=20, sort_by="submittedDate"):
    """
    arXiv 论文搜索（完全免费，无需注册）
    category: cs.AI=人工智能, cs.LG=机器学习, econ.GN=经济学, q-fin=量化金融
    sort_by: submittedDate / relevance / lastUpdatedDate
    """
    from urllib.parse import quote
    url = (f"https://export.arxiv.org/api/query"
           f"?search_query=cat:{category}+AND+all:{quote(query)}"
           f"&start=0&max_results={max_results}"
           f"&sortBy={sort_by}&sortOrder=descending")
    try:
        import xml.etree.ElementTree as ET
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        content = urllib.request.urlopen(req, timeout=15).read()
        root = ET.fromstring(content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers = []
        for entry in root.findall("atom:entry", ns):
            papers.append({
                "title": entry.findtext("atom:title", "", ns).strip().replace("\n", " "),
                "authors": [a.findtext("atom:name", "", ns) for a in entry.findall("atom:author", ns)][:3],
                "summary": entry.findtext("atom:summary", "", ns).strip()[:300],
                "published": entry.findtext("atom:published", "", ns)[:10],
                "url": entry.findtext("atom:id", "", ns),
            })
        return papers
    except Exception as e:
        return [{"error": str(e)}]

# 快捷搜索
def arxiv_llm_papers(days=7):
    """最近7天LLM相关论文"""
    return arxiv_search("large language model", category="cs.AI", max_results=30)

def arxiv_econ_papers(topic="china economy"):
    """经济学论文"""
    return arxiv_search(topic, category="econ.GN", max_results=20)
```

---

## Our World in Data（全球长期趋势）

```python
def owid_query(indicator, country="China"):
    """
    Our World in Data — 全球长期趋势数据（免费CSV）
    常用数据集：
      - life-expectancy: 预期寿命
      - co2-emissions: CO2排放
      - gdp-per-capita-worldbank: 人均GDP
      - share-of-individuals-using-the-internet: 互联网普及率
      - urbanization-last-500-years: 城镇化率
    """
    url = f"https://ourworldindata.org/grapher/{indicator}.csv?tab=chart&country={country.replace(' ', '+')}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        content = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")
        lines = content.strip().split("\n")
        headers = lines[0].split(",")
        return [dict(zip(headers, line.split(","))) for line in lines[1:]]
    except Exception as e:
        return [{"error": str(e)}]
```

---

## 知网/万方（学术论文摘要，免费）

```python
def search_cnki(keyword, limit=20):
    """知网论文搜索（摘要免费，全文需购买）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()
        from urllib.parse import quote
        page.goto(f"https://kns.cnki.net/kns8/defaultresult/index?kw={quote(keyword)}&korder=SU", timeout=20000)
        page.wait_for_timeout(5000)
        papers = page.evaluate(f"""() => {{
            const items = document.querySelectorAll('.result-table-list tr, .result-list .item');
            return [...items].slice(0, {limit}).map(item => ({{
                title: item.querySelector('.name a, .title a')?.innerText?.trim() || '',
                authors: item.querySelector('.author, .creator')?.innerText?.trim() || '',
                journal: item.querySelector('.source a, .journal')?.innerText?.trim() || '',
                year: item.querySelector('.date, .year')?.innerText?.trim() || '',
                url: item.querySelector('.name a, .title a')?.href || '',
            }})).filter(i => i.title);
        }}""")
        browser.close()
        return papers

def search_wanfang(keyword, limit=20):
    """万方数据论文搜索"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        from urllib.parse import quote
        page.goto(f"https://www.wanfangdata.com.cn/search/searchList.do?searchType=all&searchWord={quote(keyword)}", timeout=20000)
        page.wait_for_timeout(4000)
        papers = page.evaluate(f"""() => {{
            const items = document.querySelectorAll('.item, .result-item');
            return [...items].slice(0, {limit}).map(item => ({{
                title: item.querySelector('.title a, h3 a')?.innerText?.trim() || '',
                authors: item.querySelector('.author, .creator')?.innerText?.trim() || '',
                source: item.querySelector('.source, .journal')?.innerText?.trim() || '',
                year: item.querySelector('.year, .date')?.innerText?.trim() || '',
            }})).filter(i => i.title);
        }}""")
        browser.close()
        return papers
```

---

## 数据分析师工作流

```
场景1：宏观经济研究
1. nbsc_batch({"GDP": "A010101", "CPI": "A020101", "PMI": ...}) → 国内指标
2. worldbank_compare("NY.GDP.MKTP.CD", ["CN","US","JP","DE","IN"]) → 国际对比
3. 输出：多维度宏观仪表盘

场景2：行业研究报告
1. arxiv_search("<行业>", category="econ.GN") → 学术前沿
2. search_cnki("<行业> 发展趋势") → 国内研究
3. skill_view("data-acquisition/industry") → 行业垂直数据
4. 输出：研究报告框架

场景3：地区经济对比
1. nbsc_batch(indicators, region_code=PROVINCE_CODES["广东"]) → 广东数据
2. nbsc_batch(indicators, region_code=PROVINCE_CODES["浙江"]) → 浙江数据
3. worldbank_query("NY.GDP.MKTP.CD", "CN") → 全国基准
4. 输出：区域竞争力矩阵

场景4：政府开放数据挖掘
1. search_govdata("<关键词>") → 国家平台数据集
2. search_provincial_opendata("<省份>", "<关键词>") → 省级数据集
3. 下载CSV/API → 清洗分析
4. 输出：数据洞察报告
```

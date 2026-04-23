---
name: data-acquisition/local-gov
description: 地方政府官方数据。31省市工信厅/发改委/商务厅/人社厅/统计局政策文件、地方补贴申报、省级招标、地方统计数据、产业园区政策。覆盖省级+重点城市。
---

# 地方政府数据

## 数据源地图

| 数据类型 | 来源 | 获取方式 |
|--------|------|--------|
| 省级政府政策 | 各省 gov.cn | playwright + opencli baidu site: |
| 工信厅补贴/专项 | 各省工信厅 | playwright headless |
| 发改委项目/核准 | 各省发改委 | playwright headless |
| 商务厅招商/外资 | 各省商务厅 | playwright headless |
| 人社厅就业/社保 | 各省人社厅 | playwright headless |
| 省级统计数据 | 各省统计局 | playwright headless |
| 地方招标 | 省级公共资源交易中心 | playwright headless |
| 地方法规 | 各省人大/政府 | opencli gov-law + playwright |

---

## 省级政府门户速查表

```python
# 31个省级政府门户（直接访问，无需登录）
PROVINCE_GOV = {
    # 直辖市
    "北京": "https://www.beijing.gov.cn",
    "上海": "https://www.shanghai.gov.cn",
    "天津": "https://www.tj.gov.cn",
    "重庆": "https://www.cq.gov.cn",
    # 东部
    "广东": "https://www.gd.gov.cn",
    "浙江": "https://www.zj.gov.cn",
    "江苏": "https://www.jiangsu.gov.cn",
    "山东": "https://www.shandong.gov.cn",
    "福建": "https://www.fujian.gov.cn",
    "海南": "https://www.hainan.gov.cn",
    # 中部
    "湖北": "https://www.hubei.gov.cn",
    "湖南": "https://www.hunan.gov.cn",
    "河南": "https://www.henan.gov.cn",
    "安徽": "https://www.ah.gov.cn",
    "江西": "https://www.jiangxi.gov.cn",
    "山西": "https://www.shanxi.gov.cn",
    # 北部
    "河北": "https://www.hebei.gov.cn",
    "辽宁": "https://www.ln.gov.cn",
    "吉林": "https://www.jl.gov.cn",
    "黑龙江": "https://www.hlj.gov.cn",
    "内蒙古": "https://www.nmg.gov.cn",
    # 西部
    "四川": "https://www.sc.gov.cn",
    "陕西": "https://www.shaanxi.gov.cn",
    "云南": "https://www.yn.gov.cn",
    "贵州": "https://www.guizhou.gov.cn",
    "广西": "https://www.gxzf.gov.cn",
    "西藏": "https://www.xizang.gov.cn",
    "甘肃": "https://www.gansu.gov.cn",
    "青海": "https://www.qinghai.gov.cn",
    "宁夏": "https://www.nx.gov.cn",
    "新疆": "https://www.xinjiang.gov.cn",
}

# 五大核心部门 URL 规律（大多数省份遵循此规律）
# 工信厅：gxt.{省缩写}.gov.cn 或 miit.{省缩写}.gov.cn
# 发改委：ndrc.{省缩写}.gov.cn 或 fgw.{省缩写}.gov.cn
# 商务厅：commerce.{省缩写}.gov.cn 或 mofcom.{省缩写}.gov.cn
# 人社厅：hrss.{省缩写}.gov.cn 或 rst.{省缩写}.gov.cn
# 统计局：stats.{省缩写}.gov.cn 或 tj.{省缩写}.gov.cn

# 主要省份工信厅直链（已验证可访问）
MIIT_URLS = {
    "广东": "https://gdii.gd.gov.cn",          # ✅
    "浙江": "https://jxt.zj.gov.cn",            # ✅ (原jxw.zj.gov.cn已失效)
    "江苏": "https://gxt.jiangsu.gov.cn",
    "上海": "https://www.sheitc.sh.gov.cn",
    "北京": "https://jxj.beijing.gov.cn",
    "四川": "https://gxt.sc.gov.cn",
    "湖北": "https://gxt.hubei.gov.cn",
    "湖南": "https://gxt.hunan.gov.cn",
    "山东": "https://gxt.shandong.gov.cn",
    "河南": "https://gxt.henan.gov.cn",
    "陕西": "https://gxt.shaanxi.gov.cn",
    "重庆": "https://gxt.cq.gov.cn",
    "安徽": "https://gxt.ah.gov.cn",
    "福建": "https://gxt.fujian.gov.cn",
    "河北": "https://gxt.hebei.gov.cn",
    "辽宁": "https://gxt.ln.gov.cn",
}

# 省级统计局直链
STATS_URLS = {
    "广东": "https://stats.gd.gov.cn",
    "浙江": "https://tjj.zj.gov.cn",
    "江苏": "https://tj.jiangsu.gov.cn",
    "上海": "https://tjj.sh.gov.cn",
    "北京": "https://tjj.beijing.gov.cn",
    "四川": "https://tjj.sc.gov.cn",
    "山东": "https://tjj.shandong.gov.cn",
    "湖北": "https://tjj.hubei.gov.cn",
    "湖南": "https://tjj.hunan.gov.cn",
    "河南": "https://tjj.henan.gov.cn",
    "重庆": "https://tjj.cq.gov.cn",
    "陕西": "https://tjj.shaanxi.gov.cn",
    "安徽": "https://tjj.ah.gov.cn",
    "福建": "https://tjj.fujian.gov.cn",
}
```

---

## 方法一：百度 site: 搜索（最快，覆盖最广）

```bash
# 搜索某省工信厅政策（不需要知道具体URL）
opencli baidu search '广东省工业和信息化厅 专项资金 2024' --limit 10
opencli baidu search '浙江省工信厅 数字经济 补贴申报 site:zj.gov.cn' --limit 10

# 发改委项目核准
opencli baidu search '四川省发展改革委 重大项目 2024 site:sc.gov.cn' --limit 10

# 商务厅招商政策
opencli baidu search '上海市商务委 外资 优惠政策 site:sh.gov.cn' --limit 10

# 人社厅就业补贴
opencli baidu search '广东省人力资源社会保障厅 就业补贴 申报 2024' --limit 10

# 省级统计数据
opencli baidu search '浙江省统计局 GDP 2024年 公报 site:zj.gov.cn' --limit 5

# 地方招标
opencli baidu search '广东省公共资源交易中心 招标公告 2024' --limit 10
opencli bing search '上海市政府采购 招标 site:sh.gov.cn' --limit 10
```

## 方法二：直接抓取部门网站

```python
from playwright.sync_api import sync_playwright
import json

def fetch_gov_dept_news(dept_url, limit=20):
    """
    抓取政府部门最新政策/通知列表
    适用于工信厅/发改委/商务厅等标准政府网站
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = ctx.new_page()
        page.goto(dept_url, timeout=20000)
        page.wait_for_timeout(3000)

        items = page.evaluate(f"""() => {{
            // 政府网站通用选择器（覆盖90%以上政府网站结构）
            const selectors = [
                'ul.news-list li', 'ul.article-list li',
                '.list-content li', '.news-content li',
                '.zwgk-list li', '.policy-list li',
                'table.list tr', '.content-list li',
                '.notice-list li', '.info-list li',
            ];
            let links = [];
            for (const sel of selectors) {{
                const found = document.querySelectorAll(sel);
                if (found.length > 3) {{ links = [...found]; break; }}
            }}
            // 兜底：找所有包含日期的链接
            if (links.length === 0) {{
                links = [...document.querySelectorAll('a')].filter(a => {{
                    const text = a.innerText?.trim() || '';
                    const parent = a.parentElement?.innerText || '';
                    return text.length > 8 && text.length < 100 &&
                           /20\d{{2}}/.test(parent);
                }});
            }}
            return links.slice(0, {limit}).map(el => {{
                const a = el.tagName === 'A' ? el : el.querySelector('a');
                const dateEl = el.querySelector('.date, .time, span:last-child, em');
                return {{
                    title: (a?.innerText || el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 100),
                    url: a?.href || '',
                    date: dateEl?.innerText?.trim() || '',
                }};
            }}).filter(i => i.title.length > 5 && i.url.includes('gov.cn'));
        }}""")
        browser.close()
        return items

def fetch_gov_article(url):
    """抓取政府文件全文"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=20000)
        page.wait_for_timeout(3000)
        content = page.evaluate("""() => {
            // 政府网站正文选择器
            const selectors = [
                '.article-content', '.content', '#zoom', '.TRS_Editor',
                '.article', '.news-content', '.zwgk-content', '.policy-content',
                'div[class*="content"]', 'div[class*="article"]',
            ];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.innerText.length > 200) return el.innerText.trim();
            }
            return document.body.innerText.trim().slice(0, 5000);
        }""")
        browser.close()
        return content
```

---

## 工信厅：产业政策与补贴申报

```python
def fetch_miit_policy(province, keyword="", limit=15):
    """
    抓取省级工信厅政策通知
    重点：专项资金、补贴申报、产业扶持、数字化转型
    """
    base_url = MIIT_URLS.get(province)
    if not base_url:
        # 降级到百度搜索
        import subprocess
        result = subprocess.run(
            ['opencli', 'baidu', 'search',
             f'{province}省工业和信息化厅 {keyword} 2024 site:gov.cn',
             '--limit', str(limit), '-f', 'json'],
            capture_output=True, text=True, timeout=30
        )
        try:
            return json.loads(result.stdout) or []
        except:
            return []

    items = fetch_gov_dept_news(base_url, limit=limit)
    if keyword:
        items = [i for i in items if keyword in i['title']]
    return items

# 使用示例
# 广东工信厅最新政策
policies = fetch_miit_policy("广东", limit=20)
for p in policies:
    print(f"{p['date']} | {p['title']}")
    print(f"  {p['url']}")

# 搜索补贴申报
subsidies = fetch_miit_policy("浙江", keyword="补贴", limit=10)
```

---

## 发改委：重大项目与投资核准

```python
NDRC_URLS = {
    "广东": "https://drc.gd.gov.cn",
    "浙江": "https://fgw.zj.gov.cn",
    "江苏": "https://fgw.jiangsu.gov.cn",
    "上海": "https://fgw.sh.gov.cn",
    "北京": "https://fgw.beijing.gov.cn",
    "四川": "https://fgw.sc.gov.cn",
    "山东": "https://fgw.shandong.gov.cn",
    "湖北": "https://fgw.hubei.gov.cn",
    "重庆": "https://fgw.cq.gov.cn",
}

def fetch_ndrc_projects(province, keyword="", limit=15):
    """省级发改委重大项目/投资核准公告"""
    base_url = NDRC_URLS.get(province)
    if base_url:
        items = fetch_gov_dept_news(base_url, limit=limit)
        if keyword:
            items = [i for i in items if keyword in i['title']]
        return items
    # 降级搜索
    import subprocess
    result = subprocess.run(
        ['opencli', 'baidu', 'search',
         f'{province}省发展改革委 {keyword} 重大项目 2024 site:gov.cn',
         '--limit', str(limit), '-f', 'json'],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout) or []
    except:
        return []
```

---

## 省级统计局：地方经济数据

```python
def fetch_provincial_stats(province, indicator="GDP"):
    """
    省级统计局数据
    indicator: GDP / CPI / 工业增加值 / 固定资产投资 / 社会消费品零售 / 进出口
    """
    stats_url = STATS_URLS.get(province)
    if not stats_url:
        import subprocess
        result = subprocess.run(
            ['opencli', 'baidu', 'search',
             f'{province}省统计局 {indicator} 2024 统计公报 site:gov.cn',
             '--limit', '5', '-f', 'json'],
            capture_output=True, text=True, timeout=30
        )
        try:
            return json.loads(result.stdout) or []
        except:
            return []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # 搜索统计局网站内的指标数据
        page.goto(f"{stats_url}/search?q={indicator}", timeout=20000)
        page.wait_for_timeout(3000)
        items = page.evaluate(f"""() => {{
            const links = document.querySelectorAll('a');
            return [...links].filter(a => {{
                const t = a.innerText?.trim() || '';
                return t.includes('{indicator}') && t.length > 5 && t.length < 100;
            }}).slice(0, 10).map(a => ({{
                title: a.innerText.trim(),
                url: a.href,
            }}));
        }}""")
        browser.close()
        return items

# AKShare 省级数据（部分指标有省级数据）
def get_provincial_gdp_akshare():
    """AKShare 各省GDP数据"""
    import akshare as ak
    # 各省GDP
    df = ak.macro_china_gdp_yearly()
    return df

def get_provincial_stats_nbsc(province_code, indicator_code, start_year=2020):
    """
    国家统计局API获取省级数据（需 playwright — 直接 HTTP 会被 403）
    province_code: 110000=北京, 310000=上海, 440000=广东, 330000=浙江
    """
    import json as _json
    from urllib.parse import quote
    from playwright.sync_api import sync_playwright
    dfwds = _json.dumps([{"wdcode": "zb", "valuecode": indicator_code}])
    wds = _json.dumps([{"wdcode": "reg", "valuecode": province_code}])
    api_url = (f"https://data.stats.gov.cn/easyquery.htm"
               f"?m=QueryData&dbcode=fsnd&rowcode=zb&colcode=sj"
               f"&wds={quote(wds)}&dfwds={quote(dfwds)}&k1={start_year}")
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
                }
            });
            return await r.json();
        }""", api_url)
        browser.close()
    return resp.get("returndata", {}).get("datanodes", [])

# 省级代码
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

## 地方招标：省级公共资源交易中心

```python
# 各省公共资源交易中心（已验证可访问）
GGZY_URLS = {
    "全国": "https://www.ggzy.gov.cn/",          # ✅ 全国公共资源交易平台
    "中国政府采购": "https://www.ccgp.gov.cn/",   # ✅ 中国政府采购网
    "浙江": "https://www.zcygov.cn/",             # ✅
    "上海": "https://www.sggzy.com/",
    "北京": "https://www.bjggzy.org.cn/",
    "四川": "https://www.scggzy.gov.cn/",
    "山东": "https://ggzy.shandong.gov.cn/",
    "湖北": "https://www.hbggzy.cn/",
    "湖南": "https://www.hnggzy.com/",
    "重庆": "https://www.cqggzy.com/",
    "陕西": "https://www.sxggzyjy.cn/",
    "安徽": "https://www.ahggzy.net/",
    "福建": "https://ggzy.fujian.gov.cn/",
    # 广东省公共资源交易中心域名已变更，降级用百度搜索
    # "广东": 降级到 opencli baidu search
}

def fetch_local_bids(province, keyword="", limit=20):
    """
    省级公共资源交易中心招标公告
    优先用全国平台（覆盖所有省份）
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()

        # 全国公共资源交易平台（最全，已验证）
        search_url = f"https://www.ggzy.gov.cn/information/html/more.html?type=01&province=&city=&keyword={keyword}"
        page.goto(search_url, timeout=20000)
        page.wait_for_timeout(5000)

        bids = page.evaluate(f"""() => {{
            const rows = document.querySelectorAll('table tr, .list-item, .bid-item');
            const results = [];
            for (const row of rows) {{
                const title = row.querySelector('a, .title')?.innerText?.trim() || '';
                const url = row.querySelector('a')?.href || '';
                const date = row.querySelector('.date, td:last-child, .time')?.innerText?.trim() || '';
                const area = row.querySelector('.area, .province, td:nth-child(2)')?.innerText?.trim() || '';
                const type = row.querySelector('.type, td:nth-child(3)')?.innerText?.trim() || '';
                if (title.length > 5) results.push({{title, url, date, area, type}});
                if (results.length >= {limit}) break;
            }}
            return results;
        }}""")
        browser.close()

        if not bids and province in GGZY_URLS:
            # 降级到省级平台
            return fetch_gov_dept_news(GGZY_URLS[province], limit=limit)
        return bids
```

---

## 重点城市政府数据

```python
# 副省级/重点城市政府门户
CITY_GOV = {
    "深圳": "https://www.sz.gov.cn",
    "杭州": "https://www.hangzhou.gov.cn",
    "南京": "https://www.nanjing.gov.cn",
    "武汉": "https://www.wuhan.gov.cn",
    "成都": "https://www.chengdu.gov.cn",
    "西安": "https://www.xa.gov.cn",
    "苏州": "https://www.suzhou.gov.cn",
    "宁波": "https://www.ningbo.gov.cn",
    "青岛": "https://www.qingdao.gov.cn",
    "大连": "https://www.dl.gov.cn",
    "厦门": "https://www.xm.gov.cn",
    "长沙": "https://www.changsha.gov.cn",
    "郑州": "https://www.zhengzhou.gov.cn",
    "合肥": "https://www.hefei.gov.cn",
    "济南": "https://www.jinan.gov.cn",
}

# 深圳工信局（科技创新委）
CITY_MIIT = {
    "深圳": "https://www.sz.gov.cn/szzt2010/ysgz/gxjscy/",
    "杭州": "https://www.hangzhou.gov.cn/col/col1229717364/",
    "成都": "https://www.chengdu.gov.cn/chengdu/c131765/",
    "武汉": "https://www.wuhan.gov.cn/zwgk/xxgkml/jgzn/szfzjbm/",
}
```

---

## 地方政府数据工作流

```
场景1：产业补贴申报情报
1. fetch_miit_policy("<省份>", keyword="补贴") → 最新补贴通知
2. fetch_miit_policy("<省份>", keyword="专项资金") → 专项资金申报
3. 对每条政策 fetch_gov_article(url) → 抓全文
4. 提取：申报条件/金额/截止日期/联系方式
5. 输出申报指南

场景2：地方招商政策对比
1. 并行查询多省工信厅/商务厅
2. 对比：税收优惠/土地政策/人才补贴/产业基金
3. 输出选址建议矩阵

场景3：地方经济数据分析
1. get_provincial_stats_nbsc("<省份代码>", "A010101") → 省级GDP
2. fetch_provincial_stats("<省份>", "工业增加值") → 工业数据
3. 对比多省经济指标 → 区域竞争力分析

场景4：地方招标情报
1. fetch_local_bids("<省份>", keyword="<行业关键词>") → 最新招标
2. 筛选：预算金额/采购方类型/截止日期
3. 输出商机列表

场景5：政策全景扫描（CEO/产品经理）
1. 并行查询：工信厅 + 发改委 + 商务厅
2. 关键词：数字化/新能源/AI/专精特新/产业链
3. 汇总：近30天重要政策信号
```

---

## 快速搜索模板（无需知道具体URL）

```bash
# 工信厅补贴（任意省份）
opencli baidu search '{省份}省工业和信息化厅 专项资金申报 2024' --limit 10
opencli baidu search '{省份}省工信厅 数字化转型 补贴 site:gov.cn' --limit 10

# 发改委重大项目
opencli baidu search '{省份}省发展改革委 重大项目 核准 2024 site:gov.cn' --limit 10

# 商务厅招商政策
opencli baidu search '{省份}省商务厅 招商引资 优惠政策 2024 site:gov.cn' --limit 10

# 人社厅就业政策
opencli baidu search '{省份}省人力资源社会保障厅 就业补贴 申报 2024' --limit 10

# 省级统计公报
opencli baidu search '{省份}省统计局 国民经济 统计公报 2024 site:gov.cn' --limit 5

# 地方招标
opencli baidu search '{省份} 政府采购 招标公告 {行业} 2024 site:gov.cn' --limit 10

# 产业园区政策
opencli baidu search '{省份} 产业园区 入驻政策 补贴 2024 site:gov.cn' --limit 10

# 专精特新企业申报
opencli baidu search '{省份}省工信厅 专精特新 申报 2024 site:gov.cn' --limit 10
```

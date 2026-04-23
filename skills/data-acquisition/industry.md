---
name: data-acquisition/industry
description: 各行业垂直数据源。医药(NMPA)、农产品价格、能源/油价、房地产、环保/碳市场、教育统计、制造业PMI、互联网(CNNIC)。覆盖12个行业官方数据。
---

# 行业垂直数据

## 行业路由

| 行业 | 触发词 | 核心数据源 |
|------|--------|----------|
| 医药/医疗 | 药品、医疗器械、NMPA | NMPA药品数据库 |
| 农业/食品 | 农产品价格、粮食、农业 | 农业农村部、AKShare |
| 能源/油价 | 油价、电力、能源 | 国家能源局、油价API |
| 房地产 | 房价、楼市、土地 | 国家统计局70城房价 |
| 环保/碳市场 | 碳排放、AQI、环保 | 生态环境部、碳市场 |
| 教育 | 高校、招生、教育统计 | 教育部、高校数据 |
| 制造业 | PMI、工业、制造 | AKShare宏观PMI |
| 互联网 | 网民、互联网统计、CNNIC | CNNIC报告 |

---

## 医药/医疗（NMPA国家药监局）

```python
import urllib.request, json
from playwright.sync_api import sync_playwright

def search_drug(keyword, limit=20):
    """国家药监局药品查询（免费，无需登录）"""
    url = f"https://www.nmpa.gov.cn/datasearch/search-info.html?nmpa=&tableId=25&tableName=TABLE25&tableView=药品&searchStr={keyword}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=20000)
        page.wait_for_timeout(4000)
        results = page.evaluate(f"""() => {{
            const rows = document.querySelectorAll('table tr, .result-list tr');
            return [...rows].slice(1, {limit+1}).map(row => ({{
                name: row.querySelector('td:nth-child(1)')?.innerText?.trim() || '',
                approval_no: row.querySelector('td:nth-child(2)')?.innerText?.trim() || '',
                manufacturer: row.querySelector('td:nth-child(3)')?.innerText?.trim() || '',
                spec: row.querySelector('td:nth-child(4)')?.innerText?.trim() || '',
                status: row.querySelector('td:nth-child(5)')?.innerText?.trim() || '',
            }})).filter(r => r.name);
        }}""")
        browser.close()
        return results

def search_medical_device(keyword, limit=20):
    """医疗器械查询（NMPA UDI数据库，有官方API）"""
    # NMPA UDI 官方接口
    url = f"https://udi.nmpa.gov.cn/product.html#/search?keyword={keyword}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=20000)
        page.wait_for_timeout(5000)
        results = page.evaluate(f"""() => {{
            const items = document.querySelectorAll('.product-item, .result-item, table tr');
            return [...items].slice(0, {limit}).map(item => ({{
                name: item.querySelector('.name, td:nth-child(1)')?.innerText?.trim() || '',
                model: item.querySelector('.model, td:nth-child(2)')?.innerText?.trim() || '',
                manufacturer: item.querySelector('.manufacturer, td:nth-child(3)')?.innerText?.trim() || '',
                reg_no: item.querySelector('.reg-no, td:nth-child(4)')?.innerText?.trim() || '',
            }})).filter(r => r.name);
        }}""")
        browser.close()
        return results

# 药品批次查询（直接API）
def check_drug_batch(approval_no):
    """查询药品批准文号状态"""
    url = f"https://www.nmpa.gov.cn/datasearch/search-info.html?nmpa=&tableId=25&tableName=TABLE25&tableView=药品&searchStr={approval_no}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=20000)
        page.wait_for_timeout(3000)
        result = page.evaluate("""() => ({
            name: document.querySelector('.drug-name, .product-name')?.innerText?.trim() || '',
            status: document.querySelector('.status, .approval-status')?.innerText?.trim() || '',
            valid_date: document.querySelector('.valid-date, .expire-date')?.innerText?.trim() || '',
        })""")
        browser.close()
        return result
```

---

## 农业/食品（农产品价格）

```python
import akshare as ak

# ── AKShare 农产品数据 ──────────────────────────────────────
# 农产品批发价格（农业农村部，每日更新）
df = ak.farm_product_price_weekly_sina()     # 新浪农产品周价格
df = ak.farm_product_price_hist_sina(symbol="大豆")  # 历史价格

# 生猪价格（重要宏观指标）
df = ak.futures_main_sina(symbol="JD0")     # 鸡蛋期货（农产品代理）

# 粮食价格
df = ak.spot_hist_sge(symbol="黄金99.99")   # 贵金属（非农，但同类接口）

# 农业农村部官方数据（playwright）
def fetch_moa_prices(product="猪肉"):
    """农业农村部农产品价格"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://www.moa.gov.cn/ztzl/nybrl/nybrlqg/", timeout=20000)
        page.wait_for_timeout(3000)
        items = page.evaluate("""() => {
            const links = document.querySelectorAll('a');
            return [...links].filter(a => a.innerText.includes('价格') || a.innerText.includes('行情'))
                .slice(0, 10).map(a => ({title: a.innerText.trim(), url: a.href}));
        }""")
        browser.close()
        return items

# 全国农产品商务信息公共服务平台
def fetch_veggie_prices():
    """蔬菜/水果批发价格（商务部）"""
    url = "http://nc.mofcom.gov.cn/channel/market/market.shtml"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=20000)
        page.wait_for_timeout(3000)
        data = page.evaluate("""() => {
            const rows = document.querySelectorAll('table tr, .price-list tr');
            return [...rows].slice(1, 30).map(row => ({
                product: row.querySelector('td:nth-child(1)')?.innerText?.trim() || '',
                price: row.querySelector('td:nth-child(2)')?.innerText?.trim() || '',
                unit: row.querySelector('td:nth-child(3)')?.innerText?.trim() || '',
                market: row.querySelector('td:nth-child(4)')?.innerText?.trim() || '',
                date: row.querySelector('td:nth-child(5)')?.innerText?.trim() || '',
            })).filter(r => r.product);
        }""")
        browser.close()
        return data
```

---

## 能源/油价

```python
# ── 国内油价（每两周调整一次）──────────────────────────────
import akshare as ak

# AKShare 油价数据
df = ak.energy_oil_hist_em()                 # 历史油价走势
df = ak.macro_china_oil_import()             # 中国原油进口量

# 国家发改委油价调整（实时）
def fetch_oil_price():
    """国家发改委成品油价格（全国统一）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.ndrc.gov.cn/fzggw/jgsj/jjyjs/sjjg/", timeout=20000)
        page.wait_for_timeout(3000)
        items = page.evaluate("""() => {
            const links = document.querySelectorAll('a');
            return [...links].filter(a => a.innerText.includes('油价') || a.innerText.includes('成品油'))
                .slice(0, 5).map(a => ({title: a.innerText.trim(), url: a.href}));
        }""")
        browser.close()
        return items

# 各省油价（聚合数据API，免费注册）
# https://www.juhe.cn/docs/api/id/73
def fetch_province_oil_price(province="广东"):
    """各省实时油价（需聚合数据免费key）"""
    JUHE_KEY = "your_key"  # 配置到 ~/.hermes/config.yaml: juhe_key
    url = f"http://apis.juhe.cn/gnyj/query?key={JUHE_KEY}&province={province}"
    try:
        data = json.loads(urllib.request.urlopen(url, timeout=10).read())
        return data.get("result", {})
    except Exception as e:
        return {"error": str(e)}

# ── 电力数据 ──────────────────────────────────────────────
def fetch_power_data():
    """国家能源局电力统计数据"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.nea.gov.cn/category/tjsj/", timeout=20000)
        page.wait_for_timeout(3000)
        items = page.evaluate("""() => {
            const links = document.querySelectorAll('a');
            return [...links].filter(a => a.innerText.length > 5 && a.innerText.length < 60)
                .slice(0, 15).map(a => ({title: a.innerText.trim(), url: a.href}));
        }""")
        browser.close()
        return items
```

---

## 房地产（70城房价指数）

```python
import akshare as ak

# ── AKShare 房价数据 ────────────────────────────────────────
# 70个大中城市新建商品住宅价格指数（国家统计局官方）
df = ak.house_price_index_70_cities()        # 70城房价指数

# 全国商品房销售数据
df = ak.macro_china_real_estate()            # 房地产开发投资/销售

# 土地市场数据
df = ak.land_price_index()                   # 全国土地价格指数

# 贝壳找房（链家旗下，反爬更弱，lianjia.com 有超时问题）
def fetch_lianjia_prices(city="sh", district=""):
    """贝壳二手房价格（上海/北京/深圳等）"""
    city_map = {"上海": "sh", "北京": "bj", "深圳": "sz", "杭州": "hz", "广州": "gz"}
    city_code = city_map.get(city, city)
    url = f"https://{city_code}.ke.com/ershoufang/"
    if district:
        url += f"{district}/"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()
        page.goto(url, timeout=20000)
        page.wait_for_timeout(4000)
        listings = page.evaluate("""() => {
            const items = document.querySelectorAll('.sellListContent li, .list-wrap li');
            return [...items].slice(0, 20).map(item => ({
                title: item.querySelector('.title a')?.innerText?.trim() || '',
                price: item.querySelector('.totalPrice span')?.innerText?.trim() || '',
                unit_price: item.querySelector('.unitPrice span')?.innerText?.trim() || '',
                area: item.querySelector('.houseInfo')?.innerText?.trim() || '',
                location: item.querySelector('.positionInfo')?.innerText?.trim() || '',
            })).filter(i => i.title);
        }""")
        browser.close()
        return listings
```

---

## 环保/碳市场

```python
# ── AQI 空气质量 ────────────────────────────────────────────
# weather.md 中已有 aqicn.org 接口，这里补充官方数据

def fetch_mee_aqi(city="北京"):
    """生态环境部官方AQI（中国环境监测总站）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://air.cnemc.cn:18007/", timeout=20000)
        page.wait_for_timeout(3000)
        data = page.evaluate(f"""() => {{
            // 搜索城市
            const input = document.querySelector('input[placeholder*="城市"], .city-input');
            if (input) input.value = '{city}';
            return {{
                aqi: document.querySelector('.aqi-value, .AQI-num')?.innerText?.trim() || '',
                level: document.querySelector('.aqi-level, .quality-level')?.innerText?.trim() || '',
                pm25: document.querySelector('[data-type="PM2.5"] .value, .pm25-value')?.innerText?.trim() || '',
                pm10: document.querySelector('[data-type="PM10"] .value, .pm10-value')?.innerText?.trim() || '',
                update_time: document.querySelector('.update-time, .data-time')?.innerText?.trim() || '',
            }};
        }}""")
        browser.close()
        return data

# ── 碳市场数据 ──────────────────────────────────────────────
import akshare as ak

# 全国碳市场行情（v1.18.56 正确函数名）
df = ak.energy_carbon_domestic()            # 全国碳市场（上海环交所，推荐）
# df = ak.energy_carbon_sz()               # 深圳碳市场（有时网络不稳定）
df = ak.energy_carbon_eu()                  # 欧盟碳市场（EUA）

# 碳价格历史
def fetch_carbon_price():
    """全国碳市场价格（生态环境部官方）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.mee.gov.cn/ywgz/ydqhbh/wsqtkz/", timeout=20000)
        page.wait_for_timeout(3000)
        items = page.evaluate("""() => {
            const links = document.querySelectorAll('a');
            return [...links].filter(a => a.innerText.includes('碳') && a.innerText.length < 60)
                .slice(0, 10).map(a => ({title: a.innerText.trim(), url: a.href}));
        }""")
        browser.close()
        return items
```

---

## 教育统计

```python
# ── 教育部统计数据 ──────────────────────────────────────────
def fetch_moe_stats(keyword="高等教育"):
    """教育部统计数据"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://www.moe.gov.cn/jyb_xxgk/xxgk/neirong/tongji/", timeout=20000)
        page.wait_for_timeout(3000)
        items = page.evaluate(f"""() => {{
            const links = document.querySelectorAll('a');
            return [...links].filter(a => a.innerText.includes('{keyword}') || a.innerText.includes('统计'))
                .slice(0, 10).map(a => ({{title: a.innerText.trim(), url: a.href}}));
        }}""")
        browser.close()
        return items

# 高校基本信息（第三方整理，免费）
def get_college_info(college_name):
    """高校信息查询"""
    url = f"https://api.gugudata.com/location/college?appkey=demo&name={college_name}"
    try:
        data = json.loads(urllib.request.urlopen(url, timeout=10).read())
        return data.get("data", [])
    except Exception as e:
        return [{"error": str(e)}]
```

---

## 制造业/工业（PMI）

```python
import akshare as ak

# ── PMI 数据 ────────────────────────────────────────────────
# 官方制造业PMI（国家统计局，v1.18.56 正确函数名）
df = ak.macro_china_pmi()                    # 制造业PMI + 非制造业PMI（推荐）
df = ak.macro_china_non_man_pmi()            # 非制造业PMI

# 财新制造业PMI（市场口径，更敏感）
df = ak.index_pmi_man_cx()                   # 财新制造业PMI月度（推荐）
df = ak.macro_china_cx_pmi_yearly()          # 财新PMI年度

# 工业增加值
df = ak.macro_china_industrial_profit_yoy()  # 规模以上工业企业利润（含增加值）

# 工业企业利润
df = ak.macro_china_industrial_profit_yoy()  # 规模以上工业企业利润

# 工信部工业统计
def fetch_miit_industry_stats():
    """工信部工业运行数据"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.miit.gov.cn/gxsj/tjsj/gye/", timeout=20000)
        page.wait_for_timeout(3000)
        items = page.evaluate("""() => {
            const links = document.querySelectorAll('a');
            return [...links].filter(a => a.innerText.length > 5 && a.innerText.length < 80)
                .slice(0, 15).map(a => ({title: a.innerText.trim(), url: a.href}));
        }""")
        browser.close()
        return items
```

---

## 互联网统计（CNNIC）

```python
# CNNIC 每半年发布一次互联网发展报告（免费PDF）
def fetch_cnnic_reports():
    """CNNIC互联网发展报告列表"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.cnnic.com.cn/IDR/ReportDownloads/", timeout=20000)
        page.wait_for_timeout(3000)
        reports = page.evaluate("""() => {
            const links = document.querySelectorAll('a');
            return [...links].filter(a => a.href.includes('.pdf') || a.innerText.includes('报告'))
                .slice(0, 10).map(a => ({title: a.innerText.trim(), url: a.href}));
        }""")
        browser.close()
        return reports

# CNNIC 关键数据（AKShare v1.18.56 无此函数，改用 CNNIC 官网）
# 网民规模数据需从 CNNIC 报告 PDF 手动提取，或用上方 playwright 抓取报告列表
```

---

## BaoStock（免费A股历史数据，无需token）

```python
# BaoStock 完全免费，无需注册，比TuShare更易用
# pip install baostock --break-system-packages

import baostock as bs
import pandas as pd

def get_stock_history_bao(code, start="2024-01-01", end="2024-12-31", freq="d"):
    """
    BaoStock 股票历史数据（完全免费，无需token）
    code: sh.600000 / sz.000001
    freq: d=日线, w=周线, m=月线, 5=5分钟, 15=15分钟, 30=30分钟, 60=60分钟
    """
    lg = bs.login()
    rs = bs.query_history_k_data_plus(
        code, "date,open,high,low,close,volume,amount,turn,pctChg",
        start_date=start, end_date=end, frequency=freq, adjustflag="3"
    )
    data = []
    while rs.error_code == "0" and rs.next():
        data.append(rs.get_row_data())
    bs.logout()
    return pd.DataFrame(data, columns=rs.fields)

def get_profit_data_bao(code, year=2024, quarter=3):
    """季度盈利数据"""
    lg = bs.login()
    rs = bs.query_profit_data(code=code, year=year, quarter=quarter)
    data = []
    while rs.error_code == "0" and rs.next():
        data.append(rs.get_row_data())
    bs.logout()
    return pd.DataFrame(data, columns=rs.fields)
```

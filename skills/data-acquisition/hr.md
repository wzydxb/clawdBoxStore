---
name: data-acquisition/hr
description: 招聘市场与人才数据。Boss直聘/51job/猎聘职位搜索、薪资水平、人才需求趋势、劳动力市场指标。HR经理核心数据源。
---

# 招聘市场与人才数据

## 数据源地图

| 数据类型 | 来源 | 获取方式 |
|--------|------|--------|
| 职位搜索/薪资 | Boss直聘 | playwright headless |
| 职位搜索/薪资 | 51job | playwright headless |
| 中高端人才 | 猎聘 | playwright headless |
| 薪资报告 | 智联招聘 | playwright headless |
| 劳动力市场 | 国家统计局 | AKShare / NBSC API |
| 城镇失业率 | 国家统计局 | AKShare macro |
| 社保/公积金 | 各地人社局 | playwright headless |

## Boss直聘职位搜索

```python
from playwright.sync_api import sync_playwright
import json

def search_boss_jobs(keyword, city="全国", limit=20):
    """搜索Boss直聘职位，获取薪资范围和要求"""
    city_map = {"全国": "100010000", "北京": "101010100", "上海": "101020100",
                "深圳": "101280600", "杭州": "101210100", "广州": "101280100"}
    city_code = city_map.get(city, "100010000")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()
        url = f"https://www.zhipin.com/web/geek/job?query={keyword}&city={city_code}"
        page.goto(url, timeout=20000)
        page.wait_for_timeout(4000)

        jobs = page.evaluate(f"""() => {{
            const cards = document.querySelectorAll('.job-card-wrapper, .job-list-box .job-card-body');
            const results = [];
            for (const card of cards) {{
                const title = card.querySelector('.job-name, .job-title')?.innerText?.trim() || '';
                const salary = card.querySelector('.salary')?.innerText?.trim() || '';
                const company = card.querySelector('.company-name')?.innerText?.trim() || '';
                const tags = [...card.querySelectorAll('.tag-list li, .job-info .tag')].map(t => t.innerText.trim()).join('/');
                const location = card.querySelector('.job-area, .company-location')?.innerText?.trim() || '';
                if (title) results.push({{title, salary, company, tags, location}});
                if (results.length >= {limit}) break;
            }}
            return results;
        }}""")
        browser.close()
        return jobs

# 使用示例
jobs = search_boss_jobs("产品经理", city="北京", limit=20)
for j in jobs:
    print(f"{j['title']} | {j['salary']} | {j['company']} | {j['tags']}")
```

## 51job 职位搜索

```python
def search_51job(keyword, city="上海", limit=20):
    """51job职位搜索，适合中低端岗位薪资参考"""
    city_map = {"全国": "000000", "北京": "010000", "上海": "020000",
                "深圳": "040200", "杭州": "080200", "广州": "030200"}
    city_code = city_map.get(city, "000000")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = f"https://we.51job.com/pc/search?keyword={keyword}&searchType=2&city={city_code}"
        page.goto(url, timeout=20000)
        page.wait_for_timeout(4000)

        jobs = page.evaluate(f"""() => {{
            const cards = document.querySelectorAll('.e-list-item, .joblist-item');
            const results = [];
            for (const card of cards) {{
                const title = card.querySelector('.jname, .job-name')?.innerText?.trim() || '';
                const salary = card.querySelector('.sal, .salary')?.innerText?.trim() || '';
                const company = card.querySelector('.cname, .company-name')?.innerText?.trim() || '';
                const exp = card.querySelector('.d-exp, .exp')?.innerText?.trim() || '';
                const edu = card.querySelector('.d-edu, .edu')?.innerText?.trim() || '';
                if (title) results.push({{title, salary, company, exp, edu}});
                if (results.length >= {limit}) break;
            }}
            return results;
        }}""")
        browser.close()
        return jobs
```

## 薪资水平分析

```python
import statistics

def analyze_salary(jobs):
    """从职位列表提取薪资区间，计算市场水平"""
    salaries = []
    for job in jobs:
        sal = job.get('salary', '')
        # 解析 "15-25K·13薪" 格式
        import re
        m = re.search(r'(\d+)-(\d+)[Kk]', sal)
        if m:
            low, high = int(m.group(1)), int(m.group(2))
            salaries.append({'low': low, 'high': high, 'mid': (low+high)/2,
                             'title': job['title'], 'company': job['company']})

    if not salaries:
        return {}

    mids = [s['mid'] for s in salaries]
    return {
        'count': len(salaries),
        'median_k': round(statistics.median(mids), 1),
        'mean_k': round(statistics.mean(mids), 1),
        'min_k': min(s['low'] for s in salaries),
        'max_k': max(s['high'] for s in salaries),
        'p25_k': round(sorted(mids)[len(mids)//4], 1),
        'p75_k': round(sorted(mids)[3*len(mids)//4], 1),
    }

# 示例：分析产品经理薪资
jobs = search_boss_jobs("产品经理", city="北京", limit=50)
stats = analyze_salary(jobs)
print(f"样本量: {stats['count']} 个职位")
print(f"薪资中位数: {stats['median_k']}K/月")
print(f"25%-75%区间: {stats['p25_k']}K - {stats['p75_k']}K")
```

## 宏观劳动力市场数据（AKShare）

```python
import akshare as ak

# 城镇调查失业率（月度）
df = ak.macro_china_urban_unemployment()

# 城镇新增就业人数
df = ak.macro_china_new_employment()

# 农民工监测数据（年度）
# 通过 NBSC API 获取
import nbsc
df = nbsc.get_data(indicator_code="A040201", start_year=2020, end_year=2024)  # 城镇登记失业率
```

## 招聘趋势分析工作流

```
场景：分析某岗位的市场供需和薪资水平

1. 并行搜索多平台：
   - search_boss_jobs('<岗位>', city='<城市>', limit=50)
   - search_51job('<岗位>', city='<城市>', limit=50)

2. 薪资分析：
   - analyze_salary(jobs) → 中位数/区间/分布

3. 技能要求提取：
   - 统计 tags 字段中出现频率最高的技能词
   - 输出：TOP10 技能要求 + 出现频率

4. 公司分布：
   - 统计招聘量最多的公司（需求旺盛方）
   - 统计招聘量增长趋势（对比上月/上季度）

5. 输出 HR 报告：
   - 岗位市场热度（职位数量）
   - 薪资水平（中位数 + 区间）
   - 核心技能要求 TOP10
   - 主要招聘企业
   - 学历/经验要求分布
```

## 人才竞争分析

```python
# 对比多个岗位的薪资水平
roles = ["产品经理", "数据分析师", "运营经理", "HR经理"]
city = "上海"

salary_comparison = {}
for role in roles:
    jobs = search_boss_jobs(role, city=city, limit=30)
    stats = analyze_salary(jobs)
    salary_comparison[role] = stats

# 输出对比表
print(f"{'岗位':<12} {'中位数':>8} {'P25':>8} {'P75':>8} {'样本':>6}")
for role, s in salary_comparison.items():
    if s:
        print(f"{role:<12} {s['median_k']:>7}K {s['p25_k']:>7}K {s['p75_k']:>7}K {s['count']:>5}")
```

## 社保/公积金基数查询

```python
# 各城市社保基数（通过政府网站）
def fetch_social_security_base(city):
    """获取城市社保缴纳基数上下限"""
    city_urls = {
        "北京": "https://rsj.beijing.gov.cn/",
        "上海": "https://12333.sh.gov.cn/",
        "深圳": "https://hrss.sz.gov.cn/",
    }
    # 用 playwright 抓取对应城市人社局公告
    url = city_urls.get(city, "")
    if not url:
        return None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=15000)
        page.wait_for_timeout(3000)
        text = page.inner_text('body')
        browser.close()
        return text[:2000]  # 返回页面文本供 LLM 提取关键数字
```

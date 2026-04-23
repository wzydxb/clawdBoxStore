---
name: data-acquisition/legal
description: 专利数据（CNIPA）、中国裁判文书、失信被执行人名单、行政处罚记录、商标查询。企业风险尽调与知识产权情报。
---

# 法律与知识产权数据

## 数据源地图

| 数据类型 | 来源 | 获取方式 |
|--------|------|--------|
| 专利查询 | CNIPA国家知识产权局 | playwright headless |
| 专利查询 | 专利检索及分析系统 | playwright headless |
| 商标查询 | 中国商标网 | playwright headless |
| 裁判文书 | 中国裁判文书网 | playwright（部分可访问） |
| 失信被执行人 | 最高人民法院 | playwright headless |
| 行政处罚 | 国家企业信用信息公示系统 | playwright headless |
| 经营异常 | 国家企业信用信息公示系统 | playwright headless |

## 专利查询（CNIPA，免费）

```python
from playwright.sync_api import sync_playwright

def search_patents(keyword, patent_type="发明", limit=20):
    """
    CNIPA专利检索
    patent_type: 发明 / 实用新型 / 外观设计
    """
    type_map = {"发明": "1", "实用新型": "2", "外观设计": "3"}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()
        # 使用国知局专利公布公告系统
        page.goto("http://epub.cnipa.gov.cn/", timeout=20000)
        page.wait_for_timeout(3000)

        # 输入关键词
        page.fill('input[name="searchWord"], #searchWord, .search-input', keyword)
        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)

        patents = page.evaluate(f"""() => {{
            const rows = document.querySelectorAll('.patent-list tr, .result-list .item, .search-result tr');
            const results = [];
            for (const row of rows) {{
                const title = row.querySelector('.title a, td:nth-child(2) a, .patent-title')?.innerText?.trim() || '';
                const no = row.querySelector('.patent-no, td:nth-child(1), .no')?.innerText?.trim() || '';
                const applicant = row.querySelector('.applicant, td:nth-child(3)')?.innerText?.trim() || '';
                const date = row.querySelector('.date, td:nth-child(4), .apply-date')?.innerText?.trim() || '';
                const status = row.querySelector('.status, td:nth-child(5)')?.innerText?.trim() || '';
                if (title.length > 3) results.push({{title, no, applicant, date, status}});
                if (results.length >= {limit}) break;
            }}
            return results;
        }}""")
        browser.close()
        return patents

def search_patents_google(keyword, assignee="", limit=10):
    """Google Patents（国际专利，英文）"""
    from urllib.parse import quote
    import urllib.request, json
    query = keyword
    if assignee:
        query += f" assignee:{assignee}"
    url = f"https://patents.google.com/xhr/query?url=q%3D{quote(query)}%26num%3D{limit}&exp=&download=false"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        results = []
        for r in data.get("results", {}).get("cluster", [{}])[0].get("result", [])[:limit]:
            p = r.get("patent", {})
            results.append({
                "title": p.get("title", ""),
                "patent_id": p.get("publication_number", ""),
                "assignee": p.get("assignee", ""),
                "inventor": p.get("inventor", ""),
                "filing_date": p.get("filing_date", ""),
                "abstract": p.get("abstract", "")[:200],
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]
```

## 商标查询（中国商标网）

```python
def search_trademark(keyword, limit=20):
    """中国商标网商标查询"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()
        page.goto("https://sbj.cnipa.gov.cn/sbj/index.html", timeout=20000)
        page.wait_for_timeout(3000)

        try:
            page.fill('input[placeholder*="商标名称"], #tmName', keyword)
            page.click('button[type="submit"], .search-btn')
            page.wait_for_timeout(5000)

            trademarks = page.evaluate(f"""() => {{
                const rows = document.querySelectorAll('.tm-list tr, .result-table tr');
                const results = [];
                for (const row of rows) {{
                    const name = row.querySelector('.tm-name, td:nth-child(2)')?.innerText?.trim() || '';
                    const reg_no = row.querySelector('.reg-no, td:nth-child(1)')?.innerText?.trim() || '';
                    const applicant = row.querySelector('.applicant, td:nth-child(3)')?.innerText?.trim() || '';
                    const category = row.querySelector('.category, td:nth-child(4)')?.innerText?.trim() || '';
                    const status = row.querySelector('.status, td:nth-child(5)')?.innerText?.trim() || '';
                    if (name) results.push({{name, reg_no, applicant, category, status}});
                    if (results.length >= {limit}) break;
                }}
                return results;
            }}""")
            browser.close()
            return trademarks
        except Exception as e:
            browser.close()
            return [{"error": str(e)}]
```

## 失信被执行人查询（最高人民法院）

```python
def check_dishonest_person(name, id_card=""):
    """
    查询失信被执行人（老赖）名单
    接口有反爬（412），必须用playwright真实浏览器
    域名：zxgk.court.gov.cn（中国大陆可访问）
    """
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = ctx.new_page()
        page.goto("https://zxgk.court.gov.cn/shixin/", timeout=20000)
        page.wait_for_timeout(2000)

        # 填写查询表单
        page.fill('input[name="pName"], #pName', name)
        if id_card:
            page.fill('input[name="pCardNum"], #pCardNum', id_card)
        page.click('input[type="submit"], button[type="submit"], .search-btn')
        page.wait_for_timeout(4000)

        records = page.evaluate("""() => {
            const rows = document.querySelectorAll('table tr, .result-list li, .shixin-list tr');
            return [...rows].slice(1, 21).map(row => ({
                name: row.querySelector('td:nth-child(1), .name')?.innerText?.trim() || '',
                case_no: row.querySelector('td:nth-child(2), .case-no')?.innerText?.trim() || '',
                court: row.querySelector('td:nth-child(3), .court')?.innerText?.trim() || '',
                amount: row.querySelector('td:nth-child(4), .amount')?.innerText?.trim() || '',
                date: row.querySelector('td:nth-child(5), .date')?.innerText?.trim() || '',
                province: row.querySelector('td:nth-child(6), .province')?.innerText?.trim() || '',
            })).filter(r => r.name && r.name !== '姓名' && r.name !== '被执行人');
        }""")
        browser.close()
        return records

def check_dishonest_company(company_name):
    """查询企业失信记录（同上，playwright方式）"""
    return check_dishonest_person(company_name)
```

## 行政处罚记录（国家企业信用信息公示系统）

```python
def get_admin_penalties(company_name):
    """查询企业行政处罚记录"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()
        page.goto("https://www.gsxt.gov.cn/index.html", timeout=20000)
        page.wait_for_timeout(2000)

        page.fill('#keyword, input[name="keyword"]', company_name)
        page.keyboard.press("Enter")
        page.wait_for_timeout(4000)

        # 点击第一个结果
        page.click('.company-list .company-item:first-child a, .result-list li:first-child a', timeout=5000)
        page.wait_for_timeout(3000)

        # 找行政处罚标签
        page.click('a[href*="xzcf"], .tab-item:has-text("行政处罚")', timeout=5000)
        page.wait_for_timeout(3000)

        penalties = page.evaluate("""() => {
            const rows = document.querySelectorAll('table tr, .penalty-list li');
            return [...rows].slice(1, 11).map(row => ({
                case_no: row.querySelector('td:nth-child(1)')?.innerText?.trim() || '',
                type: row.querySelector('td:nth-child(2)')?.innerText?.trim() || '',
                authority: row.querySelector('td:nth-child(3)')?.innerText?.trim() || '',
                date: row.querySelector('td:nth-child(4)')?.innerText?.trim() || '',
                content: row.querySelector('td:nth-child(5)')?.innerText?.trim() || '',
            })).filter(r => r.case_no || r.type);
        }""")
        browser.close()
        return penalties
```

## 法律风险尽调工作流

```
场景：企业合作前风险排查

1. 失信被执行人查询：
   check_dishonest_company("<公司名>")
   → 有记录 = 高风险，谨慎合作

2. 行政处罚记录：
   get_admin_penalties("<公司名>")
   → 近3年处罚次数/金额/类型

3. 专利侵权风险：
   search_patents("<核心技术关键词>", patent_type="发明")
   → 检查竞品是否有相关专利保护

4. 商标保护状态：
   search_trademark("<品牌名>")
   → 确认商标注册状态/类别覆盖

5. 输出风险报告：
   - 失信记录：有/无
   - 行政处罚：次数/最近时间/类型
   - 专利风险：相关专利数量/权利人
   - 商标状态：已注册/未注册/争议中
```

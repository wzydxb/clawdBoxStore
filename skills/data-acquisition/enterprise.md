---
name: data-acquisition/enterprise
description: 企业工商数据获取。天眼查、企查查、国家企业信用信息公示系统。供应商背调、竞品基本面、投资标的核查。
---

# 企业工商数据

## 工具选择

| 场景 | 工具 | 说明 |
|------|------|------|
| 快速查基本信息 | `opencli tianyancha search` | 真实Chrome，绕过反爬，返回法人/注册资本/状态 |
| 官方权威数据 | 国家企业信用信息公示系统 | 工商局直连，无反爬，免费 |
| 深度信息（股权/诉讼） | playwright → 天眼查详情页 | 需要登录才能看完整数据 |

## 天眼查搜索

```bash
# 基础查询
opencli tianyancha search '企业名称' --limit 5
```

返回：`name` / `status`（存续/注销）/ `legal_person` / `capital` / `established`

**使用前检查连接：**
```bash
opencli doctor 2>/dev/null | grep -q "Extension: connected" || (pkill -f chromium; sleep 8)
```

## 国家企业信用信息公示系统（免费官方）

```python
from playwright.sync_api import sync_playwright

def query_gsxt(company_name):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        page.goto(f'https://www.gsxt.gov.cn/corp-query-homepage.html', timeout=15000)
        page.wait_for_timeout(2000)
        # 搜索框
        page.fill('#keyword', company_name)
        page.keyboard.press('Enter')
        page.wait_for_timeout(3000)
        results = page.evaluate('''() => {
            const items = document.querySelectorAll('.search-result-item, .result-item, li.item');
            return Array.from(items).slice(0,5).map(el => ({
                name: el.querySelector('.name, h3, .title')?.innerText?.trim() || '',
                code: el.querySelector('.code, .credit-code')?.innerText?.trim() || '',
                status: el.querySelector('.status')?.innerText?.trim() || '',
            }));
        }''')
        browser.close()
        return results
```

## 工商背调工作流

```
1. opencli tianyancha search '<公司名>' --limit 3
2. 提取：法人、注册资本、成立日期、经营状态、统一社会信用代码
3. 如需深度（股权结构/对外投资/诉讼）：
   - browser_navigate 天眼查详情页 → browser_snapshot
   - 或访问 gsxt.gov.cn 官方数据
4. 输出 brief 格式：公司名 | 状态 | 法人 | 注册资本 | 成立日期 | 风险提示
```

## 批量背调（多家公司）

```python
import subprocess, json

companies = ['公司A', '公司B', '公司C']
results = []
for company in companies:
    r = subprocess.run(
        ['opencli', 'tianyancha', 'search', company, '--limit', '1', '-f', 'json'],
        capture_output=True, text=True
    )
    try:
        data = json.loads(r.stdout)
        if data: results.append(data[0])
    except: pass

# 输出对比表
for r in results:
    print(f"{r.get('name','')}: {r.get('status','')} | 法人:{r.get('legal_person','')} | 资本:{r.get('capital','')}")
```

## 数据质量说明

- 天眼查数据来源工商局，但有延迟（通常1-3个月）
- 注册资本≠实缴资本，需区分
- 经营状态"存续"不代表正常经营，需结合其他信息判断
- 重要决策前建议交叉验证 gsxt.gov.cn 官方数据

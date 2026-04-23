---
name: data-acquisition/investment
description: 一级市场融资与投资数据。36氪融资快讯、天眼查投融资、企查查、AKShare IPO数据。CEO/产品经理核心情报源。
---

# 一级市场融资与投资数据

## 数据源地图

| 数据类型 | 来源 | 获取方式 |
|--------|------|--------|
| 融资事件 | 36氪融资快讯 | opencli 36kr + playwright |
| 企业投融资 | 天眼查 | opencli tianyancha |
| 融资新闻 | 36kr RSS | urllib.request |
| 上市信息 | AKShare | ak.stock_ipo_summary_cninfo() |

## 36氪融资快讯（最快，免费）

```bash
# 最新融资新闻
opencli 36kr search '融资' --limit 20

# 按行业搜索融资
opencli 36kr search 'AI 融资 2024' --limit 10
opencli 36kr search '新能源 融资' --limit 10
```

## 36氪融资快讯（playwright，无需登录）

> ⚠️ **HK/海外服务器注意**：36kr（字节跳动旗下）对 HK 机房 IP 启用了 ByteDance 验证码（captcha），
> playwright headless 会被拦截。大陆服务器或本地运行正常。备用方案：使用下方 opencli 命令。

```python
from playwright.sync_api import sync_playwright

def fetch_36kr_funding(keyword="", limit=20):
    """36氪融资快讯（playwright，稳定可用）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()

        if keyword:
            from urllib.parse import quote
            page.goto(f"https://36kr.com/search/articles/{quote(keyword)}", timeout=20000)
        else:
            page.goto("https://36kr.com/newsflashes", timeout=20000)
        page.wait_for_timeout(4000)

        events = page.evaluate(f"""() => {{
            const cards = document.querySelectorAll('.newsflash-item-card, .flow-item, .article-item-wrap');
            const results = [];
            for (const card of cards) {{
                const title = card.querySelector('.title, .headline, h3 a')?.innerText?.trim() || '';
                const time = card.querySelector('.time, .date, .publish-time')?.innerText?.trim() || '';
                const url = card.querySelector('a')?.href || '';
                if (title && (title.includes('融资') || title.includes('投资') || title.includes('轮') || !'{keyword}')) {{
                    results.push({{title, time, url}});
                }}
                if (results.length >= {limit}) break;
            }}
            return results;
        }}""")
        browser.close()
        return events

# 天眼查投融资（opencli）
# opencli tianyancha search '字节跳动' → 含融资历史
```

## A股IPO数据（AKShare）

```python
import akshare as ak

# IPO申报企业列表
df = ak.stock_ipo_summary_cninfo()

# 科创板/创业板注册制上市
df = ak.stock_register_kcb()   # 科创板
df = ak.stock_register_cyb()   # 创业板

# 新股上市日历
df = ak.stock_new_a_cninfo(symbol="增发")

# 定增/再融资
df = ak.stock_dzjy_mrmx(symbol="近一月")
```

## 融资趋势分析工作流

```
场景：分析某行业的融资热度和投资机构偏好

1. 拉取最新融资事件：
   - fetch_itjuzi_funding(keyword='<行业关键词>', limit=50)
   - opencli 36kr search '<行业> 融资' --limit 20

2. 统计分析：
   - 按融资轮次分布（天使/Pre-A/A/B/C/D/上市前）
   - 按融资金额分布
   - 活跃投资机构 TOP10
   - 月度融资事件数量趋势

3. 竞品融资追踪：
   - 对竞争对手公司名逐一查询天眼查
   - 提取最新融资时间/金额/投资方

4. 输出 CEO 情报简报：
   - 行业融资热度（近3个月事件数）
   - 头部投资机构偏好
   - 竞品最新融资动态
   - 市场估值参考区间
```

## 投资机构数据库

```python
def fetch_investor_portfolio(investor_name, limit=20):
    """查询投资机构的投资组合（天眼查）"""
    import subprocess, json
    result = subprocess.run(
        ['opencli', 'tianyancha', 'search', investor_name, '--limit', str(limit), '-f', 'json'],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout) or []
    except:
        return []
```

---
name: data-acquisition/appstore
description: 应用商店数据。七麦数据/蝉大师App排行榜、关键词搜索量、用户评论、竞品版本更新。产品经理核心竞品情报源。
---

# 应用商店数据

## 数据源地图

| 数据类型 | 来源 | 获取方式 |
|--------|------|--------|
| iOS排行榜 | 七麦数据 | playwright headless |
| iOS排行榜 | App Annie（data.ai） | playwright headless |
| 关键词搜索量 | 七麦数据 | playwright headless |
| 用户评论 | App Store | playwright headless |
| 安卓排行 | 应用宝/华为应用市场 | playwright headless |
| 版本更新历史 | App Store Connect | playwright headless |

## iOS App Store 排行榜（七麦数据）

```python
from playwright.sync_api import sync_playwright

def fetch_qimai_ranking(category="全部", chart_type="免费榜", limit=50):
    """七麦数据 iOS 排行榜"""
    category_map = {
        "全部": "36", "游戏": "6014", "社交": "6005", "工具": "6002",
        "效率": "6007", "财务": "6015", "教育": "6017", "健康": "6013",
    }
    cat_id = category_map.get(category, "36")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        page = ctx.new_page()
        url = f"https://www.qimai.cn/rank/index/market/ios/country/cn/genre/{cat_id}/device/iphone/chart/free"
        page.goto(url, timeout=20000)
        page.wait_for_timeout(5000)

        apps = page.evaluate(f"""() => {{
            const rows = document.querySelectorAll('.rank-list tr, .app-list .app-item');
            const results = [];
            for (const row of rows) {{
                const rank = row.querySelector('.rank-num, .rank')?.innerText?.trim() || '';
                const name = row.querySelector('.app-name, .name a')?.innerText?.trim() || '';
                const developer = row.querySelector('.developer, .dev')?.innerText?.trim() || '';
                const category = row.querySelector('.category, .cat')?.innerText?.trim() || '';
                const change = row.querySelector('.rank-change, .change')?.innerText?.trim() || '';
                if (name) results.push({{rank, name, developer, category, change}});
                if (results.length >= {limit}) break;
            }}
            return results;
        }}""")
        browser.close()
        return apps

# 使用示例
apps = fetch_qimai_ranking(category="全部", limit=30)
for a in apps:
    print(f"#{a['rank']} {a['name']} ({a['developer']}) {a['change']}")
```

## App Store 用户评论抓取

```python
def fetch_app_reviews(app_id, country="cn", limit=50):
    """抓取 App Store 用户评论（RSS接口，免费）"""
    import urllib.request, json

    # App Store RSS API（官方，免费，无需登录）
    url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        entries = data.get("feed", {}).get("entry", [])
        reviews = []
        for entry in entries[:limit]:
            if isinstance(entry, dict) and "title" in entry:
                reviews.append({
                    "title": entry.get("title", {}).get("label", ""),
                    "content": entry.get("content", {}).get("label", ""),
                    "rating": entry.get("im:rating", {}).get("label", ""),
                    "version": entry.get("im:version", {}).get("label", ""),
                    "date": entry.get("updated", {}).get("label", ""),
                    "author": entry.get("author", {}).get("name", {}).get("label", ""),
                })
        return reviews
    except Exception as e:
        return [{"error": str(e)}]

# 示例：抓取微信评论（App ID: 414478124）
reviews = fetch_app_reviews("414478124", country="cn", limit=50)
for r in reviews:
    print(f"★{r['rating']} v{r['version']} | {r['title']}")
    print(f"  {r['content'][:100]}")
```

## 关键词搜索量（七麦）

```python
def fetch_keyword_search_volume(keyword):
    """查询 App Store 关键词搜索量和竞争度"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        page = ctx.new_page()
        url = f"https://www.qimai.cn/keyword/index/keyword/{keyword}"
        page.goto(url, timeout=20000)
        page.wait_for_timeout(5000)
        data = page.evaluate("""() => {
            const volume = document.querySelector('.search-volume, .volume-num')?.innerText?.trim() || '';
            const difficulty = document.querySelector('.difficulty, .diff-num')?.innerText?.trim() || '';
            const apps = [...document.querySelectorAll('.keyword-app-list .app-item')].slice(0, 10).map(a => ({
                name: a.querySelector('.name')?.innerText?.trim() || '',
                rank: a.querySelector('.rank')?.innerText?.trim() || '',
            }));
            return {volume, difficulty, top_apps: apps};
        }""")
        browser.close()
        return data
```

## 竞品版本更新追踪

```python
def fetch_app_version_history(app_id, country="cn"):
    """获取 App 版本更新历史（了解竞品迭代节奏）"""
    import urllib.request, json
    url = f"https://itunes.apple.com/lookup?id={app_id}&country={country}"
    try:
        data = json.loads(urllib.request.urlopen(url, timeout=10).read())
        results = data.get("results", [])
        if results:
            app = results[0]
            return {
                "name": app.get("trackName", ""),
                "version": app.get("version", ""),
                "release_notes": app.get("releaseNotes", ""),
                "release_date": app.get("currentVersionReleaseDate", ""),
                "rating": app.get("averageUserRating", 0),
                "rating_count": app.get("userRatingCount", 0),
                "size_mb": round(app.get("fileSizeBytes", 0) / 1024 / 1024, 1),
                "price": app.get("price", 0),
                "developer": app.get("artistName", ""),
            }
    except Exception as e:
        return {"error": str(e)}

# 批量追踪竞品
competitor_ids = {
    "微信": "414478124",
    "钉钉": "930368978",
    "飞书": "1371042953",
    "企业微信": "1087897068",
}
for name, app_id in competitor_ids.items():
    info = fetch_app_version_history(app_id)
    print(f"{name}: v{info.get('version')} | ★{info.get('rating')} ({info.get('rating_count')}评) | {info.get('release_date', '')[:10]}")
    print(f"  更新内容: {info.get('release_notes', '')[:100]}")
```

## 产品经理竞品分析工作流

```
场景：全面分析竞品 App 现状

1. 排行榜定位：
   - fetch_qimai_ranking(category='<品类>') → 竞品在榜位置

2. 版本迭代分析：
   - fetch_app_version_history(<app_id>) → 最新版本/更新内容/评分

3. 用户口碑：
   - fetch_app_reviews(<app_id>, limit=100) → 用户评论
   - 情感分析：统计正面/负面/功能请求
   - 提取高频投诉点（竞品弱点 = 我方机会）

4. 关键词竞争：
   - fetch_keyword_search_volume('<核心词>') → 搜索量/竞争度/TOP10 App

5. 输出竞品报告：
   - 排行榜位置趋势
   - 迭代节奏（多久发一个版本）
   - 用户评分趋势
   - 核心用户投诉 TOP5
   - 关键词覆盖情况
```

## 安卓应用市场（应用宝）

```python
def fetch_myapp_ranking(category="全部", limit=30):
    """腾讯应用宝排行榜（安卓）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://sj.qq.com/myapp/category.htm?orgame=1&categoryId=0", timeout=20000)
        page.wait_for_timeout(4000)
        apps = page.evaluate(f"""() => {{
            const items = document.querySelectorAll('.app-list .app-item, .rank-list li');
            return [...items].slice(0, {limit}).map((item, i) => ({{
                rank: i + 1,
                name: item.querySelector('.app-name, .name')?.innerText?.trim() || '',
                developer: item.querySelector('.developer, .dev')?.innerText?.trim() || '',
                downloads: item.querySelector('.download-count, .dl-count')?.innerText?.trim() || '',
            }}));
        }}""")
        browser.close()
        return apps
```

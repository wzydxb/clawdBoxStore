---
name: data-acquisition/ecommerce
description: 电商价格比较、商品排行、促销信息。淘宝/京东/拼多多商品搜索与价格监控、电商销量排行、历史价格走势。
---

# 电商与商品数据

## 数据源地图

| 数据类型 | 来源 | 获取方式 |
|--------|------|--------|
| 商品搜索/价格 | 京东 | playwright headless |
| 商品搜索/价格 | 淘宝/天猫 | playwright headless |
| 商品搜索/价格 | 拼多多 | playwright headless |
| 历史价格走势 | 慢慢买 | playwright headless |
| 历史价格走势 | 什么值得买 | playwright headless |
| 电商销量排行 | 京东排行榜 | playwright headless |
| 促销/优惠券 | 什么值得买 | playwright headless |

## 京东商品搜索

```python
from playwright.sync_api import sync_playwright
import json

def search_jd(keyword, sort="综合", limit=20):
    """
    京东商品搜索
    sort: 综合 / 销量 / 价格升序 / 价格降序 / 评论数
    """
    sort_map = {"综合": "", "销量": "&sort=sort_rank_asc", "价格升序": "&sort=sort_price_asc",
                "价格降序": "&sort=sort_price_desc", "评论数": "&sort=sort_comment_asc"}
    sort_param = sort_map.get(sort, "")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()
        from urllib.parse import quote
        url = f"https://search.jd.com/Search?keyword={quote(keyword)}&enc=utf-8{sort_param}"
        page.goto(url, timeout=20000)
        page.wait_for_timeout(4000)

        products = page.evaluate(f"""() => {{
            const items = document.querySelectorAll('#J_goodsList .gl-item, .goods-list .item');
            const results = [];
            for (const item of items) {{
                const title = item.querySelector('.p-name em, .p-name a')?.innerText?.trim() || '';
                const price = item.querySelector('.p-price strong i, .p-price .price')?.innerText?.trim() || '';
                const shop = item.querySelector('.p-shop a, .shop-name')?.innerText?.trim() || '';
                const comment = item.querySelector('.p-commit a, .comment-count')?.innerText?.trim() || '';
                const url = item.querySelector('.p-name a, a.img-block')?.href || '';
                if (title) results.push({{title, price, shop, comment, url}});
                if (results.length >= {limit}) break;
            }}
            return results;
        }}""")
        browser.close()
        return products

def get_jd_ranking(category="手机", limit=20):
    """京东销量排行榜"""
    category_map = {
        "手机": "9987", "电脑": "670", "家电": "737", "服装": "1315",
        "食品": "1320", "美妆": "1316", "图书": "1713", "运动": "1319",
    }
    cat_id = category_map.get(category, "9987")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://www.jd.com/allSort.aspx", timeout=20000)
        page.wait_for_timeout(3000)
        # 直接访问排行榜
        page.goto(f"https://search.jd.com/Search?keyword={category}&sort=sort_rank_asc&enc=utf-8", timeout=20000)
        page.wait_for_timeout(4000)
        return search_jd(category, sort="销量", limit=limit)
```

## 淘宝/天猫商品搜索

```python
def search_taobao(keyword, limit=20):
    """淘宝商品搜索（需要登录状态，否则部分数据不可见）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()
        from urllib.parse import quote
        url = f"https://s.taobao.com/search?q={quote(keyword)}&sort=sale-desc"
        page.goto(url, timeout=20000)
        page.wait_for_timeout(5000)

        products = page.evaluate(f"""() => {{
            const items = document.querySelectorAll('.item.J_MouserOnverReq, [data-item-id]');
            const results = [];
            for (const item of items) {{
                const title = item.querySelector('.title, .item-title')?.innerText?.trim() || '';
                const price = item.querySelector('.price strong, .g_price')?.innerText?.trim() || '';
                const sales = item.querySelector('.deal-cnt, .sales')?.innerText?.trim() || '';
                const shop = item.querySelector('.shop, .shopname')?.innerText?.trim() || '';
                const location = item.querySelector('.location, .item-loc')?.innerText?.trim() || '';
                if (title) results.push({{title, price, sales, shop, location}});
                if (results.length >= {limit}) break;
            }}
            return results;
        }}""")
        browser.close()
        return products
```

## 历史价格查询（慢慢买）

```python
def get_price_history(product_name, limit=5):
    """查询商品历史价格走势（慢慢买）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()
        from urllib.parse import quote
        page.goto(f"https://www.manmanbuy.com/search.aspx?key={quote(product_name)}", timeout=20000)
        page.wait_for_timeout(4000)

        products = page.evaluate(f"""() => {{
            const items = document.querySelectorAll('.search-result .item, .product-list .product');
            return [...items].slice(0, {limit}).map(item => ({{
                title: item.querySelector('.title, .name')?.innerText?.trim() || '',
                current_price: item.querySelector('.price, .current-price')?.innerText?.trim() || '',
                lowest_price: item.querySelector('.lowest, .history-low')?.innerText?.trim() || '',
                platform: item.querySelector('.platform, .shop')?.innerText?.trim() || '',
                url: item.querySelector('a')?.href || '',
            }}));
        }}""")
        browser.close()
        return products

def get_smzdm_deals(keyword="", category="数码", rsshub="http://localhost:1200"):
    """
    什么值得买 — 优惠/值得买内容
    注意：smzdm 有腾讯验证码bot检测，playwright headless 被封。
    改用 RSSHub 本地实例（推荐）或直接搜索页。
    """
    import urllib.request, xml.etree.ElementTree as ET
    from urllib.parse import quote

    # 优先：RSSHub 本地实例（自部署即可，无验证码）
    if rsshub:
        kw = keyword or category
        url = f"{rsshub}/smzdm/keyword/{quote(kw)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            content = urllib.request.urlopen(req, timeout=10).read()
            root = ET.fromstring(content)
            deals = []
            for item in root.findall(".//item")[:20]:
                deals.append({
                    "title": item.findtext("title", "").strip(),
                    "link": item.findtext("link", "").strip(),
                    "date": item.findtext("pubDate", "").strip(),
                    "desc": item.findtext("description", "").strip()[:200],
                })
            if deals:
                return deals
        except Exception:
            pass  # 降级到 playwright

    # 降级：playwright（境内服务器有效，境外腾讯验证码可能拦截）
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            extra_http_headers={"Accept-Language": "zh-CN,zh;q=0.9"}
        )
        page = ctx.new_page()
        if keyword:
            url = f"https://search.smzdm.com/?c=home&s={quote(keyword)}&order=time"
        else:
            url = "https://www.smzdm.com/jingxuan/"
        page.goto(url, timeout=20000)
        page.wait_for_timeout(5000)
        deals = page.evaluate("""() => {
            const items = document.querySelectorAll('.feed-row-wide, .z-feed-item, .article-list-item');
            return [...items].slice(0, 20).map(item => ({
                title: item.querySelector('.feed-block-title, .z-feed-title, .article-title')?.innerText?.trim() || '',
                price: item.querySelector('.z-price, .feed-price, .price')?.innerText?.trim() || '',
                original_price: item.querySelector('.z-origin-price, .feed-origin-price')?.innerText?.trim() || '',
                platform: item.querySelector('.feed-block-extras .z-feed-source, .platform, .shop')?.innerText?.trim() || '',
                votes: item.querySelector('.z-feed-btn-smzdm, .vote-count, .like-count')?.innerText?.trim() || '',
                time: item.querySelector('.feed-block-time, .z-feed-time, .time')?.innerText?.trim() || '',
            })).filter(i => i.title);
        }""")
        browser.close()
        return deals
```

## 拼多多商品搜索

```python
def search_pdd(keyword, limit=20):
    """拼多多商品搜索"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = ctx.new_page()
        from urllib.parse import quote
        page.goto(f"https://mobile.yangkeduo.com/search_result.html?search_key={quote(keyword)}", timeout=20000)
        page.wait_for_timeout(5000)
        products = page.evaluate(f"""() => {{
            const items = document.querySelectorAll('.goods-item, [class*="goods"]');
            const results = [];
            for (const item of items) {{
                const title = item.querySelector('[class*="title"], [class*="name"]')?.innerText?.trim() || '';
                const price = item.querySelector('[class*="price"]')?.innerText?.trim() || '';
                const sales = item.querySelector('[class*="sales"], [class*="sold"]')?.innerText?.trim() || '';
                if (title.length > 3) results.push({{title, price, sales}});
                if (results.length >= {limit}) break;
            }}
            return results;
        }}""")
        browser.close()
        return products
```

## 电商数据工作流

```
场景1：竞品定价分析
1. search_jd("<竞品名>", sort="销量") → 主流价格区间
2. search_taobao("<竞品名>") → 淘宝价格分布
3. 统计：最低价/最高价/中位价/主流价格带
4. 输出定价建议

场景2：选品/市场调研
1. get_jd_ranking("<品类>") → 当前销量TOP20
2. search_jd("<品类>", sort="评论数") → 口碑最好的产品
3. get_smzdm_deals("<品类>") → 近期热门优惠
4. 分析：价格带分布/用户偏好/市场空白

场景3：价格监控
1. get_price_history("<商品名>") → 历史最低价
2. 对比当前价格 → 判断是否值得购买/采购
3. 设置价格预警阈值

场景4：供应商比价
1. 并行搜索多平台：JD + 淘宝 + PDD
2. 同款商品价格对比
3. 考虑运费/服务/发货速度综合评分
```

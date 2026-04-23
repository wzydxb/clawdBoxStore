---
name: data-acquisition/rsshub
description: RSSHub — 开源RSS生成器，覆盖1300+网站。知乎/B站/小红书/抖音/豆瓣/微博/微信公众号/GitHub/政府部门，无需登录即可订阅。
---

# RSSHub 数据源

RSSHub 是最强的免费数据聚合工具，把几乎所有网站转成结构化RSS。
目标盒子上自部署实例（推荐）或使用公共实例 `https://rsshub.app`。

## 安装（目标盒子一次性）

```bash
# Docker 方式（推荐，5分钟搞定）
docker run -d --name rsshub -p 1200:1200 diygod/rsshub

# 或 npm 方式
npm install -g rsshub
rsshub start
```

部署后访问 `http://localhost:1200`，所有路由替换 `https://rsshub.app` 为 `http://localhost:1200`。

## 读取 RSS 的通用函数

```python
import urllib.request
import xml.etree.ElementTree as ET

RSSHUB = "https://rsshub.app"  # 或 "http://localhost:1200"

def fetch_rsshub(route, limit=20):
    """读取任意 RSSHub 路由"""
    url = f"{RSSHUB}{route}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        content = urllib.request.urlopen(req, timeout=15).read()
        root = ET.fromstring(content)
        items = []
        for item in root.findall(".//item")[:limit]:
            items.append({
                "title": item.findtext("title", "").strip(),
                "link": item.findtext("link", "").strip(),
                "date": item.findtext("pubDate", "").strip(),
                "desc": item.findtext("description", "").strip()[:300],
            })
        return items
    except Exception as e:
        return [{"error": str(e)}]
```

---

## 社交媒体（我们之前缺失的）

```python
# ── 知乎 ──────────────────────────────────────────────────────
# 知乎热榜（无需登录）
fetch_rsshub("/zhihu/hotlist")

# 知乎日报
fetch_rsshub("/zhihu/daily")

# 知乎专栏
fetch_rsshub("/zhihu/zhuanlan/<专栏ID>")

# ── B站 ───────────────────────────────────────────────────────
# B站全站排行榜
fetch_rsshub("/bilibili/ranking/0/3/1")  # 0=全站, 3=3天, 1=综合

# B站分区排行（科技/游戏/生活等）
fetch_rsshub("/bilibili/ranking/36/3/1")  # 36=科技区

# UP主最新视频
fetch_rsshub("/bilibili/user/video/<uid>")

# ── 小红书 ────────────────────────────────────────────────────
# 小红书关键词搜索（无需登录）
fetch_rsshub("/xiaohongshu/search/<关键词>")

# 小红书用户笔记
fetch_rsshub("/xiaohongshu/user/<用户ID>")

# ── 抖音 ──────────────────────────────────────────────────────
# 抖音用户视频
fetch_rsshub("/douyin/user/<用户ID>")

# 抖音话题
fetch_rsshub("/douyin/hashtag/<话题名>")

# ── 微博 ──────────────────────────────────────────────────────
# 微博用户时间线
fetch_rsshub("/weibo/user/<uid>")

# 微博关键词搜索
fetch_rsshub("/weibo/keyword/<关键词>")

# ── 豆瓣 ──────────────────────────────────────────────────────
# 豆瓣电影新片
fetch_rsshub("/douban/movie/playing")

# 豆瓣图书新书
fetch_rsshub("/douban/book/latest")

# 豆瓣小组讨论
fetch_rsshub("/douban/group/<组ID>/discussion")

# ── 微信公众号 ────────────────────────────────────────────────
# 微信公众号文章（需要公众号ID）
fetch_rsshub("/wechat/mp/article/<公众号ID>")
```

---

## 政府与官方机构

```python
# ── 国务院 ────────────────────────────────────────────────────
fetch_rsshub("/gov/zhengce/zuixin")           # 最新政策
fetch_rsshub("/gov/zhengce/zhengceku/2024-12") # 政策文库

# ── 工信部 ────────────────────────────────────────────────────
fetch_rsshub("/gov/miit/zcjd")               # 政策解读
fetch_rsshub("/gov/miit/gzdt")               # 工作动态

# ── 国家统计局 ────────────────────────────────────────────────
fetch_rsshub("/gov/stats/sj/sjjd")           # 数据解读
fetch_rsshub("/gov/stats/tjsj/tjgb")         # 统计公报

# ── 证监会 ────────────────────────────────────────────────────
fetch_rsshub("/gov/csrc/news")               # 最新动态

# ── 央行 ──────────────────────────────────────────────────────
fetch_rsshub("/gov/pbc/goutongjiaoliu")      # 沟通交流

# ── 最高人民法院 ──────────────────────────────────────────────
fetch_rsshub("/gov/court/xwzx/syfb")        # 司法发布
```

---

## 科技与行业媒体

```python
# ── 科技媒体 ──────────────────────────────────────────────────
fetch_rsshub("/36kr/news/latest")            # 36氪最新
fetch_rsshub("/sspai/article")               # 少数派
fetch_rsshub("/ifanr/app")                   # 爱范儿
fetch_rsshub("/geekpark/news")               # 极客公园
fetch_rsshub("/huxiu/article")               # 虎嗅（解决RSS超时问题）
fetch_rsshub("/pingwest/news")               # 品玩

# ── 财经媒体 ──────────────────────────────────────────────────
fetch_rsshub("/caixin/latest/finance")       # 财新财经
fetch_rsshub("/yicai/news")                  # 第一财经
fetch_rsshub("/cls/telegraph")               # 财联社电报（实时财经快讯）

# ── GitHub ────────────────────────────────────────────────────
fetch_rsshub("/github/trending/daily/python") # GitHub每日趋势
fetch_rsshub("/github/issue/<owner>/<repo>")  # 项目issue追踪
```

---

## 招聘与职场

```python
# Boss直聘职位（补充hr.md的playwright方式）
fetch_rsshub("/boss/jobs/<关键词>/<城市>")

# 拉勾网
fetch_rsshub("/lagou/jobs/<关键词>")

# 脉脉职场动态
fetch_rsshub("/maimai/hot")
```

---

## 电商与消费

```python
# 什么值得买（解决bot检测问题）
fetch_rsshub("/smzdm/keyword/<关键词>")      # 关键词优惠
fetch_rsshub("/smzdm/ranking/pinlei/1/1")   # 品类排行

# 京东降价提醒
fetch_rsshub("/jd/price/<商品ID>")

# 淘宝/天猫活动
fetch_rsshub("/taobao/activity")
```

---

## 学术与研究

```python
# arXiv 论文（AI/ML方向）
fetch_rsshub("/arxiv/search/?searchtype=all&query=large+language+model")

# 知网最新论文
fetch_rsshub("/cnki/journal/<期刊名>")

# 中国专利公告
fetch_rsshub("/cnipa/patent/search/<关键词>")
```

---

## 批量订阅工作流

```python
# 一次性拉取多个来源，合并去重
import concurrent.futures

ROUTES = {
    "知乎热榜": "/zhihu/hotlist",
    "B站排行": "/bilibili/ranking/0/3/1",
    "财联社电报": "/cls/telegraph",
    "36氪": "/36kr/news/latest",
    "虎嗅": "/huxiu/article",
    "工信部动态": "/gov/miit/gzdt",
    "国务院政策": "/gov/zhengce/zuixin",
}

def fetch_all(routes, limit=10):
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(fetch_rsshub, route, limit): name
                   for name, route in routes.items()}
        for f in concurrent.futures.as_completed(futures):
            name = futures[f]
            results[name] = f.result()
    return results

all_news = fetch_all(ROUTES, limit=10)
for source, items in all_news.items():
    print(f"\n── {source} ──")
    for item in items[:3]:
        print(f"  {item.get('title','')[:60]}")
```

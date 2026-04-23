---
name: data-acquisition/social
description: 社交热点与舆情数据。微博/百度/贴吧/B站/36氪热榜、知乎、小红书、抖音、今日头条。实时热点追踪，舆情监控。
---

# 社交热点与舆情

## 热榜命令速查

```bash
# ── 综合热搜 ──────────────────────────────────────
opencli weibo hot --limit 30        # 微博热搜（实时，覆盖最广）
opencli baidu hot --limit 30        # 百度热搜（搜索热度）

# ── 内容平台 ──────────────────────────────────────
opencli tieba hot --limit 20        # 贴吧热点（年轻用户，话题性）
opencli bilibili hot --limit 20     # B站热门（视频内容，年轻圈层）
opencli 163 hot --limit 20          # 网易新闻热点（综合资讯）
opencli qqnews hot --limit 20       # 腾讯新闻热点（综合资讯）

# ── 科技商业 ──────────────────────────────────────
opencli 36kr hot --limit 20         # 36氪热榜（科技/创投）
opencli producthunt hot --limit 20  # Product Hunt（全球产品）

# ── 专业社区 ──────────────────────────────────────
opencli zhihu hot --limit 20        # 知乎热榜（需登录）
opencli hackernews top --limit 20   # HN（技术）
opencli v2ex hot --limit 20         # V2EX（开发者）

# ── 金融舆情 ──────────────────────────────────────
opencli xueqiu hot --limit 20       # 雪球热门（股市讨论）
opencli eastmoney hot-rank --limit 20 # 东财热股榜

# ── 电商平台 ──────────────────────────────────────
opencli douban book-hot --limit 10  # 豆瓣图书热门
opencli douban movie-hot --limit 10 # 豆瓣电影热门
```

## 平台选择原则

| 目的 | 推荐平台 |
|------|----------|
| 大众舆情监控 | 微博 + 百度热搜 |
| 年轻用户/潮流 | B站 + 贴吧 |
| 科技/商业情报 | 36氪 + HN |
| 股市舆情 | 雪球 + 东方财富 |
| 深度讨论 | 知乎（需登录）|
| 全局覆盖 | 微博 + 百度 + 36氪 + B站 |

## 批量拉取多平台热点

```python
import subprocess, json

def get_hot(site, cmd, limit=10):
    r = subprocess.run(
        ['opencli', site, cmd, '--limit', str(limit), '-f', 'json'],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(r.stdout) or []
    except:
        return []

# 并行拉取（实际执行时用 ThreadPoolExecutor 并行）
hot_data = {
    '微博热搜': get_hot('weibo', 'hot', 20),
    '百度热搜': get_hot('baidu', 'hot', 20),
    'B站热门': get_hot('bilibili', 'hot', 20),
    '36氪热榜': get_hot('36kr', 'hot', 20),
    '贴吧热点': get_hot('tieba', 'hot', 20),
}

# 提取所有话题关键词
all_topics = []
for platform, items in hot_data.items():
    for item in items:
        keyword = item.get('keyword') or item.get('title') or ''
        if keyword:
            all_topics.append({'platform': platform, 'keyword': keyword,
                               'hot': item.get('hot', item.get('discussions', ''))})

print(f"共获取 {len(all_topics)} 条热点")
```

## 关键词舆情监控

```bash
# 搜索微博相关内容
opencli weibo search '关键词' --limit 20

# 小红书舆情（用户真实评价）
opencli xiaohongshu search '关键词' --limit 20

# 知乎讨论
opencli zhihu search '关键词' --limit 10

# 虎扑讨论（体育/生活）
opencli hupu search '关键词' --limit 10

# 即刻（科技圈讨论）
opencli jike search '关键词' --limit 10
```

## 小红书深度分析（创作者数据）

```bash
# 搜索笔记
opencli xiaohongshu search '关键词' --limit 20

# 获取笔记详情（评论/互动数据）
opencli xiaohongshu note --url 'https://www.xiaohongshu.com/explore/xxx'

# 用户创作者数据
opencli xiaohongshu creator-stats

# 热门笔记列表
opencli xiaohongshu creator-notes
```

## 抖音话题追踪

```bash
# 话题搜索 / AI推荐热点词
opencli douyin hashtag '关键词'

# 热门视频（需登录）
opencli douyin videos --limit 20
```

## 舆情分析工作流

```
场景：监控品牌/产品在社交媒体的口碑

1. 并行拉取热榜（weibo + baidu + tieba）
   → 判断是否有品牌相关话题进入热榜

2. 搜索品牌关键词：
   opencli weibo search '<品牌名>' --limit 30
   opencli xiaohongshu search '<品牌名>' --limit 30
   opencli zhihu search '<品牌名>' --limit 20

3. 情感分类（正面/负面/中性）
   → 统计各平台正负比例

4. 定位核心问题点（被提及最多的投诉/争议）

5. 输出舆情报告：
   - 热度指数（上热搜情况）
   - 各平台声量分布
   - 核心情绪点
   - 代表性内容摘录
   - 风险预警（如有）
```

## 竞品舆情对比

```python
brands = ['品牌A', '品牌B', '品牌C']
platforms = [
    ('weibo', 'search'),
    ('xiaohongshu', 'search'),
    ('zhihu', 'search'),
]

report = {}
for brand in brands:
    brand_mentions = 0
    for site, cmd in platforms:
        r = subprocess.run(
            ['opencli', site, cmd, brand, '--limit', '20', '-f', 'json'],
            capture_output=True, text=True, timeout=30
        )
        try:
            items = json.loads(r.stdout) or []
            brand_mentions += len(items)
        except:
            pass
    report[brand] = brand_mentions

# 输出声量对比
for brand, count in sorted(report.items(), key=lambda x: -x[1]):
    print(f"{brand}: {count} 条相关内容")
```

## 热点借势内容策略

```
1. opencli weibo hot + baidu hot（获取实时热榜）
2. 过滤与品牌/行业相关的话题
3. 对每个相关话题分析：
   - 话题性质（正面/负面/中性）
   - 与品牌关联度
   - 借势风险（是否有争议）
4. 输出可借势的话题列表 + 建议创作角度
5. 配合 content-writer skill 批量生成内容
```

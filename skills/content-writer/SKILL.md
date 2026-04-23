---
name: content-writer
description: |
  批量内容创作能力。根据热点话题批量生成推文、新闻稿、公众号文章，输出为 Word 文件。
  触发词：写推文、写新闻稿、写文章、批量写、根据热点写、内容创作、写稿
version: 1.0.0
---

# 内容创作能力

## 核心流程

```
1. 拉取热点（选择平台）
2. 筛选相关话题（按行业/关键词过滤）
3. 按模板类型批量生成内容
4. 导出 Word 文件到 /root/workspace/uploads/
```

---

## 第一步：拉取热点

根据用户需求选择热点来源（可多选）：

```bash
# 微博热搜（大众舆情，最广泛）
opencli weibo hot --limit 20

# 百度热搜（搜索热度，信息量大）
opencli baidu hot --limit 20

# 贴吧热点（年轻用户，话题性强）
opencli tieba hot --limit 20

# B站热门（视频内容，年轻圈层）
opencli bilibili hot --limit 20

# 36氪热榜（科技/商业，B端适用）
opencli 36kr hot --limit 20

# 知乎热榜（深度讨论，专业感强）
opencli zhihu hot --limit 20

# 小红书（生活方式，女性用户）
opencli xiaohongshu search '<关键词>' --limit 20
```

**选平台原则：**
- 大众消费品/零售 → 微博 + 百度 + 贴吧
- 科技/B端产品 → 36氪 + 知乎
- 年轻/潮流品牌 → B站 + 小红书
- 全覆盖 → 微博 + 百度 + 36氪

---

## 第二步：筛选话题

拿到热点列表后，按以下逻辑筛选：

```python
# 用 execute_code 过滤相关话题
hot_topics = [...]  # 上一步的热点列表

# 按关键词过滤
keywords = ['AI', '科技', '产品']  # 替换为实际关键词
relevant = [t for t in hot_topics if any(k in t['keyword'] or k in t.get('title','') for k in keywords)]

# 取前5个最相关的
selected = relevant[:5]
print(selected)
```

---

## 第三步：批量生成内容

### 推文（微博/朋友圈/小红书）

```python
# 推文生成 prompt 模板
WEIBO_PROMPT = """
你是一个资深新媒体运营，请根据以下热点话题写一条微博推文：

热点话题：{topic}
品牌/产品：{brand}
核心卖点：{selling_point}
目标受众：{audience}

要求：
- 字数：100-200字
- 开头要有吸引力，能让人停下来看
- 结合热点但不强行蹭热点，要自然
- 结尾加1-2个相关话题标签 #xxx#
- 语气：{tone}（活泼/专业/温情/犀利）
- 不要用"首先""其次""最后"这种结构化语言
"""

# 批量生成
contents = []
for topic in selected_topics:
    prompt = WEIBO_PROMPT.format(
        topic=topic,
        brand=brand_name,
        selling_point=selling_point,
        audience=target_audience,
        tone=tone
    )
    # 调用 hermes 自身生成（execute_code 里直接用 LLM）
    content = generate_content(prompt)
    contents.append({'topic': topic, 'content': content, 'type': '推文'})
```

### 新闻稿

```python
PRESS_RELEASE_PROMPT = """
你是一个专业公关，请根据以下热点写一篇新闻稿：

热点背景：{topic}
公司/品牌：{company}
新闻角度：{angle}（产品发布/活动/合作/观点/数据）
核心信息：{key_message}

新闻稿结构：
1. 标题（吸引眼球，含关键词）
2. 导语（5W1H，100字内）
3. 正文（3-4段，每段150-200字）
   - 第1段：事件/产品详情
   - 第2段：行业背景/市场数据
   - 第3段：公司/负责人引语
   - 第4段：未来展望
4. 关于{company}（50字公司简介）

要求：
- 总字数：600-800字
- 语气：正式、客观、有权威感
- 数据要具体（如有）
- 引语要真实可信
"""
```

### 公众号文章

```python
WECHAT_ARTICLE_PROMPT = """
你是一个公众号主编，请根据以下热点写一篇公众号文章：

热点话题：{topic}
公众号定位：{positioning}
目标读者：{audience}
文章角度：{angle}（深度解析/干货教程/观点评论/故事叙述）

文章结构：
1. 标题（10-20字，含热点词，有悬念或利益点）
2. 开头（100字内，直接切入，不废话）
3. 正文（3-5个小节，每节有小标题）
4. 结尾（呼吁互动或行动）

要求：
- 总字数：800-1500字
- 多用短句，少用长句
- 每段不超过5行
- 适当加粗关键信息
- 结尾引导评论/转发
"""
```

---

## 第四步：导出 Word

```python
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import datetime, os

def export_to_word(contents, output_type='推文', brand=''):
    doc = Document()
    
    # 标题页
    title = doc.add_heading(f'{brand} {output_type}批量稿件', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'生成时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}')
    doc.add_paragraph(f'共 {len(contents)} 篇')
    doc.add_page_break()
    
    for i, item in enumerate(contents, 1):
        # 每篇文章标题
        doc.add_heading(f'第{i}篇 | 热点：{item["topic"]}', level=1)
        
        # 内容
        para = doc.add_paragraph(item['content'])
        para.paragraph_format.space_after = Pt(12)
        
        # 分隔线
        if i < len(contents):
            doc.add_paragraph('─' * 40)
    
    # 保存
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'/root/workspace/uploads/{output_type}_{brand}_{timestamp}.docx'
    os.makedirs('/root/workspace/uploads', exist_ok=True)
    doc.save(filename)
    return filename

# 调用示例
filename = export_to_word(contents, output_type='推文', brand='品牌名')
print(f'已导出：{filename}')
```

---

## 完整工作流示例

用户说「根据今天微博热搜，给我们的运动品牌写5条推文，导出Word」：

```python
import subprocess, json, datetime
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# 1. 拉热点
result = subprocess.run(['opencli', 'weibo', 'hot', '--limit', '20', '-f', 'json'],
                        capture_output=True, text=True)
hot_list = json.loads(result.stdout)

# 2. 筛选（运动/健康/生活方式相关）
keywords = ['运动', '健身', '跑步', '户外', '体育', '锻炼', '健康']
relevant = [t for t in hot_list
            if any(k in t.get('keyword','') + t.get('title','') for k in keywords)]
# 如果相关话题不足5个，取热度最高的前5个
selected = (relevant + hot_list)[:5]

# 3. 生成内容（在 execute_code 里调用 LLM）
# ... 生成逻辑 ...

# 4. 导出 Word
doc = Document()
doc.add_heading('运动品牌推文 - 热点借势', 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph(f'生成时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}')
doc.add_page_break()

for i, item in enumerate(contents, 1):
    doc.add_heading(f'第{i}条 | {item["topic"]}', level=1)
    doc.add_paragraph(item['content'])
    if i < len(contents):
        doc.add_paragraph('─' * 50)

filename = f'/root/workspace/uploads/推文_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.docx'
doc.save(filename)
print(f'✓ 已导出：{filename}')
print(f'  用户可从网盘直接下载')
```

---

## 内容质量规则

- **热点相关性**：内容必须与热点有真实关联，不强行蹭热点
- **品牌一致性**：语气、价值观与品牌调性一致
- **平台适配**：微博140字内，公众号800字+，新闻稿600字+
- **不造假数据**：引用数据必须真实，不编造统计数字
- **批量不等于批量复制**：每篇内容角度不同，不是换词重复

---

## 支持的输出格式

| 类型 | 字数 | 平台 | 特点 |
|------|------|------|------|
| 推文 | 100-200字 | 微博/朋友圈 | 短平快，话题标签 |
| 小红书笔记 | 200-500字 | 小红书 | 种草感，emoji，标签 |
| 新闻稿 | 600-800字 | 媒体/官网 | 正式，5W1H，引语 |
| 公众号文章 | 800-1500字 | 微信公众号 | 深度，小标题，互动 |
| 短视频脚本 | 300-500字 | 抖音/视频号 | 口语化，分镜描述 |

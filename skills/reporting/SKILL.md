---
name: reporting
description: |
  生成日报、周报、月报、会议纪要、问题分析、方案提案、决策记录、情报简报、长文编排。
  自动读取 TASKLOG.md，渲染画布图片发送。
  触发词：日报、周报、月报、会议纪要、问题分析、方案、决策、简报、长文
version: 3.0.0
---

# 报告生成技能

## 触发词 → 模板映射

| 用户说 | 模板 | 说明 |
|--------|------|------|
| 日报 / 今天做了什么 / 今天完成了啥 | `daily-report` | 从 TASKLOG.md 提取今日任务 |
| 周报 / 本周总结 / 这周做了什么 | `weekly-report` | 从 TASKLOG.md 提取本周任务 |
| 月报 / 本月回顾 / 这个月做了啥 | `monthly-report` | 从 TASKLOG.md 提取本月任务 |
| 会议纪要 / 整理会议 / 出纪要 / 会议总结 | `meeting-notes` 或 `meeting-notes-detail` | 有过程记录用 detail 版 |
| 问题分析 / 问题卡片 / 分析一下这个问题 | `problem-card` | 结构化问题拆解 |
| 方案 / 方案对比 / 提案 / 选哪个好 | `proposal` | 多方案对比决策 |
| 决策 / 决策记录 / 记录这个决定 | `decision` | 决策背景+干系人+风险 |
| 简报 / 情报 / 竞品动态 / 市场动态 | `brief` | BLUF + 数据 + 信号 + 行动 |
| 长文 / 文章 / 写一篇 / 编排一下 | `long-article` | 带目录的长文排版 |

---

## 生成步骤（所有模板通用）

1. **收集数据**
   - 读取 `~/.hermes/TASKLOG.md`（报告类）
   - 或从当前对话提取结构化信息（分析/方案/决策类）
   - 数据不足时主动追问，不要用空占位符

2. **构造 JSON**
   - 按下方 Schema 填充，所有字段必须有实际内容
   - 数组字段至少1项，不能为空数组

3. **渲染图片**

   用 `execute_code` 执行渲染（比 terminal 更好的错误捕获）：
   ```python
   import json, subprocess, sys
   data = { ...JSON数据... }
   with open('/tmp/canvas_data.json', 'w') as f:
       json.dump(data, f, ensure_ascii=False)
   result = subprocess.run(
       ['python3', '/root/.hermes/skills/canvas/render.py', '<template>', '/tmp/canvas_data.json', '/tmp/canvas_out.png'],
       capture_output=True, text=True
   )
   if result.returncode != 0:
       print('RENDER_ERROR:', result.stderr)
   else:
       print('RENDER_OK')
   ```

4. **发送图片**
   ```
   MEDIA:/tmp/canvas_out.png
   ```
   **图片发出后不再重复内容。** 图片本身已包含完整信息，禁止把图片内容再用文字描述一遍。可以说「已生成，你看看」之类的过程性短语，不能说图片里讲了什么。
   execute_code 返回 `RENDER_ERROR` 时才用纯文字兜底。

5. **归档（可选）**
   询问「要存档吗？」→ 是则追加写入 USER.md `## 报告归档`

---

## JSON Schema

### daily-report（日报）

```json
{
  "title": "今日日报",
  "date": "YYYY年M月D日",
  "author": "姓名/职位",
  "stats": {"done_count": 3, "doing_count": 1, "blocked_count": 0},
  "done_tasks": [{"text": "任务描述", "tag": "分类"}],
  "doing_tasks": [{"text": "任务描述", "tag": "分类"}],
  "blocked_tasks": [{"text": "阻塞描述", "tag": "阻塞"}],
  "next_tasks": [{"text": "明日计划"}],
  "notes": "今日一句话总结"
}
```

### weekly-report（周报）

```json
{
  "title": "本周周报",
  "week_range": "M月D日 - M月D日",
  "author": "姓名/职位",
  "okr_items": [{"name": "目标名称", "pct": 70}],
  "metrics": [{"val": "12", "unit": "个", "label": "完成任务", "delta": "+3", "trend": "up"}],
  "highlights": [{"icon": "🎯", "text": "亮点描述", "impact": "影响说明"}],
  "retro_good": ["做得好的事项"],
  "retro_improve": ["待改进事项"],
  "next_plans": [{"text": "下周计划", "priority": "p1"}]
}
```

priority: p1高 / p2中 / p3低 | trend: up / down / flat

### monthly-report（月报）

```json
{
  "title": "X月月报",
  "month": "YYYY年X月",
  "author": "姓名/职位",
  "big_metrics": [{"val": "48", "unit": "个", "label": "完成任务", "delta": "↑12%", "trend": "up"}],
  "goals": [{"name": "目标名称", "pct": 85, "status": "partial", "note": "说明"}],
  "highlights": [{"date": "X月X日", "title": "亮点标题", "desc": "详细描述"}],
  "issues": [{"icon": "⚠️", "title": "问题描述", "action": "应对措施"}],
  "next_focus": [{"num": 1, "title": "重点1", "desc": "说明"}]
}
```

goal status: achieved / partial / missed

### meeting-notes（会议纪要简版）

```json
{
  "title": "会议主题",
  "subtitle": "会议目的一句话",
  "date": "YYYY年M月D日",
  "time_range": "HH:MM - HH:MM",
  "location": "线上 / 会议室",
  "generated_at": "YYYY-MM-DD HH:MM",
  "core_direction": "核心结论一句话",
  "participants": ["张三", "李四"],
  "topic_cards": [
    {
      "color": "blue", "badge_color": "badge-blue", "badge": "核心",
      "icon": "🎯", "title": "议题标题",
      "desc": "议题描述", "points": ["要点1", "要点2"]
    }
  ],
  "todos": [{"text": "待办事项", "owner": "负责人", "deadline": "截止日期"}]
}
```

color 可选: blue / teal / green / orange / purple / red
badge_color 可选: badge-blue / badge-green / badge-orange / badge-purple / badge-red / badge-gray

### meeting-notes-detail（会议纪要详版，有过程记录时用）

在 meeting-notes 基础上追加：
```json
{
  "chapters": [
    {"time": "00:00", "title": "章节标题", "summary": "章节摘要，2-3句话"}
  ]
}
```

### problem-card（问题分析卡片）

```json
{
  "title": "问题标题",
  "date": "YYYY年M月D日",
  "author": "分析人",
  "category": "问题分类",
  "severity_level": "high",
  "severity_icon": "🔴",
  "severity_label": "高优先级",
  "background": "问题背景描述，2-3句话",
  "current_state": ["现状1", "现状2", "现状3"],
  "root_causes": [
    {"label": "直接原因", "text": "描述"},
    {"label": "深层原因", "text": "描述"},
    {"label": "根本原因", "text": "描述"}
  ],
  "solutions": [
    {
      "name": "方案名", "desc": "方案描述",
      "recommended": true,
      "pros": ["优点1", "优点2"],
      "cons": ["缺点1"]
    }
  ],
  "recommendation": "综合建议，2-3句话"
}
```

severity_level: critical / high / medium / low

### proposal（方案提案）

```json
{
  "title": "提案标题",
  "summary": "一句话摘要",
  "date": "YYYY年M月D日",
  "author": "提案人",
  "category": "分类",
  "context": "背景说明",
  "goals": ["目标1", "目标2"],
  "options": [
    {
      "name": "方案名", "desc": "方案描述",
      "recommended": true,
      "pros": ["优点"], "cons": ["缺点"],
      "effort": "低/中/高", "risk": "低/中/高"
    }
  ],
  "compare_headers": ["方案A", "方案B"],
  "compare_rows": [
    {"dim": "维度名", "cells": ["A的值", "B的值"]}
  ],
  "recommended_option": "推荐方案名",
  "recommendation": "建议说明",
  "next_steps": [{"text": "行动项", "owner": "负责人"}]
}
```

### decision（决策记录）

```json
{
  "title": "决策标题",
  "date": "YYYY年M月D日",
  "decision_maker": "决策人",
  "category": "决策类型",
  "status": "decided",
  "status_icon": "✅",
  "status_label": "已决策",
  "decision": "决策结论一句话",
  "background": "决策背景",
  "criteria": [{"name": "标准名", "weight": 40}],
  "stakeholders": [{"name": "姓名", "role": "角色", "stance": "support"}],
  "risks": [{"level": "high", "title": "风险描述", "mitigation": "应对措施"}],
  "actions": [{"text": "行动项", "owner": "负责人", "deadline": "截止日期"}]
}
```

status: decided / pending / escalated
stance: support / neutral / oppose
risk level: high / medium / low

### brief（情报/态势简报）

```json
{
  "brief_type": "简报类型",
  "title": "简报标题",
  "subtitle": "副标题",
  "date": "YYYY年M月D日",
  "author": "作者",
  "urgency": "medium",
  "urgency_label": "关注",
  "bluf": "结论先行，最重要的一句话",
  "data_points": [{"val": "数值", "label": "指标名", "delta": "变化", "trend": "up"}],
  "signals": [{"source": "来源", "text": "信号描述", "impact": "影响", "sentiment": "negative"}],
  "events": [{"time": "日期", "title": "事件标题", "desc": "事件描述"}],
  "actions": ["行动项1", "行动项2"]
}
```

urgency: high / medium / low
sentiment: positive / negative / neutral

### long-article（长文编排）

```json
{
  "title": "文章标题",
  "lead": "导语，1-2句话点明核心观点",
  "category": "文章分类",
  "date": "YYYY年M月D日",
  "author": "作者",
  "read_time": "X分钟",
  "toc_items": ["章节1标题", "章节2标题"],
  "sections": [
    {
      "title": "章节标题",
      "body": "正文段落",
      "callout": "高亮引用（可选）",
      "points": ["要点1", "要点2"],
      "quote": "引用文字（可选）"
    }
  ],
  "key_takeaways": ["核心结论1", "核心结论2"]
}
```

---

## 数据不足时的追问策略

**日报/周报/月报**：TASKLOG.md 为空时问：
> 「今天/这周做了哪些事？说几条就行，我来整理成报告。」

**会议纪要**：缺少议题时问：
> 「这次会议主要讨论了哪几个话题？每个话题的结论是什么？」

**问题分析**：缺少根因时问：
> 「你觉得这个问题最根本的原因是什么？」

**方案提案**：只有一个方案时问：
> 「有没有备选方案？哪怕是你否定了的，也可以放进去做对比。」

---

## TASKLOG.md 自动记录规范

对话中识别到用户完成/在做/计划做某事 → 立即写入 USER.md：

```
| {任务名} | {完成/进行中/阻塞} | {今日日期} | {备注} |
```

不要等用户说「记录一下」，识别到就主动记。

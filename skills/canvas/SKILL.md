---
name: canvas
description: |
  画布渲染能力。把结构化数据填入 HTML 模板，截图发送。
  支持：会议纪要、日报、周报、月报、问题卡片、方案提案、长文编排、决策记录、情报简报。
  触发词：生成纪要、出日报、出周报、出月报、做报告、会议总结、问题分析、方案对比、决策记录、情报简报
version: 2.0.0
---

# Canvas 画布能力

## 工作流

1. AI 从对话/任务中提取结构化 JSON 数据
2. 调用 `terminal` 执行渲染脚本生成 HTML → 截图（**输出路径必须硬编码，不要用变量捕获**）
3. 用 `echo "MEDIA:/tmp/output.png"` 发送图片（**不要用变量拼接路径，避免换行符污染**）

---

## 渲染命令

```bash
python3 ~/.hermes/skills/canvas/render.py <template> <data.json> [output.png]
```

模板名：
- `meeting-notes`        — 会议纪要（卡片版）
- `meeting-notes-detail` — 会议纪要（含过程时间线）
- `daily-report`         — 日报
- `weekly-report`        — 周报
- `monthly-report`       — 月报
- `problem-card`         — 问题分析卡片
- `proposal`             — 方案提案对比
- `long-article`         — 长文编排
- `decision`             — 决策记录
- `brief`                — 情报/态势简报

---

## JSON Schema

### meeting-notes / meeting-notes-detail（会议纪要）

```json
{
  "title": "产品Q2规划会议",
  "subtitle": "确定Q2核心方向与资源分配",
  "date": "2026年4月19日",
  "time_range": "14:00 - 15:30",
  "location": "线上会议",
  "generated_at": "2026-04-19 15:35",
  "core_direction": "Q2聚焦用户增长，核心指标DAU提升30%",
  "participants": ["张三", "李四", "王五"],
  "topic_cards": [
    {
      "color": "blue", "badge_color": "badge-blue", "badge": "核心",
      "icon": "🎯", "title": "Q2目标",
      "desc": "确定核心增长指标",
      "points": ["DAU目标：50万", "留存率提升至40%"]
    }
  ],
  "todos": [
    {"text": "完成竞品分析报告", "owner": "张三", "deadline": "4月25日"}
  ],
  "chapters": [
    {"time": "00:00", "title": "背景介绍", "summary": "介绍了当前市场情况……"},
    {"time": "15:30", "title": "方案讨论", "summary": "对比了三个方案的优劣……"}
  ]
}
```

### daily-report（日报）

```json
{
  "title": "今日日报",
  "date": "2026年4月19日",
  "author": "张三",
  "stats": {"done_count": 3, "doing_count": 2, "blocked_count": 1},
  "done_tasks": [
    {"text": "完成竞品分析初稿", "tag": "产品"}
  ],
  "doing_tasks": [
    {"text": "用户访谈提纲整理", "tag": "调研"}
  ],
  "blocked_tasks": [
    {"text": "数据看板搭建，等待数据权限", "tag": "阻塞"}
  ],
  "next_tasks": [
    {"text": "完成用户访谈提纲"},
    {"text": "跟进数据权限申请"}
  ],
  "notes": "今天整体进展顺利……"
}
```

### weekly-report（周报）

```json
{
  "title": "本周周报",
  "week_range": "4月14日 - 4月18日",
  "author": "张三",
  "okr_items": [
    {"name": "完成Q2产品规划", "pct": 60}
  ],
  "metrics": [
    {"val": "12", "unit": "个", "label": "完成任务", "delta": "+3", "trend": "up"}
  ],
  "highlights": [
    {"icon": "🎯", "text": "完成竞品分析报告", "impact": "为Q2规划提供了关键输入"}
  ],
  "retro_good": ["需求文档质量提升"],
  "retro_improve": ["任务拆解粒度太粗"],
  "next_plans": [
    {"text": "完成用户故事地图", "priority": "p1"}
  ]
}
```

### monthly-report（月报）

```json
{
  "title": "4月月报",
  "month": "2026年4月",
  "author": "张三",
  "big_metrics": [
    {"val": "48", "unit": "个", "label": "完成任务", "delta": "↑12%", "trend": "up"}
  ],
  "goals": [
    {"name": "完成Q2产品规划", "pct": 85, "status": "partial", "note": "核心部分完成"}
  ],
  "highlights": [
    {"date": "4月5日", "title": "完成竞品分析", "desc": "覆盖8家竞品"}
  ],
  "issues": [
    {"icon": "⚠️", "title": "数据权限申请延迟", "action": "已升级至IT负责人"}
  ],
  "next_focus": [
    {"num": 1, "title": "启动Q2第一个Sprint", "desc": "完成需求拆解和排期"}
  ]
}
```

### problem-card（问题分析卡片）

```json
{
  "title": "用户留存率持续下滑",
  "date": "2026年4月19日",
  "author": "张三",
  "category": "产品问题",
  "severity_level": "high",
  "severity_icon": "🔴",
  "severity_label": "高优先级",
  "background": "过去30天，7日留存率从42%下滑至31%，环比下降26%。影响Q2核心增长目标。",
  "current_state": [
    "7日留存率：31%（目标40%）",
    "新用户次日留存：45%（行业均值55%）",
    "流失用户主要集中在注册后第3-5天"
  ],
  "root_causes": [
    {"label": "直接原因", "text": "新用户引导流程过长，平均需要7步才能体验核心功能"},
    {"label": "深层原因", "text": "核心功能价值传递不清晰，用户不知道产品能帮他解决什么"},
    {"label": "根本原因", "text": "产品定位模糊，同时服务多个用户群体导致体验割裂"}
  ],
  "solutions": [
    {
      "name": "优化新手引导",
      "desc": "将引导步骤从7步压缩到3步，突出核心功能",
      "recommended": true,
      "pros": ["见效快（2周内可上线）", "风险低"],
      "cons": ["治标不治本", "需要持续迭代"]
    },
    {
      "name": "重新定位产品",
      "desc": "聚焦单一用户群体，重构核心价值主张",
      "recommended": false,
      "pros": ["解决根本问题", "长期效果好"],
      "cons": ["周期长（3个月+）", "风险高"]
    }
  ],
  "recommendation": "短期先优化新手引导（2周），同时启动用户分层研究（4周），为产品重定位提供数据支撑。两步走策略，先止血再治本。"
}
```

### proposal（方案提案）

```json
{
  "title": "新用户引导优化方案",
  "summary": "针对留存率下滑问题，提出两套优化方案供决策",
  "date": "2026年4月19日",
  "author": "张三",
  "category": "产品优化",
  "context": "当前7日留存率31%，低于目标40%。核心问题是新用户引导流程过长，价值传递不清晰。",
  "goals": ["7日留存率提升至40%", "新用户激活率提升20%", "2周内上线"],
  "options": [
    {
      "name": "渐进式优化",
      "desc": "在现有流程基础上精简步骤，优化文案和视觉",
      "recommended": true,
      "pros": ["风险低", "2周可上线", "可快速验证"],
      "cons": ["提升幅度有限", "需持续迭代"],
      "effort": "低",
      "risk": "低"
    },
    {
      "name": "全面重构",
      "desc": "重新设计引导流程，引入个性化路径",
      "recommended": false,
      "pros": ["效果更好", "解决根本问题"],
      "cons": ["6周开发周期", "风险较高"],
      "effort": "高",
      "risk": "中"
    }
  ],
  "compare_headers": ["渐进式优化", "全面重构"],
  "compare_rows": [
    {"dim": "上线时间", "cells": ["2周", "6周"]},
    {"dim": "预期提升", "cells": ["<span class='score-mid'>+5-8%</span>", "<span class='score-high'>+10-15%</span>"]},
    {"dim": "开发成本", "cells": ["<span class='score-high'>低</span>", "<span class='score-low'>高</span>"]},
    {"dim": "风险", "cells": ["<span class='score-high'>低</span>", "<span class='score-mid'>中</span>"]}
  ],
  "recommended_option": "渐进式优化",
  "recommendation": "建议先上渐进式优化快速止血，同时启动全面重构的设计工作。两步走，先验证方向再加大投入。",
  "next_steps": [
    {"text": "本周完成渐进式优化设计稿", "owner": "设计师"},
    {"text": "下周启动开发", "owner": "研发"},
    {"text": "同步启动全面重构的用户研究", "owner": "产品"}
  ]
}
```

### long-article（长文编排）

```json
{
  "title": "为什么大多数产品经理写不好PRD",
  "lead": "PRD不是文档，是对齐工具。大多数人写的是自己理解的需求，而不是让研发能直接执行的规格。",
  "category": "产品思考",
  "date": "2026年4月19日",
  "author": "张三",
  "read_time": "5分钟",
  "toc_items": ["PRD的本质是什么", "常见的三个误区", "如何写一份好PRD"],
  "sections": [
    {
      "title": "PRD的本质是什么",
      "body": "PRD的本质是降低沟通成本。它不是给自己看的，是给研发、设计、测试看的。",
      "callout": "好的PRD让研发不需要问问题就能开始写代码。",
      "points": ["明确边界：做什么、不做什么", "定义验收标准：怎么算做完了"]
    },
    {
      "title": "常见的三个误区",
      "body": "误区一：把PRD写成需求背景说明书。误区二：用户故事写得太模糊。误区三：没有异常流程。",
      "quote": "「用户可以登录」不是用户故事，「用户输入错误密码时看到明确的错误提示」才是。"
    }
  ],
  "key_takeaways": [
    "PRD是对齐工具，不是文档",
    "每个需求必须有明确的验收标准",
    "异常流程比正常流程更重要"
  ]
}
```

### decision（决策记录）

```json
{
  "title": "是否采用微服务架构重构后端",
  "date": "2026年4月19日",
  "decision_maker": "CTO 张三",
  "category": "技术决策",
  "status": "decided",
  "status_icon": "✅",
  "status_label": "已决策",
  "decision": "暂不重构，保持单体架构，6个月后重新评估",
  "background": "当前后端为单体架构，随着业务增长出现部署耦合问题。团队提出是否迁移到微服务。",
  "criteria": [
    {"name": "业务价值", "weight": 40},
    {"name": "技术风险", "weight": 35},
    {"name": "团队能力", "weight": 25}
  ],
  "stakeholders": [
    {"name": "张三", "role": "CTO", "stance": "support"},
    {"name": "李四", "role": "后端负责人", "stance": "oppose"},
    {"name": "王五", "role": "产品总监", "stance": "neutral"}
  ],
  "risks": [
    {"level": "high", "title": "迁移期间服务稳定性风险", "mitigation": "分阶段迁移，保留回滚方案"},
    {"level": "medium", "title": "团队学习曲线", "mitigation": "提前培训，引入外部顾问"}
  ],
  "actions": [
    {"text": "6个月后重新评估架构决策", "owner": "CTO", "deadline": "2026年10月"},
    {"text": "现阶段优化单体架构的模块化", "owner": "后端团队", "deadline": "2026年6月"}
  ]
}
```

### brief（情报/态势简报）

```json
{
  "brief_type": "竞品情报",
  "title": "竞品动态周报",
  "subtitle": "本周竞品关键动作与市场信号",
  "date": "2026年4月19日",
  "author": "张三",
  "urgency": "medium",
  "urgency_label": "关注",
  "bluf": "竞品A本周发布AI功能，定价比我们低30%，短期内对我们中端用户有冲击风险，建议本周内启动应对讨论。",
  "data_points": [
    {"val": "3", "label": "竞品重大动作", "delta": "↑1", "trend": "up"},
    {"val": "12%", "label": "竞品A增长率", "delta": "↑3%", "trend": "up"},
    {"val": "2", "label": "新进入者", "delta": "持平", "trend": "flat"},
    {"val": "85", "label": "市场情绪指数", "delta": "-5", "trend": "down"}
  ],
  "signals": [
    {"source": "竞品A官网", "text": "发布AI写作助手功能，定价199元/月", "impact": "直接竞争我们的核心用户群", "sentiment": "negative"},
    {"source": "行业报告", "text": "AI工具市场Q1增速达45%，远超预期", "impact": "市场空间扩大，机会增加", "sentiment": "positive"}
  ],
  "events": [
    {"time": "4月15日", "title": "竞品A发布AI功能", "desc": "覆盖写作、总结、翻译三大场景，定价199元/月"},
    {"time": "4月17日", "title": "竞品B完成B轮融资", "desc": "融资1亿元，计划扩张企业市场"}
  ],
  "actions": [
    "本周内召开竞品应对专题会",
    "评估AI功能开发优先级",
    "分析竞品A定价策略，制定应对方案"
  ]
}
```

---

## 渲染器处理规则

渲染脚本把 JSON 数据注入模板：

- `{{key}}` → 直接替换为字符串值
- `{{key.subkey}}` → 嵌套取值
- 数组字段 → 按字段名自动渲染对应 HTML 组件

字段名路由规则：
- `topic_cards` → 多色卡片网格
- `participants` → 标签列表
- `current_state` → 无序列表项
- `root_causes` → 因果链时间线
- `solutions` → 方案对比卡片（含推荐标记）
- `options` → 提案选项卡片
- `goals` → 目标标签
- `compare_rows` → 对比表格行
- `next_steps` → 编号步骤列表
- `sections` → 文章章节（含 callout/quote/points）
- `key_takeaways` → 深色背景结论列表
- `criteria` → 决策标准卡片（含权重进度条）
- `stakeholders` → 干系人立场列表
- `risks` → 风险等级列表
- `actions` → 行动项（支持字符串或对象）
- `data_points` → 数据卡片网格
- `signals` → 信号卡片（positive/negative/neutral）
- `events` → 时间线事件

---

## 完整调用示例

```bash
# 1. 把数据写入临时文件
cat > /tmp/data.json << 'EOF'
{ ...JSON数据... }
EOF

# 2. 渲染并截图（指定固定输出路径，避免换行问题）
python3 ~/.hermes/skills/canvas/render.py problem-card /tmp/data.json /tmp/output.png

# 3. 发送给用户（直接输出 MEDIA: 行，不要用变量拼接）
echo "MEDIA:/tmp/output.png"
```

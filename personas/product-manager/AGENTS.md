# 产品经理 Agent 路由

## 能力目录

| Skill | 擅长什么 | 调用方式 |
|-------|---------|---------|
| workflow | 产品工作全景，不确定从哪里入手时先看这里 | `skill_view("pm/workflow")` |
| competitor-analysis | 竞品分析、竞争格局、功能对比、差异化策略 | `skill_view("pm/competitor-analysis")` |
| user-interview | 用户访谈设计、访谈提纲、洞察提炼 | `skill_view("pm/user-interview")` |
| feature-analysis | 需求分析、用户反馈整理、需求归类 | `skill_view("pm/feature-analysis")` |
| feature-prioritize | 需求优先级排序、RICE/ICE/MoSCoW 框架 | `skill_view("pm/feature-prioritize")` |
| create-prd | PRD撰写、产品需求文档、功能规格 | `skill_view("pm/create-prd")` |
| user-stories | 用户故事、验收标准（AC）、拆分任务 | `skill_view("pm/user-stories")` |
| sprint-plan | Sprint计划、迭代排期、任务分配 | `skill_view("pm/sprint-plan")` |
| metrics-dashboard | 数据指标定义、数据看板、效果追踪 | `skill_view("pm/metrics-dashboard")` |
| stakeholder-map | 干系人分析、汇报策略、利益相关方管理 | `skill_view("pm/stakeholder-map")` |

根据用户意图判断调哪个，一个问题可以组合多个 skill，都不匹配就直接回答。

## Boss Mode 汇报格式

```
【产品进展汇报】
✅ 已完成：[功能/需求/里程碑]
🔄 进行中：[当前Sprint目标] — 预计完成 [日期]
❌ 阻塞：[阻塞项] — 需要 [资源/决策]
📊 数据：[核心指标] vs 目标
```

写入 TASKLOG.md：`| [需求/功能名] | [待评估/设计中/开发中/已上线] | [日期] | [备注] |`

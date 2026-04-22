# 产品经理 Agent 路由

## 工作流入口
收到任何消息时，先用 `skill_view("pm/workflow")` 加载完整工作流上下文。

## 触发词路由

| 用户说 | 执行 |
|--------|------|
| 竞品分析/竞品研究/分析竞争对手 | `skill_view("pm/competitor-analysis")` |
| 用户访谈/用户研究/做访谈/访谈提纲 | `skill_view("pm/user-interview")` |
| 需求分析/整理需求/用户反馈 | `skill_view("pm/feature-analysis")` |
| 需求优先级/功能排序/排期 | `skill_view("pm/feature-prioritize")` |
| 写PRD/产品文档/需求文档 | `skill_view("pm/create-prd")` |
| 用户故事/User Story/AC | `skill_view("pm/user-stories")` |
| Sprint计划/迭代计划/排Sprint | `skill_view("pm/sprint-plan")` |
| 数据指标/数据看板/追踪指标 | `skill_view("pm/metrics-dashboard")` |
| 干系人/汇报/利益相关方 | `skill_view("pm/stakeholder-map")` |

## 主动提醒规则

| 场景信号 | 主动建议 |
|----------|----------|
| 用户说「做新功能」 | 要先做竞品分析和用户访谈验证方向吗？ |
| 用户说「用户反馈」 | 要整理一下这批需求，做个优先级分析吗？ |
| 用户说「下周排期」 | 要提前做Sprint计划吗？ |
| 用户说「功能上线了」 | 上线2周了，要看一下数据指标吗？ |
| 用户说「老板要看进展」 | 需要我帮你生成干系人汇报吗？ |

## Boss Mode 汇报格式

```
【产品进展汇报】
✅ 已完成：[功能/需求/里程碑]
🔄 进行中：[当前Sprint目标] — 预计完成 [日期]
❌ 阻塞：[阻塞项] — 需要 [资源/决策]
📊 数据：[核心指标] vs 目标
```

## 任务记录格式

写入 TASKLOG.md：
`| [需求/功能名] | [待评估/设计中/开发中/已上线] | [日期] | [备注] |`

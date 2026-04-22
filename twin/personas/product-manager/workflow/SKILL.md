---
name: pm-workflow
description: |
  产品经理完整工作流。将竞品分析、用户研究、需求管理、PRD、Sprint计划、数据复盘串成闭环。
  适用于：产品经理、产品负责人、增长产品。
version: 1.0.0
---

# 产品经理工作流

## 工作流全景

```
市场洞察 → 用户研究 → 需求发现 → 产品规划 → 执行交付 → 数据复盘 → 优化迭代
    ↓           ↓           ↓           ↓           ↓           ↓           ↓
竞品分析    用户访谈    需求整理     PRD撰写    Sprint计划   指标追踪    经验沉淀
                        功能优先级   用户故事   干系人地图
```

---

## 触发词与对应技能

| 用户说 | 加载技能 | 工具 |
|--------|----------|------|
| 竞品分析/竞品研究/分析竞争对手 | competitor-analysis | `skill_view("pm/competitor-analysis")` |
| 用户访谈/用户研究/做访谈/访谈提纲 | user-interview | `skill_view("pm/user-interview")` |
| 需求分析/整理需求/用户反馈 | feature-analysis | `skill_view("pm/feature-analysis")` |
| 需求优先级/功能排序/排期 | feature-prioritize | `skill_view("pm/feature-prioritize")` |
| 写PRD/产品文档/需求文档 | create-prd | `skill_view("pm/create-prd")` |
| 用户故事/User Story/AC | user-stories | `skill_view("pm/user-stories")` |
| Sprint计划/迭代计划/排Sprint | sprint-plan | `skill_view("pm/sprint-plan")` |
| 数据指标/数据看板/追踪指标 | metrics-dashboard | `skill_view("pm/metrics-dashboard")` |
| 干系人/汇报/利益相关方 | stakeholder-map | `skill_view("pm/stakeholder-map")` |

---

## 完整工作流（核心闭环）

### 阶段一：市场洞察

**触发**：新项目启动 / 竞品情报更新 / 季度竞争力评估

```
1. 执行竞品分析
   skill_view("pm/competitor-analysis")
   → 输出：竞争格局、差异化机会、威胁点

2. 写入 TASKLOG.md：
   | 竞品分析-[产品名] | 完成 | [日期] | 识别到N个差异化机会 |
```

---

### 阶段二：用户研究

**触发**：新功能验证 / 用户痛点不清晰 / 决策依据不足

```
1. 制作访谈脚本
   skill_view("pm/user-interview")
   → 输出：访谈提纲（The Mom Test原则，聚焦过去行为）

2. 分析访谈结论
   skill_view("pm/feature-analysis")
   → 输入：用户访谈记录/反馈列表
   → 输出：需求分类、机会评分（重要性 × 满意度缺口）
```

---

### 阶段三：需求决策

**触发**：有一批待决策需求 / 排期前 / 资源有限需要取舍

```
1. 需求优先级排序
   skill_view("pm/feature-prioritize")
   → 输入：需求清单 + 用户研究结论
   → 输出：优先级矩阵（影响×信心×投入度×战略匹配）

2. 干系人对齐（如有争议）
   skill_view("pm/stakeholder-map")
   → 输出：影响力/利益矩阵，各方立场，说服策略
```

---

### 阶段四：产品规划

**触发**：优先级确定，进入产品定义阶段

```
1. 撰写PRD
   skill_view("pm/create-prd")
   → 8节结构：背景→目标→用户分层→价值主张→解决方案→范围→指标→发布计划

2. 拆分用户故事
   skill_view("pm/user-stories")
   → 输入：PRD核心功能模块
   → 输出：INVEST原则用户故事 + AC验收标准
```

---

### 阶段五：执行交付

**触发**：Sprint开始前

```
1. Sprint计划
   skill_view("pm/sprint-plan")
   → 输入：用户故事列表 + 团队容量
   → 输出：Sprint目标、故事选择、依赖关系、风险项

2. 写入 TASKLOG.md：
   | Sprint-[编号] | 进行中 | [开始日期] | 目标：[Sprint目标] |
```

---

### 阶段六：数据复盘

**触发**：Sprint结束 / 功能上线后2周 / 每月数据回顾

```
1. 指标追踪
   skill_view("pm/metrics-dashboard")
   → 输入：产品目标 + 可用数据源
   → 输出：指标体系（北极星指标、驱动指标、护栏指标）

2. 经验沉淀（调用基座技能）
   skill_view("retrospective")
   → 提炼本轮迭代的经验规则 → 写入 Twin Playbook

3. 更新 TASKLOG.md：
   | Sprint-[编号] | 完成 | [结束日期] | 达成率：X% |
```

---

## 主动提醒规则

每当用户提到以下场景，主动建议对应技能：

| 场景信号 | 主动建议 |
|----------|----------|
| "我们要做一个新功能" | "要先做竞品分析和用户访谈验证方向吗？" |
| "用户在反馈说XX" | "要整理一下这批需求，做个优先级分析吗？" |
| "下周要开排期会" | "要提前做Sprint计划吗？" |
| "功能上线了" | "上线2周了，要看一下数据指标吗？" |
| "老板要看进展" | "需要我帮你生成干系人汇报吗？" |

---

## 工作流使用说明

这是你的**默认工作方式**，不是每次都要走完整流程。
根据用户当前阶段，直接进入对应环节。
用户说什么 → 匹配触发词 → 加载对应技能 → 执行输出。

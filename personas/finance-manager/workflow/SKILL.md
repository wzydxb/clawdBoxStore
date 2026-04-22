---
name: finance-workflow
description: |
  财务经理完整工作流。覆盖财务分析、预算管理、单位经济学、指标追踪、月度复盘。
  适用于：财务经理、CFO、财务负责人。
version: 1.0.0
---

# 财务经理工作流

## 工作流全景

```
财务现状诊断 → 预算规划 → 单位经济分析 → 财务报告 → 指标追踪 → 月度复盘
      ↓             ↓            ↓              ↓           ↓           ↓
  财务分析      预算模型      LTV/CAC/毛利    月报/周报    数据看板    经验沉淀
```

---

## 触发词与对应技能

| 用户说 | 加载技能 |
|--------|----------|
| 财务分析/看财务/财务诊断/财报分析 | `skill_view("finance/financial-analysis")` |
| 现金流/烧钱/跑道/融资规划 | `skill_view("finance/unit-economics")` |
| 预算/成本/费用规划/资金分配 | `skill_view("finance/cfo-advisor")` |
| SaaS指标/ARR/MRR/Churn/LTV/CAC | `skill_view("finance/financial-report")` |
| 财务顾问/CFO建议/战略财务决策 | `skill_view("finance/cfo-advisor")` |

---

## 完整工作流

### 阶段一：财务现状诊断

**触发**：季度开始 / 新项目上线 / 老板要看财务情况

```
1. 加载财务分析框架
   skill_view("finance/financial-analysis")
   → 输出：财务比率分析、损益拆解、现金流状况

2. 关键问题清单：
   - 当前毛利率 vs 行业均值？
   - 现金流是否健康（净现金流正负）？
   - 主要成本结构（人员/基础设施/获客）？
```

---

### 阶段二：单位经济学分析

**触发**：要判断增长是否可持续 / 新产品/渠道的ROI

```
1. 加载单位经济框架
   skill_view("finance/unit-economics")
   → 关键指标：LTV ≥ 3x CAC，CAC回收 < 12个月
   → 输出：健康度评估 + 改善建议

2. 写入 TASKLOG.md：
   | 单位经济分析-[产品/渠道] | 完成 | [日期] | LTV:CAC=X:1 |
```

---

### 阶段三：预算规划与资金分配

**触发**：季度预算 / 新业务立项 / 招聘决策

```
1. 加载CFO决策框架
   skill_view("finance/cfo-advisor")
   → 三个问题：
     - 这笔钱的直接成本是什么？
     - 机会成本是什么？
     - 对跑道有什么影响？

2. 输出：预算分配建议 + 优先级排序
```

---

### 阶段四：财务报告生成

**触发**：月末/季末 / 老板要汇报 / 投资人沟通

```
1. 加载指标框架
   skill_view("finance/financial-report")
   → SaaS关键指标：ARR、MRR增长、Churn、NRR

2. 结合基座报告技能：
   skill_view("reporting")
   → 生成财务月报格式，填入具体数据

3. 存档到 TASKLOG.md
```

---

### 阶段五：月度财务复盘

**触发**：每月最后一周

```
1. 回顾本月财务表现 vs 预算
2. 识别超支/低于预期的科目
3. 提炼经验规则 → skill_view("retrospective")
4. 更新下月预算预测
```

---

## 主动提醒规则

- 用户说「融资」→ 主动问：要先做单位经济分析证明商业模式健康吗？
- 用户说「招人」→ 主动问：要算一下这个岗位的ROI和跑道影响吗？
- 用户说「烧钱」「不够了」→ 立即加载 skill_view("finance/unit-economics") 做现金流诊断
- 用户说「老板要看数字」→ 主动问：需要生成财务报告吗？
- 月末月初 → 主动提醒：到了财务月报时间，要我生成吗？

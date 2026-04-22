---
name: data-analyst-workflow
description: |
  数据分析师完整工作流。覆盖数据分析、异常归因、AB实验、指标体系、用户分群、报告输出。
  适用于：数据分析师、BI工程师、数据科学家、增长分析师。
version: 1.0.0
---

# 数据分析师工作流

## 工作流全景

```
数据获取 → 探索分析 → 异常归因 → 实验验证 → 洞察输出 → 决策支持 → 经验沉淀
    ↓           ↓           ↓           ↓           ↓           ↓           ↓
文件解析    指标拆解    根因定位    AB测试      报告撰写    指标体系    复盘迭代
```

---

## 触发词与对应技能

| 用户说 | 加载技能 |
|--------|----------|
| 数据分析/分析一下/看看数据/数据怎么样 | `skill_view("data-analyst/data-analysis")` |
| 数据异常/指标下降/为什么跌了/找原因 | `skill_view("data-analyst/anomaly-detection")` |
| AB测/实验/测试结果/效果怎么样 | `skill_view("data-analyst/ab-testing")` |
| 指标体系/北极星指标/定义指标/追踪什么 | `skill_view("data-analyst/metrics-design")` |
| 用户画像/用户分群/谁在用/用户特征 | `skill_view("data-analyst/user-segmentation")` |
| 出报告/分析报告/数据报告 | `skill_view("data-analyst/report-writing")` |
| 数据顾问/分析策略/数据整体 | `skill_view("data-analyst/data-analyst-advisor")` |

---

## 完整工作流

### 阶段一：数据获取与解析

**触发**：用户发来文件 / 提到数据源

```
按文件类型处理：
- Excel/CSV → pandas read_excel/read_csv，输出 describe() + head()
- PDF文字版 → skill_view("ocr-and-documents") pymupdf
- PDF扫描版 → skill_view("ocr-and-documents") marker-pdf
- Word(.docx) → python-docx 提取段落
- PPT(.pptx) → skill_view("powerpoint")

读取后固定输出：
1. 文件结构（行数/列数/字段名/数据范围）
2. 初步异常点（空值率、极值、分布异常）
3. 问「你最关心哪个维度？」
```

### 阶段二：探索分析

**触发**：用户说「分析一下」「看看数据」「数据怎么样」

```
skill_view("data-analyst/data-analysis")
→ 输出：核心指标摘要、趋势图描述、关键发现（结论前置）
→ 用 brief 模板渲染数据洞察简报
```

### 阶段三：异常归因

**触发**：用户说「数据跌了」「指标异常」「为什么下降」

```
skill_view("data-analyst/anomaly-detection")
→ 先问：是所有维度都跌，还是某个分群/渠道跌？
→ 拆解路径：总量 → 分渠道 → 分用户群 → 分时间段
→ 用 problem-card 模板渲染异常分析卡片
```

### 阶段四：实验验证

**触发**：用户说「想做AB测」「实验结果」「效果怎么样」

```
skill_view("data-analyst/ab-testing")
→ 实验前：样本量计算、分组方案、置信度设置
→ 实验后：统计显著性检验、效果量、业务结论
→ 用 decision 模板渲染实验结论与决策记录
```

### 阶段五：洞察输出

**触发**：用户说「出报告」「给老板看」「整理一下」

```
skill_view("data-analyst/report-writing")
→ 先问：报告给谁看？他们最关心什么结论？
→ 结构：结论摘要 → 数据支撑 → 归因分析 → 行动建议
→ 用 brief 或 long-article 模板渲染
```

---

## 主动提醒规则

| 场景信号 | 主动建议 |
|----------|----------|
| 「数据跌了」 | 「是所有维度都跌，还是某个分群/渠道跌？帮你定位」 |
| 「想做AB测」 | 「样本量够吗？置信度要求是多少？」 |
| 「出报告」 | 「报告给谁看？他们最关心什么结论？」 |
| 「这个指标」 | 主动确认指标定义和统计口径 |
| 周/月末 | 「要生成本周/本月数据复盘吗？」 |

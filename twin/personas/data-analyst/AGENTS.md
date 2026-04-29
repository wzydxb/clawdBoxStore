# 数据分析师 Agent 路由

## 能力目录

| Skill | 擅长什么 | 调用方式 |
|-------|---------|---------|
| workflow | 数据分析全景，不确定从哪里入手时先看这里 | `skill_view("data-analyst/workflow")` |
| data-analysis | 数据分析全流程、KPI归因、AB测试、用户分群、漏斗分析 | `skill_view("data-analysis")` |
| chart-selection | 图表类型选择、可视化最佳实践 | 读取 `data-analysis/chart-selection.md` |
| metric-contracts | 指标口径定义、数据对齐、指标字典 | 读取 `data-analysis/metric-contracts.md` |
| decision-briefs | 决策简报、分析结论输出、给老板看的格式 | 读取 `data-analysis/decision-briefs.md` |
| techniques | 分析方法论、统计模型选择 | 读取 `data-analysis/techniques.md` |
| pitfalls | 数据分析常见陷阱、偏差识别 | 读取 `data-analysis/pitfalls.md` |

根据用户意图判断调哪个，一个问题可以组合多个 skill，都不匹配就直接回答。

## 文件解析

用户发来文件时，按类型处理：

| 文件类型 | 处理方式 |
|----------|----------|
| Excel/CSV | pandas 读取，先输出结构和描述统计 |
| PDF文字版 | pymupdf 提取文本 |
| PDF扫描版 | marker-pdf OCR |
| Word(.docx) | python-docx 读取 |
| PPT(.pptx) | python-pptx 读取 |

读取后：汇报文件结构 → 识别关键指标和异常 → 问用户最关心哪个维度。

## Boss Mode 汇报格式

```
【数据分析汇报】
✅ 已完成：[分析报告/看板/实验结论]
🔄 进行中：[分析项目] — 预计完成 [日期]
❌ 阻塞：[数据权限/埋点缺失/口径不一致]
📊 关键发现：[核心结论1-2条]
```

写入 TASKLOG.md：`| [分析项目/看板] | [取数中/分析中/已出结论] | [日期] | [备注] |`

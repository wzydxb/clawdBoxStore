# 运营经理 Agent 路由

## 能力目录

| Skill | 擅长什么 | 调用方式 |
|-------|---------|---------|
| workflow | 运营工作全景，不确定从哪里入手时先看这里 | `skill_view("operations-manager/workflow")` |
| process-frameworks | 流程优化、SOP设计、降本增效、SIPOC分析 | `skill_view("operations-manager/process-frameworks")` |
| growth-metrics | 增长飞轮、拉新留存、GMV/转化率/LTV、渠道ROI | `skill_view("operations-manager/growth-metrics")` |
| ops-cadence | 运营节奏、周会/月会设计、OKR执行、汇报模板 | `skill_view("operations-manager/ops-cadence")` |
| scaling-playbook | 规模化复制、跨地区扩张、标准化vs本地化 | `skill_view("operations-manager/scaling-playbook")` |
| coo-advisor | COO级运营战略、经营分析、跨部门协调 | `skill_view("operations-manager/coo-advisor")` |

根据用户意图判断调哪个，一个问题可以组合多个 skill，都不匹配就直接回答。

## Boss Mode 汇报格式

```
【运营进展汇报】
✅ 已完成：[流程优化/增长项目]
🔄 进行中：[运营项目] — 进度 X%
❌ 阻塞：[资源/跨部门协作问题]
📊 核心指标：GMV X | 转化率 X% | 留存率 X% | 效率提升 X%
```

写入 TASKLOG.md：`| [运营项目/流程优化] | [规划中/执行中/验证中/已完成] | [日期] | [备注] |`

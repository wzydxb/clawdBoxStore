# 运营经理 Agent 路由

## 工作流入口
收到任何消息时，先用 `skill_view("operations-manager/workflow")` 加载完整工作流上下文。

## 触发词路由

| 用户说 | 执行 |
|--------|------|
| 流程优化/SOP/标准化/降本增效 | `skill_view("operations-manager/process-frameworks")` |
| 增长/拉新/留存/GMV/转化率 | `skill_view("operations-manager/growth-metrics")` |
| 运营节奏/周会/例行汇报/OKR | `skill_view("operations-manager/ops-cadence")` |
| 规模化/扩张/快速复制/标准化 | `skill_view("operations-manager/scaling-playbook")` |
| COO顾问/运营战略/经营分析 | `skill_view("operations-manager/coo-advisor")` |

## 主动提醒规则

| 场景信号 | 主动建议 |
|----------|----------|
| 用户说「流程太乱」 | 要做流程诊断和SOP梳理吗？ |
| 用户说「增长停滞」 | 要做增长漏斗分析吗？ |
| 用户说「要开周会」 | 要生成本周运营数据简报吗？ |
| 用户说「要复制到新城市/新渠道」 | 要做规模化扩张方案吗？ |
| 用户说「效率太低」 | 要做运营效率诊断吗？ |

## Boss Mode 汇报格式

```
【运营进展汇报】
✅ 已完成：[流程优化/增长项目]
🔄 进行中：[运营项目] — 进度 X%
❌ 阻塞：[资源/跨部门协作问题]
📊 核心指标：GMV X | 转化率 X% | 留存率 X% | 效率提升 X%
```

## 任务记录格式

写入 TASKLOG.md：
`| [运营项目/流程优化] | [规划中/执行中/验证中/已完成] | [日期] | [备注] |`

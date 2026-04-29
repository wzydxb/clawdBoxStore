# 行政经理 Agent 路由

## 工作流入口
收到任何消息时，先用 `skill_view("admin-manager/workflow")` 加载完整工作流上下文。

## 触发词路由

| 用户说 | 执行 |
|--------|------|
| 采购/供应商/比价/合同到期/采购审批 | `skill_view("admin-manager/procurement")` |
| 资产/固定资产/盘点/折旧/报废 | `skill_view("admin-manager/asset-management")` |
| 预算/报销/费用/成本控制/行政开支 | `skill_view("admin-manager/expense-control")` |
| 制度/规章/合规/文件管理/公司政策 | `skill_view("admin-manager/policy-compliance")` |
| 差旅/出差/机票/酒店/行程安排 | `skill_view("admin-manager/travel-logistics")` |
| 行政顾问/办公规划/行政战略/办公空间 | `skill_view("admin-manager/admin-advisor")` |

## 主动提醒规则

| 场景信号 | 主动建议 |
|----------|----------|
| 用户说「合同快到期了」 | 要整理合同到期清单吗？ |
| 用户说「要出差」 | 要做行程规划和费用预算吗？ |
| 用户说「要盘点」 | 要生成资产盘点表吗？ |
| 用户说「预算超了」 | 要做费用分析找超支原因吗？ |
| 用户说「制度要更新」 | 要整理制度文件版本和修订建议吗？ |
| 用户说「有客户来访」 | 要做来访接待方案吗？ |

## Boss Mode 汇报格式

```
【行政工作汇报】
✅ 已完成：[采购/资产/制度/差旅项目]
🔄 进行中：[行政事项] — 进度 X%
❌ 阻塞：[审批/供应商/预算问题]
📊 核心指标：行政预算执行率 X% | 采购节省 X万 | 资产完好率 X% | 制度覆盖率 X%
```

## 任务记录格式

写入 TASKLOG.md：
`| [采购/资产/费控/制度/差旅] | [待办/进行中/已完成] | [日期] | [备注] |`

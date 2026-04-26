# AGENTS.md — 路由决策

## 启动时：状态检查

读取 USER.md，检查 `Onboarding Status`：
- `pending` → 执行 **Onboarding Flow**（流程在 SOUL.md 中定义）
- `role_assigned` → 进入 **正常工作模式**

---

## 正常工作模式

每次对话按以下顺序路由：

### 1. 加载角色路由

读取 USER.md 的 `Role Dir` 字段，执行：
```
skill_view("<role_dir>/agents")
```

角色路由文件包含该角色的触发词映射、主动提醒规则、Boss Mode 格式。

| 角色 | Role Dir |
|------|----------|
| 产品经理 | `product-manager` |
| 财务经理 | `finance-manager` |
| HR经理 | `hr-manager` |
| 运营经理 | `operations-manager` |
| CEO | `ceo` |
| 数据分析师 | `data-analyst` |
| 其他职业 | 动态生成（onboarding 写入） |

### 2. 选 Skill 前查索引

不确定用哪个 skill 时：
```
skill_view("skill-registry")
```

### 3. 始终激活的能力

无论角色是什么，以下能力随时可触发：

| 触发词 | 执行 |
|--------|------|
| 日报、周报、月报、帮我写报告 | `skill_view("reporting")` |
| 复盘、反思、经验沉淀、总结一下 | `skill_view("retrospective")` |
| 整理文件、找文件、知识库、归档 | `skill_view("knowledge-base")` |
| 分享、二维码、怎么加你 | `skill_view("share-bot")` |
| 帮我写文章、写一篇、公众号推文 | `skill_view("content-writer")` |
| 打开网页、搜索、帮我看看这个网站 | `skill_view("browser")` |

### 4. 偏好蒸馏（后台静默）

满足以下任一条件时，执行 `skill_view("twin-distillation")`：
- 用户明确表达偏好或纠正行为
- 当前会话超过 5 轮
- 完成了一个完整任务（触发 Workflow Adapt）

蒸馏和 Workflow Adapt 的完整逻辑在 twin-distillation/SKILL.md 中。

---

## 硬性规则

- USER.md 是唯一状态存储
- 切换视角时直接行动，不说「我现在切换到XX模式」
- SOUL.md 的 `ARCHETYPE_LOCK` 区域任何 skill 都不得修改

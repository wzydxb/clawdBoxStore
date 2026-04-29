# AGENTS.md — 路由决策

## 启动时：状态检查

读取 USER.md，检查 `Onboarding Status`：
- `pending` → 执行 **Onboarding Flow**（流程在 SOUL.md 中定义）
- `role_assigned` → 进入 **正常工作模式**

---

## 正常工作模式

### 1. 加载角色能力目录

读取 USER.md 的 `Role Dir` 字段，执行：
```
skill_view("<role_dir>/agents")
```

| 角色 | Role Dir |
|------|----------|
| 产品经理 | `product-manager` |
| 财务经理 | `finance-manager` |
| HR经理 | `hr-manager` |
| 运营经理 | `operations-manager` |
| CEO | `ceo` |
| 数据分析师 | `data-analyst` |
| 行政经理/副总裁 | `admin-manager` |
| 其他职业 | 动态生成（onboarding 写入） |

有 Secondary Role Dir 时，同样加载副角色的 agents。

### 2. 通用能力

以下能力根据用户意图自主判断调用，不依赖触发词：

- 报告类（日报/周报/月报）→ `skill_view("reporting")`
- 复盘反思 → `skill_view("retrospective")`
- 文件归档/知识库检索 → `skill_view("knowledge-base")`
- 长文写作/文案 → `skill_view("content-writer")`
- 浏览器/网页操作 → `skill_view("browser")`
- 分享二维码 → `skill_view("share-bot")`
- 不确定用哪个 skill → `skill_view("skill-registry")`

### 3. 偏好蒸馏（后台静默）

满足以下任一条件时，执行 `skill_view("twin-distillation")`：
- 用户明确表达偏好或纠正行为
- 当前会话超过 5 轮
- 完成了一个完整任务（触发 Workflow Adapt）

---

## 硬性规则

- USER.md 是唯一状态存储
- 切换视角时直接行动，不说「我现在切换到XX模式」
- SOUL.md 的 `ARCHETYPE_LOCK` 区域任何 skill 都不得修改

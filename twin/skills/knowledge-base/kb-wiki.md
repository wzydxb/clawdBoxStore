---
name: kb-wiki
description: LLM Wiki 编译与知识问答：新文件触发编译 concept 页，问答结论沉淀到 insights
version: 1.0.0
---

# LLM Wiki

## 目录结构

```
.hermes-index/wiki/
├── _index.md       ← 所有文件的摘要目录
├── concepts/       ← 主题知识页（如「采购合同」「Q4报告」）
├── insights/       ← 问答结论沉淀
└── log.md          ← 变更日志
```

---

## 新文件触发编译

每次索引新增文件后执行：

1. **更新 `_index.md`**，追加条目：

```markdown
## [文件名]（YYYY-MM-DD）
- 路径：[path]
- 类型：[PDF/Word/Excel/...]
- 标签：#标签1 #标签2
- 摘要：[一句话核心内容]
- 关联：[[concept-page]]
```

2. **判断是否涉及已有主题** → 更新对应 `concepts/[主题].md`

3. **写入 `log.md`**：
```markdown
- YYYY-MM-DD HH:MM：新增 [文件名]，涉及主题：[主题]
```

---

## Concept 页格式

```markdown
# [主题名]

> 最后更新：YYYY-MM-DD | 来源文件数：N

## 核心内容
[LLM 综合多个文件提炼的主题知识]

## 相关文件
- [[文件名]]（路径）— 摘要

## 时间线
- YYYY-MM-DD：[事件/文件变更]
```

文件更新时（来自 kb-index 的通知）：
- 重新读取 diff 涉及的关键信息
- 更新 concept 页的「核心内容」和「时间线」

---

## 知识问答流程

```
用户提问
    ↓
Step 1：读 wiki/insights/ → 有现成结论？
    ↓ 有 → 直接回答，附来源文件
    ↓ 无
Step 2：读 wiki/_index.md + 相关 concepts/ → 有主题页？
    ↓ 有 → LLM 基于 concept 页回答
    ↓ 无
Step 3：调用 skill_view("knowledge-base/kb-search") 全文检索
    ↓
Step 4：读原文相关段落 → LLM 综合回答
    ↓
Step 5：结论写入 wiki/insights/[主题].md
```

---

## Insights 页格式

```markdown
## [问题摘要]（YYYY-MM-DD）
- 问题：[用户问的]
- 结论：[回答要点]
- 来源：[文件路径]
```

知识越问越厚，同类问题下次直接命中 Step 1。

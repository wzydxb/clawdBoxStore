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
└── log.md          ← 更新记录
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

## Session 开始时注入实体指纹

每次 session 开始，静默执行（不发消息给用户）：

```bash
# 读取挂载路径（从 USER.md 解析）
MOUNT=$(python3 -c "
import re
c = open('/root/.hermes/USER.md').read()
m = re.search(r'挂载路径:\s*(.+)', c)
print(m.group(1).strip() if m else '')
")

if [ -n "$MOUNT" ]; then
  python3 ~/.hermes/skills/knowledge-base/scripts/kb_entities.py "$MOUNT" --read
fi
```

- 有输出 → 注入到 context，LLM 自动感知知识库实体
- 无输出（entities.json 不存在或为空）→ 跳过，不影响正常对话

---

## 知识问答流程

```
用户提问
    ↓
Step 0：context 实体表命中用户问题里的词？
    ↓ 命中 → 已知要查哪些文件，直接跳 Step 2.5
    ↓ 未命中
Step 1：读 wiki/insights/ → 有现成结论？
    ↓ 有 → 直接回答，附来源文件
    ↓ 无
Step 2：读 wiki/_index.md + 相关 concepts/ → 有主题页？
    ↓ 有 → LLM 基于 concept 页回答
    ↓ 无
Step 2.5（HyDE 降级检索）：
    LLM 先生成假设答案（内部，不输出给用户）
    从假设答案提取关键词列表
    用关键词跑 kb_search.py（比口语问题命中率高 3-5x）
    ↓
Step 3：读原文相关段落 → LLM 综合回答
    ↓
Step 4：结论写入 wiki/insights/[主题].md
```

**HyDE 假设答案提取 prompt**（内部执行）：
```
用户问题：[原始问题]

请生成一段假设性回答（假设你已经知道答案），然后从中提取用于文档检索的关键词。

输出格式：
关键词：词1 词2 词3 词4 词5
```

---

## 实体图谱更新流程

每次 kb-index 完成后（新增或更新文件），触发实体提取：

```bash
MOUNT=<挂载路径>
SCRIPT=~/.hermes/skills/knowledge-base/scripts/kb_entities.py

# 1. 获取待提取文件列表（含内容）
FILE_LIST=$(python3 $SCRIPT "$MOUNT" --list)

# 2. LLM 提取实体（系统直接处理，不需要额外调用）
# 使用下方 prompt 模板，对 FILE_LIST 里每个文件提取实体
# 将结果合并为一个 JSON

# 3. 写入 entities.json
python3 $SCRIPT "$MOUNT" --write '<LLM输出的JSON>'
```

**实体提取 prompt 模板**（对每个文件执行）：
```
文件：[文件名]
内容：[content，最多3000字符]

请提取：
1. 实体：组织名、人名、产品名、指标名、时间点（只提取文中明确出现的）
2. 关系：[实体A] → [关系动词] → [实体B]（有明确关联才写，不要推断）
3. 时间线：实体+日期+事件（有明确日期才写）

输出 JSON（严格格式，不要加注释）：
{
  "entities": {
    "实体名": {"type": "组织|人名|产品|指标|时间", "summary": "一句话描述", "files": ["文件名"], "last_seen": "YYYY-MM-DD"}
  },
  "relations": [
    {"from": "实体A", "rel": "关系", "to": "实体B", "date": "YYYY-MM-DD", "files": ["文件名"]}
  ]
}
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

---

## Wiki 格式校验（每次编译后必须执行）

每次写入或更新 wiki 内容后，**必须**运行格式校验：

```bash
python3 ~/.hermes/skills/knowledge-base/scripts/kb_wiki_check.py MOUNT_PATH
```

校验项目：
1. _index.md 每个条目必须有路径/摘要/关联三个字段
2. 摘要不能是占位符，必须是实际内容的一句话概括
3. wiki link 必须双方括号闭合，不能写成单闭合
4. _index.md 关联的 concept 页必须实际存在
5. concept 页必须包含核心内容和相关文件章节
6. concept 页的核心内容不能为空

**校验失败时：根据输出逐一修复，再次运行直到通过。不得跳过。**

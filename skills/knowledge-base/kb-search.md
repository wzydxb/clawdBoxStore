---
name: kb-search
description: 知识库 FTS5 全文检索，支持多网盘并行查询，1-5ms 返回结果
version: 2.0.0
---

# 知识库检索

脚本：`~/.hermes/skills/knowledge-base/scripts/kb_search.py`

**触发词**：帮我找 / 搜一下 / 有没有关于XX的 / 上次那个

## 命令

```bash
# 检索单个网盘
python3 ~/.hermes/skills/knowledge-base/scripts/kb_search.py "关键词" /Volumes/uploads

# 检索多个网盘
python3 ~/.hermes/skills/knowledge-base/scripts/kb_search.py "关键词" \
  /Volumes/uploads /Volumes/docs

# 检索所有配置网盘（读 USER.md）
python3 ~/.hermes/skills/knowledge-base/scripts/kb_search.py "关键词" --all

# 限制返回条数
python3 ~/.hermes/skills/knowledge-base/scripts/kb_search.py "关键词" --all --limit 20
```

## 输出格式

```
找到 N 个相关文件：

📄 合同.pdf
   路径：/Volumes/uploads/2024/合同/合同.pdf
   匹配：...甲方：>>>北京供应商<<<，采购金额...
```

## 说明

- 使用 SQLite FTS5 `snippet()` 高亮匹配片段
- 多网盘结果按 FTS5 rank 排序合并
- 网盘未挂载时自动跳过，不报错

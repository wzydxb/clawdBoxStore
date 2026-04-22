---
name: kb-index
description: 知识库索引管理：FTS5 初始化、增量扫描、内容提取、文件更新 diff
version: 2.0.0
---

# 知识库索引

脚本：`~/.hermes/skills/knowledge-base/scripts/kb_index.py`

## 命令

```bash
# 初始化（首次使用）
python3 ~/.hermes/skills/knowledge-base/scripts/kb_index.py /Volumes/uploads --init

# 增量扫描（只处理新增/修改文件）
python3 ~/.hermes/skills/knowledge-base/scripts/kb_index.py /Volumes/uploads

# 单文件更新 + 输出 diff（用户说「我更新了某文件」时）
python3 ~/.hermes/skills/knowledge-base/scripts/kb_index.py /Volumes/uploads \
  --update /Volumes/uploads/合同.pdf
```

## 支持的文件类型

| 类型 | 提取方式 |
|------|----------|
| PDF | pymupdf |
| Word (.docx) | python-docx |
| Excel (.xlsx) / CSV | pandas |
| PPT (.pptx) | python-pptx |
| 文本/代码/Markdown | 直接读取 |
| 图片/视频 | 只存元数据，不提取内容 |
| 含敏感词文件名 | 跳过内容，只记录路径 |

## 文件更新流程（顺序不能乱）

1. 从索引取旧内容
2. 提取新内容
3. **diff（先做，再覆盖）**
4. 更新 index.db
5. 输出 diff 供 LLM 解读，生成变更摘要
6. 通知 kb-wiki 更新相关 concept 页

## 索引结构

```
.hermes-index/
├── index.db          ← SQLite FTS5，存 path/name/content/tags/summary
└── wiki/
    └── log.md        ← 每次扫描/更新自动追加记录
```

## 依赖安装

```bash
pip install pymupdf python-docx pandas openpyxl python-pptx
```

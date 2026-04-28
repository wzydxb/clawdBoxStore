---
name: knowledge-base
description: |
  管理网盘文件作为个人知识库。双层架构：FTS5 全文检索 + LLM Wiki 知识沉淀。
  索引存放在每个网盘的 .hermes-index/ 目录，支持多网盘并行检索。
  触发词：整理文件、知识库、扫一下、帮我找、归档、文件分类、上次那个文件
version: 2.0.0
---

# 知识库管理

## 架构

```
网盘（smb://...）
├── [原始文件，用户直接操作]
└── .hermes-index/
    ├── index.db        ← FTS5 全文检索
    └── wiki/
        ├── _index.md   ← 文件摘要目录
        ├── concepts/   ← 主题知识页
        ├── insights/   ← 问答结论沉淀
        └── log.md      ← 变更日志
```

- **FTS5**：找文件，1-5ms，关键词精准定位
- **LLM Wiki**：沉淀知识，回答综合性问题，越用越厚

多网盘：每个网盘各自维护 `.hermes-index/`，查询时并行搜索合并结果。

---

## 触发词路由

| 用户说 | 加载 |
|--------|------|
| 扫一下 / 建索引 / 更新知识库 | `skill_view("knowledge-base/kb-index")` |
| 帮我找 / 搜 / 有没有关于XX的 | `skill_view("knowledge-base/kb-search")` |
| 我更新了 / 改了文件 / 重新上传了 | `skill_view("knowledge-base/kb-index")` → 文件更新流程 |
| 总结一下 / 提炼 / 上次那个 | `skill_view("knowledge-base/kb-wiki")` |
| 整理文件 / 归档 / 文件太乱了 | `skill_view("knowledge-base/kb-organize")` |
| kb_notify 推送 / 收到 inbox 文件通知 | `skill_view("knowledge-base/kb-inbox")` → 执行 ETL 流程 |

---

## 网盘配置（USER.md）

```yaml
知识库:
  - 名称: uploads
    挂载路径: /Volumes/uploads
  - 名称: docs
    挂载路径: /Volumes/docs
```

---

## 主动提醒规则

| 场景 | 主动建议 |
|------|----------|
| 用户上传文件后 | 要加入知识库索引吗？ |
| 用户说「找不到那个文件」 | 用知识库搜索一下？ |
| 用户说「我更新了文件」 | 自动走更新流程：diff → 展示变更 → 更新索引和 wiki |
| 用户问综合性问题 | 先查 wiki insights，有现成结论直接给 |
| 索引超过30天未更新 | 知识库索引可能过期，要更新一下吗？ |
| session 开始时 entities.json 存在 | 静默注入实体表到 context（不发消息给用户） |
| 用户问题命中 context 实体表里的词 | 直接定向检索对应文件，不等触发词 |

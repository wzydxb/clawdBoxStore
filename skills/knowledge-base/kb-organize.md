---
name: kb-organize
description: 知识库文件整理：自动分类归档、重命名、移动后索引同步、重复检测、健康检查
version: 2.0.0
---

# 文件整理与维护

脚本：`~/.hermes/skills/knowledge-base/scripts/kb_organize.py`

**触发词**：整理文件 / 文件太乱了 / 归档 / 帮我整理一下

## 命令

```bash
# 预览归档建议（不移动文件）
python3 ~/.hermes/skills/knowledge-base/scripts/kb_organize.py /Volumes/uploads

# 确认后执行归档
python3 ~/.hermes/skills/knowledge-base/scripts/kb_organize.py /Volumes/uploads --execute

# 移动单个文件（手动指定目标路径）
python3 ~/.hermes/skills/knowledge-base/scripts/kb_organize.py /Volumes/uploads \
  --file /Volumes/uploads/合同.pdf \
  --dest /Volumes/uploads/2024/合同/2024-01-15-北京供应商-采购合同.pdf
```

## 分类逻辑

扫描网盘**根目录**散落文件，按以下维度推断归属：

| 优先级 | 维度 | 示例 |
|--------|------|------|
| 1 | 业务主题 | 合同、发票、报告、方案、会议纪要 |
| 2 | 年份 | 2024/ |
| 3 | 主题子目录 | 合同/、报告/ |

目标路径格式：`[年份]/[主题]/[规范化文件名]`

## 重命名规范

`YYYY-MM-DD-[主题]-[原文件名]`

日期来源优先级：文件名中的日期 > 文件修改时间

## 执行流程

1. 扫描根目录散落文件
2. 读取 FTS5 索引中的内容摘要辅助分类
3. 输出预览，等待用户确认
4. 执行 `shutil.move` 移动文件
5. 同步更新 `index.db` 中的 path 字段
6. 同步更新 `wiki/_index.md` 中的路径引用

## 健康检查

```bash
# 检查孤儿索引 + 重复文件
python3 ~/.hermes/skills/knowledge-base/scripts/kb_health.py /Volumes/uploads

# 自动清理孤儿索引
python3 ~/.hermes/skills/knowledge-base/scripts/kb_health.py /Volumes/uploads --fix

# 检查所有配置网盘
python3 ~/.hermes/skills/knowledge-base/scripts/kb_health.py --all
```

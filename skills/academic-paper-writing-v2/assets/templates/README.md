# 论文模板资产

本目录包含各类学术论文的标准模板文件。

## 模板列表

### 1. 期刊论文模板 (journal_template.docx)

**适用范围**：
- 国内核心期刊（北大核心、CSSCI、CSCD等）
- 国际SCI/SSCI期刊
- 普通学术期刊

**结构特点**：
- 摘要（200-300字）
- 关键词（3-5个）
- 正文章节（引言、方法、结果、讨论、结论）
- 参考文献

**使用说明**：
使用 `paper_template_filler.py` 脚本自动填充内容：
```bash
python scripts/paper_template_filler.py --template journal --data paper_data.json --output journal_paper.docx
```

---

### 2. 学位论文模板 (thesis_template.docx)

**适用范围**：
- 博士学位论文
- 硕士学位论文
- 学士学位论文

**结构特点**：
- 中英文摘要
- 详细目录
- 完整章节结构（绪论、文献综述、方法、结果、讨论、结论）
- 附录
- 致谢
- 发表论文列表

**使用说明**：
```bash
python scripts/paper_template_filler.py --template thesis --data thesis_data.json --output thesis.docx
```

---

### 3. 会议论文模板 (conference_template.docx)

**适用范围**：
- 国际学术会议（CVPR、ICCV、NeurIPS等）
- 国内学术会议
- 研讨会论文

**结构特点**：
- 精简摘要
- 重点突出创新点
- 图表紧凑布局
- 参考文献精简

**使用说明**：
```bash
python scripts/paper_template_filler.py --template conference --data conference_data.json --output conference_paper.docx
```

---

## 数据格式说明

模板填充脚本需要JSON格式的数据文件，基本结构如下：

```json
{
  "title": "论文标题",
  "authors": ["作者1", "作者2"],
  "institution": "作者机构",
  "date": "2024年1月",
  "abstract": "摘要内容...",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "sections": {
    "引言": "引言内容...",
    "研究方法": "方法内容...",
    "研究结果": "结果内容...",
    "讨论": "讨论内容...",
    "结论": "结论内容..."
  },
  "references": [
    "[1] 参考文献条目1",
    "[2] 参考文献条目2"
  ]
}
```

## 注意事项

1. **模板定制**：如需根据特定期刊/学校要求定制模板，请修改对应模板文件
2. **格式要求**：各期刊/学校的具体格式要求可能不同，请以官方要求为准
3. **内容质量**：模板仅提供格式框架，内容质量由撰写者负责
4. **引用格式**：参考文献格式需符合目标期刊要求，可使用 `citation_formatter.py` 生成

## 快速开始

1. 准备论文数据文件（JSON格式）
2. 选择合适的模板类型
3. 运行模板填充脚本
4. 打开生成的文档进行内容调整

```bash
# 快速生成示例文档
python scripts/paper_template_filler.py --sample

# 使用实际数据生成文档
python scripts/paper_template_filler.py --template journal --data my_paper.json --output my_paper.docx
```

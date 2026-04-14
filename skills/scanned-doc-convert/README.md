# scanned-doc-convert

## 简介

将扫描 PDF、拍照页、截图页或其他图片型文档转换为可编辑格式，支持输出 TXT、可编辑 PDF 或 DOCX。

## 主要功能

- 识别扫描 PDF 中的图片页并提取文字（OCR）
- 支持手机拍照文档、截图等图片输入
- 输出格式：纯文本 TXT、可编辑 PDF、Word DOCX
- 保留原始排版结构（段落、标题等）

## 使用方式

通过 OpenClaw 对话触发，示例：

```
把这份扫描合同 PDF 转成 Word 文档
把这张拍照的表格转成 TXT
```

核心脚本：
- `run.py`：主入口，接收文件路径和输出格式参数
- `scripts/run_scanned_doc_convert.py`：OCR 识别与格式转换核心逻辑

## 依赖 / 前置条件

- Python 3.8+
- OCR 引擎（如 PaddleOCR 或 Tesseract，具体见 requirements.txt）
- `python-docx`、`reportlab` 等输出格式依赖

## 注意事项

- 图片清晰度直接影响识别准确率，建议使用 300dpi 以上的扫描件
- 手写内容识别准确率较低，以印刷体为主
- 复杂表格和多栏排版可能存在格式偏差，建议人工校对
- 处理大文件时耗时较长，请耐心等待

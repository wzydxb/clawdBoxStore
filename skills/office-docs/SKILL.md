---
name: office-docs
description: |
  离线办公文档创建与编辑：Excel、Word、PPT、PDF，全部基于本地 Python 库，无需联网。
  触发词：做表格、做报表、写报告、出PPT、做PPT、生成Word、导出PDF、制作文档、做Excel
version: 1.0.0
---

# 离线办公文档能力

所有操作均在本地执行，无需联网。输出文件默认保存到 `/root/workspace/`。

---

## Excel / 表格 (.xlsx)

### 创建新表格
```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Sheet1"

# 写入数据
ws['A1'] = '姓名'
ws['B1'] = '部门'
ws['C1'] = '数值'

# 标题行样式
header_font = Font(bold=True, color="FFFFFF")
header_fill = PatternFill("solid", fgColor="366092")
for cell in ws[1]:
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal='center')

# 写入数据行
data = [('张三', '研发部', 95), ('李四', '市场部', 88)]
for row in data:
    ws.append(row)

# 自动列宽
for col in ws.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    ws.column_dimensions[get_column_letter(col[0].column)].width = max_len + 4

wb.save('/root/workspace/output.xlsx')
print('MEDIA:/root/workspace/output.xlsx')
```

### 读取并修改已有表格
```python
import openpyxl
wb = openpyxl.load_workbook('/path/to/file.xlsx')
ws = wb.active
# 读取
for row in ws.iter_rows(min_row=2, values_only=True):
    print(row)
# 修改
ws['A1'] = '新值'
wb.save('/root/workspace/modified.xlsx')
```

### 添加图表
```python
from openpyxl.chart import BarChart, Reference
chart = BarChart()
chart.title = "数据对比"
chart.y_axis.title = "数值"
chart.x_axis.title = "类别"
data_ref = Reference(ws, min_col=3, min_row=1, max_row=ws.max_row)
chart.add_data(data_ref, titles_from_data=True)
ws.add_chart(chart, "E2")
wb.save('/root/workspace/chart.xlsx')
```

---

## Word 文档 (.docx)

### 创建新文档
```python
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# 标题
doc.add_heading('文档标题', level=0)
doc.add_heading('一级标题', level=1)

# 正文段落
p = doc.add_paragraph('正文内容，支持')
run = p.add_run('加粗')
run.bold = True
p.add_run('和')
run2 = p.add_run('斜体')
run2.italic = True

# 表格
table = doc.add_table(rows=3, cols=3)
table.style = 'Table Grid'
table.cell(0, 0).text = '列1'
table.cell(0, 1).text = '列2'
table.cell(0, 2).text = '列3'

# 页眉页脚
section = doc.sections[0]
header = section.header
header.paragraphs[0].text = '页眉文字'

doc.save('/root/workspace/output.docx')
print('MEDIA:/root/workspace/output.docx')
```

### 读取并修改已有文档
```python
from docx import Document
doc = Document('/path/to/file.docx')
# 读取所有段落
for para in doc.paragraphs:
    print(para.text)
# 读取表格
for table in doc.tables:
    for row in table.rows:
        print([cell.text for cell in row.cells])
# 追加内容
doc.add_paragraph('新增段落')
doc.save('/root/workspace/modified.docx')
```

---

## PPT 演示文稿 (.pptx)

### 创建新 PPT
```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

prs = Presentation()
# 幻灯片尺寸（16:9）
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)

# 封面页
slide_layout = prs.slide_layouts[0]  # 标题页
slide = prs.slides.add_slide(slide_layout)
slide.shapes.title.text = '报告标题'
slide.placeholders[1].text = '副标题 / 日期'

# 内容页
content_layout = prs.slide_layouts[1]  # 标题+内容
slide2 = prs.slides.add_slide(content_layout)
slide2.shapes.title.text = '第一章'
tf = slide2.placeholders[1].text_frame
tf.text = '要点一'
tf.add_paragraph().text = '要点二'
tf.add_paragraph().text = '要点三'

# 空白页（自由布局）
blank_layout = prs.slide_layouts[6]
slide3 = prs.slides.add_slide(blank_layout)
# 添加文本框
txBox = slide3.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(2))
tf = txBox.text_frame
tf.text = '自定义文本'
tf.paragraphs[0].font.size = Pt(24)
tf.paragraphs[0].font.bold = True
tf.paragraphs[0].font.color.rgb = RGBColor(0x36, 0x60, 0x92)

# 添加图片
# slide3.shapes.add_picture('/path/to/img.png', Inches(1), Inches(3), Inches(4), Inches(3))

prs.save('/root/workspace/output.pptx')
print('MEDIA:/root/workspace/output.pptx')
```

### 读取已有 PPT
```python
from pptx import Presentation
prs = Presentation('/path/to/file.pptx')
for i, slide in enumerate(prs.slides):
    print(f'--- 第{i+1}页 ---')
    for shape in slide.shapes:
        if shape.has_text_frame:
            print(shape.text_frame.text)
```

---

## PDF 生成

### 方式一：fpdf2（简单文档）
```python
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, '文档标题', align='C', new_x='LMARGIN', new_y='NEXT')

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'第 {self.page_no()} 页', align='C')

pdf = PDF()
pdf.add_page()
# 中文需要添加字体
# pdf.add_font('NotoSans', '', '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc')
# pdf.set_font('NotoSans', size=12)
pdf.set_font('Helvetica', size=12)
pdf.multi_cell(0, 10, 'PDF content here')
pdf.output('/root/workspace/output.pdf')
print('MEDIA:/root/workspace/output.pdf')
```

### 方式二：reportlab（复杂排版）
```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors

doc = SimpleDocTemplate('/root/workspace/output.pdf', pagesize=A4)
styles = getSampleStyleSheet()
story = []

story.append(Paragraph('标题', styles['Title']))
story.append(Spacer(1, 12))
story.append(Paragraph('正文内容', styles['Normal']))

# 表格
data = [['列1', '列2', '列3'], ['A', 'B', 'C'], ['D', 'E', 'F']]
t = Table(data)
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#366092')),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
]))
story.append(t)
doc.build(story)
print('MEDIA:/root/workspace/output.pdf')
```

---

## 注意事项

- 输出文件用 `print('MEDIA:/path/to/file')` 发送给用户
- 中文 PDF 需要系统中文字体，路径通常在 `/usr/share/fonts/` 或 `/root/.hermes/hermes-agent/venv/lib/python3.11/site-packages/reportlab/fonts/`
- 大文件（>10MB）建议先告知用户文件大小
- 修改已有文件前先读取确认结构，避免覆盖用户数据

# 合同生成器 Pro

## 简介

通用合同生成工具，支持雇佣合同、租房合同、服务合同等多种类型的专业合同文档生成，提供模板填充和批量生成能力。

## 主要功能

- 多类型合同生成：雇佣合同、租房合同、服务合同、保密协议等
- 模板填充：基于 `templates/` 目录下的 DOCX 模板，自动替换占位符（支持 `[VAR]` 和 `{{var}}` 格式）
- 批量生成：从 CSV/JSON 批量生成多份合同
- 字段验证：自动检查必填项，生成前提示缺失字段

## 使用方式

核心脚本：`contract_generator.py`

```bash
# 生成单份合同
python contract_generator.py generate \
  --template templates/employment_contract.docx \
  --vars candidate.json \
  --output contract.docx

# 批量生成
python contract_generator.py batch \
  --template templates/offer_letter.docx \
  --csv new_hires.csv \
  --output-dir offers/

# 验证合同完整性
python contract_generator.py validate contract.docx
```

也可以通过对话描述需求，助手会引导填写关键信息并生成合同。

示例提示：
- "帮我生成一份软件开发服务合同，甲方是A公司，乙方是B公司"
- "批量生成员工劳动合同，数据在 employees.csv 里"

## 依赖/前置条件

- Python >= 3.8
- 安装依赖：`pip install -r requirements.txt`
- 无需 API Key

模板文件位于 `templates/` 目录，可自行添加 DOCX 模板，用 `[变量名]` 格式标记占位符。

## 注意事项

- 生成的合同仅供参考，重要合同签署前请经过法律专业人士审核
- 模板条款基于通用场景，特殊行业或跨境合同需单独定制
- 批量生成时建议先用少量数据测试，确认格式正确后再全量执行
- CSV 第一行必须是变量名，文件需使用 UTF-8 编码

---
name: contract-generator-pro
description: 通用合同生成器 - 生成雇佣合同、租房合同、服务合同等专业文档。支持自动化模板填充、批量生成（CSV/Excel/JSON）和 DOCX 输出。有模板走模板，没模板 AI 直接生成。v1.4.0
---

# Universal Contract Generator v1.4.0

生成专业的合同文档（雇佣合同、录用通知书、租房合同、NDA、服务合同等），结合自动化模板填充与法律最佳实践。

---

## 🤖 AI 对话引导流程（必读）

**当用户请求生成合同时，按以下步骤执行，不要一次性问所有问题：**

### Step 1：判断合同类型

用户说"帮我生成合同"→ 先问合同类型：

```
支持以下合同类型：
1. 雇佣合同（劳动合同）
2. 录用通知书（Offer Letter）
3. 租房合同
4. 保密协议（NDA）
5. 服务合同 / 合作协议

请问您需要哪种合同？
```

### Step 2：收集必填信息（按类型）

确认类型后，按对应字段列表收集信息。**分批询问，每次最多问 5 个字段。**

#### 雇佣合同必填字段
| 字段 | 说明 | 示例 |
|------|------|------|
| company_name | 公司名称 | 某某科技有限公司 |
| employee_name | 员工姓名 | 张三 |
| employee_id | 员工身份证号 | 110101199001011234 |
| position | 职位名称 | 高级软件工程师 |
| department | 部门 | 技术部 |
| base_salary | 月基本工资（元，税前） | 25000 |
| start_date | 入职日期（如 2024年4月1日） | 2024年4月1日 |
| contract_years | 合同年限 | 3 |
| probation_months | 试用期（月） | 3 |
| work_location | 工作地点 | 北京市朝阳区 |
| reporting_to | 直属上级姓名/职位 | 技术总监 |
| notice_period_days | 离职通知期（天） | 30 |

> **自动计算字段**（无需用户填写）：end_date、probation_end_date

#### 录用通知书必填字段
| 字段 | 说明 | 示例 |
|------|------|------|
| company_name | 公司名称 | 某某科技有限公司 |
| candidate_name | 候选人姓名 | 李四 |
| position | 职位名称 | 产品经理 |
| department | 部门 | 产品部 |
| base_salary | 年薪（元，税前） | 300000 |
| start_date | 入职日期 | 2024年4月1日 |
| offer_expiry_date | Offer 有效期 | 2024年3月28日 |
| hr_contact | HR 联系人姓名+邮箱 | 王五 wangwu@company.com |
| reporting_to | 直属上级 | 产品总监 |
| work_location | 工作地点 | 上海市浦东新区 |

#### 租房合同必填字段
| 字段 | 说明 | 示例 |
|------|------|------|
| landlord_name | 出租方姓名 | 张伟 |
| landlord_id | 出租方身份证号 | 110101197001011234 |
| tenant_name | 承租方姓名 | 李娜 |
| tenant_id | 承租方身份证号 | 110101199501011234 |
| property_address | 房屋地址 | 北京市朝阳区XX路XX号XX室 |
| monthly_rent | 月租金（元） | 8000 |
| deposit_amount | 押金（元） | 16000 |
| lease_start_date | 租期开始日期 | 2024年4月1日 |
| lease_months | 租期（月） | 12 |
| payment_day | 每月租金支付日（几号） | 5 |

> **自动计算字段**：lease_end_date

#### NDA（保密协议）必填字段
| 字段 | 说明 | 示例 |
|------|------|------|
| party_a_name | 甲方名称（信息披露方） | 某某科技有限公司 |
| party_b_name | 乙方名称（信息接收方） | 张三 |
| purpose | 保密目的 | 商务合作洽谈 |
| confidential_period_years | 保密期限（年） | 3 |
| governing_law | 适用法律/管辖地 | 北京市 |
| sign_date | 签署日期 | 2024年4月1日 |

#### 服务合同必填字段
| 字段 | 说明 | 示例 |
|------|------|------|
| party_a_name | 甲方名称（委托方） | 某某科技有限公司 |
| party_b_name | 乙方名称（服务方） | 张三 / 某某咨询有限公司 |
| service_content | 服务内容描述 | 软件开发咨询服务 |
| service_fee | 服务费用（元） | 50000 |
| payment_terms | 付款方式 | 签约后7日内支付50%，验收后支付50% |
| start_date | 服务开始日期 | 2024年4月1日 |
| end_date | 服务结束日期 | 2024年9月30日 |
| sign_date | 签署日期 | 2024年4月1日 |
| governing_law | 管辖地 | 北京市 |

### Step 3：确认信息并生成

收集完信息后，**汇总展示给用户确认**，格式如下：

```
以下是您的合同信息：

- 合同类型：雇佣合同
- 公司名称：某某科技有限公司
- 员工姓名：张三
- ...

确认无误后，我将生成合同文档。如需修改请告知。
```

### Step 4：生成合同文档

用户确认信息后，**先检查对应 DOCX 模板是否存在**，按两条路径处理：

---

#### 路径 A：DOCX 模板存在（employment_contract / offer_letter / rental_contract）

将变量写入临时 JSON 文件，调用 Python 脚本生成：

```bash
# 1. 将变量写入临时文件
# （AI 用 write 工具写到 ~/.openclaw/workspace/contracts/tmp_vars.json）

# 2. 生成合同
cd ~/.openclaw/skills/contract-generator-pro-v2
python contract_generator.py generate \
  -t employment_contract.docx \
  -v ~/.openclaw/workspace/contracts/tmp_vars.json \
  -o ~/.openclaw/workspace/contracts/雇佣合同_张三_20240401.docx
```

输出路径格式：`~/.openclaw/workspace/contracts/合同类型_姓名_日期.docx`

---

#### 路径 B：DOCX 模板不存在（NDA / 服务合同 / 其他自定义合同）

**AI 直接生成完整合同正文，然后用 Python 写入 DOCX 文件。**

具体步骤：

1. **AI 根据用户提供的信息，直接撰写完整合同内容**
   - 不使用固定模板，根据实际需求灵活生成条款
   - 金额自动附上中文大写
   - 日期计算自动完成
   - 内容质量对标专业律师事务所标准

2. **将生成的合同文本写入 DOCX 文件**，使用以下脚本：

```python
# AI 用 exec 工具运行此脚本（将 CONTRACT_TEXT 替换为实际内容）
import sys
sys.path.insert(0, r'~/.openclaw/skills/contract-generator-pro-v2')
from contract_generator import ContractGenerator

gen = ContractGenerator()
gen.set_variables({})  # 变量已直接填入文本，无需替换
gen.save_from_text("""
[AI 生成的完整合同正文，变量已直接填入]
""", r'~/.openclaw/workspace/contracts/NDA_张三_20240401.docx')
```

或者更简便地直接用 python-docx 写入：

```python
from docx import Document
from pathlib import Path

content = """[AI 生成的完整合同正文]"""

doc = Document()
for line in content.splitlines():
    doc.add_paragraph(line)

output = Path(r'~/.openclaw/workspace/contracts/NDA_张三_20240401.docx')
output.parent.mkdir(parents=True, exist_ok=True)
doc.save(output)
print(f"已保存：{output}")
```

3. **生成完成后，用 `MEDIA:` 指令将文件发送给用户**

---

> **判断规则（优先级）**：
> - `employment_contract.docx` → 路径 A（雇佣合同）
> - `offer_letter.docx` → 路径 A（录用通知书）
> - `rental_contract.docx` → 路径 A（租房合同）
> - NDA、服务合同、合作协议、其他 → **路径 B（AI 直接生成）**
> - 用户提供了自定义 DOCX 模板路径 → 路径 A

### Step 5：验证（可选）

```bash
python ~/.openclaw/skills/contract-generator-pro-v2/contract_generator.py validate \
  ~/.openclaw/workspace/contracts/雇佣合同_张三_20240401.docx
```

---

## 批量生成流程（HR/运营场景）

当用户提供 CSV/Excel/JSON 数据文件时：

1. 询问数据文件路径和合同模板类型
2. 询问输出目录（默认 `~/.openclaw/workspace/contracts/batch_日期/`）
3. 调用 batch 命令
4. 汇报生成结果（成功/失败数量）

```bash
# CSV 批量
python contract_generator.py batch \
  -t offer_letter.docx \
  -c new_hires.csv \
  -o ~/contracts/batch/ \
  -n employee_name

# Excel 批量
python contract_generator.py batch \
  -t offer_letter.docx \
  -e new_hires.xlsx \
  -o ~/contracts/batch/
```

---

## AI 直接生成合同（模板不存在时的降级路径）

当用户请求的合同类型没有对应 DOCX 模板时（如 NDA、服务合同、合作协议、采购合同等），
**AI 不报错，而是直接撰写完整合同内容**，然后写入 DOCX 文件发送给用户。

这是本技能的核心设计理念：**有模板走模板，没模板 AI 来写**。

### AI 生成合同的质量标准

- 条款完整，覆盖该合同类型的所有必要条款
- 用语规范，符合中国法律语境
- 金额同时写数字和中文大写
- 争议解决条款、违约责任条款不得遗漏
- 签字栏格式规范（双方各一份）
- 在文末注明"本合同由 AI 辅助生成，建议重要合同请专业律师审阅"

### 内置参考模板（AI 生成时可参考，但不必照搬）

需要时用 `read` 工具读取对应模板文件作为参考结构，根据用户具体需求灵活调整：
- NDA：`~/.openclaw/skills/contract-generator-pro-v2/templates/nda_template.txt`
- 服务合同：`~/.openclaw/skills/contract-generator-pro-v2/templates/service_template.txt`

---

## 核心功能

### 1. 自动化合同生成

- **模板系统**: 预置专业 DOCX 模板（雇佣合同、录用通知书、租房合同）
- **变量替换**: 自动填充所有 `[字段名]` 占位符；已修复跨 Run 截断问题
- **日期自动计算**: 提供 `start_date + contract_years` 自动推算 `end_date`、`probation_end_date`、`lease_end_date`
- **批量生成**: 从 CSV / Excel (.xlsx) / JSON 批量生成多个合同，单条失败不中断整批
- **格式输出**: 深拷贝模板生成 DOCX，完整保留字体/样式/页眉页脚
- **字段验证**: 检查必填项是否完整；生成后自动检测残留未替换占位符
- **合同完整性校验**: 按合同类型使用对应关键词集，支持 employment/rental/nda/service 等

### 2. 模板库

#### 当前可用模板（templates/ 目录）
| 文件名 | 文档类型 | 用途 |
|--------|---------|------|
| `employment_contract.docx` | 正式劳动合同 | 入职签约 |
| `offer_letter.docx` | 录用通知书 | 发 Offer 阶段 |
| `rental_contract.docx` | 房屋租赁合同 | 出租/承租 |

#### 纯文本路径（AI 直接生成内容，写入 DOCX）
| 文档类型 | 生成方式 |
|---------|---------|
| NDA 保密协议 | AI 用内置模板生成文本 → 写入 DOCX |
| 服务合同/合作协议 | AI 用内置模板生成文本 → 写入 DOCX |

### 3. 法律合规指导

- ⚖️ **管辖权提示**: 标注不同地区法律差异（如加州禁竞业限制；北京/上海/深圳房屋租赁差异）
- 📋 **必备条款清单**: 确保合同包含所有法律要求的条款
- ⚠️ **风险警示**: 自动标记可能需要法律顾问审查的条款

---

## 技术文档

Python API、CLI 完整用法详见 `README.md`，此处不展开。

---

## 内置文本模板（NDA / 服务合同）

模板已单独存放，按需用 `read` 工具读取，不在此展开以节省 token：

| 合同类型 | 模板文件路径 |
|---------|------------|
| NDA 保密协议 | `~/.openclaw/skills/contract-generator-pro-v2/templates/nda_template.txt` |
| 服务合同 | `~/.openclaw/skills/contract-generator-pro-v2/templates/service_template.txt` |

---

## 最佳实践

### ✅ 应该做的

- **咨询法律顾问** - 法律因地区而异，重要合同请律师审查
- **保留签署副本** - 所有签署文件都要存档
- **定期更新** - 法律法规变化时及时更新模板
- **明确具体** - 避免模糊表述，减少歧义
- **核实身份信息** - 签约前核查双方身份证号、营业执照等

### ❌ 不应该做的

- **不要使用通用模板不修改** - 必须根据公司情况和当地法律定制
- **不要歧视性条款** - 确保合同条款公平合法
- **不要遗漏必备条款** - 如试用期、工资、工作内容等
- **不要口头约定代替书面合同**

---

## 法律免责声明

⚠️ **重要提示：** 本技能提供的模板仅供参考，不构成法律意见。使用前请咨询当地合格法律顾问。

- 劳动法/租赁法规因国家/地区而异
- 竞业限制条款效力因地区不同（如加州不允许竞业限制）
- 建议重大合同决策前咨询专业律师

---

## 资源链接

- [中国人力资源和社会保障部](http://www.mohrss.gov.cn/)
- [劳动合同法全文](http://www.gov.cn/flfg/2007-06/29/content_669768.htm)
- [住房和城乡建设部](http://www.mohurd.gov.cn/)

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.4.0 | 2026-03-23 | 新增 AI 对话引导流程；路径A/B 生成策略；NDA/服务合同文本模板抽离；list-templates CLI；金额大写自动转换（修复万级零补位 bug）；修复 batch 非法文件名；修复 validate warnings 时 valid 状态错误 |
| 1.3.0 | 2026-03-21 | validate 按合同类型区分关键词；BatchGenerator 错误隔离+结果报告；支持 Excel；残留占位符检测；日期自动计算；CSV 编码自动检测 |
| 1.2.0 | 2026-03-21 | 修复跨 Run 占位符替换；改用 deepcopy 保留模板格式；表格单元格扫描 |
| 1.1.0 | 2026-03-21 | 添加租房合同支持、修复变量替换 bug、增强错误处理 |
| 1.0.0 | 2026-03-21 | 初始版本 |

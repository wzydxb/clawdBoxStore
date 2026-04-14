"""
文档生成模块 (优化版 V2.0)
优化内容：
1. 批注版合同更加详细
2. 支持完整的批注和风险标注
3. 改进格式和可读性
"""

from pathlib import Path
from typing import Dict, List
from datetime import datetime


class DocumentGenerator:
    """文档生成器 (优化版)"""

    def __init__(self, output_dir: str):
        """初始化文档生成器"""
        self.output_dir = Path(output_dir)
        print(f"📄 文档输出目录: {self.output_dir}")

        # 不创建子目录，直接输出到指定目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_legal_opinion(self, contract_name: str, analysis_result: Dict,
                              risk_report: Dict, user_context: Dict) -> str:
        """生成法律审核意见书"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{contract_name}-法律审核意见书.md"
        filepath = self.output_dir / filename

        content = self._generate_opinion_content(
            contract_name, analysis_result, risk_report, user_context
        )

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 法律审核意见书已生成: {filepath}")
        return str(filepath)

    def _generate_opinion_content(self, contract_name: str, analysis_result: Dict,
                                 risk_report: Dict, user_context: Dict) -> str:
        """生成意见书内容 (详细版)"""
        content = f"""# {contract_name} - 法律审核意见书

**文件名称：** {contract_name}
**审核日期：** {datetime.now().strftime('%Y年%m月%d日')}
**审核律师：** Contract Review Pro v2.0
**合同类型：** {analysis_result.get('identified_type', '未知')}

---

## 📋 一、委托方确认信息

| 项目 | 内容 |
|------|------|
| **委托方身份** | {user_context.get('party', '未指定')} |
| **市场地位** | {user_context.get('position', '未指定')} |
| **合作背景** | {user_context.get('history', '首次合作')} |
| **重点关切** | {user_context.get('focus', '无')} |
| **审核深度** | {user_context.get('review_depth', '标准审核')} |

---

## 📊 二、风险汇总统计

"""

        # 风险汇总表格
        summary = risk_report.get('summary', {})
        total_risks = sum(summary.values())

        content += "| 风险等级 | 数量 | 占比 |\n"
        content += "|---------|------|------|\n"

        for level in ['致命风险', '重要风险', '一般风险', '轻微瑕疵']:
            count = summary.get(level, 0)
            percentage = f"{count/total_risks*100:.0f}%" if total_risks > 0 else "0%"
            emoji = "🔴" if level == "致命风险" else "🟠" if level == "重要风险" else "🟡" if level == "一般风险" else "🔵"
            content += f"| {emoji} {level} | {count} | {percentage} |\n"

        content += f"| **合计** | **{total_risks}** | **100%** |\n\n"

        # 详细审核意见
        content += "## ⚠️ 三、详细审核意见\n\n"

        risks_by_level = risk_report.get('risks_by_level', {})

        for level in ['致命风险', '重要风险', '一般风险', '轻微瑕疵']:
            risks = risks_by_level.get(level, [])
            if not risks:
                continue

            emoji = "🔴" if level == "致命风险" else "🟠" if level == "重要风险" else "🟡" if level == "一般风险" else "🔵"
            content += f"### {emoji} {level}（{len(risks)}项）\n\n"

            for i, risk in enumerate(risks, 1):
                content += f"#### 风险{i}：{risk['description']}\n\n"
                content += f"**位置：** {risk.get('location', '未知')}\n\n"
                content += f"**风险等级：** {level} {'⭐' * (5 if level=='致命风险' else 4 if level=='重要风险' else 3 if level=='一般风险' else 2)}\n\n"
                content += f"**原文：**\n> {risk.get('original_text', '无')}\n\n"
                content += f"**问题分析：**\n{risk.get('analysis', '无')}\n\n"
                content += f"**法律依据：**\n{risk.get('legal_basis', '无')}\n\n"
                content += f"**修改建议：**\n```\n{risk.get('suggestion', '无')}\n```\n\n"
                content += "---\n\n"

        # 总体建议
        content += """## 📝 四、总体建议

### （一）必须修改的内容（签约前完成）

"""

        fatal_risks = risks_by_level.get('致命风险', [])
        important_risks = risks_by_level.get('重要风险', [])

        if fatal_risks or important_risks:
            for i, risk in enumerate(fatal_risks + important_risks, 1):
                content += f"{i}. ✅ **{risk['description']}** - {risk.get('location', '未知')}\n"
        else:
            content += "无\n"

        content += "\n### （二）建议修改的内容\n\n"

        general_risks = risks_by_level.get('一般风险', [])
        if general_risks:
            for i, risk in enumerate(general_risks[:5], 1):
                content += f"{i}. 🔄 **{risk['description']}**\n"
        else:
            content += "无\n"

        content += f"""
---

## ⚖️ 五、法律风险评估

**整体风险等级：** {'高风险' if summary.get('致命风险', 0) > 0 else '中等风险' if summary.get('重要风险', 0) > 2 else '低风险'}

**关键风险点：**
"""

        if fatal_risks:
            content += "\n1. ⚠️ " + fatal_risks[0]['description'] + "\n"

        content += f"""

---

## 📚 六、法律依据索引

1. **《中华人民共和国民法典》** - 合同编
2. **《中华人民共和国律师法》**
3. **相关司法解释和行业规范**

---

**审核律师：** Contract Review Pro v2.0
**审核日期：** {datetime.now().strftime('%Y年%m月%d日')}

---

## ⚠️ 免责声明

本法律审核意见书由AI系统基于预设规则生成，仅供参考，不构成正式法律意见。

对于重大、复杂的交易，建议咨询专业律师。

最终修改决策权由委托方根据实际情况自行判断。

---

**© 2026 Contract Review Pro - 专业合同审核系统**
"""

        return content

    def generate_detailed_annotated_contract(self, contract_name: str, original_contract: str,
                                            analysis_result: Dict, risk_report: Dict,
                                            user_context: Dict) -> str:
        """
        生成详细批注版合同 (新增功能)

        优化点：
        1. 完整保留原合同内容
        2. 逐条添加批注
        3. 标注风险点和修改建议
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{contract_name}-批注版.md"
        filepath = self.output_dir / filename

        content = f"""# {contract_name} - 批注版

**审核日期：** {datetime.now().strftime('%Y年%m月%d日')}
**审核重点：** 全面审核
**风险等级标识：**
- 🔴 致命风险（必须修改）
- 🟠 重要风险（建议修改）
- 🟡 一般风险（可协商修改）
- 🔵 轻微瑕疵（可选修改）

---

## 📊 批注汇总表

| 批注编号 | 风险等级 | 问题摘要 | 位置 |
|---------|---------|---------|------|
"""

        # 生成批注汇总表
        risks_by_level = risk_report.get('risks_by_level', {})
        annotation_num = 1

        for level in ['致命风险', '重要风险', '一般风险', '轻微瑕疵']:
            risks = risks_by_level.get(level, [])
            emoji = "🔴" if level == "致命风险" else "🟠" if level == "重要风险" else "🟡" if level == "一般风险" else "🔵"
            for risk in risks:
                content += f"| 批注{annotation_num} | {emoji} {level} | {risk['description'][:30]}... | {risk.get('location', '未知')} |\n"
                annotation_num += 1

        total_annotations = annotation_num - 1
        content += f"\n**统计：**\n"
        content += f"- 🔴 致命风险：{len(risks_by_level.get('致命风险', []))}项\n"
        content += f"- 🟠 重要风险：{len(risks_by_level.get('重要风险', []))}项\n"
        content += f"- 🟡 一般风险：{len(risks_by_level.get('一般风险', []))}项\n"
        content += f"- 🔵 轻微瑕疵：{len(risks_by_level.get('轻微瑕疵', []))}项\n"
        content += f"- **合计：{total_annotations}项**\n\n"

        content += """---

## ⚠️ 核心问题快速定位

### 🔴 必须修改（P0级）- 致命风险

"""

        fatal_risks = risks_by_level.get('致命风险', [])
        if fatal_risks:
            for i, risk in enumerate(fatal_risks, 1):
                content += f"{i}. **{risk['description']}** → {risk.get('suggestion', '无')}\n\n"
        else:
            content += "无致命风险\n\n"

        content += "### 🟠 强烈建议修改（P1级）- 重要风险\n\n"

        important_risks = risks_by_level.get('重要风险', [])
        if important_risks:
            for i, risk in enumerate(important_risks[:5], 1):
                content += f"{i}. **{risk['description']}** → {risk.get('suggestion', '无')[:50]}...\n\n"
        else:
            content += "无重要风险\n\n"

        content += """---

## 📝 详细批注内容

### 【合同标题】

**""" + contract_name + """**

✅ **条款评价：** 合同标题明确

---

### 【合同正文】

"""

        # 添加原合同内容并添加批注
        # 改进：优先按条款编号/关键词定位批注，original_text为空时按description关键词匹配
        lines = original_contract.split('\n')
        annotation_num = 1

        # 预处理：为每个风险提取匹配关键词
        def _get_match_keys(risk: dict) -> list:
            keys = []
            orig = risk.get('original_text', '').strip()
            if orig:
                keys.append(orig)
            loc = risk.get('location', '').strip()
            if loc:
                keys.append(loc)
            # 从description中提取前10个中文字作为备用匹配
            desc = risk.get('description', '')
            if desc:
                cn_chars = re.findall(r'[\u4e00-\u9fff]{2,8}', desc)
                keys.extend(cn_chars[:2])
            return [k for k in keys if len(k) >= 2]

        import re as _re

        for line in lines:
            if not line.strip():
                content += "\n"
                continue

            line_has_annotation = False
            for level in ['致命风险', '重要风险', '一般风险', '轻微瑕疵']:
                risks = risks_by_level.get(level, [])
                for risk in risks:
                    match_keys = _get_match_keys(risk)
                    if match_keys and any(k in line for k in match_keys):
                        emoji = ("🔴" if level == "致命风险" else
                                 "🟠" if level == "重要风险" else
                                 "🟡" if level == "一般风险" else "🔵")
                        stars = '⭐' * (5 if level == '致命风险' else
                                        4 if level == '重要风险' else
                                        3 if level == '一般风险' else 2)
                        content += f"\n{line}\n\n"
                        content += f"{emoji} **[批注{annotation_num}] {risk['description']}** {stars}\n\n"
                        content += f"> **问题：** {risk.get('analysis', risk.get('description', '无'))}\n\n"
                        content += f"> **修改建议：**\n> ```\n> {risk.get('suggestion', '无')}\n> ```\n\n"
                        content += "---\n\n"
                        annotation_num += 1
                        line_has_annotation = True
                        break
                if line_has_annotation:
                    break

            if not line_has_annotation:
                content += line + "\n"

        content += f"""
---

**审核律师：** Contract Review Pro v2.0
**审核日期：** {datetime.now().strftime('%Y年%m月%d日')}
**文件版本：** 批注版 v2.0（详细版）

---

**使用说明：**
1. 本批注版共标注 **{total_annotations}** 个问题点，按风险等级分为四级
2. 建议优先处理 🔴致命风险、🟠重要风险
3. 每个批注包含：问题描述、风险分析、法律依据、修改建议
4. 修改建议可直接用于合同修订谈判

---

**© 2026 Contract Review Pro - 专业合同审核系统**
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 批注版合同已生成: {filepath}")
        return str(filepath)

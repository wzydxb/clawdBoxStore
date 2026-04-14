"""
三观四步法深度分析模块
V1.2: 集成三观四步法和三维审查法
"""

from typing import Dict, List
import re


class SanguanAnalysis:
    """三观四步法分析器"""

    def __init__(self):
        """初始化三观分析器"""
        pass

    def analyze_commercial_dimension(self, contract_text: str, user_context: Dict) -> Dict:
        """
        商业维度分析

        核心问题: 这笔交易从商业上是否合理?

        分析要点:
        1. 理解交易本质
        2. 识别商业风险
        3. 评估交易条款的商业合理性
        """
        analysis = {
            'dimension': '商业维度',
            'rating': '中等',  # 优秀/良好/中等/较差/差
            'findings': [],
            'risks': [],
            'suggestions': []
        }

        # 提取商业要素
        parties = self._extract_parties(contract_text)
        price_terms = self._extract_price_terms(contract_text)
        delivery_terms = self._extract_delivery_terms(contract_text)

        # 分析1: 交易本质
        if parties:
            analysis['findings'].append({
                'category': '交易主体',
                'content': f'识别到交易主体: {", ".join(parties)}',
                'significance': '重要'
            })

        # 分析2: 商业合理性
        if user_context.get('position') == '弱势':
            analysis['risks'].append({
                'risk_type': '商业风险',
                'description': '用户处于弱势地位,可能面临不对等条款',
                'level': '重要风险',
                'suggestion': '重点关注权利义务平衡性,必要时要求调整'
            })

        # 分析3: 价格合理性
        if price_terms:
            analysis['findings'].append({
                'category': '价格条款',
                'content': f'价格条款: {price_terms}',
                'significance': '关键'
            })

        # 分析4: 关注点
        focus = user_context.get('focus', '')
        if focus:
            analysis['suggestions'].append({
                'aspect': '用户关注点',
                'content': f'用户关注: {focus},审核时应重点审查相关条款'
            })

        return analysis

    def analyze_legal_dimension(self, contract_text: str, contract_type: str) -> Dict:
        """
        法律维度分析

        核心问题: 从法律上是否有效、完整?

        分析要点:
        1. 合法性审查
        2. 有效性审查
        3. 权利义务平衡性
        """
        analysis = {
            'dimension': '法律维度',
            'rating': '良好',
            'findings': [],
            'risks': [],
            'suggestions': []
        }

        # 检查1: 合同类型合法性
        analysis['findings'].append({
            'category': '合同类型',
            'content': f'识别为: {contract_type}',
            'significance': '基础'
        })

        # 检查2: 必要条款
        essential_clauses = self._check_essential_clauses(contract_text, contract_type)
        if essential_clauses['missing']:
            analysis['risks'].append({
                'risk_type': '致命风险',
                'description': f'缺少必要条款: {", ".join(essential_clauses["missing"])}',
                'level': '致命风险',
                'suggestion': '必须补充,否则合同可能无法履行或产生争议'
            })

        # 检查3: 权利义务平衡
        balance_score = self._assess_balance(contract_text)
        if balance_score < 0.3:
            analysis['risks'].append({
                'risk_type': '重要风险',
                'description': '权利义务严重不平衡',
                'level': '重要风险',
                'suggestion': '建议调整违约责任、解除权等条款,增强平衡性'
            })

        # 检查4: 免责条款
        exemption_clauses = self._find_exemption_clauses(contract_text)
        if exemption_clauses:
            analysis['findings'].append({
                'category': '免责条款',
                'content': f'发现{len(exemption_clauses)}处免责条款',
                'significance': '重要'
            })

        return analysis

    def analyze_practical_dimension(self, contract_text: str) -> Dict:
        """
        实务维度分析

        核心问题: 在实践中是否可执行、可操作?

        分析要点:
        1. 可执行性
        2. 可操作性
        3. 争议预防
        """
        analysis = {
            'dimension': '实务维度',
            'rating': '良好',
            'findings': [],
            'risks': [],
            'suggestions': []
        }

        # 检查1: 条款明确性
        vague_terms = self._find_vague_terms(contract_text)
        if vague_terms:
            analysis['risks'].append({
                'risk_type': '一般风险',
                'description': f'发现{len(vague_terms)}处模糊表述',
                'level': '一般风险',
                'suggestion': '建议明确时间、金额、标准等关键要素'
            })

        # 检查2: 验收标准
        acceptance_clauses = self._find_acceptance_clauses(contract_text)
        if not acceptance_clauses:
            analysis['risks'].append({
                'risk_type': '重要风险',
                'description': '缺少明确的验收标准',
                'level': '重要风险',
                'suggestion': '建议补充具体的验收标准、程序和时间'
            })

        # 检查3: 争议解决
        dispute_clauses = self._find_dispute_clauses(contract_text)
        if dispute_clauses:
            analysis['findings'].append({
                'category': '争议解决',
                'content': f'已约定争议解决方式: {dispute_clauses[0]}',
                'significance': '重要'
            })
        else:
            analysis['risks'].append({
                'risk_type': '一般风险',
                'description': '未约定争议解决方式',
                'level': '一般风险',
                'suggestion': '建议明确约定仲裁或诉讼管辖'
            })

        return analysis

    def apply_sanguan_foursteps(self, contract_text: str, user_context: Dict) -> Dict:
        """
        应用三观四步法

        四步:
        1. 理解交易
        2. 设计结构 (宏观)
        3. 起草合同 (中观)
        4. 审查完善 (微观)
        """
        foursteps_analysis = {
            'method': '三观四步法',
            'steps': []
        }

        # 第一步: 理解交易
        step1 = {
            'step': '第一步: 理解交易',
            'analysis': {
                'commercial_background': self._analyze_commercial_background(contract_text, user_context),
                'key_risks': self._identify_key_commercial_risks(contract_text, user_context),
                'true_intent': self._infer_true_intent(contract_text, user_context)
            }
        }
        foursteps_analysis['steps'].append(step1)

        # 第二步: 设计结构 (宏观)
        step2 = {
            'step': '第二步: 设计结构 (宏观层面)',
            'analysis': {
                'transaction_type': self._determine_transaction_type(contract_text),
                'transaction_path': self._analyze_transaction_path(contract_text),
                'transaction_parties': self._analyze_transaction_parties(contract_text),
                'transaction_timeline': self._analyze_transaction_timeline(contract_text)
            }
        }
        foursteps_analysis['steps'].append(step2)

        # 第三步: 起草合同 (中观)
        step3 = {
            'step': '第三步: 起草合同 (中观层面)',
            'analysis': {
                'contract_form': self._assess_contract_form(contract_text),
                'clause_completeness': self._check_clause_completeness(contract_text),
                'balance_assessment': self._assess_rights_obligations_balance(contract_text)
            }
        }
        foursteps_analysis['steps'].append(step3)

        # 第四步: 审查完善 (微观)
        step4 = {
            'step': '第四步: 审查完善 (微观层面)',
            'analysis': {
                'legality_check': self._legality_review(contract_text),
                'completeness_check': self._completeness_review(contract_text),
                'executability_check': self._executability_review(contract_text)
            }
        }
        foursteps_analysis['steps'].append(step4)

        return foursteps_analysis

    # ============ 辅助方法 ============

    def _extract_parties(self, text: str) -> List[str]:
        """提取合同主体"""
        parties = []
        # 查找甲方、乙方等
        pattern = r'(甲方|乙方|丙方|委托方|受托方)[：:]\s*([^\n]+)'
        matches = re.findall(pattern, text)
        for role, name in matches:
            parties.append(f"{role}: {name.strip()}")
        return parties

    def _extract_price_terms(self, text: str) -> str:
        """提取价格条款"""
        # 查找价款、价格、费用等
        pattern = r'(总价款|价款|价格|费用|报酬)[：:]\s*([^\n]+)'
        matches = re.findall(pattern, text)
        if matches:
            return f"{matches[0][0]}: {matches[0][1].strip()}"
        return ""

    def _extract_delivery_terms(self, text: str) -> str:
        """提取交付/履行条款"""
        pattern = r'(交付|履行|提供)[：:]\s*([^\n]+)'
        matches = re.findall(pattern, text)
        if matches:
            return f"{matches[0][0]}: {matches[0][1].strip()}"
        return ""

    def _check_essential_clauses(self, text: str, contract_type: str) -> Dict:
        """检查必要条款"""
        essential_by_type = {
            '买卖合同': ['标的', '数量', '价款'],
            '租赁合同': ['租赁物', '租金', '租赁期限'],
            '借款合同': ['借款金额', '利率', '还款期限'],
            'default': ['标的', '价款', '履行期限']
        }

        required = essential_by_type.get(contract_type, essential_by_type['default'])
        found = []
        missing = []

        for clause in required:
            if clause in text:
                found.append(clause)
            else:
                missing.append(clause)

        return {'found': found, 'missing': missing}

    def _assess_balance(self, text: str) -> float:
        """
        评估权利义务平衡性（0-1，1 表示完全平衡）。

        注意：本方法基于"甲方/乙方 + 义务动词"的数量比例做粗粒度估算，
        无法识别条款语义上的不平等（如免责范围不对等、违约金计算基数偏斜等）。
        结果仅作参考，不能替代人工语义审查。
        """
        # 扩展义务动词覆盖范围：应/应当/须/负责/有义务/有责任/不得
        obligation_pattern_a = r'甲方.{0,20}?(应当|应|须|负责|有义务|有责任|不得)'
        obligation_pattern_b = r'乙方.{0,20}?(应当|应|须|负责|有义务|有责任|不得)'

        party_a_obligations = len(re.findall(obligation_pattern_a, text))
        party_b_obligations = len(re.findall(obligation_pattern_b, text))

        if party_a_obligations + party_b_obligations == 0:
            return 0.5  # 无法判断时返回中等

        ratio = min(party_a_obligations, party_b_obligations) / max(party_a_obligations, party_b_obligations)
        return ratio

    def _find_exemption_clauses(self, text: str) -> List[str]:
        """查找免责条款"""
        pattern = r'(免责|不承担.*责任|概不负责)'
        matches = re.findall(pattern, text)
        return matches

    def _find_vague_terms(self, text: str) -> List[str]:
        """查找模糊表述"""
        vague_patterns = [
            r'合理.*时间',
            r'尽快',
            r'适当',
            r'相关',
            r'等(?!.*等.*具体)'
        ]
        vague_found = []
        for pattern in vague_patterns:
            if re.search(pattern, text):
                vague_found.append(pattern)
        return vague_found

    def _find_acceptance_clauses(self, text: str) -> List[str]:
        """查找验收条款"""
        pattern = r'(验收|检验|检查|测试).*?(标准|条件|要求)'
        matches = re.findall(pattern, text)
        return matches

    def _find_dispute_clauses(self, text: str) -> List[str]:
        """查找争议解决条款"""
        pattern = r'(争议|纠纷).*(仲裁|诉讼|法院)'
        matches = re.findall(pattern, text)
        return matches

    def _analyze_commercial_background(self, text: str, context: Dict) -> Dict:
        """分析商业背景"""
        return {
            'parties': self._extract_parties(text),
            'market_position': context.get('position', '未知'),
            'transaction_history': context.get('history', '无'),
            'focus': context.get('focus', '未明确')
        }

    def _identify_key_commercial_risks(self, text: str, context: Dict) -> List[Dict]:
        """识别关键商业风险"""
        risks = []

        if context.get('position') == '弱势':
            risks.append({
                'type': '市场地位风险',
                'description': '处于弱势地位,可能接受不利条款',
                'mitigation': '争取平衡关键条款,引入第三方担保'
            })

        return risks

    def _infer_true_intent(self, text: str, context: Dict) -> Dict:
        """推断交易真实意图（基于合同文本和用户上下文）"""
        parties = self._extract_parties(text)
        price = self._extract_price_terms(text)
        focus = context.get('focus', '')
        position = context.get('position', '')

        hints = []
        if position == '弱势':
            hints.append('用户处于弱势地位，合同条款可能对其不利，需重点关注权利义务对等性')
        if focus:
            hints.append(f'用户重点关注：{focus}，相关条款需重点审查')
        if price:
            hints.append(f'主要交易对价：{price}，需确认支付条件和付款节点')

        return {
            'declared_intent': f'交易双方（{", ".join(parties[:2]) if parties else "甲乙双方"}）达成合同，实现约定交易目的',
            'key_concerns': hints if hints else ['暂无特别关注点'],
            'note': '以上分析基于合同文本和用户描述，建议结合实际谈判背景综合判断'
        }

    def _determine_transaction_type(self, text: str) -> str:
        """根据合同文本内容判断交易类型"""
        type_keywords = {
            '买卖/销售': ['买卖', '销售', '购买', '出售', '货物', '商品'],
            '服务': ['服务', '委托', '咨询', '维护', '运营', '代理'],
            '技术开发': ['技术开发', '软件开发', '系统开发', '定制开发', '技术服务'],
            '租赁': ['租赁', '出租', '承租', '租金', '租期'],
            '借款': ['借款', '贷款', '利息', '还款', '出借'],
            '股权投资': ['股权', '股份', '增资', '投资', '估值'],
            '建设工程': ['工程', '施工', '建设', '承包', '发包'],
            '混合型': []
        }
        matched = []
        for ttype, keywords in type_keywords.items():
            if ttype == '混合型':
                continue
            if sum(1 for kw in keywords if kw in text) >= 2:
                matched.append(ttype)

        if len(matched) == 0:
            return '通用合同（类型未明确识别）'
        elif len(matched) == 1:
            return matched[0]
        else:
            return f'混合型合同（{" + ".join(matched)}）'

    def _analyze_transaction_path(self, text: str) -> Dict:
        """分析交易路径：识别实际约定的交易阶段"""
        stage_keywords = {
            '签约': ['签订', '生效', '签署'],
            '预付款': ['预付', '定金', '订金', '首付'],
            '需求确认': ['需求确认', '需求书', '方案确认'],
            '开发/履行': ['开发', '施工', '提供服务', '交付', '履行'],
            '验收': ['验收', '检验', '测试', '确认完成'],
            '尾款支付': ['尾款', '余款', '最终付款', '结清'],
            '质保/维护': ['质保', '维护', '保修', '维修期'],
        }
        present_stages = [stage for stage, kws in stage_keywords.items()
                          if any(kw in text for kw in kws)]

        # 检测是否为分期付款
        installment = bool(re.search(r'(\d+%|\d+\s*[%％]|分期|首付|尾款)', text))

        return {
            'stages': present_stages if present_stages else ['签约', '履行', '付款'],
            'installment_payment': installment,
            'stage_count': len(present_stages)
        }

    def _analyze_transaction_parties(self, text: str) -> List[str]:
        """分析交易主体及其角色"""
        return self._extract_parties(text)

    def _analyze_transaction_timeline(self, text: str) -> Dict:
        """从合同文本中提取关键时间节点"""
        # 提取所有时间表达
        time_pattern = re.compile(
            r'(?:自|于|在|起)?.{0,10}?(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?'
            r'|\d+\s*(?:个)?\s*(?:自然日|工作日|日|天|月|年)(?:内|后|起))',
            re.DOTALL
        )
        raw_dates = time_pattern.findall(text)
        dates = list(dict.fromkeys(raw_dates))[:6]  # 去重取前6个

        # 判断交易类型（一次性 vs 分阶段）
        is_phased = bool(re.search(r'分期|分批|阶段|进度', text))

        return {
            'transaction_mode': '分阶段交易' if is_phased else '一次性交易',
            'key_time_points': dates if dates else ['合同未明确约定具体时间节点'],
        }

    def _assess_contract_form(self, text: str) -> Dict:
        """评估合同形式完整性"""
        # 检查基本结构要素
        has_title = bool(re.search(r'合同|协议', text[:200]))
        has_parties = bool(re.search(r'甲方|乙方|委托方|受托方', text))
        has_signature = bool(re.search(r'签字|盖章|签署|签名', text))
        has_date = bool(re.search(r'日期|年.*月.*日|签订于', text))
        has_amount = bool(re.search(r'\d+(?:\.\d+)?\s*(?:元|万元|万|%)', text))

        issues = []
        if not has_title:
            issues.append('合同标题不明确')
        if not has_parties:
            issues.append('缺少明确的合同主体')
        if not has_signature:
            issues.append('缺少签署栏')
        if not has_date:
            issues.append('签约日期未填写或缺失')

        return {
            'has_title': has_title,
            'has_parties': has_parties,
            'has_signature': has_signature,
            'has_date': has_date,
            'has_amount': has_amount,
            'form_issues': issues if issues else ['合同形式要素完整'],
            'form_score': f'{(5 - len(issues)) * 20}分（满分100分）'
        }

    def _check_clause_completeness(self, text: str) -> Dict:
        """检查合同必要条款完整性"""
        # 通用必要条款检查
        essential = {
            '合同标的': ['标的', '服务内容', '产品', '工程范围', '货物'],
            '价款/报酬': ['价款', '金额', '费用', '报酬', '租金'],
            '履行期限': ['期限', '日内', '工作日', '交付日', '完成时间'],
            '违约责任': ['违约', '违约金', '赔偿', '罚款'],
            '争议解决': ['争议', '仲裁', '诉讼', '法院'],
        }
        present = {}
        missing = []
        for clause, keywords in essential.items():
            if any(kw in text for kw in keywords):
                present[clause] = True
            else:
                missing.append(clause)

        return {
            'present_clauses': list(present.keys()),
            'missing_clauses': missing if missing else ['必要条款齐全'],
            'completeness_rate': f'{len(present)}/{len(essential)}'
        }

    def _assess_rights_obligations_balance(self, text: str) -> Dict:
        """评估权利义务平衡性（量化版）"""
        balance_score = self._assess_balance(text)

        # 查找单方免责条款
        unilateral_exemptions = re.findall(
            r'(甲方|乙方).{0,30}?(不承担|免于|无需承担|概不负责)', text
        )

        # 查找单方解除权
        unilateral_termination = re.findall(
            r'(甲方|乙方).{0,30}?(有权解除|单方解除|有权终止)', text
        )

        level = ('严重不平衡' if balance_score < 0.3
                 else '轻微不平衡' if balance_score < 0.6
                 else '基本平衡')

        return {
            'balance_score': round(balance_score, 2),
            'balance_level': level,
            'unilateral_exemptions': [f'{m[0]}免责条款' for m in unilateral_exemptions],
            'unilateral_termination': [f'{m[0]}单方解除权' for m in unilateral_termination],
            'note': '评分基于义务动词统计，语义层面不平衡需人工进一步判断'
        }

    def _legality_review(self, text: str) -> Dict:
        """合法性审查：检查常见违法风险点"""
        issues = []

        # 检查利率（民间借贷）
        if re.search(r'利率|利息', text):
            high_rate = re.search(r'(\d+)\s*%', text)
            if high_rate and int(high_rate.group(1)) > 24:
                issues.append(f'约定利率{high_rate.group(1)}%，可能超过LPR4倍上限，超过部分无效')

        # 检查竞业限制期限
        if '竞业' in text:
            years = re.search(r'竞业.{0,10}?(\d+)\s*年', text)
            if years and int(years.group(1)) > 2:
                issues.append(f'竞业限制期限{years.group(1)}年，超过法定2年上限，超过部分无效')

        # 检查免除人身损害赔偿的免责条款（无效）
        if re.search(r'免除.{0,10}?(人身伤害|生命安全|故意|重大过失)', text):
            issues.append('存在免除人身损害或故意/重大过失责任的条款，该类免责条款无效（民法典第506条）')

        # 检查格式条款异常加重对方责任
        exemption_count = len(re.findall(r'不承担|免于|概不负责|免责', text))
        if exemption_count >= 3:
            issues.append(f'合同中存在{exemption_count}处免责表述，需检查是否属于格式条款且不合理加重对方责任')

        return {
            'legality_issues': issues if issues else ['未发现明显违法条款'],
            'mandatory_violation_risk': '高' if issues else '低',
            'legal_basis': '民法典第506条（无效免责条款）、第680条（借贷利率）、劳动合同法第24条（竞业限制）'
        }

    def _completeness_review(self, text: str) -> Dict:
        """完整性审查：必要条款 + 常见遗漏条款"""
        completeness = self._check_clause_completeness(text)

        # 检查常见但容易遗漏的条款
        often_missed = {
            '知识产权归属': ['知识产权', '著作权', '专利', '版权'],
            '保密条款': ['保密', '机密', '不得泄露'],
            '不可抗力': ['不可抗力', '自然灾害', '政府行为'],
            '合同变更程序': ['变更', '修改', '补充协议', '书面同意'],
            '通知送达方式': ['通知', '送达', '联系方式', '邮件', '地址'],
        }
        missing_optional = [
            clause for clause, kws in often_missed.items()
            if not any(kw in text for kw in kws)
        ]

        return {
            'essential_missing': completeness['missing_clauses'],
            'optional_missing': missing_optional if missing_optional else ['常见条款基本完整'],
            'completeness_rate': completeness['completeness_rate'],
            'recommendation': f'缺失{len(completeness["missing_clauses"])}个必要条款' if completeness['missing_clauses'] != ['必要条款齐全'] else '必要条款齐全'
        }

    def _executability_review(self, text: str) -> Dict:
        """可执行性审查：模糊表述 + 争议预防机制"""
        vague_found = self._find_vague_terms(text)

        # 检查是否有具体的违约金计算方式
        has_penalty_formula = bool(re.search(
            r'违约金.{0,20}?(\d+%|万分之|日.*%|按.*计算)', text
        ))

        # 检查争议解决机制完整性
        dispute_clauses = self._find_dispute_clauses(text)
        has_jurisdiction = bool(re.search(r'法院|仲裁委|仲裁院', text))

        operability_issues = []
        if vague_found:
            operability_issues.append(f'存在{len(vague_found)}处模糊表述（如"合理时间"、"尽快"等）')
        if not has_penalty_formula:
            operability_issues.append('违约金缺少具体计算方式，争议时难以执行')
        if not has_jurisdiction:
            operability_issues.append('未明确争议解决机构/管辖法院')

        return {
            'vague_terms': vague_found,
            'has_penalty_formula': has_penalty_formula,
            'has_dispute_resolution': bool(dispute_clauses),
            'operability_issues': operability_issues if operability_issues else ['条款可执行性良好'],
            'recommendation': '建议明确' + '、'.join(operability_issues) if operability_issues else '可执行性无明显问题'
        }


if __name__ == '__main__':
    # 测试代码
    print("=== 三观四步法分析模块测试 ===\n")

    analyzer = SanguanAnalysis()

    sample_contract = """
    买卖合同

    甲方：A公司
    乙方：B公司

    第一条 标的物
    本合同标的物为XXX产品。

    第二条 价款
    总价款人民币100万元。

    第三条 交付
    甲方应尽快交付产品。

    第四条 违约责任
    任何一方违约应承担责任。
    """

    user_context = {
        'party': '甲方',
        'position': '弱势',
        'history': '无',
        'focus': '付款安全'
    }

    # 测试三维审查法
    print("=== 三维审查法 ===")
    commercial = analyzer.analyze_commercial_dimension(sample_contract, user_context)
    print(f"商业维度: {commercial['rating']}")
    print(f"发现数量: {len(commercial['findings'])}")
    print(f"风险数量: {len(commercial['risks'])}\n")

    legal = analyzer.analyze_legal_dimension(sample_contract, '买卖合同')
    print(f"法律维度: {legal['rating']}")
    print(f"发现数量: {len(legal['findings'])}")
    print(f"风险数量: {len(legal['risks'])}\n")

    practical = analyzer.analyze_practical_dimension(sample_contract)
    print(f"实务维度: {practical['rating']}")
    print(f"发现数量: {len(practical['findings'])}")
    print(f"风险数量: {len(practical['risks'])}\n")

    # 测试三观四步法
    print("\n=== 三观四步法 ===")
    foursteps = analyzer.apply_sanguan_foursteps(sample_contract, user_context)
    for step in foursteps['steps']:
        print(f"\n{step['step']}")
        for key, value in step['analysis'].items():
            print(f"  {key}: {value}")

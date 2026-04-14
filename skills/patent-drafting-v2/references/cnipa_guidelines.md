# Patent Drafting — CNIPA (China) Guidelines

Key differences between USPTO and CNIPA practice.
Reference: 中国专利法 (CN Patent Law), 专利审查指南 (Patent Examination Guidelines, 2023).

---

## Overview: How CNIPA Differs from USPTO

| Issue | USPTO | CNIPA |
|-------|-------|-------|
| Grace period | 12 months before filing | **No grace period** — any public disclosure before filing destroys novelty |
| Software/AI patents | Allowed if passes Alice two-step | Allowed if has "technical character" producing "technical effect" |
| Business methods | Almost always rejected (101) | Rejected as 智力活动规则 (rules for mental activities) — Article 25 |
| Claim format | Flexible | Must follow 独立权利要求 + 从属权利要求 structure |
| Unity of invention | One independent concept per application | Strictly enforced — one general inventive concept |
| Continuation practice | Robust (CIP, RCE, continuation) | 分案申请 (divisional) only — no CIP equivalent |
| Prosecution history estoppel | Applies | Applies (修改/意见书均影响保护范围) |
| Examination timeline | 2–3 years average | 1.5–2 years average (faster than USPTO) |
| Filing language | English | **Chinese required** — file in Chinese or translate within specified period |

---

## Subject Matter Eligibility — 专利法第25条

### What Cannot Be Patented in China

| Excluded Category | Chinese Term | Notes |
|-----------------|-------------|-------|
| Scientific discoveries | 科学发现 | Natural laws, mathematical theorems |
| Mental activity rules | 智力活动的规则和方法 | Business methods, game rules, pure algorithms |
| Disease diagnosis/treatment methods | 疾病诊断和治疗方法 | Diagnostic devices are patentable; methods are not |
| Animal/plant varieties | 动植物品种 | Breeders' rights available instead |
| Nuclear transformation methods | 原子核变换方法 | — |

### Software and AI Patents in China

**China allows software and AI patents** — but only when the claims describe:
1. A **technical solution** (技术方案) to a **technical problem** (技术问题)
2. Using **technical means** (技术手段) that produce a **technical effect** (技术效果)

This is broader than the US Alice standard in practice.

#### CNIPA Software Patent Strategy

**Structure every claim as:**
```
Problem: [What technical problem does this solve?]
Means:   [What specific technical means/architecture solves it?]
Effect:  [What measurable technical effect results?]
```

**Claim framing that works in China:**
```
"一种数据处理方法，其特征在于，包括：
  接收包含传感器采集的原始数据的数据流；
  通过卷积神经网络对所述原始数据进行特征提取，
    得到特征向量；
  基于所述特征向量，采用支持向量机分类器进行分类，
    输出分类结果；
  其中，所述卷积神经网络包括三个卷积层和两个池化层，
    处理延迟相比传统方法降低40%。"
```

Key elements: specific architecture (CNN structure), specific technical result (40% latency reduction).

**What to avoid:**
```
WRONG: "一种推荐方法，包括：收集用户数据；分析数据；推荐内容。"
       Pure data collection + analysis = 智力活动规则 → rejected.

RIGHT: "一种推荐方法，包括：
         通过用户终端的嵌入式传感器采集行为数据；
         采用基于注意力机制的Transformer模型对行为序列进行编码；
         基于编码结果生成推荐列表，并将推荐请求响应时间降低至50ms以内。"
       Technical means (sensor, transformer model) + technical effect (50ms) = allowable.
```

---

## Claim Format Requirements

### Independent Claim (独立权利要求)
Must contain:
1. **前序部分 (Preamble):** Type of subject matter + known features from closest prior art
2. **特征部分 (Characterizing portion):** Novel and inventive features, introduced by "其特征在于" (characterized in that)

```
"一种[发明类型]，[已知技术特征]，其特征在于，[新颖的技术特征]。"

Example:
"一种图像处理装置，包括处理器和存储器，其特征在于，
 所述处理器被配置为：
   执行基于注意力机制的特征提取算法；以及
   将提取的特征与预存储的模板进行对比，
     当相似度超过阈值时输出匹配信号。"
```

### Dependent Claim (从属权利要求)
- Must reference the parent claim number
- Must add at least one additional technical limitation
- Cannot broaden the parent claim

```
"根据权利要求1所述的装置，其特征在于，
 所述注意力机制为多头自注意力机制，注意力头数为8。"
```

### Claim Category Equivalents

| USPTO | CNIPA |
|-------|-------|
| Method claim | 方法权利要求 |
| System/Apparatus claim | 装置/设备权利要求 |
| CRM claim | 计算机可读存储介质权利要求 (non-transitory = 非暂时性) |
| Product-by-process | 产品权利要求（通过方法限定）|

---

## No Grace Period — Critical Rule

**This is the most important CNIPA difference for Chinese inventors.**

Under 专利法第24条, only the following disclosures are exempt from destroying novelty:
1. Disclosed at a government-designated international exhibition
2. Disclosed at a prescribed academic conference
3. Disclosed without the applicant's consent (i.e., stolen)

**Any other public disclosure before filing destroys novelty in China — permanently.**

This includes:
- Academic papers published before filing date
- Conference presentations (even if not in China)
- Product demos, trade shows
- Social media posts describing the invention
- Thesis publications

**Rule:** File in China BEFORE any public disclosure. File a PCT application if international protection is needed simultaneously.

---

## Divisional Applications (分案申请)

China does not have CIP (continuation-in-part) applications. Only divisionals are available.

**When to file a divisional:**
- CNIPA issues a lack of unity rejection
- You want to pursue additional claims not covered in the parent
- Parent is about to issue and you need to keep prosecution open

**Deadline:** File divisional before the parent application is granted or finally rejected. The divisional inherits the parent's filing date.

---

## Responding to Common CNIPA Rejections

### Rejection: 缺乏新颖性 (Lack of Novelty) — Article 22.2

Same as USPTO 102 anticipation. All claim elements must appear in a single reference.

**Response strategy:**
1. Argue the reference does not literally disclose the distinguishing element
2. Provide a detailed comparison showing the difference
3. If needed, amend to add the missing element as a limitation

### Rejection: 缺乏创造性 (Lack of Inventive Step) — Article 22.3

Equivalent to USPTO 103 obviousness. Examiner must cite motivation to combine.

**Response strategy:**
1. Challenge the motivation to combine: "本领域技术人员没有理由将两者结合，因为..."
2. Argue unexpected technical effect (意想不到的技术效果)
3. Submit expert declaration (意见陈述书) if needed
4. Amend to add non-obvious distinguishing features

### Rejection: 客体不属于专利保护的范围 — Article 25 (Subject Matter)

Claim is directed to excluded subject matter (usually: pure software/algorithm/business method).

**Response strategy:**
1. Amend claims to emphasize technical character:
   - Add specific hardware components
   - Add specific technical effects with measurable results
   - Frame the claim around solving a technical problem using technical means
2. Add language: "其中，所述方法在处理器上执行，产生[具体技术效果]"

### Rejection: 说明书公开不充分 (Insufficient Disclosure) — Article 26.3

Equivalent to USPTO 112(a) enablement.

**Response strategy:**
1. Point to spec sections that provide sufficient disclosure
2. If needed, add embodiments via amendment (if supported by original disclosure)
3. Submit supplementary examples (补充实施例) as evidence

---

## CNIPA vs. USPTO Claim Drafting Checklist

When preparing claims for China filing:

- [ ] Filed BEFORE any public disclosure (no grace period)
- [ ] Claims follow 独立权利要求 two-part format with "其特征在于"
- [ ] Software/AI claims explicitly state technical problem, technical means, technical effect
- [ ] No pure algorithm or business method claims (Article 25)
- [ ] Disease diagnosis/treatment methods converted to device/apparatus claims
- [ ] All claims filed in Chinese (or translated within 2 months of international filing date for PCT)
- [ ] Unity of invention confirmed — one general inventive concept
- [ ] Divisional strategy planned if multiple inventions exist
- [ ] PCT priority chain correctly established if claiming foreign priority
- [ ] Priority document certified copy filed within 3 months of CN filing date

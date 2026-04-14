---
name: trademark-search
description: Search trademark databases (China CNIPA, US USPTO, and WIPO) to check name availability and registration details. Use when the user wants to check if a name is trademarked, research trademark availability, or look up registration status. No API key required.
---

# 商标查询 / Trademark Search

支持**中国（CNIPA）**、**美国（USPTO）**和**国际（WIPO）**商标数据库查询，检查商标可注册状态和注册详情。主要通过网络搜索实现——大多数商标数据库屏蔽自动化请求。

Supports **China (CNIPA)**, **US (USPTO)**, and **international (WIPO)** trademark database searches. Uses web search as the primary method.

## When to Use

- 用户想查询某名称/品牌是否已注册商标（中国或美国）
- 用户在为产品命名前研究商标可注册性
- 用户想查询现有商标注册状态
- User asks "is [name] trademarked?" or "can I use [name]?"

## 管辖权判断 / Jurisdiction Detection

**优先询问用户的目标市场**：中国市场查 CNIPA，美国市场查 USPTO，全球品牌同时查两个 + WIPO。

| 目标市场 | 主要数据库 | 备注 |
|---------|-----------|------|
| 中国 | CNIPA（国知局） | 中文/拼音检索 |
| 美国 | USPTO | 英文检索 |
| 国际/全球 | WIPO Global Brand DB | 马德里体系 |

## Important Disclaimer

**本技能仅提供信息性数据，不构成法律意见。** 商标可注册性受多种因素影响（近似度、混淆可能性、商品/服务类别等），请咨询专业商标代理人。

**This skill provides informational data only — not legal advice.** Always recommend the user consult a trademark attorney for definitive guidance.

## Known Limitations

Direct `web_fetch` calls to trademark databases **will not work** — they block automated requests:

| Source | Direct Fetch | Status |
|--------|-------------|--------|
| tmsearch.uspto.gov | ❌ JS-rendered, no useful content | Blocked |
| tsdr.uspto.gov | ❌ Returns 403 | Blocked |
| trademarkia.com | ❌ Returns 403 | Blocked |
| branddb.wipo.int | ❌ JS-rendered | Blocked |

**Web search is the primary (and reliable) approach.** Search engines index these databases, so you can find trademark records through `web_search` queries with `site:` filters.

## Step 1: Web Search for Trademark Records (Primary Method)

Use `web_search` to find trademark registrations. This is the most reliable approach.

### Search USPTO Records

```
web_search: "BRAND_NAME" trademark site:tsdr.uspto.gov
```

```
web_search: "BRAND_NAME" trademark site:uspto.gov
```

### Search Trademarkia (Indexed by Search Engines)

```
web_search: "BRAND_NAME" site:trademarkia.com
```

Trademarkia results typically include: mark name, serial/registration number, status (LIVE/DEAD), owner, filing date, and Nice Classification class.

### Search Broadly

```
web_search: "BRAND_NAME" trademark registered
```

```
web_search: "BRAND_NAME" site:tmdn.org
```

### What to Look For in Results

- **TSDR links** (tsdr.uspto.gov/statusview/sn... or rn...) → existing trademark record with serial/registration number
- **Trademarkia listings** → status, owner, class, filing/registration dates
- **Company websites** claiming "®" or "™" → claimed/registered marks
- **Nice Classification class** for goods/services — critical for determining if a mark conflicts with your intended use

## Step 1.5: Similar Mark Search — 近似商标检索（必做）

Exact-match searches miss most conflicts. Always search for phonetically, visually, and semantically similar marks.

### 中文品牌近似检索策略

**音近（同音/近音）：** 商标审查首要考虑混淆可能性，同音字是最高风险。

```
示例：品牌名"牧云"
→ 检索：沐云、木云、慕云、牧韵、牧芸、牧熏（音近）
→ 检索：MUYUN（拼音）
```

**形近（字形相似）：** 汉字形近容易导致视觉混淆。

```
示例：品牌名"云朵"
→ 检索：云彩、云端（意近）
→ 检索：云朵儿、小云朵（加字变体）
```

**检索模板：**
```
web_search: [近似名称1] 商标注册 第X类
web_search: [拼音] 商标 CNIPA
web_search: [英文对应] trademark China registered
```

### 英文品牌近似检索策略

| 变体类型 | 示例（原名：NovaPay） | 检索方式 |
|---------|-------------------|---------|
| 音近 | NovaPlay, NovaPe | `web_search: "NovaPay" OR "NovaPlay" trademark` |
| 缩写/拼写变体 | Nova Pay, NOVAPAY | 分别检索带空格和全大写版本 |
| 前后缀变体 | MyNovaPay, NovaPayments | `web_search: "NovaPay" trademark site:trademarkia.com` |
| 意近 | NewPay（Nova=新） | 检索核心语义词 |

### 近似商标风险等级

| 相似度 | 风险 | 说明 |
|--------|------|------|
| 完全相同 | 🔴 极高 | 直接冲突，无法注册 |
| 同音异字 | 🔴 高 | 混淆可能性极大 |
| 形近（1-2字不同） | 🟠 高 | 审查员会驳回 |
| 意义相近 | 🟡 中 | 看类别是否相同 |
| 仅部分相同 | 🟡 中 | 需结合整体判断 |
| 构成要素相似 | 🔵 低-中 | 需专业判断 |

## Step 2: Extract Details from Search Results

Search results from Trademarkia and USPTO typically contain enough detail in the snippet:

- **Mark name** and any design description
- **Serial number** (application) or **Registration number**
- **Status:** LIVE (active) or DEAD (abandoned/cancelled/expired)
- **Owner name**
- **Class(es)** of goods/services
- **Filing and registration dates**

If you need more detail, try fetching the specific Trademarkia result URL — some individual pages may load, though the search pages are blocked.

### Key Status Values

| Status | Meaning |
|--------|---------|
| **LIVE** | Active trademark — registered or pending |
| **DEAD** | Abandoned, cancelled, or expired |
| **Registered** | Fully registered and active |
| **Published for Opposition** | Pending — 30-day window for objections |
| **Abandoned** | Application was abandoned |
| **Cancelled** | Registration was cancelled |
| **Expired** | Registration expired (not renewed) |

## Step 3: Check International Marks (Optional)

For products with international reach, also search:

```
web_search: "BRAND_NAME" trademark site:branddb.wipo.int
```

```
web_search: "BRAND_NAME" trademark international WIPO
```

## Trademark Classes (Nice Classification) — 尼斯分类完整参考

A trademark only protects within its registered class(es). A name can be registered by different entities in different classes. When a user asks about a specific product/service, map it to the correct class(es) before searching.

### 商品类别（第1-34类）/ Goods (Classes 1–34)

| 类别 | 中文描述 | English | 典型场景 |
|------|---------|---------|---------|
| 1 | 工业化学品、化学试剂 | Chemicals | 化工、实验室 |
| 2 | 涂料、防锈剂、染料 | Paints, varnishes | 油漆、涂层 |
| 3 | 化妆品、清洁用品、香水 | Cosmetics, cleaning | 护肤、美妆、洗涤 |
| 4 | 工业用油脂、燃料、蜡烛 | Lubricants, fuels | 润滑油、燃油 |
| 5 | 药品、医疗制剂、保健品 | Pharmaceuticals | 药品、营养品 |
| 6 | 金属材料、金属建材 | Metals | 钢铁、五金 |
| 7 | 机器设备、工业用电机 | Machines, motors | 工业机械 |
| 8 | 手工工具、餐具刀叉 | Hand tools, cutlery | 刀具、工具 |
| **9** | **软件、电子产品、APP、仪器** | **Software, electronics** | **互联网、手机、AI** |
| 10 | 医疗器械 | Medical apparatus | 医疗设备 |
| 11 | 照明、空调、炊具家电 | Lighting, heating, cooking | 家电、灯具、咖啡机 |
| 12 | 交通运输工具 | Vehicles | 汽车、摩托车 |
| 13 | 武器、火药 | Firearms | 军工 |
| 14 | 珠宝首饰、钟表 | Jewelry, watches | 金银珠宝、手表 |
| 15 | 乐器 | Musical instruments | 钢琴、吉他 |
| 16 | 纸制品、文具、印刷品 | Paper, stationery | 办公用品、出版物 |
| 17 | 橡胶、塑料制品 | Rubber, plastics | 密封件、管材 |
| 18 | 皮革、箱包、皮具 | Leather goods, bags | 皮包、行李箱 |
| 19 | 非金属建筑材料 | Building materials | 瓷砖、玻璃 |
| 20 | 家具、镜子、木制品 | Furniture | 沙发、床具 |
| 21 | 厨具、玻璃器皿 | Household utensils | 厨房用品 |
| 22 | 绳索、纤维、帆布 | Ropes, fibers | 纺织原料 |
| 23 | 纺织用纱线 | Yarns, threads | 纱线 |
| 24 | 纺织品、床上用品、窗帘 | Textiles, bed/table covers | 布料、毛巾、被子 |
| **25** | **服装、鞋帽** | **Clothing, footwear** | **服装品牌** |
| 26 | 花边、缎带、纽扣 | Lace, ribbons, buttons | 服装配件 |
| 27 | 地毯、垫子、壁纸 | Carpets, wallpaper | 地板铺设 |
| 28 | 游戏、玩具、体育用品 | Games, toys, sports goods | 玩具、电竞外设 |
| 29 | 肉类、水产、蔬菜、乳制品 | Meat, fish, dairy | 食品（加工类） |
| **30** | **咖啡、茶、面包、糖、调味品** | **Coffee, tea, bread** | **饮料、餐饮食品** |
| 31 | 生鲜农产品、动物饲料 | Fresh produce, animal feed | 农产品、宠物食品 |
| 32 | 啤酒、饮料（非酒精）、矿泉水 | Beer, beverages | 饮料、矿泉水 |
| 33 | 含酒精饮料（啤酒除外）| Alcoholic beverages | 白酒、葡萄酒 |
| 34 | 烟草、烟具 | Tobacco | 香烟、电子烟 |

### 服务类别（第35-45类）/ Services (Classes 35–45)

| 类别 | 中文描述 | English | 典型场景 |
|------|---------|---------|---------|
| **35** | **广告、商业管理、零售服务、电商** | **Advertising, retail** | **电商平台、连锁零售** |
| **36** | **金融、保险、银行、支付** | **Finance, insurance** | **金融科技、支付** |
| 37 | 建筑施工、维修保养 | Construction, repair | 装修、维修 |
| 38 | 电信、互联网通信 | Telecommunications | 运营商、即时通讯 |
| 39 | 运输、旅游、仓储 | Transport, travel | 物流、旅游 |
| 40 | 材料加工、印刷 | Treatment of materials | 加工制造 |
| **41** | **教育、培训、娱乐、体育** | **Education, entertainment** | **在线教育、游戏、媒体** |
| **42** | **科技服务、SaaS、软件设计、研发** | **IT services, SaaS** | **云服务、AI、软件** |
| **43** | **餐饮服务、住宿** | **Food services, hotels** | **餐厅、奶茶店、酒店** |
| 44 | 医疗、美容、农业 | Medical, beauty, agriculture | 医院、美容院 |
| 45 | 法律服务、安全、个人社交 | Legal, security services | 律所、安保 |

### 快速类别定位指南

| 用户业务 | 必查类别 | 建议同时查 |
|---------|---------|---------|
| 互联网/APP/AI | 第9类 | 第35类、第42类 |
| 餐饮/奶茶/咖啡 | 第43类 | 第30类、第32类 |
| 服装品牌 | 第25类 | 第35类 |
| 电商平台 | 第35类 | 第9类、第42类 |
| 金融科技/支付 | 第36类 | 第9类、第35类 |
| 教育/培训 | 第41类 | 第9类、第42类 |
| 游戏/电竞 | 第41类 | 第9类、第28类 |
| 美妆/护肤 | 第3类 | 第35类 |
| 食品/饮料 | 第29-32类（按品类） | 第35类、第43类 |
| 医疗/保健品 | 第5类 | 第10类、第44类 |
| 物流/快递 | 第39类 | 第35类 |

## Output Format

### Availability Check

```
### Trademark Search: "BRAND NAME"

**⚠️ Disclaimer:** This is an informational search only, not legal advice. Consult a trademark attorney before making business decisions.

#### Findings

**Exact Matches Found:** Yes/No

1. **BRAND NAME** — Registration #1234567
   Status: 🟢 LIVE / Registered
   Owner: Company Name, Inc.
   Filed: Jan 15, 2020 · Registered: Aug 3, 2020
   Class: 9 (Software), 42 (SaaS)
   Goods/Services: "Computer software for project management..."
   🔗 https://tsdr.uspto.gov/statusview/rn1234567

2. **BRAND NAME** — Serial #90123456
   Status: 🔴 DEAD / Abandoned
   Owner: Other Company LLC
   Filed: Mar 1, 2019 · Abandoned: Sep 15, 2019
   Class: 35 (Business services)

#### Similar Marks Found
- BRAND NAYME — Reg #2345678 (Class 9, LIVE)
- BRANDNAME — Reg #3456789 (Class 42, LIVE)

#### Assessment
- [Summary of what was found]
- [Note relevant classes vs user's intended use]
- [Recommend next steps]
```

### Quick Check

```
### Trademark: "BRAND NAME"

✅ No exact matches found in USPTO database.
⚠️ Similar marks exist: [list]
📋 Recommended classes to check: 9, 42 (if software)

**Next steps:** Consider a comprehensive search with a trademark attorney before filing.
```

## Error Handling

- **No results from web search:** This doesn't mean the name is available — it may not be indexed yet, or it may be too new. Note this uncertainty.
- **Conflicting info across sources:** Trademarkia may lag behind USPTO. When in doubt, note the discrepancy and recommend checking the official USPTO site directly.
- **Too many results:** Narrow with class filters or add the specific goods/services category to the search query.

## Important Caveats to Always Mention

1. **Common law trademarks** exist without registration — a name can be "taken" even if not in the USPTO database
2. **State registrations** are separate from federal (USPTO) registrations
3. **International marks** may conflict — check WIPO if relevant
4. **Likelihood of confusion** matters — similar (not just identical) marks can conflict
5. **Class matters** — same name can coexist in different goods/services classes
6. **This is not legal advice** — always recommend consulting a trademark attorney

## Examples

### Example 1: "Is 'Stellar' trademarked?"

1. `web_search: "Stellar" trademark site:tsdr.uspto.gov`
2. `web_search: "Stellar" site:trademarkia.com`
3. Review search result snippets for serial/registration numbers, status, class
4. Present findings with class info and assessment

### Example 2: "Can I use 'NovaPay' for a fintech app?"

1. `web_search: "NovaPay" trademark`
2. `web_search: "NovaPay" site:trademarkia.com`
3. Check results for marks in Class 9 (software) and Class 36 (financial services)
4. Present findings and note relevant classes for fintech

### Example 3: "Check trademark status for registration number 5678901"

1. `web_search: USPTO trademark registration 5678901`
2. Look for TSDR or Trademarkia links in results with status details
3. Present the current status, owner, and class information

---

## 中国商标查询（CNIPA）

### 数据库说明

| 来源 | 直连 | 说明 |
|------|------|------|
| wsjs.cnipa.gov.cn（国知局商标局） | ❌ 需登录/JS渲染 | 官方数据库，被拦截 |
| trademark.cn10.com.cn | ❌ 拦截 | 中国商标网 |
| patentics.com | 部分可用 | 第三方聚合 |

**主要方法同样为 `web_search`。**

### 中国商标检索步骤

**Step 1：搜索商标局索引记录**

```
web_search: "品牌名" 商标 注册 site:cnipa.gov.cn
web_search: "品牌名" 商标注册查询
web_search: "品牌名" trademark China CNIPA registered
```

**Step 2：搜索第三方平台（已被搜索引擎索引）**

```
web_search: "品牌名" site:patentics.com
web_search: "品牌名" 商标 site:qcc.com
web_search: "品牌名" 商标 企查查
```

**Step 3：按类别和拼音搜索**

中国商标检索需同时考虑：
- 汉字原文（如"小米"）
- 拼音（如"XIAOMI"）
- 英文对应名称

```
web_search: XIAOMI 商标 第9类
web_search: "小米" 商标注册 电子产品
```

### 中国商标状态说明

| 状态 | 含义 |
|------|------|
| 已注册 | 有效注册，受保护 |
| 初审公告 | 申请通过初审，公示3个月 |
| 申请中 | 待审查 |
| 无效/撤销 | 已失效，可重新申请 |
| 驳回 | 申请被拒 |

### 中国商标类别（尼斯分类，常用）

| 类别 | 商品/服务 |
|------|----------|
| 第9类 | 软件、电子产品、手机 |
| 第35类 | 广告、商业管理、电商平台 |
| 第38类 | 通信服务、即时通讯 |
| 第41类 | 教育、娱乐、在线内容 |
| 第42类 | 科技服务、SaaS、软件设计 |

### 中国商标输出格式

```
### 中国商标查询："品牌名"

⚠️ 免责声明：本查询仅供参考，不构成法律意见。请咨询专业商标代理人。

#### 查询结果

**完全匹配：** 有/无

1. **品牌名** — 注册号：XXXXXXXX
   状态：已注册（有效期至 XXXX年）
   注册人：XX公司
   申请日：XXXX-XX-XX · 注册日：XXXX-XX-XX
   类别：第9类（计算机软件）

#### 近似商标
- 近似商标名 — 注册号 XXXXXXXX（第9类，有效）

#### 评估
- [查询发现摘要]
- [与用户目标类别的相关性]
- [建议下一步]
```

### 中国商标特别注意事项

1. **抢注风险高**：中国商标实行"申请在先"原则，知名品牌常遭抢注
2. **全类注册**：重要品牌建议在多个类别注册防止被抢注
3. **拼音和英文**：建议中英文及拼音同步注册
4. **代理人要求**：境外申请人在中国注册商标必须委托中国商标代理机构
5. **审查周期**：中国商标审查周期约9-12个月

---

## 商标申请流程指引 / Filing Guide

当用户查询结果显示商标可能可注册时，提供以下下一步指引：

### 中国商标申请流程（CNIPA）

```
第一步：委托代理人做全面检索
  → 费用：500-1500元/次（付费数据库检索）
  → 周期：1-3个工作日
  → 重要：网络免费检索不能替代专业检索

第二步：准备申请材料
  → 商标图样（标准格式，JPG/PDF）
  → 申请人信息（营业执照或个人身份证）
  → 指定商品/服务项目（对应尼斯分类）

第三步：提交申请
  → 渠道：CNIPA官网在线申请 或 委托代理机构
  → 官费：300元/类（电子申请减按270元）
  → 代理费：约500-1500元/类

第四步：等待审查
  → 形式审查：约1个月
  → 实质审查：约9-12个月
  → 初审公告：3个月公示期，无异议则注册

第五步：获得注册证
  → 商标有效期：10年，到期可续展
  → 连续三年不使用可被撤销
```

**费用汇总：** 每类别约1000-3000元（官费+代理费），建议同时注册2-3个核心类别。

**境外申请人注意：** 在中国境外的申请人必须委托中国商标代理机构，不能自行申请。

---

### 美国商标申请流程（USPTO）

```
第一步：全面检索（Knockout Search）
  → 推荐工具：USPTO TESS免费检索 + 付费数据库
  → 建议聘请商标律师进行专业检索

第二步：选择申请基础（Filing Basis）
  → Use in Commerce (1a)：已在商业中实际使用
  → Intent to Use (1b)：有使用意图但尚未使用

第三步：提交申请（TEAS系统）
  → TEAS Plus：250美元/类（限制性较多）
  → TEAS Standard：350美元/类（灵活性更高）

第四步：等待审查
  → 审查员分配：约3-4个月
  → 审查意见（Office Action）：如有需在3个月内回复
  → 公告（Publication）：30天异议期

第五步：注册/使用声明
  → 1a申请：直接注册，每10年续展
  → 1b申请：收到允许通知后6个月内提交使用声明
  → 首次续展：注册后第5-6年需提交使用声明（Section 8）
```

**费用参考：** 每类别250-350美元申请费，加律师费约1000-3000美元/类。

---

### 什么时候必须找专业代理人

以下情况强烈建议聘请专业商标代理人/律师：

| 情况 | 原因 |
|------|------|
| 发现近似商标 | 需要专业判断混淆可能性 |
| 收到审查意见（Office Action/审查意见书） | 回复质量直接影响注册成功率 |
| 需要在多个国家同时注册 | 涉及马德里协议的复杂程序 |
| 品牌价值较高 | 错误可能造成重大损失 |
| 有他人提出异议 | 需要法律答辩 |
| 涉及驰名商标主张 | 高度专业化 |

---

## Data Sources

All accessed via `web_search` (direct fetch is blocked by these sites):

**中国 / China:**
- **CNIPA 商标局:** [wsjs.cnipa.gov.cn](https://wsjs.cnipa.gov.cn/) — 官方中国商标数据库（需登录）
- **企查查/天眼查:** 第三方，含商标信息

**美国 / United States:**
- **USPTO Trademark Search:** [tmsearch.uspto.gov](https://tmsearch.uspto.gov/) — Official US trademark database
- **USPTO TSDR:** [tsdr.uspto.gov](https://tsdr.uspto.gov/) — Status and document retrieval
- **Trademarkia:** [trademarkia.com](https://www.trademarkia.com/) — User-friendly trademark search

**国际 / International:**
- **WIPO Global Brand Database:** [branddb.wipo.int](https://branddb.wipo.int/) — International trademarks (Madrid System)

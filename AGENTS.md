# AGENTS.md - 路由与工作流

## 系统状态检查（每次启动时执行）

读取 USER.md，检查 `Onboarding Status` 字段：
- `pending` → 进入 **Onboarding Flow**（SOUL.md 中定义，5步初始化）
- `role_assigned` → 进入 **Role Layer**（已有角色，正常工作）

---

## Onboarding Flow（首次对话）

**触发条件**：USER.md 中 `Onboarding Status: pending`

**执行方式**：SOUL.md 中已内嵌完整流程，按顺序执行：

1. 问职业
2. 问行业 + 公司/产品（两个问题分开问）
3. 3道选择题（每道单独发，等回答再发下一道）
4. 匹配认知原型 → 展示推荐 → 用户确认
5. 加载原型 SKILL.md → 写入 USER.md + SOUL.md → 创建定时任务

---

## Base Layer（通用能力，始终激活）

不管角色是什么，以下能力永远可用：

### 1. 记忆管理
- 对话中识别重要信息 → 写入 USER.md
- 每5轮对话检查一次：有没有新的偏好信号？

### 2. 任务追踪
- 接收任务 → 写入 TASKLOG.md
- 执行后更新状态
- Boss Mode 时从 TASKLOG.md 生成汇报

### 3. 报告生成（日报/周报/月报）

**触发词**：日报、周报、月报、今天做了什么、本周总结、本月回顾、帮我写报告

执行：`skill_view("reporting")`

数据来源：TASKLOG.md + 当前对话中提到的事项

### 4. 总结反思与经验沉淀

**触发词**：复盘、反思、总结一下、经验沉淀、我学到了什么、这件事做完了

执行：`skill_view("retrospective")`

提炼的经验规则自动写入 USER.md Twin Playbook。

### 5. Boss / Twin 视角切换

**Boss Mode 触发词**：老板、汇报、进展、任务状态、KPI、本周完成
- 语气：专业简洁，数据说话
- 格式：`【汇报】✅已完成 / 🔄进行中 / ❌阻塞`

**Twin Mode**（默认）：
- 语气：参考 USER.md Twin Playbook
- 行为：代理执行，先做后说

### 6. 知识库管理

**触发词**：整理文件、知识库、扫一下目录、帮我找文件、归档、文件分类

执行：`skill_view("knowledge-base")`

数据来源：USER.md 中配置的「知识库根目录」，索引存 `~/.hermes/kb/`

### 7. 偏好蒸馏触发
当满足以下任一条件时，执行 `skill_view("twin-distillation")`：
- 用户明确表达偏好（「就这样」「记住这个」「以后都这样」）
- 用户纠正行为方式
- 当前会话超过5轮

蒸馏后，若检测到**稳定偏好**，用 fact_store 记录计数：
```
fact_store(action="add", content="偏好信号：<描述>", category="user_pref", tags="preference_signal,<角色>")
```
然后用 fact_store(action="search", query="preference_signal", category="user_pref") 查询，读取返回 JSON 的 `count` 字段。
若 `count >= 2`，询问用户是否固化，确认后用 `skill_manage` 写入角色工作流文件：
```
skill_manage(action="edit", skill="<角色命名空间>/workflow", append="## 用户偏好规则\n- <偏好描述>（固化于 YYYY-MM-DD）")
```
只写角色命名空间下的技能文件，不修改 SOUL.md 和基座技能。

---

## Role Layer（角色路由，动态加载）

Onboarding 完成后，每次对话开始时：

1. 读取 USER.md 中的 `Role Dir` 字段，得到 `<role_dir>`
2. 执行 `skill_view("<role_dir>/agents")` 加载该角色的专属路由

角色路由文件位于 `personas/<role_dir>/AGENTS.md`，包含：
- 触发词 → skill 映射表
- 主动提醒规则
- Boss Mode 汇报格式
- 任务记录格式

| 角色 | Role Dir | 路由文件 |
|------|----------|---------|
| 产品经理 | `product-manager` | `skill_view("pm/agents")` |
| 财务经理 | `finance-manager` | `skill_view("finance-manager/agents")` |
| HR经理 | `hr-manager` | `skill_view("hr-manager/agents")` |
| 运营经理 | `operations-manager` | `skill_view("operations-manager/agents")` |
| CEO | `ceo` | `skill_view("ceo/agents")` |
| 数据分析师 | `data-analyst` | `skill_view("data-analyst/agents")` |
| 其他职业 | 动态生成 | `skill_view("<role_dir>/agents")` |

---

## Skill Registry（选 skill 前先查这张表）

> **使用规则**：每次需要调用 skill 前，先在此表按功能分类找到正确入口。
> 命中多个时，选 description 最具体的那个。若表中没有，再用 `skill_view` 探索。

### 通用能力（Base Layer）

| Skill | 调用方式 | 一句话描述 | 触发词示例 |
|-------|---------|-----------|-----------|
| reporting | `skill_view("reporting")` | 生成日报/周报/月报 | 日报、周报、月报、帮我写报告 |
| retrospective | `skill_view("retrospective")` | 复盘反思、经验沉淀 | 复盘、反思、总结一下、经验沉淀 |
| twin-distillation | `skill_view("twin-distillation")` | 从对话中提炼用户偏好，更新工作流 | 记住这个、以后都这样、不要这种风格 |
| canvas | `skill_view("canvas")` | 把结构化数据渲染成图片发送 | 生成纪要、出日报图、做报告卡片 |
| knowledge-base | `skill_view("knowledge-base")` | 文件归档、知识库索引、找文件 | 整理文件、扫一下目录、帮我找文件 |
| browser | `skill_view("browser")` | 浏览器自动化：搜索、抓取、截图 | 打开网页、搜索、帮我看看这个网站 |
| share-bot | `skill_view("share-bot")` | 生成 bot 二维码供他人添加 | 分享、二维码、怎么加你、邀请别人 |
| content-writer | `skill_view("content-writer")` | 长文写作、公众号文章、营销文案 | 帮我写文章、写一篇、公众号推文 |
| output-format | `skill_view("output-format")` | 控制输出格式（表格/列表/段落） | 用表格、换个格式、简洁一点 |

### 数据获取（data-acquisition 子模块）

> 入口：`skill_view("data-acquisition")` 查看完整路由；直接用子模块更快。

| Skill | 调用方式 | 一句话描述 | 触发词示例 |
|-------|---------|-----------|-----------|
| 企业工商 | `skill_view("data-acquisition/enterprise")` | 企业背调、法人、注册资本、工商信息 | 查这家公司、法人是谁、注册资本 |
| 股票/金融 | `skill_view("data-acquisition/finance")` | 股价、基金净值、GDP、CPI、汇率 | 股价、行情、基金净值、汇率 |
| 新闻资讯 | `skill_view("data-acquisition/news")` | 最新新闻、媒体报道、行业资讯 | 最新新闻、媒体报道、找文章 |
| 国家政策 | `skill_view("data-acquisition/policy")` | 国务院政策、国家法规、全国招标 | 国务院政策、国家法规、全国招标 |
| 地方政府 | `skill_view("data-acquisition/local-gov")` | 省级政策、工信厅补贴、地方招标 | 省级政策、工信厅补贴、产业园区 |
| 社交热点 | `skill_view("data-acquisition/social")` | 热搜、热榜、舆情监控 | 热搜、热点、微博热榜 |
| 招聘薪资 | `skill_view("data-acquisition/hr")` | 招聘数据、薪资水平、人才趋势 | 招聘数据、薪资水平、岗位需求 |
| 一级市场 | `skill_view("data-acquisition/investment")` | 融资事件、投资机构、融资轮次 | 融资事件、投资机构、一级市场 |
| 应用商店 | `skill_view("data-acquisition/appstore")` | App排行、用户评论、版本更新 | App排行、用户评论、关键词搜索量 |
| 天气环境 | `skill_view("data-acquisition/weather")` | 天气预报、AQI、气候、灾害预警 | 天气、气温、AQI、空气质量 |
| 地图POI | `skill_view("data-acquisition/geo")` | 地址查询、周边搜索、路线规划 | 地址查询、周边搜索、门店分布 |
| 交通物流 | `skill_view("data-acquisition/transport")` | 火车余票、航班、快递追踪 | 火车余票、航班查询、快递追踪 |
| 法律知产 | `skill_view("data-acquisition/legal")` | 专利、商标、失信被执行人、行政处罚 | 专利查询、商标注册、失信 |
| 电商价格 | `skill_view("data-acquisition/ecommerce")` | 商品价格、历史最低价、电商排行 | 商品价格、历史最低价、什么值得买 |
| 行业垂直 | `skill_view("data-acquisition/industry")` | 医药、农产品价格、油价、PMI、碳市场 | 油价、PMI、药品查询、碳价格 |
| RSS聚合 | `skill_view("data-acquisition/rsshub")` | 知乎/B站/小红书/微博/政府部门订阅 | 知乎热榜、B站热门、GitHub趋势 |
| 开放数据 | `skill_view("data-acquisition/opendata")` | 国家统计局API、世界银行、arXiv | 国家统计局、世界银行数据、论文 |

### 角色专属能力（Role Layer）

> 仅在对应角色激活时可用，通过角色 AGENTS.md 路由触发。

| 角色 | Skill | 调用方式 | 一句话描述 |
|------|-------|---------|-----------|
| 产品经理 | competitor-analysis | `skill_view("pm/competitor-analysis")` | 竞品分析、竞争格局 |
| 产品经理 | user-interview | `skill_view("pm/user-interview")` | 用户访谈、访谈提纲 |
| 产品经理 | feature-analysis | `skill_view("pm/feature-analysis")` | 需求分析、用户反馈整理 |
| 产品经理 | feature-prioritize | `skill_view("pm/feature-prioritize")` | 需求优先级排序 |
| 产品经理 | create-prd | `skill_view("pm/create-prd")` | 写PRD、产品需求文档 |
| 产品经理 | user-stories | `skill_view("pm/user-stories")` | 用户故事、AC验收标准 |
| 产品经理 | sprint-plan | `skill_view("pm/sprint-plan")` | Sprint计划、迭代排期 |
| 产品经理 | metrics-dashboard | `skill_view("pm/metrics-dashboard")` | 数据指标、数据看板 |
| 产品经理 | stakeholder-map | `skill_view("pm/stakeholder-map")` | 干系人分析、汇报准备 |
| CEO | strategy | `skill_view("ceo/strategy")` | 战略方向、长期规划 |
| CEO | decisions | `skill_view("ceo/decisions")` | 重大决策、可逆性分析 |
| CEO | board | `skill_view("ceo/board")` | 董事会、投资人材料 |
| CEO | people | `skill_view("ceo/people")` | 团队文化、高管招聘 |
| CEO | competitive-intel | `skill_view("ceo/competitive-intel")` | 竞争情报、市场格局 |
| CEO | c-level-advisor | `skill_view("ceo/c-level-advisor")` | CEO战略咨询 |
| 财务 | financial-analysis | `skill_view("finance-manager/financial-analysis")` | 财务诊断、利润分析 |
| 财务 | financial-report | `skill_view("finance-manager/financial-report")` | 月报/季报生成 |
| 财务 | unit-economics | `skill_view("finance-manager/unit-economics")` | LTV/CAC/ARR/毛利 |
| 财务 | cfo-advisor | `skill_view("finance-manager/cfo-advisor")` | CFO级财务决策咨询 |
| HR | people-strategy | `skill_view("hr-manager/people-strategy")` | 招聘、JD、面试、人才 |
| HR | comp-frameworks | `skill_view("hr-manager/comp-frameworks")` | 薪酬对标、offer设计 |
| HR | org-design | `skill_view("hr-manager/org-design")` | 组织架构、团队设计 |
| HR | chro-advisor | `skill_view("hr-manager/chro-advisor")` | CHRO级人才战略咨询 |
| 运营 | process-frameworks | `skill_view("operations-manager/process-frameworks")` | 流程优化、SOP标准化 |
| 运营 | growth-metrics | `skill_view("operations-manager/growth-metrics")` | 增长、拉新、留存、GMV |
| 运营 | ops-cadence | `skill_view("operations-manager/ops-cadence")` | 运营节奏、周会、OKR |
| 运营 | scaling-playbook | `skill_view("operations-manager/scaling-playbook")` | 规模化扩张方案 |
| 运营 | coo-advisor | `skill_view("operations-manager/coo-advisor")` | COO级运营战略咨询 |
| 数据 | data-analysis | `skill_view("data-analysis")` | 数据分析、KPI归因、AB测 |

### 注册规则

**每次 hermes 自动生成新 skill 时，必须同步更新此表：**
1. 在对应分类下新增一行
2. 填写：Skill名 | 调用方式 | 一句话描述（≤15字）| 触发词（2-3个）
3. 若与已有 skill 功能重叠 >80%，先删除旧的再注册新的

---

## 硬性规则

- USER.md 是唯一的状态存储，所有更新都写这里
- Base Layer 规则不被蒸馏修改（蒸馏只写 Twin Playbook）
- 切换视角时不说「我现在切换到XX模式」，直接行动
- **选 skill 时必须先查 Skill Registry，不要直接猜路径**

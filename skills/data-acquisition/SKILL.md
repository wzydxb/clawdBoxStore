---
name: data-acquisition
description: |
  数据获取总入口。按需求类型路由到对应子模块：
  企业工商 → enterprise | 金融市场 → finance | 新闻资讯 → news | 国家政策法规 → policy
  地方政府/工信厅/发改委 → local-gov | 社交热点 → social | 招聘薪资 → hr
  一级市场融资 → investment | 应用商店 → appstore | 天气环境 → weather
  地图POI → geo | 交通物流 → transport | 法律知产 → legal | 电商价格 → ecommerce
  行业垂直数据 → industry | RSS聚合订阅 → rsshub | 开放数据/学术 → opendata
version: 8.0.0
---

# 数据获取能力

## 路由规则

| 需求类型 | 子模块 | 触发词示例 |
|----------|--------|-----------|
| 企业工商/背调/竞品基本面 | `skill_view("data-acquisition/enterprise")` | 查这家公司、企业背调、法人是谁、注册资本 |
| 股票/基金/期货/宏观/汇率 | `skill_view("data-acquisition/finance")` | 股价、行情、基金净值、GDP、CPI、汇率 |
| 新闻/资讯/媒体内容 | `skill_view("data-acquisition/news")` | 最新新闻、行业资讯、媒体报道、找文章 |
| 国家政策/法规/招标/统计 | `skill_view("data-acquisition/policy")` | 国务院政策、国家法规、全国招标、国家统计局 |
| 地方政府/工信厅/发改委 | `skill_view("data-acquisition/local-gov")` | 省级政策、工信厅补贴、地方招标、省级统计、产业园区 |
| 社交热点/舆情/热榜 | `skill_view("data-acquisition/social")` | 热搜、热点、舆情、微博热榜、今天发生了什么 |
| 招聘/薪资/人才市场 | `skill_view("data-acquisition/hr")` | 招聘数据、薪资水平、岗位需求、人才趋势 |
| 一级市场/融资/投资 | `skill_view("data-acquisition/investment")` | 融资事件、投资机构、融资轮次、一级市场 |
| 应用商店/竞品App | `skill_view("data-acquisition/appstore")` | App排行、用户评论、版本更新、关键词搜索量 |
| 天气/气候/空气质量 | `skill_view("data-acquisition/weather")` | 天气、气温、AQI、空气质量、预报、灾害预警 |
| 地图/POI/路线规划 | `skill_view("data-acquisition/geo")` | 地址查询、周边搜索、路线规划、门店分布 |
| 火车/航班/快递物流 | `skill_view("data-acquisition/transport")` | 火车余票、航班查询、快递追踪、物流状态 |
| 专利/商标/裁判文书/失信 | `skill_view("data-acquisition/legal")` | 专利查询、商标注册、失信被执行人、行政处罚 |
| 电商价格/排行/促销 | `skill_view("data-acquisition/ecommerce")` | 商品价格、历史最低价、电商排行、什么值得买 |
| 行业垂直数据 | `skill_view("data-acquisition/industry")` | 医药NMPA、农产品价格、油价、房价、碳市场、PMI、CNNIC |
| RSS聚合/内容订阅 | `skill_view("data-acquisition/rsshub")` | 知乎/B站/小红书/微博/豆瓣/政府部门/GitHub趋势 |
| 开放数据/学术论文 | `skill_view("data-acquisition/opendata")` | 国家统计局API、世界银行、arXiv、知网、政府开放数据平台 |

## 混合需求

多类型需求时并行调用多个子模块，最后汇总输出。

**典型组合：**
- 「分析XX公司市场地位」→ enterprise + finance + news + social
- 「找某省产业补贴」→ local-gov（工信厅）+ policy（国家级）
- 「企业合作风险排查」→ enterprise + legal（失信/处罚）
- 「选址/投资某省」→ local-gov + geo + weather + finance
- 「竞品全景分析」→ enterprise + finance + appstore + social + ecommerce
- 「出差行程规划」→ transport + weather + geo
- 「行业研究报告」→ industry + opendata + finance + news + rsshub
- 「宏观经济分析」→ opendata（国家统计局/世界银行）+ finance + industry
- 「舆情监控」→ social + rsshub + news（并行拉取多源）
- 「供应链/采购情报」→ ecommerce + industry（原材料价格）+ transport + local-gov

> 浏览器使用方式 → `skill_view("browser")`
> **playwright 注意**：子模块代码中的 `chromium.launch(headless=True)` 在部分盒子上会因 ozone platform 报错失败，优先改用 `connect_over_cdp("http://localhost:9222")` 连接系统 Chromium。

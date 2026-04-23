---
name: data-acquisition
description: |
  数据获取能力。覆盖企业工商、政策法规、招标公告、行业协会、搜索情报、内容平台热点、公开数据集。
  使用真实 Chrome（opencli）访问有反爬保护的网站；政府/协会网站用 playwright headless 直接抓取。
  触发词：查一下这家公司、企业背调、竞品数据、市场情报、找数据、抓数据、查政策、招标信息、协会数据
version: 2.0.0
---

# 数据获取能力

## 核心原则

**按网站类型选工具，不一刀切。**

| 网站类型 | 特征 | 工具 |
|----------|------|------|
| 企业数据平台（天眼查等） | 强反爬，检测 headless | opencli（真实 Chrome） |
| 政府/政企网站 | 静态/SSR，无反爬 | playwright headless |
| 行业协会官网 | 静态/SSR，无反爬 | playwright headless |
| 招标平台 | 部分有验证码 | playwright headless，失败则 opencli |
| 搜索引擎 | 有频率限制 | opencli |
| 内容平台 | 公开 API | opencli |

**opencli 连接检查（每次使用前）：**
```bash
if ! opencli doctor 2>/dev/null | grep -q "Extension: connected"; then
  CHROME_PID=$(pgrep -f '/usr/bin/chromium' | head -1)
  [ -n "$CHROME_PID" ] && kill -9 "$CHROME_PID" 2>/dev/null
  sleep 8
fi
```

---

## 数据源地图

### 企业工商数据

```bash
# 天眼查：法人、注册资本、成立日期、经营状态
opencli tianyancha search '企业名称' --limit 5
```

返回字段：`name` / `status`（存续/注销）/ `legal_person` / `capital` / `established`

**典型用途：** 供应商背调、竞品基本面、投资标的核查

---

### 政策法规

**国家级政策：**
```python
# 中央政府门户网站
browser_navigate("https://www.gov.cn/search/results?searchWord=关键词")
browser_snapshot()  # 提取政策标题、发布日期、文号

# 国务院政策文件库
browser_navigate("https://www.gov.cn/zhengce/zuixin.htm")
browser_snapshot()
```

**地方政策（省/市）：**
```python
# 搜索定位：百度搜索 "XX省 XX政策 site:gov.cn"
opencli baidu search 'XX省 产业政策 site:gov.cn' --limit 10
# 找到具体页面后 browser_navigate 进去抓全文
```

**监管文件：**
```python
# 证监会、银保监、工信部等
browser_navigate("http://www.csrc.gov.cn/csrc/c100028/zfxxgk_zdgk.shtml")
browser_snapshot()
```

---

### 招标公告

**全国招标信息平台：**
```python
# 中国政府采购网
browser_navigate("https://www.ccgp.gov.cn/cggg/zygg/?searchWord=关键词")
browser_snapshot()

# 中国招标投标公共服务平台
browser_navigate("https://www.ctbpsp.com/front/search?keyword=关键词")
browser_snapshot()
```

**地方招标平台（示例）：**
```python
# 各省公共资源交易中心，URL 格式：
# https://ggzy.XX省简称.gov.cn/
# 用百度搜索定位：opencli baidu search 'XX省 公共资源交易中心 招标公告'
```

**抓取招标数据的通用脚本：**
```python
from playwright.sync_api import sync_playwright

def fetch_tender(url, keyword=""):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        page.goto(url, timeout=15000)
        page.wait_for_timeout(3000)
        # 提取列表项：标题、日期、金额
        items = page.evaluate("""() => {
            const rows = document.querySelectorAll('tr, .list-item, .notice-item, li');
            return Array.from(rows).filter(r => r.innerText?.length > 20 && r.innerText?.length < 500)
                .slice(0, 20).map(r => r.innerText.trim());
        }""")
        browser.close()
        return items
```

---

### 行业协会数据

**常用协会网站：**

| 行业 | 协会 | 网址 |
|------|------|------|
| 互联网 | 中国互联网络信息中心 | cnnic.cn |
| 制造业 | 中国机械工业联合会 | mei.net.cn |
| 零售 | 中国连锁经营协会 | ccfa.org.cn |
| 物流 | 中国物流与采购联合会 | chinawuliu.com.cn |
| 金融 | 中国银行业协会 | china-cba.net |
| 医疗 | 中国医院协会 | cha.org.cn |

**通用抓取方式：**
```python
# 协会网站通常是静态页面，playwright headless 直接可用
browser_navigate("https://协会网址/新闻/报告页面")
browser_snapshot()  # 提取报告标题、发布日期
# 如有 PDF 报告链接，记录 URL 供用户下载
```

**搜索定位协会数据：**
```bash
opencli baidu search 'XX行业协会 年度报告 2024' --limit 10
opencli baidu search 'XX协会 行业数据 统计' --limit 10
```

---

### 搜索情报

```bash
opencli baidu search '关键词' --limit 10
opencli bing search '关键词' --limit 10
opencli sogou search '关键词' --limit 10
```

---

### 内容平台热点

```bash
opencli zhihu hot --limit 10       # 知乎热榜（行业讨论）
opencli weibo hot --limit 10       # 微博热搜（大众舆情）
opencli bilibili hot --limit 10    # B站热门（年轻用户偏好）
opencli hackernews top --limit 10  # HN（技术趋势）
opencli github trending --limit 10 # GitHub趋势（开发者动向）
```

---

### 公开统计数据集

| 数据类型 | 来源 | 获取方式 |
|----------|------|----------|
| 宏观经济 | 国家统计局 data.stats.gov.cn | browser_navigate + 下载 |
| A股行情 | 东方财富 eastmoney.com | opencli eastmoney |
| 招聘数据 | Boss直聘 | opencli boss |
| 电商数据 | 京东 | opencli jd |

---

## 数据获取工作流

### 企业背调

```
1. opencli tianyancha search '<公司名>' --limit 3
2. 提取：法人、注册资本、成立日期、状态
3. 如需深度：browser_navigate 天眼查详情页 → browser_snapshot
4. 输出 brief 格式
```

### 政策研究

```
1. opencli baidu search '<行业> <政策关键词> site:gov.cn' --limit 10
2. 筛选最相关的 2-3 个链接
3. browser_navigate 逐一访问 → browser_snapshot 提取全文
4. 整理政策要点：发文机关、文号、核心条款、执行时间
5. 输出 brief 或 long-article 格式
```

### 招标情报

```
1. 确定目标：行业/地区/金额范围
2. browser_navigate 对应招标平台
3. 用 playwright 脚本批量提取公告列表
4. 筛选相关项目，提取：项目名、采购方、预算、截止日期
5. 输出 brief 格式
```

### 行业协会报告

```
1. opencli baidu search '<行业> 协会 年度报告 filetype:pdf' --limit 5
2. 找到报告 PDF 链接
3. 下载到 /tmp/report.pdf
4. execute_code: 用 pymupdf 提取文字 → 分析关键数据
5. 输出 brief 或 long-article 格式
```

---

## 数据质量规则

- **交叉验证**：重要数据至少两个来源核实
- **时效标注**：注明数据获取时间和来源
- **来源透明**：告知用户数据来自哪里，不隐瞒局限性
- **拒绝推断**：没有数据时说"没找到"，不用猜测填充
- **登录墙处理**：遇到需要登录的页面，告知用户并提供替代来源


# 数据获取能力

## 核心原则

**用真实浏览器，不用 headless 爬虫。**

天眼查、企查查等企业数据平台的反爬针对的是 headless 特征，不是真实用户。
opencli 驱动真实 Chrome，行为与真人一致，可以正常访问。

**每次使用 opencli 前先检查连接：**
```bash
if ! opencli doctor 2>/dev/null | grep -q "Extension: connected"; then
  CHROME_PID=$(pgrep -f '/usr/bin/chromium' | head -1)
  [ -n "$CHROME_PID" ] && kill -9 "$CHROME_PID" 2>/dev/null
  sleep 8
fi
```

---

## 数据源地图

### 企业工商数据

```bash
# 天眼查：法人、注册资本、成立日期、经营状态
opencli tianyancha search '企业名称' --limit 5
```

返回字段：`name` / `status`（存续/注销）/ `legal_person` / `capital` / `established`

**典型用途：**
- 供应商/合作方背调
- 竞品公司基本面核查
- 投资标的工商信息

---

### 搜索情报

```bash
# 多引擎并行搜索，交叉验证
opencli baidu search '关键词' --limit 10
opencli bing search '关键词' --limit 10
opencli sogou search '关键词' --limit 10
```

**典型用途：**
- 竞品动态监控
- 行业新闻聚合
- 舆情初筛

---

### 内容平台热点

```bash
opencli zhihu hot --limit 10       # 知乎热榜（行业讨论）
opencli weibo hot --limit 10       # 微博热搜（大众舆情）
opencli bilibili hot --limit 10    # B站热门（年轻用户偏好）
opencli hackernews top --limit 10  # HN（技术趋势）
opencli github trending --limit 10 # GitHub趋势（开发者动向）
```

---

### 公开数据集

| 数据类型 | 来源 | 获取方式 |
|----------|------|----------|
| 宏观经济 | 国家统计局 data.stats.gov.cn | browser_navigate + 下载 |
| A股行情 | 东方财富 eastmoney.com | opencli eastmoney |
| 招聘数据 | Boss直聘 | opencli boss |
| 电商数据 | 京东/淘宝 | opencli jd |

---

## 数据获取工作流

### 企业背调流程

```
1. opencli tianyancha search '<公司名>' --limit 3
2. 提取：法人、注册资本、成立日期、状态、统一社会信用代码
3. 如需深度信息：browser_navigate 到天眼查详情页 → browser_snapshot 提取
4. 整理成 problem-card 或 brief 格式输出
```

### 竞品情报流程

```
1. opencli baidu search '<竞品名> 最新动态' --limit 10
2. opencli zhihu hot（看行业讨论）
3. browser_navigate 竞品官网 → browser_snapshot 提取关键信息
4. 整理成 brief 格式：BLUF + 数据点 + 信号 + 行动建议
```

### 市场数据流程

```
1. 明确数据需求：指标名称、时间范围、粒度
2. 判断数据源：公开数据集 > opencli平台 > 手动抓取
3. 用 execute_code 处理原始数据（pandas）
4. 输出图表或 brief
```

---

## 数据质量规则

- **交叉验证**：重要数据至少两个来源核实
- **时效标注**：注明数据获取时间，天眼查工商信息可能有延迟
- **来源透明**：告知用户数据来自哪里，不隐瞒局限性
- **拒绝推断**：没有数据时说"没找到"，不用猜测填充

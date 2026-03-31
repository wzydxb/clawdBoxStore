---
name: stock-announcement-fetcher
description: >-
  获取A股上市公司公告信息（真实数据）。基于AkShare从东方财富网获取当日全部公告，支持按股票代码筛选、关键词过滤。
  适用于监控重大事件、业绩快报、股东变动、重组公告等投资决策关键信息。数据源：东方财富网（稳定可靠）。
---

# Stock Announcement Fetcher

获取A股上市公司的官方公告信息（真实数据），帮助投资者及时掌握重要信息披露。

## ✅ 真实数据保证

- **数据来源：** 东方财富网（通过AkShare开源库）
- **更新频率：** 实时（当日公告）
- **覆盖范围：** 全部A股上市公司
- **数据质量：** 官方权威数据

## When to Use This Skill

触发条件（用户提及以下任一场景时激活）：

1. **查询特定公司公告**
   - "查看五粮液最近的公告"
   - "002368有什么新公告？"
   - "贵州茅台发布了什么？"

2. **监控特定事件**
   - "哪些公司今天发布了业绩预告？"
   - "查询股权激励公告"

3. **投资决策辅助**
   - "公司有利好消息吗？"
   - "检查是否有业绩变脸"

## Quick Start

### 基础用法

```bash
# 查询今日公告
uv run --script scripts/fetch_announcements.py 000858

# 查询最近7天
uv run --script scripts/fetch_announcements.py 600519 --days 7

# 查询最近30天（默认）
uv run --script scripts/fetch_announcements.py 002368.SZ
```

### 高级筛选

```bash
# 关键词筛选：业绩
uv run --script scripts/fetch_announcements.py 600519 --keyword 业绩

# JSON格式输出
uv run --script scripts/fetch_announcements.py 000858 --format json
```

## Workflow

### Step 1: 识别股票代码

用户可能提供以下任一格式：
- 公司名称："五粮液"  
- Yahoo Finance格式："000858.SZ"
- 纯代码："000858"

**处理流程：**
1. 如果是名称，先用 web_search 查询股票代码
2. 提取纯数字代码（去掉.SZ/.SS后缀）
3. 传递给脚本

### Step 2: 执行查询

```bash
uv run --script scripts/fetch_announcements.py <股票代码> [参数]
```

**注意：**
- 确保 `uv` 已在PATH中
- 脚本会自动安装akshare依赖
- **查询当日全部公告**，然后筛选特定股票（AkShare的限制）

### Step 3: 解读结果

**输出示例：**
```
================================================================================
Found 1 announcements
Stock: 五粮液 (000858)
Source: Eastmoney (AkShare)
================================================================================

[1] 2026-02-28
    Title: 五粮液:关于董事长变更的公告
    Type: 公告
    URL: https://data.eastmoney.com/notices/detail/000858/...
```

**Agent 应该：**
1. 提取关键信息（标题、类型、日期）
2. 分类汇总（业绩类、股东类、重大合同等）
3. 标注重要性（🔴高/🟡中/⚪低）
4. 提供简洁解读

**示例回复：**
```
五粮液今日发布 1 条公告：

🔴 重要：
- [02-28] 关于董事长变更的公告 → 公司治理重大变化

这是重大人事变动，可能影响公司战略方向，建议关注后续动态。
```

## Parameters

| 参数 | 说明 | 示例 | 默认值 |
|------|------|------|--------|
| `stock_code` | 股票代码（必填） | 000001, 600000.SS | - |
| `--days` | 最近N天 | 7 | 30 |
| `--format` | 输出格式 | json/text | text |
| `--keyword` | 标题关键词筛选 | 业绩 | None |

**注意：** `--from` 和 `--to` 参数保留但不生效，因为AkShare只支持查询当日公告。

## Limitations & Workarounds

### ⚠️ 当前限制

1. **只能查询当日公告**  
   - 原因：AkShare的`stock_notice_report`接口只返回指定日期的全部公告
   - 解决：如需历史公告，可以每天运行一次并保存结果

2. **需要先获取全部公告再筛选**
   - 原因：API不支持按股票代码直接查询
   - 影响：查询速度约7-10秒（需遍历1000+条公告）

3. **中文显示乱码**
   - 原因：Windows PowerShell GBK编码
   - 解决：数据本身正确，只是显示问题；使用`--format json`可正常显示

### ✅ 优点

1. **真实数据** - 直接来自东方财富网官方
2. **无需API Key** - AkShare免费开源
3. **稳定可靠** - 东方财富是国内主流财经网站
4. **数据全面** - 覆盖全部A股公司

## Tips

1. **最佳使用场景：** 查询当日最新公告
2. **配合使用：** 发现重要公告后，用 stock-info-explorer 查看股价反应
3. **定期监控：** 建议设置每日定时任务，自动获取重点股票公告
4. **历史查询：** 如需历史公告，考虑注册Tushare Pro（免费版可用）

---

详细技术文档见 `references/akshare-api.md`

---
name: data-acquisition/finance
description: 金融市场数据获取。AKShare（A股/基金/期货/宏观/汇率）+ TuShare（量化/资金流）+ 东方财富opencli。官方数据源，实时准确，不走搜索引擎。
---

# 金融市场数据

## 工具优先级

| 数据类型 | 首选 | 备选 |
|----------|------|------|
| A股行情/历史 | AKShare | opencli eastmoney quote |
| 基金净值/持仓 | AKShare | opencli xueqiu |
| 期货/商品 | AKShare | - |
| 宏观经济（GDP/CPI/PMI） | AKShare | NBSC API |
| 资金流/主力 | AKShare | TuShare（需token） |
| 港股/美股 | AKShare | opencli yahoo-finance |
| 财经快讯 | opencli eastmoney kuaixun | opencli sinafinance news |

## AKShare 安装检查

```python
try:
    import akshare as ak
except ImportError:
    import subprocess
    subprocess.run(["pip3", "install", "akshare", "--break-system-packages", "-q"])
    import akshare as ak
print(f"AKShare {ak.__version__}")
```

## A股行情

```python
import akshare as ak

# 实时行情（全市场）
df = ak.stock_zh_a_spot_em()
# 字段：代码、名称、最新价、涨跌幅、成交量、市值

# 单只股票历史（前复权）— 东方财富数据源，HK服务器可能被墙，备用新浪源
df = ak.stock_zh_a_hist(symbol="000001", period="daily",
                         start_date="20240101", end_date="20241231", adjust="qfq")
# 备用（新浪源，HK服务器稳定）：
# df = ak.stock_zh_a_daily(symbol="sh000001", adjust="qfq")  # sh/sz前缀

# 财务数据
df_profit = ak.stock_profit_sheet_by_report_em(symbol="000001")   # 利润表
df_balance = ak.stock_balance_sheet_by_report_em(symbol="000001") # 资产负债表
df_cash = ak.stock_cash_flow_sheet_by_report_em(symbol="000001")  # 现金流量表

# 个股基本信息
df_info = ak.stock_individual_info_em(symbol="000001")
```

## 指数与板块

```python
# 主要指数
df = ak.stock_zh_index_daily(symbol="sh000001")  # 上证
df = ak.stock_zh_index_daily(symbol="sz399001")  # 深证
df = ak.stock_zh_index_daily(symbol="sz399006")  # 创业板

# 行业板块排行
df = ak.stock_board_industry_name_em()
df = ak.stock_board_industry_hist_em(symbol="银行", period="daily",
                                      start_date="20240101", end_date="20241231")

# 北向资金
df = ak.stock_hsgt_north_net_flow_in_em(symbol="沪深港通")
```

## 基金数据

```python
# 公募基金净值走势
df = ak.fund_open_fund_info_em(symbol="000001", indicator="单位净值走势")

# ETF实时行情
df = ak.fund_etf_spot_em()

# 基金持仓（季报）
df = ak.fund_portfolio_hold_em(symbol="000001", date="2024")

# 基金排行
df = ak.fund_open_fund_rank_em(symbol="全部")
```

## 期货与商品

```python
# 期货主力合约历史
df = ak.futures_main_sina(symbol="RB0", start_date="20240101")  # 螺纹钢

# 期货实时行情
df = ak.futures_zh_spot(subscribe_list=["螺纹钢", "铁矿石", "原油"])

# 大宗商品现货价格
df = ak.spot_hist_sge(symbol="黄金99.99")  # 上海黄金交易所
```

## 宏观经济数据

```python
# GDP
df = ak.macro_china_gdp()

# CPI / PPI（v1.18.56 正确函数名）
df = ak.macro_china_cpi_monthly()            # CPI月度（函数存在）
df = ak.macro_china_ppi()                    # PPI（ppi_monthly不存在，用macro_china_ppi）

# PMI（v1.18.56 正确函数名）
df = ak.macro_china_pmi()                    # 制造业+非制造业PMI

# M2货币供应
df = ak.macro_china_money_supply()

# 社会融资规模
df = ak.macro_china_shrzgm()

# 进出口
df = ak.macro_china_trade_balance()

# 国家统计局 API（NBSC，免费官方）
# pip install nbsc
# import nbsc
# df = nbsc.get_data(indicator_code="A010101", start_year=2020, end_year=2024)
```

## 外汇与债券

```python
# 人民币汇率中间价（中行历史数据）
df = ak.currency_boc_sina(symbol="美元")
df = ak.currency_boc_sina(symbol="欧元")
df = ak.currency_boc_sina(symbol="日元")

# 实时汇率
df = ak.forex_spot_em()

# 国债收益率曲线
df = ak.bond_china_yield(start_date="20240101", end_date="20241231")

# 可转债实时行情（v1.18.56: bond_zh_cov，非 bond_zh_cov_spot）
df = ak.bond_zh_cov()  # 可转债列表
# df = ak.bond_zh_hs_cov_daily(symbol="127043")  # 单只可转债日线
```

## TuShare（量化/资金流，需免费token）

```python
# TuShare 免费 token 申请：tushare.pro/register
# 免费额度：每分钟200次，基础数据全免费
import tushare as ts
ts.set_token('YOUR_TOKEN')
pro = ts.pro_api()

# 资金流向
df = pro.moneyflow(ts_code='000001.SZ', start_date='20240101', end_date='20241231')

# 龙虎榜
df = pro.top_list(trade_date='20241201')

# 融资融券
df = pro.margin_detail(trade_date='20241201', ts_code='000001.SZ')
```

## opencli 金融命令（实时行情）

```bash
# 东方财富实时行情
opencli eastmoney quote --symbol 000001

# 东方财富热股榜
opencli eastmoney hot-rank

# 东方财富财经快讯
opencli eastmoney kuaixun --limit 20

# 雪球热门股票
opencli xueqiu hot-stock --limit 20

# 雪球股票实时行情
opencli xueqiu stock --symbol SH000001

# 新浪财经快讯
opencli sinafinance news --limit 20
```

## 金融分析工作流

```
1. 明确需求：股票代码/指数/基金/宏观指标 + 时间范围
2. 用 AKShare 获取数据（execute_code）
3. pandas 处理：清洗、计算技术指标、聚合
4. 输出：数据表 + 关键结论 + 图表（可选）
```

## 数据质量说明

- AKShare 数据来源：上交所、深交所、Wind、东方财富等官方渠道
- 实时行情有15分钟延迟（非付费）
- 历史数据完整，适合回测和分析
- 财务数据按报告期更新，非实时

---
name: stock-info-explorer
description: >-
  A Yahoo Finance (yfinance) powered financial analysis tool.
  Get real-time quotes, generate high-resolution charts with moving averages + indicators (RSI/MACD/Bollinger/VWAP/ATR),
  summarize fundamentals, and run a one-shot report that outputs both a text summary and a Pro chart.
---

# Stock Information Explorer

This skill fetches OHLCV data from Yahoo Finance via `yfinance` and computes technical indicators **locally** (no API key required).

## Commands

### 1) Real-time Quotes (`price`)
```bash
uv run --script scripts/yf.py price TSLA
# shorthand
uv run --script scripts/yf.py TSLA
```

### 2) Fundamental Summary (`fundamentals`)
```bash
uv run --script scripts/yf.py fundamentals NVDA
```

### 3) ASCII Trend (`history`)
```bash
uv run --script scripts/yf.py history AAPL 6mo
```

### 4) Professional Analysis (`pro`)
⚠️ **已改为文本报告模式** - 不再生成PNG图表，输出详细的技术指标文本分析。

```bash
# 基础分析（价格区间）
uv run --script scripts/yf.py pro 000660.KS 6mo

# 带技术指标
uv run --script scripts/yf.py pro 002368.SZ 6mo --rsi --macd --bb
```

#### 可用指标 (optional)
添加标志以包含相应技术指标分析。

```bash
uv run --script scripts/yf.py pro TSLA 6mo --rsi --macd --bb
uv run --script scripts/yf.py pro TSLA 6mo --vwap --atr
```

- `--rsi` : RSI(14) - 超买超卖指标
- `--macd`: MACD(12,26,9) - 趋势动量指标
- `--bb`  : Bollinger Bands(20,2) - 布林带
- `--vwap`: VWAP - 成交量加权均价
- `--atr` : ATR(14) - 平均真实波幅

**输出格式：** 文本报告，包含当前值、状态判断、交易建议

### 5) One-shot Report (`report`) ⭐
⚠️ **已改为纯文本模式** - 输出综合分析报告（行情+基本面+技术信号），不再生成PNG图表。

```bash
uv run --script scripts/yf.py report 000660.KS 6mo
# 输出：文本格式的综合分析报告
```

**报告内容：**
- 行情概要（价格、涨跌、市值、市盈率）
- 技术信号（RSI、布林带位置、MACD趋势）
- 详细技术指标分析（同pro命令）

## Ticker Examples
- US stocks: `AAPL`, `NVDA`, `TSLA`
- KR stocks: `005930.KS`, `000660.KS`
- Crypto: `BTC-USD`, `ETH-KRW`
- Forex: `USDKRW=X`

## Notes / Limitations
- Indicators are **computed locally** from price data (Yahoo does not reliably provide precomputed indicator series).
- Data quality may vary by ticker/market (e.g., missing volume for some symbols).
- This is a no-key path and should be preferred before any token-based market data route.
- ⚠️ **PNG图表功能已禁用** - 所有输出均为文本格式，适合命令行环境。
- 中文输出在Windows PowerShell中可能显示为乱码（GBK编码问题），但数据准确。

---
Korean note: 실시간 시세 + 펀더멘털 + 기술지표(차트/요약)까지 한 번에 처리하는 종합 주식 분석 스킬입니다.

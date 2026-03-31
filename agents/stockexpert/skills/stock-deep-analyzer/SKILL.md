---
name: stock-deep-analyzer
description: >-
  A comprehensive stock deep analysis tool that combines real-time quotes, fundamental metrics, 
  technical indicators, and growth analysis into a single professional report. 
  Supports A-share, US stocks, HK stocks. Generates detailed investment recommendations 
  with risk assessment and actionable trading strategies.
---

# Stock Deep Analyzer

One-stop comprehensive stock analysis tool that generates professional-grade investment reports.

## Features

✅ **Real-time Market Data** - Current price, volume, market cap, beta  
✅ **Value Investing Metrics** - P/E, P/B, ROE, ROA, dividend yield, payout ratio  
✅ **Technical Indicators** - MA5/20/60, RSI, MACD, Bollinger Bands, VWAP  
✅ **Growth Analysis** - Revenue growth, earnings growth, profit margins  
✅ **Financial Health** - Asset/liability ratio, liquidity ratio  
✅ **Investment Rating** - Multi-dimensional scoring (value/growth/technical/financial)  
✅ **Trading Strategies** - Long-term hold, swing trade, short-term speculation  
✅ **Risk Assessment** - Key risks and price levels  

## Usage

### Basic Analysis

```powershell
# Analyze a stock (default: 6-month period)
$env:PYTHONIOENCODING='utf-8'; python scripts/deep_analyze.py 601288.SS

# Specify analysis period
$env:PYTHONIOENCODING='utf-8'; python scripts/deep_analyze.py 000001.SZ --period 1y

# US stocks
$env:PYTHONIOENCODING='utf-8'; python scripts/deep_analyze.py AAPL
```

### Parameters

| Parameter | Description | Example | Default |
|-----------|-------------|---------|---------|
| `ticker` | Stock ticker symbol (required) | 601288.SS, AAPL | - |
| `--period` | Analysis period | 1mo, 3mo, 6mo, 1y, 2y | 6mo |
| `--output` | Output format | text, json | text |

## Stock Ticker Formats

- **A-share (Shanghai)**: `600519.SS`, `601288.SS`
- **A-share (Shenzhen)**: `000001.SZ`, `002594.SZ`
- **US stocks**: `AAPL`, `TSLA`, `NVDA`
- **HK stocks**: `0700.HK`, `9988.HK`

## Output Structure

The analysis report includes:

### 1. Real-time Market Overview
- Current price, change %, volume
- 52-week range, market cap, beta

### 2. Value Investing Indicators
- Valuation: P/E, P/B, PEG
- Profitability: ROE, ROA, profit margin
- Dividends: yield, payout ratio
- **Value Score: /10**

### 3. Technical Analysis
- Moving Averages: MA5, MA20, MA60
- Momentum: RSI(14)
- Trend: MACD
- Volatility: Bollinger Bands
- Volume: VWAP analysis
- **Technical Score: /10**

### 4. Growth Indicators
- Revenue growth (YoY)
- Earnings growth (YoY)
- Margin trends
- **Growth Score: /10**

### 5. Financial Health
- Debt-to-equity ratio
- Current ratio (liquidity)
- Asset efficiency

### 6. Comprehensive Investment Advice
- **Overall Rating: /10**
- Investment strategies:
  - Long-term hold (for value investors)
  - Swing trade (for traders)
  - Short-term speculation (for aggressive)
- Key price levels (support/resistance)
- Risk warnings
- Valuation targets

## Requirements

Python packages (auto-installed by uv):
- yfinance
- pandas
- numpy

## Workflow

When user requests stock analysis:

1. **Identify ticker symbol**
   - User may provide company name → use web_search to find ticker
   - Extract ticker from Yahoo Finance format (e.g., "601288.SS" → "601288.SS")

2. **Execute analysis**
   ```powershell
   $env:PYTHONIOENCODING='utf-8'; python scripts/deep_analyze.py <ticker>
   ```

3. **Interpret results**
   - Extract overall rating and key findings
   - Highlight investment recommendation
   - Emphasize risk warnings
   - Provide actionable price levels

## Example Output

```
============================================================
农业银行 (601288.SS) - Deep Analysis Report
============================================================

[Real-time Overview]
  Current: ¥6.48 (+1.25%)
  Market Cap: ¥22,679亿
  52-Week Range: ¥4.92 - ¥8.68

[Value Investing - Score: 90/100]
  ✅ P/E: 8.31 (Undervalued)
  ✅ P/B: 0.83 (Below book value)
  ✅ ROE: 9.37%
  ✅ Dividend Yield: 3.83%

[Technical Analysis - Score: 45/100]
  ⚠️ RSI: 33.56 (Oversold)
  ✅ MACD: Golden cross
  ✅ Price near lower Bollinger Band

[Growth - Score: 65/100]
  ⭐ Earnings Growth: +15.8%
  ⚠️ Revenue Growth: +5.6%

[Investment Rating: ⭐⭐⭐⭐ Strong Buy]
  
Recommended Strategy:
- Long-term hold: 20-30% position, target ¥7.8-9.0
- Swing trade: Buy ¥6.30-6.48, sell ¥6.90-7.20
- Stop loss: ¥6.25

Key Risks:
- Asset quality (NPL ratio)
- Interest rate environment
- Market sentiment (value trap)
```

## Notes

- Always prefix commands with `$env:PYTHONIOENCODING='utf-8';` to avoid encoding issues
- Use English variable names in Python scripts
- Data source: Yahoo Finance via yfinance
- No API key required
- Analysis period affects technical indicators accuracy

## Limitations

- Yahoo Finance data quality varies by market
- Some metrics may be N/A for loss-making companies
- Historical data limited for newly listed stocks
- Real-time quotes may have 15-min delay

---

**When to use this skill:**
- User requests "深度分析", "complete analysis", "comprehensive report"
- User wants multi-dimensional evaluation (value + growth + technical)
- User needs actionable trading strategies
- User asks for investment recommendations with risk assessment

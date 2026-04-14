---
name: stock-price-checker
description: Get stock prices using the yfinance library. No API key required.
homepage: https://finance.yahoo.com
metadata: {"yuanqiai":{"emoji":"📈","requires":{"bins":["python3","yfinance"]}}}
version: 1.0.0
---

# Stock Price Checker

Get current stock prices from Yahoo Finance using the yfinance library.

## Prerequisites

Complete these steps before first use:

**1. Install yfinance**

```bash
pip install yfinance
```

On Windows, if `pip` is not available, try:

```bash
pip3 install yfinance
```

**2. Network requirements**

This skill requires access to `finance.yahoo.com`. Users in mainland China need a proxy to use this skill.

## Quick Start

```bash
# Query a stock price
python3 ${SKILL_DIR}/stock-price.py NVDA

# Windows: use python instead of python3
python ${SKILL_DIR}/stock-price.py NVDA
```

## Examples

```bash
python3 ${SKILL_DIR}/stock-price.py NVDA
python3 ${SKILL_DIR}/stock-price.py AAPL
python3 ${SKILL_DIR}/stock-price.py VOO
python3 ${SKILL_DIR}/stock-price.py 600519.SS
python3 ${SKILL_DIR}/stock-price.py 0700.HK
```

The script outputs one line per call:

```
NVDA: USD 131.38 ▲ USD 4.21 (3.31%) Vol: 287.4M Avg: 198.6M | 144% of avg
```

For multiple stocks, run the script once per symbol.

## Data Presentation

After collecting script output, clean and format before presenting to the user:

1. **Clean raw data** — Strip any HTML tags, escape sequences, or markup. The user should never see raw code or tags.
2. **Use plain Markdown only** — Present data using Markdown text, tables, or lists. Do not use the `$` character anywhere in your output — many chat platforms treat `$` as a LaTeX/KaTeX math delimiter, causing broken rendering. Write prices as `USD 180.40` or just `180.40`. Do not use LaTeX, MathML, KaTeX, or any math-mode formatting.
3. **Match the user's intent** — Choose the presentation style based on what was asked:
   - Single stock → brief text summary
   - Multiple stocks → comparison table
   - Analysis request → table with interpretation

## Notes

- No API key required
- Supports most US stocks and ETFs
- Exits with code 1 on error
- China A-shares: append `.SS` (Shanghai) or `.SZ` (Shenzhen), e.g. `600519.SS`
- Hong Kong stocks: append `.HK`, e.g. `0700.HK`

## Troubleshooting

**`ModuleNotFoundError: No module named 'yfinance'`**
→ Run `pip install yfinance`

**`No such file or directory: stock-price.py`**
→ Use `${SKILL_DIR}/stock-price.py` instead of `stock-price.py`

**`python3: command not found` (Windows)**
→ Use `python` instead of `python3`

**Network timeout / empty data**
→ Yahoo Finance is blocked in mainland China — use a proxy

**Invalid symbol**
→ The script prints an error message and exits with code 1

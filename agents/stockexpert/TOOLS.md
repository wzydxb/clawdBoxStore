# TOOLS.md - Stock Expert Environment

## System Environment

### Platform
- **OS**: Windows 10/11
- **Shell**: PowerShell (default)
- **Python**: 3.11.9 (managed by ClawBox)
- **Package Manager**: uv (Python package runner)

### Critical Constraints
⚠️ **PowerShell Syntax**
- Use `;` for command chaining, NOT `&&`
- Example: `cd dir; python script.py` ✅
- Wrong: `cd dir && python script.py` ❌

⚠️ **Chinese Character Encoding**
- Always set: `$env:PYTHONIOENCODING='utf-8'`
- Prevents GBK encoding errors in PowerShell

⚠️ **Chart Generation DISABLED**
- stock-info-explorer outputs **text reports only**
- Do NOT attempt to generate PNG charts

### Python Libraries Available
- `yfinance` - Yahoo Finance data
- `akshare` - A-share data (Eastmoney)
- `pandas`, `numpy` - Data processing
- `matplotlib` ⚠️ installed but NOT used (text-only mode)

## Stock Ticker Formats

### A-Share (Shanghai Stock Exchange)
- Format: `<code>.SS`
- Examples:
  - 贵州茅台: `600519.SS`
  - 中国平安: `601318.SS`
  - 招商银行: `600036.SS`

### A-Share (Shenzhen Stock Exchange)
- Format: `<code>.SZ`
- Examples:
  - 平安银行: `000001.SZ`
  - 万科A: `000002.SZ`
  - 比亚迪: `002594.SZ`

### US Stocks
- Format: `<TICKER>` (no suffix)
- Examples: `AAPL`, `TSLA`, `NVDA`, `MSFT`

### Hong Kong Stocks
- Format: `<code>.HK`
- Examples:
  - 腾讯: `0700.HK`
  - 阿里巴巴: `9988.HK`

## Skill Command References

### Stock Info Explorer
```powershell
# Real-time quote
uv run --script skills/stock-info-explorer/scripts/yf.py price 600519.SS

# Comprehensive report (text-only)
$env:PYTHONIOENCODING='utf-8'; uv run --script skills/stock-info-explorer/scripts/yf.py report 601318.SS 6mo

# Technical analysis with indicators
$env:PYTHONIOENCODING='utf-8'; uv run --script skills/stock-info-explorer/scripts/yf.py pro 000001.SZ 6mo --rsi --macd --bb --vwap
```

### Stock Announcement Fetcher
```powershell
# Today's announcements
$env:PYTHONIOENCODING='utf-8'; uv run --script skills/stock-announcement-fetcher/scripts/fetch_announcement.py --date today

# Specific stock announcements
$env:PYTHONIOENCODING='utf-8'; uv run --script skills/stock-announcement-fetcher/scripts/fetch_announcement.py --stock 600519
```

### Trading Coach
```powershell
# Review trading CSV
$env:PYTHONIOENCODING='utf-8'; uv run --script skills/trading-coach/scripts/analyze_trades.py --file path/to/trades.csv
```

## Debugging Tips

### Common Issues

1. **"&& is not valid" error**
   - Cause: Using Bash syntax in PowerShell
   - Fix: Replace `&&` with `;`

2. **Chinese characters show as gibberish**
   - Cause: PowerShell GBK encoding
   - Fix: Prefix command with `$env:PYTHONIOENCODING='utf-8';`

3. **"No module named 'matplotlib'" but charts disabled**
   - Cause: Agent trying to generate PNG
   - Fix: Use `report` or `pro` commands (text-only)

4. **Tool call timeout/terminated**
   - Cause: Long-running write operations
   - Fix: Break into smaller steps, use workdir parameter

---

**Updated**: 2026-03-02
**Last Tested**: Python 3.11.9, uv 0.5.x, Windows PowerShell 5.1

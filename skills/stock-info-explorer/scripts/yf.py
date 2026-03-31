#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /// script
# dependencies = [
#   "yfinance",
#   "rich",
#   "pandas",
#   "plotille",
#   "matplotlib",
#   "mplfinance"
# ]
# ///

import sys
import yfinance as yf
import pandas as pd
import plotille
import matplotlib.pyplot as plt
import mplfinance as mpf
from rich.console import Console
from rich.table import Table

# 设置UTF-8编码
if sys.stdout.encoding != 'utf-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
from rich.panel import Panel
from rich import print as rprint
import os

console = Console()

# --- Technical Indicators ---

def calc_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1/window, adjust=False, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calc_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = close.ewm(span=fast, adjust=False, min_periods=fast).mean()
    ema_slow = close.ewm(span=slow, adjust=False, min_periods=slow).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False, min_periods=signal).mean()
    hist = macd - sig
    return macd, sig, hist


def calc_bbands(close: pd.Series, window: int = 20, n_std: float = 2.0):
    ma = close.rolling(window=window, min_periods=window).mean()
    std = close.rolling(window=window, min_periods=window).std(ddof=0)
    upper = ma + n_std * std
    lower = ma - n_std * std
    return upper, ma, lower


def calc_vwap(df: pd.DataFrame) -> pd.Series:
    # VWAP over the provided window (cumulative over the selected period)
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    vol = df['Volume'].fillna(0)
    tpv = (typical_price * vol).cumsum()
    vwap = tpv / vol.cumsum().replace(0, pd.NA)
    return vwap


def calc_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    high = df['High']
    low = df['Low']
    close = df['Close']
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/window, adjust=False, min_periods=window).mean()
    return atr

def get_ticker_info(symbol):
    ticker = yf.Ticker(symbol)
    try:
        info = ticker.info
        if not info or ('regularMarketPrice' not in info and 'currentPrice' not in info):
            if not info.get('symbol'): return None, None
        return ticker, info
    except:
        return None, None

def show_price(symbol, ticker, info):
    current = info.get('regularMarketPrice') or info.get('currentPrice')
    prev_close = info.get('regularMarketPreviousClose') or info.get('previousClose')
    if current is None: return
    change = current - prev_close
    pct_change = (change / prev_close) * 100
    color = "green" if change >= 0 else "red"
    sign = "+" if change >= 0 else ""
    table = Table(title=f"Price: {info.get('longName', symbol)}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Symbol", symbol)
    table.add_row("Current Price", f"{current:,.2f} {info.get('currency', '')}")
    table.add_row("Change", f"[{color}]{sign}{change:,.2f} ({sign}{pct_change:.2f}%)[/{color}]")
    console.print(table)

def show_fundamentals(symbol, ticker, info):
    table = Table(title=f"Fundamentals: {info.get('longName', symbol)}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    metrics = [
        ("Market Cap", info.get('marketCap')),
        ("PE Ratio", info.get('forwardPE')),
        ("EPS", info.get('trailingEps')),
        ("ROE", info.get('returnOnEquity')),
    ]
    for name, val in metrics:
        table.add_row(name, str(val))
    console.print(table)

def show_history(symbol, ticker, period="1mo"):
    hist = ticker.history(period=period)
    chart = plotille.plot(hist.index, hist['Close'], height=15, width=60)
    console.print(Panel(chart, title=f"Chart: {symbol}", border_style="green"))

def save_pro_chart(symbol, ticker, period="3mo", chart_type='candle', indicators=None):
    """
    替代PNG图表生成 - 改为生成文本分析报告
    """
    indicators = indicators or {}
    hist = ticker.history(period=period)
    if hist.empty:
        return None

    close = hist['Close']
    
    # 计算所有技术指标
    output_lines = []
    output_lines.append(f"\n{'='*60}")
    output_lines.append(f"{symbol} 技术分析报告 ({period})")
    output_lines.append(f"{'='*60}\n")
    
    # 价格信息
    current_price = close.iloc[-1]
    period_high = hist['High'].max()
    period_low = hist['Low'].min()
    period_start = close.iloc[0]
    period_change = ((current_price - period_start) / period_start) * 100
    
    output_lines.append(f"[价格区间]")
    output_lines.append(f"  当前价格: {current_price:.2f}")
    output_lines.append(f"  期间高点: {period_high:.2f}")
    output_lines.append(f"  期间低点: {period_low:.2f}")
    output_lines.append(f"  期间涨幅: {period_change:+.2f}%")
    output_lines.append("")
    
    # RSI
    if indicators.get('rsi'):
        rsi = calc_rsi(close)
        rsi_val = rsi.iloc[-1]
        rsi_status = '超买' if rsi_val > 70 else ('超卖' if rsi_val < 30 else '中性')
        output_lines.append(f"[RSI(14)]")
        output_lines.append(f"  当前值: {rsi_val:.2f}")
        output_lines.append(f"  状态: {rsi_status}")
        output_lines.append("")
    
    # 布林带
    if indicators.get('bb'):
        upper, mid, lower = calc_bbands(close)
        bb_upper = upper.iloc[-1]
        bb_mid = mid.iloc[-1]
        bb_lower = lower.iloc[-1]
        bb_pos = ((current_price - bb_lower) / (bb_upper - bb_lower)) * 100
        bb_status = '上轨附近' if bb_pos > 80 else ('下轨附近' if bb_pos < 20 else '中轨附近')
        output_lines.append(f"[布林带(20,2)]")
        output_lines.append(f"  上轨: {bb_upper:.2f}")
        output_lines.append(f"  中轨: {bb_mid:.2f}")
        output_lines.append(f"  下轨: {bb_lower:.2f}")
        output_lines.append(f"  位置: {bb_pos:.1f}% ({bb_status})")
        output_lines.append("")
    
    # MACD
    if indicators.get('macd'):
        macd, sig, histo = calc_macd(close)
        macd_val = macd.iloc[-1]
        macd_sig = sig.iloc[-1]
        macd_histo = histo.iloc[-1]
        macd_status = '多头' if macd_val > macd_sig else '空头'
        output_lines.append(f"[MACD(12,26,9)]")
        output_lines.append(f"  MACD线: {macd_val:.3f}")
        output_lines.append(f"  信号线: {macd_sig:.3f}")
        output_lines.append(f"  柱状图: {macd_histo:.3f}")
        output_lines.append(f"  趋势: {macd_status}")
        output_lines.append("")
    
    # VWAP
    if indicators.get('vwap'):
        vwap = calc_vwap(hist)
        vwap_val = vwap.iloc[-1]
        vwap_status = '高于' if current_price > vwap_val else '低于'
        output_lines.append(f"[VWAP]")
        output_lines.append(f"  VWAP值: {vwap_val:.2f}")
        output_lines.append(f"  当前价格{vwap_status}VWAP")
        output_lines.append("")
    
    # ATR
    if indicators.get('atr'):
        atr = calc_atr(hist)
        atr_val = atr.iloc[-1]
        atr_pct = (atr_val / current_price) * 100
        output_lines.append(f"[ATR(14)]")
        output_lines.append(f"  ATR值: {atr_val:.2f}")
        output_lines.append(f"  占价格: {atr_pct:.2f}%")
        output_lines.append("")
    
    output_lines.append(f"{'='*60}\n")
    
    report_text = '\n'.join(output_lines)
    print(report_text)
    
    return "TEXT_REPORT"  # 返回标识表示已生成文本报告

def show_report(symbol, ticker, info, period="6mo"):
    # 1. Price & Change Summary
    current = info.get('regularMarketPrice') or info.get('currentPrice')
    prev_close = info.get('regularMarketPreviousClose') or info.get('previousClose')
    change = current - prev_close if current and prev_close else 0
    pct_change = (change / prev_close) * 100 if prev_close else 0
    
    # 2. Fundamentals Summary
    mcap = info.get('marketCap', 0)
    pe = info.get('forwardPE', 'N/A')
    
    # 3. Technical Indicators (latest)
    hist = ticker.history(period=period)
    if hist.empty:
        print("No history data for report")
        return
    
    close = hist['Close']
    rsi_val = calc_rsi(close).iloc[-1]
    upper, mid, lower = calc_bbands(close)
    bb_pos = (close.iloc[-1] - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1]) * 100
    macd, sig, histo = calc_macd(close)
    macd_val = macd.iloc[-1]
    macd_sig = sig.iloc[-1]
    
    # 4. Generate text report (with main indicators)
    indicators = {'rsi': True, 'macd': True, 'bb': True}
    save_pro_chart(symbol, ticker, period=period, indicators=indicators)
    
    # 5. Build text summary
    sign = "+" if change >= 0 else ""
    
    print(f"\n{'='*60}")
    print(f"{info.get('longName', symbol)} - 综合分析报告")
    print(f"{'='*60}\n")
    
    print(f"[行情概要]")
    print(f"  当前价格: {current:,.2f} {info.get('currency', '')}")
    print(f"  涨跌: {sign}{change:,.2f} ({sign}{pct_change:.2f}%)")
    print(f"  市值: {mcap/1e9:,.1f}B | 市盈率: {pe}")
    print()
    
    print(f"[技术信号]")
    rsi_status = '超买' if rsi_val > 70 else ('超卖' if rsi_val < 30 else '中性')
    bb_status = '上轨' if bb_pos > 80 else ('下轨' if bb_pos < 20 else '中轨')
    macd_status = '多头' if macd_val > macd_sig else '空头'
    
    print(f"  RSI(14): {rsi_val:.1f} ({rsi_status})")
    print(f"  布林带位置: {bb_pos:.1f}% ({bb_status}附近)")
    print(f"  MACD: {macd_val:.2f} | 信号: {macd_sig:.2f} ({macd_status})")
    print(f"\n{'='*60}\n")

def main():
    if len(sys.argv) < 2: sys.exit(1)
    
    import argparse
    parser = argparse.ArgumentParser(description="Stock Info Explorer")
    parser.add_argument("cmd", choices=["price", "fundamentals", "history", "pro", "chart", "report"], nargs='?', default="price")
    parser.add_argument("symbol", help="Stock ticker symbol")
    parser.add_argument("period", nargs='?', default="3mo")
    parser.add_argument("chart_type", nargs='?', default="candle")
    parser.add_argument("--rsi", action="store_true")
    parser.add_argument("--macd", action="store_true")
    parser.add_argument("--bb", action="store_true")
    parser.add_argument("--vwap", action="store_true")
    parser.add_argument("--atr", action="store_true")
    
    # Backward compatibility for positional args or simple 'yf.py TSLA'
    args_list = sys.argv[1:]
    if len(args_list) > 0 and args_list[0] not in ["price", "fundamentals", "history", "pro", "chart", "report"]:
        args_list.insert(0, "price")
    
    args = parser.parse_args(args_list)
    
    cmd = args.cmd
    symbol = args.symbol
    period = args.period
    chart_type = args.chart_type
    
    indicators = {
        'rsi': args.rsi,
        'macd': args.macd,
        'bb': args.bb,
        'vwap': args.vwap,
        'atr': args.atr
    }

    ticker, info = get_ticker_info(symbol)
    if not ticker: sys.exit(1)

    if cmd == "price": show_price(symbol, ticker, info)
    elif cmd == "fundamentals": show_fundamentals(symbol, ticker, info)
    elif cmd == "history": show_history(symbol, ticker, period=period)
    elif cmd == "report": show_report(symbol, ticker, info, period=period)
    elif cmd == "pro":
        save_pro_chart(symbol, ticker, period=period, chart_type=chart_type, indicators=indicators)

    elif cmd == "chart":
        # chart命令已改为文本模式，使用history或pro替代
        show_history(symbol, ticker, period=period)
    else:
        show_price(symbol, ticker, info)

if __name__ == "__main__":
    main()

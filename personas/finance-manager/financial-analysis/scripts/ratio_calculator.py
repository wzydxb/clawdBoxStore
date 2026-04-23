#!/usr/bin/env python3
"""
ratio_calculator.py - 财务比率计算器

用法：
  python ratio_calculator.py data.json
  python ratio_calculator.py data.json --format json
  python ratio_calculator.py data.json --category profitability

输入 JSON 格式见文件末尾 INPUT SCHEMA 注释。
"""

import json
import argparse
import sys
from typing import Optional


def safe_div(a, b, default=None):
    try:
        return a / b if b and b != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def pct(v):
    return f"{v*100:.1f}%" if v is not None else "N/A"


def fmt(v, decimals=2):
    return f"{v:.{decimals}f}" if v is not None else "N/A"


# ── 盈利能力 ──────────────────────────────────────────────

def calc_profitability(d: dict) -> dict:
    rev = d.get("revenue")
    cogs = d.get("cogs")
    op_income = d.get("operating_income")
    net_income = d.get("net_income")
    equity = d.get("total_equity")
    assets = d.get("total_assets")

    gross_profit = (rev - cogs) if rev and cogs else None

    return {
        "gross_margin":     safe_div(gross_profit, rev),
        "operating_margin": safe_div(op_income, rev),
        "net_margin":       safe_div(net_income, rev),
        "roe":              safe_div(net_income, equity),
        "roa":              safe_div(net_income, assets),
    }


# ── 流动性 ────────────────────────────────────────────────

def calc_liquidity(d: dict) -> dict:
    ca = d.get("current_assets")
    cl = d.get("current_liabilities")
    inv = d.get("inventory", 0)
    cash = d.get("cash")

    quick_assets = (ca - inv) if (ca is not None and inv is not None) else ca

    return {
        "current_ratio": safe_div(ca, cl),
        "quick_ratio":   safe_div(quick_assets, cl),
        "cash_ratio":    safe_div(cash, cl),
    }


# ── 杠杆 ──────────────────────────────────────────────────

def calc_leverage(d: dict) -> dict:
    debt = d.get("total_debt")
    equity = d.get("total_equity")
    ebit = d.get("ebit")
    interest = d.get("interest_expense")
    dscr_income = d.get("net_operating_income")
    debt_service = d.get("total_debt_service")

    return {
        "debt_to_equity":     safe_div(debt, equity),
        "interest_coverage":  safe_div(ebit, interest),
        "dscr":               safe_div(dscr_income, debt_service),
    }


# ── 效率 ──────────────────────────────────────────────────

def calc_efficiency(d: dict) -> dict:
    rev = d.get("revenue")
    assets = d.get("total_assets")
    inv = d.get("inventory")
    cogs = d.get("cogs")
    ar = d.get("accounts_receivable")

    inv_turnover = safe_div(cogs, inv)
    ar_turnover = safe_div(rev, ar)
    dso = safe_div(365, ar_turnover)

    return {
        "asset_turnover":       safe_div(rev, assets),
        "inventory_turnover":   inv_turnover,
        "receivables_turnover": ar_turnover,
        "dso_days":             dso,
    }


# ── 估值 ──────────────────────────────────────────────────

def calc_valuation(d: dict) -> dict:
    shares = d.get("shares_outstanding")
    market_cap = d.get("market_cap")

    # Derive share_price and EV if not explicitly provided
    price = d.get("share_price") or (safe_div(market_cap, shares) if market_cap and shares else None)
    ev = d.get("enterprise_value") or (
        market_cap + d.get("total_debt", 0) - d.get("cash", 0)
        if market_cap is not None else None
    )

    eps = d.get("eps") or safe_div(d.get("net_income"), shares)
    bvps = d.get("book_value_per_share") or safe_div(d.get("total_equity"), shares)
    sps = d.get("sales_per_share") or safe_div(d.get("revenue"), shares)
    ebitda = d.get("ebitda")
    growth = d.get("earnings_growth_rate")

    pe = safe_div(price, eps)
    peg = safe_div(pe, growth * 100 if growth and growth != 0 else None)

    return {
        "pe_ratio":    pe,
        "pb_ratio":    safe_div(price, bvps),
        "ps_ratio":    safe_div(price, sps),
        "ev_ebitda":   safe_div(ev, ebitda),
        "peg_ratio":   peg,
    }


# ── 基准参考 ──────────────────────────────────────────────

BENCHMARKS = {
    "gross_margin":       {"good": 0.40, "label": "毛利率 ≥40% 良好"},
    "operating_margin":   {"good": 0.15, "label": "营业利润率 ≥15% 良好"},
    "net_margin":         {"good": 0.10, "label": "净利率 ≥10% 良好"},
    "roe":                {"good": 0.15, "label": "ROE ≥15% 良好"},
    "roa":                {"good": 0.05, "label": "ROA ≥5% 良好"},
    "current_ratio":      {"good": 2.0,  "label": "流动比率 ≥2 良好"},
    "quick_ratio":        {"good": 1.0,  "label": "速动比率 ≥1 良好"},
    "debt_to_equity":     {"good": 1.0,  "label": "D/E ≤1 良好", "lower_is_better": True},
    "interest_coverage":  {"good": 3.0,  "label": "利息覆盖 ≥3 良好"},
    "dso_days":           {"good": 45,   "label": "DSO ≤45天 良好", "lower_is_better": True},
}


def status(key, value):
    if value is None:
        return ""
    b = BENCHMARKS.get(key)
    if not b:
        return ""
    lower = b.get("lower_is_better", False)
    good = b["good"]
    if lower:
        return "🟢" if value <= good else ("🟡" if value <= good * 1.5 else "🔴")
    else:
        return "🟢" if value >= good else ("🟡" if value >= good * 0.7 else "🔴")


# ── 输出 ──────────────────────────────────────────────────

CATEGORIES = {
    "profitability": ("盈利能力", calc_profitability),
    "liquidity":     ("流动性",   calc_liquidity),
    "leverage":      ("杠杆",     calc_leverage),
    "efficiency":    ("效率",     calc_efficiency),
    "valuation":     ("估值",     calc_valuation),
}

LABELS = {
    "gross_margin": "毛利率", "operating_margin": "营业利润率", "net_margin": "净利率",
    "roe": "ROE", "roa": "ROA",
    "current_ratio": "流动比率", "quick_ratio": "速动比率", "cash_ratio": "现金比率",
    "debt_to_equity": "债务/权益", "interest_coverage": "利息覆盖倍数", "dscr": "偿债覆盖率",
    "asset_turnover": "资产周转率", "inventory_turnover": "存货周转率",
    "receivables_turnover": "应收账款周转率", "dso_days": "DSO（天）",
    "pe_ratio": "P/E", "pb_ratio": "P/B", "ps_ratio": "P/S",
    "ev_ebitda": "EV/EBITDA", "peg_ratio": "PEG",
}

PCT_KEYS = {"gross_margin", "operating_margin", "net_margin", "roe", "roa"}


def print_results(results: dict, category: Optional[str]):
    cats = [category] if category else list(CATEGORIES.keys())
    for cat in cats:
        if cat not in results:
            continue
        title, _ = CATEGORIES[cat]
        print(f"\n{'─'*40}")
        print(f"  {title}")
        print(f"{'─'*40}")
        for k, v in results[cat].items():
            label = LABELS.get(k, k)
            s = status(k, v)
            display = pct(v) if k in PCT_KEYS else fmt(v)
            print(f"  {label:<20} {display:>10}  {s}")


def main():
    parser = argparse.ArgumentParser(description="财务比率计算器")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--category", choices=list(CATEGORIES.keys()))
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误：JSON 格式有误 — {e}", file=sys.stderr)
        sys.exit(1)

    results = {}
    cats = [args.category] if args.category else list(CATEGORIES.keys())
    for cat in cats:
        _, fn = CATEGORIES[cat]
        results[cat] = fn(data)

    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_results(results, args.category)


if __name__ == "__main__":
    main()

# ── INPUT SCHEMA ──────────────────────────────────────────
# {
#   "revenue": 1000000,          // 营业收入
#   "cogs": 600000,              // 营业成本
#   "operating_income": 150000,  // 营业利润
#   "ebit": 150000,              // 息税前利润
#   "net_income": 100000,        // 净利润
#   "total_equity": 500000,      // 所有者权益
#   "total_assets": 800000,      // 总资产
#   "current_assets": 300000,    // 流动资产
#   "current_liabilities": 150000,
#   "inventory": 80000,
#   "cash": 50000,
#   "total_debt": 200000,
#   "interest_expense": 20000,
#   "accounts_receivable": 120000,
#   "ebitda": 180000,
#   "enterprise_value": 2000000,
#   "share_price": 25.0,
#   "eps": 2.5,
#   "book_value_per_share": 12.0,
#   "sales_per_share": 20.0,
#   "earnings_growth_rate": 0.15
# }

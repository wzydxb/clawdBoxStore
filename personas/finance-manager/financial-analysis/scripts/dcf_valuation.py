#!/usr/bin/env python3
"""
dcf_valuation.py - DCF 估值模型

用法：
  python dcf_valuation.py data.json
  python dcf_valuation.py data.json --format json
  python dcf_valuation.py data.json --projection-years 7
"""

import json
import argparse
import sys
import math


def safe_div(a, b):
    return a / b if b and b != 0 else None


# ── WACC 计算 ─────────────────────────────────────────────

def calc_wacc(d: dict) -> float:
    rf = d.get("risk_free_rate", 0.04)
    beta = d.get("beta", 1.0)
    erp = d.get("equity_risk_premium", 0.055)
    cost_of_equity = rf + beta * erp

    debt = d.get("total_debt", 0)
    equity_mv = d.get("market_cap", d.get("total_equity", 1))
    total = debt + equity_mv
    tax_rate = d.get("tax_rate", 0.25)
    cost_of_debt = d.get("cost_of_debt", 0.05)

    we = safe_div(equity_mv, total) or 1.0
    wd = safe_div(debt, total) or 0.0

    wacc = we * cost_of_equity + wd * cost_of_debt * (1 - tax_rate)
    return wacc


# ── FCF 预测 ──────────────────────────────────────────────

def project_fcf(d: dict, years: int) -> list:
    base_fcf = d.get("free_cash_flow") or (
        d.get("ebitda", 0) * (1 - d.get("tax_rate", 0.25))
        - d.get("capex", 0)
        - d.get("change_in_working_capital", 0)
    )
    growth_rates = d.get("growth_rates")
    if not growth_rates:
        g_high = d.get("revenue_growth_rate", 0.15)
        g_low = d.get("terminal_growth_rate", 0.03)
        # 线性衰减
        growth_rates = [
            g_high + (g_low - g_high) * i / (years - 1)
            for i in range(years)
        ]

    fcfs = []
    fcf = base_fcf
    for g in growth_rates[:years]:
        fcf = fcf * (1 + g)
        fcfs.append(fcf)
    return fcfs


# ── 终值 ─────────────────────────────────────────────────

def terminal_value_perpetuity(last_fcf: float, wacc: float, tgr: float) -> float:
    if wacc <= tgr:
        return float("inf")  # perpetuity formula undefined when discount rate ≤ growth rate
    return last_fcf * (1 + tgr) / (wacc - tgr)


def terminal_value_exit_multiple(ebitda: float, multiple: float) -> float:
    return ebitda * multiple


# ── 折现 ─────────────────────────────────────────────────

def pv(cash_flows: list, wacc: float) -> float:
    return sum(cf / (1 + wacc) ** (i + 1) for i, cf in enumerate(cash_flows))


# ── 敏感性分析 ────────────────────────────────────────────

def sensitivity_table(base_ev: float, wacc: float, tgr: float,
                       fcfs: list, last_fcf: float) -> dict:
    wacc_range = [wacc - 0.02, wacc - 0.01, wacc, wacc + 0.01, wacc + 0.02]
    tgr_range = [tgr - 0.01, tgr, tgr + 0.01]
    table = {}
    for w in wacc_range:
        row = {}
        for g in tgr_range:
            if w <= g:
                row[f"{g:.1%}"] = "N/A"
                continue
            tv = terminal_value_perpetuity(last_fcf, w, g)
            ev = pv(fcfs, w) + tv / (1 + w) ** len(fcfs)
            row[f"{g:.1%}"] = f"{ev/1e6:.1f}M"
        table[f"{w:.1%}"] = row
    return table


# ── 主流程 ────────────────────────────────────────────────

def run(data: dict, years: int) -> dict:
    wacc = calc_wacc(data)
    tgr = data.get("terminal_growth_rate", 0.03)
    fcfs = project_fcf(data, years)

    pv_fcf = pv(fcfs, wacc)

    # 终值（两种方法）
    tv_perp = terminal_value_perpetuity(fcfs[-1], wacc, tgr)
    pv_tv_perp = tv_perp / (1 + wacc) ** years

    ebitda_last = data.get("ebitda", 0) * (1 + tgr) ** years
    exit_mult = data.get("exit_multiple", 12)
    tv_exit = terminal_value_exit_multiple(ebitda_last, exit_mult)
    pv_tv_exit = tv_exit / (1 + wacc) ** years

    ev_perp = pv_fcf + pv_tv_perp
    ev_exit = pv_fcf + pv_tv_exit

    net_debt = data.get("total_debt", 0) - data.get("cash", 0)
    shares = data.get("shares_outstanding", 1)

    equity_perp = ev_perp - net_debt
    equity_exit = ev_exit - net_debt

    price_perp = equity_perp / shares if shares else None
    price_exit = equity_exit / shares if shares else None

    sens = sensitivity_table(ev_perp, wacc, tgr, fcfs, fcfs[-1])

    return {
        "wacc": wacc,
        "terminal_growth_rate": tgr,
        "projected_fcfs": fcfs,
        "pv_of_fcfs": pv_fcf,
        "terminal_value_perpetuity": tv_perp,
        "terminal_value_exit_multiple": tv_exit,
        "enterprise_value_perpetuity": ev_perp,
        "enterprise_value_exit_multiple": ev_exit,
        "equity_value_perpetuity": equity_perp,
        "equity_value_exit_multiple": equity_exit,
        "implied_share_price_perpetuity": price_perp,
        "implied_share_price_exit_multiple": price_exit,
        "sensitivity_table": sens,
    }


def fmt_m(v):
    return f"{v/1e6:.2f}M" if v else "N/A"


def print_results(r: dict):
    print(f"\n{'═'*50}")
    print("  DCF 估值报告")
    print(f"{'═'*50}")
    print(f"  WACC                    {r['wacc']:.2%}")
    print(f"  终端增长率              {r['terminal_growth_rate']:.2%}")
    print(f"\n  预测期 FCF（百万）：")
    for i, fcf in enumerate(r["projected_fcfs"], 1):
        print(f"    第{i}年  {fcf/1e6:>10.2f}M")
    print(f"\n  FCF 现值合计            {fmt_m(r['pv_of_fcfs'])}")
    print(f"\n  ── 永续增长法 ──")
    print(f"  终值                    {fmt_m(r['terminal_value_perpetuity'])}")
    print(f"  企业价值 (EV)           {fmt_m(r['enterprise_value_perpetuity'])}")
    print(f"  股权价值                {fmt_m(r['equity_value_perpetuity'])}")
    if r["implied_share_price_perpetuity"]:
        print(f"  隐含股价                {r['implied_share_price_perpetuity']:.2f}")
    print(f"\n  ── 退出乘数法 ──")
    print(f"  终值                    {fmt_m(r['terminal_value_exit_multiple'])}")
    print(f"  企业价值 (EV)           {fmt_m(r['enterprise_value_exit_multiple'])}")
    print(f"  股权价值                {fmt_m(r['equity_value_exit_multiple'])}")
    if r["implied_share_price_exit_multiple"]:
        print(f"  隐含股价                {r['implied_share_price_exit_multiple']:.2f}")
    print(f"\n  ── 敏感性分析（EV，永续增长法）──")
    print(f"  WACC \\ TGR  ", end="")
    tgr_keys = list(list(r["sensitivity_table"].values())[0].keys())
    print("  ".join(f"{k:>8}" for k in tgr_keys))
    for wacc_k, row in r["sensitivity_table"].items():
        print(f"  {wacc_k:>8}    ", end="")
        print("  ".join(f"{v:>8}" for v in row.values()))


def main():
    parser = argparse.ArgumentParser(description="DCF 估值模型")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--projection-years", type=int, default=5)
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.input}", file=sys.stderr)
        sys.exit(1)

    result = run(data, args.projection_years)

    if args.format == "json":
        out = {k: v for k, v in result.items() if k != "sensitivity_table"}
        out["sensitivity_table"] = result["sensitivity_table"]
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print_results(result)


if __name__ == "__main__":
    main()

# ── INPUT SCHEMA ──────────────────────────────────────────
# {
#   "free_cash_flow": 5000000,       // 基期 FCF（或用 ebitda+capex 推算）
#   "ebitda": 8000000,
#   "capex": 1000000,
#   "change_in_working_capital": 500000,
#   "revenue_growth_rate": 0.20,     // 初始增长率
#   "terminal_growth_rate": 0.03,    // 终端增长率
#   "risk_free_rate": 0.04,
#   "beta": 1.2,
#   "equity_risk_premium": 0.055,
#   "cost_of_debt": 0.05,
#   "tax_rate": 0.25,
#   "total_debt": 10000000,
#   "cash": 3000000,
#   "market_cap": 50000000,
#   "shares_outstanding": 1000000,
#   "exit_multiple": 12
# }

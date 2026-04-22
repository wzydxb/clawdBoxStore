#!/usr/bin/env python3
"""
financial_scenario_analyzer.py - CEO 级财务情景分析 + 决策支持

用法：
  python financial_scenario_analyzer.py data.json
  python financial_scenario_analyzer.py data.json --json
  python financial_scenario_analyzer.py data.json --months 24

INPUT SCHEMA:
{
  "company_name": "Acme Inc.",
  "current_arr": 2400000,
  "current_cash": 3000000,
  "monthly_burn": 200000,
  "monthly_revenue": 200000,
  "scenarios": {
    "base":  {"arr_growth_pct": 8,  "burn_change_pct": 0,   "label": "维持现状"},
    "bull":  {"arr_growth_pct": 15, "burn_change_pct": 10,  "label": "加速增长（加大投入）"},
    "bear":  {"arr_growth_pct": 3,  "burn_change_pct": -15, "label": "保守收缩（降本）"}
  },
  "fundraise_options": [
    {"name": "不融资", "amount": 0, "dilution_pct": 0},
    {"name": "种子轮 $2M", "amount": 2000000, "dilution_pct": 15},
    {"name": "A轮 $8M", "amount": 8000000, "dilution_pct": 20}
  ]
}
"""

import argparse
import json
import sys


def project_scenario(current_arr, current_cash, monthly_burn, monthly_revenue,
                     arr_growth_pct, burn_change_pct, months=18) -> list:
    cash = current_cash
    burn = monthly_burn * (1 + burn_change_pct / 100)
    revenue = monthly_revenue
    arr = current_arr

    results = []
    for m in range(1, months + 1):
        monthly_rev = arr / 12
        net_burn = max(0, burn - monthly_rev)
        cash -= net_burn
        arr = arr * (1 + arr_growth_pct / 100 / 12)

        results.append({
            "month": m,
            "arr": round(arr, 0),
            "monthly_revenue": round(monthly_rev, 0),
            "gross_burn": round(burn, 0),
            "net_burn": round(net_burn, 0),
            "ending_cash": round(cash, 0),
            "runway_months": round(cash / net_burn, 1) if net_burn > 0 else float("inf"),
        })

        if cash <= 0:
            break

    return results


def analyze_fundraise(current_cash, monthly_net_burn, option: dict) -> dict:
    post_cash = current_cash + option["amount"]
    runway = post_cash / monthly_net_burn if monthly_net_burn > 0 else float("inf")
    return {
        "name": option["name"],
        "raise_amount": option["amount"],
        "dilution_pct": option["dilution_pct"],
        "post_cash": round(post_cash, 0),
        "runway_months": round(runway, 1) if runway != float("inf") else None,
    }


def print_report(data: dict, scenario_results: dict, fundraise_results: list, months: int):
    company = data.get("company_name", "")
    print(f"\n{'═'*65}")
    print(f"  CEO 财务情景分析 — {company}")
    print(f"{'═'*65}")

    print(f"\n  ── 情景对比（第 {months} 个月末）──")
    print(f"  {'情景':<20} {'期末ARR':>12} {'期末现金':>12} {'存活月数':>10} {'状态'}")
    for sc_name, proj in scenario_results.items():
        sc_cfg = data["scenarios"][sc_name]
        final = proj[-1]
        survived = len(proj)
        cash_s = f"{final['ending_cash']:,.0f}" if final["ending_cash"] > 0 else "耗尽"
        runway = final["runway_months"]
        if runway == float("inf") or runway is None:
            icon = "🟢"
        elif runway >= 18:
            icon = "🟢"
        elif runway >= 12:
            icon = "🟡"
        else:
            icon = "🔴"
        print(f"  {sc_name:<20} {final['arr']:>12,.0f} {cash_s:>12} {survived:>10}  {icon}")

    if fundraise_results:
        print(f"\n  ── 融资选项对比 ──")
        print(f"  {'选项':<20} {'融资额':>10} {'稀释':>8} {'融后现金':>12} {'Runway':>10}")
        for fr in fundraise_results:
            runway_s = f"{fr['runway_months']:.1f}mo" if fr["runway_months"] else "∞"
            print(f"  {fr['name']:<20} {fr['raise_amount']:>10,.0f} {fr['dilution_pct']:>7.0f}% "
                  f"{fr['post_cash']:>12,.0f} {runway_s:>10}")

    # Decision prompt
    print(f"\n  ── CEO 决策框架 ──")
    base_final = scenario_results.get("base", [{}])[-1]
    base_runway = base_final.get("runway_months", 0)
    if base_runway != float("inf") and base_runway < 12:
        print(f"  🔴 基准情景 runway < 12 个月，融资或降本是优先议题")
    elif base_runway != float("inf") and base_runway < 18:
        print(f"  🟡 基准情景 runway 12-18 个月，建议在 6 个月内启动融资流程")
    else:
        print(f"  🟢 基准情景 runway 充裕，可专注增长，择机融资")


def main():
    parser = argparse.ArgumentParser(description="CEO 财务情景分析")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("--months", type=int, default=18)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.input}", file=sys.stderr)
        sys.exit(1)

    scenario_results = {}
    for sc_name, sc_cfg in data.get("scenarios", {}).items():
        scenario_results[sc_name] = project_scenario(
            data["current_arr"],
            data["current_cash"],
            data["monthly_burn"],
            data["monthly_revenue"],
            sc_cfg["arr_growth_pct"],
            sc_cfg.get("burn_change_pct", 0),
            args.months,
        )

    base_net_burn = max(0, data["monthly_burn"] - data["monthly_revenue"])
    fundraise_results = [analyze_fundraise(data["current_cash"], base_net_burn, opt)
                         for opt in data.get("fundraise_options", [])]

    if args.json:
        print(json.dumps({
            "scenarios": {k: v for k, v in scenario_results.items()},
            "fundraise_options": fundraise_results,
        }, ensure_ascii=False, indent=2))
    else:
        print_report(data, scenario_results, fundraise_results, args.months)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
burn_rate_calculator.py - Burn Rate & Runway 情景模型

用法：
  python burn_rate_calculator.py                        # 交互模式
  python burn_rate_calculator.py --cash 1000000 --burn 80000 --arr 500000 --new-arr 20000
  python burn_rate_calculator.py --cash 1000000 --burn 80000 --arr 500000 --new-arr 20000 --json
"""

import argparse
import json
import sys


def calc_runway(cash, net_burn):
    if net_burn <= 0:
        return float("inf")
    return cash / net_burn


def burn_multiple(net_burn, net_new_arr):
    if not net_new_arr or net_new_arr <= 0:
        return None
    return net_burn / (net_new_arr / 12)


def project_runway(cash, gross_burn, monthly_revenue, hiring_plan: list,
                   revenue_growth_rate, months=18):
    """
    hiring_plan: [{"month": 3, "salary": 15000}, ...]  每月新增人力成本
    """
    results = []
    current_cash = cash
    current_burn = gross_burn
    current_revenue = monthly_revenue

    hire_schedule = {h["month"]: h.get("salary", 0) for h in (hiring_plan or [])}

    for m in range(1, months + 1):
        # 新增招聘成本
        current_burn += hire_schedule.get(m, 0)
        # 收入增长
        current_revenue *= (1 + revenue_growth_rate / 100)
        net_burn = max(0, current_burn - current_revenue)
        current_cash -= net_burn

        results.append({
            "month": m,
            "gross_burn": round(current_burn, 0),
            "revenue": round(current_revenue, 0),
            "net_burn": round(net_burn, 0),
            "ending_cash": round(current_cash, 0),
            "runway_remaining": round(current_cash / net_burn, 1) if net_burn > 0 else float("inf"),
        })

        if current_cash <= 0:
            break

    return results


SCENARIO_ADJUSTMENTS = {
    "base":  {"burn_mult": 1.00, "revenue_mult": 1.00},
    "bull":  {"burn_mult": 0.90, "revenue_mult": 1.20},
    "bear":  {"burn_mult": 1.15, "revenue_mult": 0.70},
}


def run_scenarios(cash, gross_burn, monthly_revenue, hiring_plan,
                  revenue_growth_rate, months=18):
    results = {}
    for sc, adj in SCENARIO_ADJUSTMENTS.items():
        proj = project_runway(
            cash,
            gross_burn * adj["burn_mult"],
            monthly_revenue * adj["revenue_mult"],
            hiring_plan,
            revenue_growth_rate,
            months,
        )
        final_cash = proj[-1]["ending_cash"]
        months_survived = len(proj)
        results[sc] = {
            "months_survived": months_survived,
            "final_cash": final_cash,
            "projection": proj,
        }
    return results


def status_runway(months):
    if months == float("inf"):
        return "🟢 盈利，无需担心"
    elif months >= 24:
        return "🟢 充裕（≥24个月）"
    elif months >= 12:
        return "🟡 注意（12-24个月）"
    elif months >= 6:
        return "🔴 危险（6-12个月）"
    else:
        return "🚨 紧急（<6个月）"


def print_report(cash, gross_burn, net_burn, monthly_revenue, bm, scenarios):
    runway = calc_runway(cash, net_burn)
    print(f"\n{'═'*55}")
    print("  Burn Rate & Runway 报告")
    print(f"{'═'*55}")
    print(f"  当前现金          {cash:>15,.0f}")
    print(f"  月度总支出        {gross_burn:>15,.0f}")
    print(f"  月度收入          {monthly_revenue:>15,.0f}")
    print(f"  净 Burn           {net_burn:>15,.0f}")
    runway_str = f"{runway:.1f} 个月" if runway != float("inf") else "∞（盈利）"
    print(f"  当前 Runway       {runway_str:>15}")
    print(f"  状态              {status_runway(runway)}")
    if bm is not None:
        bm_icon = "🟢" if bm < 1 else ("🟡" if bm < 2 else "🔴")
        print(f"  Burn Multiple     {bm:>15.2f}  {bm_icon}")

    print(f"\n  ── 情景对比（18个月后）──")
    print(f"  {'情景':<8} {'存活月数':>10} {'期末现金':>14}")
    for sc, r in scenarios.items():
        cash_str = f"{r['final_cash']:,.0f}" if r["final_cash"] > 0 else "耗尽"
        print(f"  {sc:<8} {r['months_survived']:>10}  {cash_str:>14}")


def interactive_mode():
    print("Burn Rate 计算器（交互模式）\n")

    def ask(prompt, required=True):
        while True:
            val = input(f"  {prompt}: ").strip()
            if val:
                try:
                    return float(val)
                except ValueError:
                    print("  请输入数字")
            elif not required:
                return None
            else:
                print("  此项必填")

    cash = ask("当前现金余额")
    gross_burn = ask("月度总支出（Gross Burn）")
    monthly_revenue = ask("月度收入")
    net_new_arr = ask("本月净新增 ARR（可选）", required=False)
    revenue_growth = ask("月收入增长率 %（如 5）", required=False) or 5

    net_burn = max(0, gross_burn - monthly_revenue)
    bm = burn_multiple(net_burn, net_new_arr) if net_new_arr else None
    scenarios = run_scenarios(cash, gross_burn, monthly_revenue, [], revenue_growth)
    print_report(cash, gross_burn, net_burn, monthly_revenue, bm, scenarios)


def main():
    parser = argparse.ArgumentParser(description="Burn Rate & Runway 情景模型")
    parser.add_argument("--cash", type=float)
    parser.add_argument("--burn", type=float, help="月度总支出")
    parser.add_argument("--revenue", type=float, default=0, help="月度收入")
    parser.add_argument("--arr", type=float, help="当前 ARR（用于计算 burn multiple）")
    parser.add_argument("--new-arr", type=float, help="本月净新增 ARR")
    parser.add_argument("--revenue-growth", type=float, default=5, help="月收入增长率（如 5 代表5%%）")
    parser.add_argument("--months", type=int, default=18)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.cash:
        interactive_mode()
        return

    net_burn = max(0, args.burn - args.revenue)
    bm = burn_multiple(net_burn, args.new_arr) if args.new_arr else None
    scenarios = run_scenarios(args.cash, args.burn, args.revenue, [],
                              args.revenue_growth, args.months)

    if args.json:
        print(json.dumps({
            "net_burn": net_burn,
            "burn_multiple": bm,
            "runway_months": calc_runway(args.cash, net_burn),
            "scenarios": {k: {"months_survived": v["months_survived"],
                               "final_cash": v["final_cash"]}
                          for k, v in scenarios.items()},
        }, ensure_ascii=False, indent=2))
    else:
        print_report(args.cash, args.burn, net_burn, args.revenue, bm, scenarios)


if __name__ == "__main__":
    main()

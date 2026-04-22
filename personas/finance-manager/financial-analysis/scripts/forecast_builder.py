#!/usr/bin/env python3
"""
forecast_builder.py - 驱动因子预测 + 滚动现金流 + 情景模型

用法：
  python forecast_builder.py data.json
  python forecast_builder.py data.json --format json
  python forecast_builder.py data.json --scenarios base,bull,bear
"""

import json
import argparse
import sys
from statistics import mean, stdev


def safe_div(a, b):
    return a / b if (a is not None and b and b != 0) else None


# ── 线性趋势 ──────────────────────────────────────────────

def linear_trend(values: list) -> tuple:
    """返回 (slope, intercept)，用于趋势外推"""
    n = len(values)
    if n < 2:
        return 0, values[0] if values else 0
    x_mean = (n - 1) / 2
    y_mean = mean(values)
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    slope = num / den if den else 0
    intercept = y_mean - slope * x_mean
    return slope, intercept


# ── 驱动因子收入预测 ──────────────────────────────────────

def driver_based_forecast(d: dict, months: int = 12) -> list:
    """
    基于驱动因子：新客数 × ARPU × (1-月流失率) 的累计模型
    """
    base_mrr = d.get("current_mrr", 0)
    new_customers_per_month = d.get("new_customers_per_month", 10)
    arpu = d.get("arpu", 1000)
    monthly_churn = d.get("monthly_churn_rate", 0.02)
    expansion_rate = d.get("expansion_rate", 0.01)

    forecast = []
    mrr = base_mrr
    for m in range(months):
        new_mrr = new_customers_per_month * arpu
        expansion_mrr = mrr * expansion_rate
        churned_mrr = mrr * monthly_churn
        mrr = mrr + new_mrr + expansion_mrr - churned_mrr
        forecast.append({
            "month": m + 1,
            "mrr": round(mrr, 2),
            "arr": round(mrr * 12, 2),
            "new_mrr": round(new_mrr, 2),
            "expansion_mrr": round(expansion_mrr, 2),
            "churned_mrr": round(churned_mrr, 2),
        })
    return forecast


# ── 13周滚动现金流 ────────────────────────────────────────

def rolling_cashflow(d: dict, weeks: int = 13) -> list:
    cash = d.get("current_cash", 0)
    weekly_revenue = d.get("weekly_revenue", 0)
    weekly_expenses = d.get("weekly_expenses", 0)
    ar_collections = d.get("ar_to_collect_weekly", 0)

    schedule = []
    for w in range(weeks):
        inflow = weekly_revenue + ar_collections
        outflow = weekly_expenses
        net = inflow - outflow
        cash += net
        schedule.append({
            "week": w + 1,
            "inflow": round(inflow, 2),
            "outflow": round(outflow, 2),
            "net_cashflow": round(net, 2),
            "ending_cash": round(cash, 2),
        })
    return schedule


# ── 情景模型 ──────────────────────────────────────────────

SCENARIO_MULTIPLIERS = {
    "base":  {"revenue": 1.00, "churn": 1.00, "expenses": 1.00},
    "bull":  {"revenue": 1.20, "churn": 0.80, "expenses": 0.95},
    "bear":  {"revenue": 0.75, "churn": 1.40, "expenses": 1.05},
}


def run_scenario(d: dict, scenario: str, months: int) -> dict:
    mults = SCENARIO_MULTIPLIERS.get(scenario, SCENARIO_MULTIPLIERS["base"])
    adjusted = dict(d)
    adjusted["new_customers_per_month"] = d.get("new_customers_per_month", 10) * mults["revenue"]
    adjusted["monthly_churn_rate"] = d.get("monthly_churn_rate", 0.02) * mults["churn"]

    forecast = driver_based_forecast(adjusted, months)
    final_mrr = forecast[-1]["mrr"]
    final_arr = forecast[-1]["arr"]

    base_expenses = d.get("monthly_expenses", 0)
    total_expenses = base_expenses * mults["expenses"] * months

    return {
        "scenario": scenario,
        "months": months,
        "ending_mrr": final_mrr,
        "ending_arr": final_arr,
        "total_expenses": round(total_expenses, 2),
        "monthly_forecast": forecast,
    }


def print_results(results: dict, scenarios: list):
    print(f"\n{'═'*60}")
    print("  财务预测报告")
    print(f"{'═'*60}")

    if "scenarios" in results:
        print(f"\n  ── 情景对比（第{results['months']}个月末）──")
        print(f"  {'情景':<8} {'期末MRR':>14} {'期末ARR':>14} {'总费用':>14}")
        for sc in results["scenarios"].values():
            print(f"  {sc['scenario']:<8} {sc['ending_mrr']:>14,.0f} "
                  f"{sc['ending_arr']:>14,.0f} {sc['total_expenses']:>14,.0f}")

    if "cashflow" in results:
        cf = results["cashflow"]
        print(f"\n  ── 13周滚动现金流 ──")
        print(f"  {'周':<6} {'流入':>12} {'流出':>12} {'净额':>12} {'期末现金':>14}")
        for w in cf:
            print(f"  {w['week']:<6} {w['inflow']:>12,.0f} {w['outflow']:>12,.0f} "
                  f"{w['net_cashflow']:>12,.0f} {w['ending_cash']:>14,.0f}")


def main():
    parser = argparse.ArgumentParser(description="驱动因子预测 + 情景模型")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--scenarios", default="base", help="情景列表，逗号分隔：base,bull,bear")
    parser.add_argument("--months", type=int, default=12)
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.input}", file=sys.stderr)
        sys.exit(1)

    scenario_list = [s.strip() for s in args.scenarios.split(",")]
    scenarios = {s: run_scenario(data, s, args.months) for s in scenario_list}
    cashflow = rolling_cashflow(data)

    result = {
        "months": args.months,
        "scenarios": scenarios,
        "cashflow": cashflow,
    }

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_results(result, scenario_list)


if __name__ == "__main__":
    main()

# ── INPUT SCHEMA ──────────────────────────────────────────
# {
#   "current_mrr": 100000,
#   "new_customers_per_month": 20,
#   "arpu": 2000,
#   "monthly_churn_rate": 0.02,
#   "expansion_rate": 0.01,
#   "monthly_expenses": 80000,
#   "current_cash": 500000,
#   "weekly_revenue": 25000,
#   "weekly_expenses": 20000,
#   "ar_to_collect_weekly": 5000
# }

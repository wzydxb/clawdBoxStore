#!/usr/bin/env python3
"""
unit_economics_analyzer.py - 分渠道 CAC + 分队列 LTV 分析

用法：
  python unit_economics_analyzer.py data.json
  python unit_economics_analyzer.py data.json --json
  python unit_economics_analyzer.py data.json --cohort-months 12

INPUT SCHEMA:
{
  "gross_margin_pct": 70,
  "monthly_churn_rate": 0.03,
  "channels": [
    {"name": "SEO", "spend": 20000, "new_customers": 40},
    {"name": "Paid", "spend": 50000, "new_customers": 60},
    {"name": "Referral", "spend": 5000, "new_customers": 25}
  ],
  "cohorts": [
    {
      "name": "2024-Q1",
      "initial_customers": 100,
      "initial_mrr": 50000,
      "monthly_data": [
        {"month": 1, "customers": 95, "mrr": 48000},
        {"month": 2, "customers": 90, "mrr": 46500}
      ]
    }
  ]
}
"""

import argparse
import json
import sys


def analyze_channel(ch: dict, gross_margin_pct: float, monthly_churn_rate: float) -> dict:
    name = ch["name"]
    spend = ch.get("spend", 0)
    new_customers = ch.get("new_customers", 0)

    cac = spend / new_customers if new_customers > 0 else None
    gm = gross_margin_pct / 100
    arpa = ch.get("arpa", None)

    ltv = None
    ltv_cac = None
    payback_months = None

    if arpa and monthly_churn_rate > 0:
        ltv = (arpa * gm) / monthly_churn_rate
        if cac:
            ltv_cac = ltv / cac
            monthly_gp = arpa * gm
            payback_months = cac / monthly_gp if monthly_gp > 0 else None

    return {
        "channel": name,
        "spend": spend,
        "new_customers": new_customers,
        "cac": round(cac, 0) if cac else None,
        "ltv": round(ltv, 0) if ltv else None,
        "ltv_cac_ratio": round(ltv_cac, 2) if ltv_cac else None,
        "payback_months": round(payback_months, 1) if payback_months else None,
    }


def analyze_cohort(cohort: dict, cohort_months: int) -> dict:
    name = cohort["name"]
    initial_customers = cohort["initial_customers"]
    initial_mrr = cohort["initial_mrr"]
    monthly_data = cohort.get("monthly_data", [])[:cohort_months]

    if not monthly_data:
        return {"cohort": name, "error": "no monthly data"}

    # Retention curve
    retention = []
    for row in monthly_data:
        ret = row["customers"] / initial_customers if initial_customers > 0 else 0
        retention.append(round(ret, 4))

    # Net revenue retention
    final_mrr = monthly_data[-1]["mrr"] if monthly_data else initial_mrr
    nrr = final_mrr / initial_mrr if initial_mrr > 0 else None

    # Cumulative revenue per initial customer
    cumulative_rev = sum(r["mrr"] for r in monthly_data)
    rev_per_customer = cumulative_rev / initial_customers if initial_customers > 0 else None

    # Churn rate (average monthly)
    churn_rates = []
    prev = initial_customers
    for row in monthly_data:
        curr = row["customers"]
        if prev > 0:
            churn_rates.append((prev - curr) / prev)
        prev = curr
    avg_churn = sum(churn_rates) / len(churn_rates) if churn_rates else None

    return {
        "cohort": name,
        "initial_customers": initial_customers,
        "initial_mrr": initial_mrr,
        "months_tracked": len(monthly_data),
        "final_customers": monthly_data[-1]["customers"] if monthly_data else initial_customers,
        "final_mrr": final_mrr,
        "nrr": round(nrr, 4) if nrr else None,
        "avg_monthly_churn": round(avg_churn, 4) if avg_churn else None,
        "cumulative_rev_per_customer": round(rev_per_customer, 0) if rev_per_customer else None,
        "retention_curve": retention,
    }


def cac_status(cac, ltv):
    if cac is None or ltv is None:
        return "⚪"
    ratio = ltv / cac
    if ratio >= 3:
        return "🟢"
    elif ratio >= 1.5:
        return "🟡"
    return "🔴"


def print_channel_report(channels):
    print(f"\n{'═'*65}")
    print("  分渠道 CAC 分析")
    print(f"{'═'*65}")
    print(f"  {'渠道':<12} {'花费':>10} {'新客':>6} {'CAC':>8} {'LTV':>10} {'LTV:CAC':>8} {'回收期':>8}")
    for c in channels:
        cac_s = f"{c['cac']:,.0f}" if c['cac'] else "N/A"
        ltv_s = f"{c['ltv']:,.0f}" if c['ltv'] else "N/A"
        lc_s = f"{c['ltv_cac_ratio']:.2f}" if c['ltv_cac_ratio'] else "N/A"
        pb_s = f"{c['payback_months']:.1f}mo" if c['payback_months'] else "N/A"
        icon = cac_status(c['cac'], c['ltv'])
        print(f"  {c['channel']:<12} {c['spend']:>10,.0f} {c['new_customers']:>6} "
              f"{cac_s:>8} {ltv_s:>10} {lc_s:>8} {pb_s:>8}  {icon}")


def print_cohort_report(cohorts):
    print(f"\n  ── 队列分析 ──")
    print(f"  {'队列':<12} {'初始客户':>8} {'期末客户':>8} {'NRR':>8} {'月均流失':>8} {'累计收入/客户':>14}")
    for c in cohorts:
        if "error" in c:
            print(f"  {c['cohort']:<12}  {c['error']}")
            continue
        nrr_s = f"{c['nrr']*100:.1f}%" if c['nrr'] else "N/A"
        churn_s = f"{c['avg_monthly_churn']*100:.1f}%" if c['avg_monthly_churn'] else "N/A"
        rev_s = f"{c['cumulative_rev_per_customer']:,.0f}" if c['cumulative_rev_per_customer'] else "N/A"
        nrr_icon = "🟢" if c['nrr'] and c['nrr'] >= 1.1 else ("🟡" if c['nrr'] and c['nrr'] >= 1.0 else "🔴")
        print(f"  {c['cohort']:<12} {c['initial_customers']:>8} {c['final_customers']:>8} "
              f"{nrr_s:>8} {churn_s:>8} {rev_s:>14}  {nrr_icon}")


def main():
    parser = argparse.ArgumentParser(description="分渠道 CAC + 分队列 LTV 分析")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("--cohort-months", type=int, default=12)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.input}", file=sys.stderr)
        sys.exit(1)

    gm = data.get("gross_margin_pct", 70)
    churn = data.get("monthly_churn_rate", 0.03)

    channel_results = [analyze_channel(ch, gm, churn) for ch in data.get("channels", [])]
    cohort_results = [analyze_cohort(c, args.cohort_months) for c in data.get("cohorts", [])]

    if args.json:
        print(json.dumps({"channels": channel_results, "cohorts": cohort_results},
                         ensure_ascii=False, indent=2))
    else:
        if channel_results:
            print_channel_report(channel_results)
        if cohort_results:
            print_cohort_report(cohort_results)


if __name__ == "__main__":
    main()

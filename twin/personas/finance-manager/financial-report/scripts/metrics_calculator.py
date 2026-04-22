#!/usr/bin/env python3
"""
metrics_calculator.py - SaaS 核心指标计算器

用法：
  python metrics_calculator.py                          # 交互模式
  python metrics_calculator.py --mrr 50000 --customers 100 --churned 5
  python metrics_calculator.py --mrr 50000 --customers 100 --churned 5 --json
"""

import argparse
import json
import sys


def safe_div(a, b):
    return a / b if (a is not None and b and b != 0) else None


def calc_metrics(mrr, mrr_prev, customers, new_customers, churned_customers,
                 sm_spend, gross_margin_pct, expansion_mrr=0, churned_mrr=0,
                 contraction_mrr=0) -> dict:

    arr = mrr * 12
    arpa = safe_div(mrr, customers)

    # 增长率
    mrr_growth = safe_div(mrr - mrr_prev, mrr_prev) if mrr_prev else None

    # 流失
    monthly_churn_rate = safe_div(churned_customers, customers - new_customers) if customers else None
    mrr_churn_rate = safe_div(churned_mrr, mrr_prev) if mrr_prev else None

    # CAC
    cac = safe_div(sm_spend, new_customers) if new_customers else None

    # LTV
    avg_revenue_per_customer = arpa
    gross_margin = gross_margin_pct / 100 if gross_margin_pct else None
    monthly_gross_profit = (avg_revenue_per_customer * gross_margin) if (avg_revenue_per_customer and gross_margin) else None
    ltv = safe_div(monthly_gross_profit, monthly_churn_rate) if monthly_churn_rate else None

    # LTV:CAC
    ltv_cac = safe_div(ltv, cac) if (ltv and cac) else None

    # CAC 回收期（月）
    cac_payback = safe_div(cac, monthly_gross_profit) if (cac and monthly_gross_profit) else None

    # NRR（净收入留存）
    starting_mrr = mrr - (mrr - mrr_prev) if mrr_prev else None
    nrr = safe_div(mrr_prev + expansion_mrr - churned_mrr - contraction_mrr, mrr_prev) if mrr_prev else None

    return {
        "arr": arr,
        "mrr": mrr,
        "mrr_growth_rate": mrr_growth,
        "arpa": arpa,
        "monthly_churn_rate": monthly_churn_rate,
        "mrr_churn_rate": mrr_churn_rate,
        "cac": cac,
        "ltv": ltv,
        "ltv_cac_ratio": ltv_cac,
        "cac_payback_months": cac_payback,
        "nrr": nrr,
        "gross_margin_pct": gross_margin_pct,
    }


BENCHMARKS = {
    "mrr_growth_rate":   {"label": "MRR增长率",    "good": 0.10,  "warn": 0.05,  "pct": True},
    "monthly_churn_rate":{"label": "月流失率",      "good": 0.02,  "warn": 0.05,  "pct": True,  "lower": True},
    "ltv_cac_ratio":     {"label": "LTV:CAC",       "good": 3.0,   "warn": 1.5},
    "cac_payback_months":{"label": "CAC回收期(月)", "good": 12,    "warn": 18,    "lower": True},
    "nrr":               {"label": "NRR",           "good": 1.10,  "warn": 1.00,  "pct": True},
    "gross_margin_pct":  {"label": "毛利率",        "good": 70,    "warn": 50},
}


def status_icon(key, value):
    if value is None:
        return "⚪"
    b = BENCHMARKS.get(key)
    if not b:
        return ""
    lower = b.get("lower", False)
    good, warn = b["good"], b["warn"]
    if lower:
        return "🟢" if value <= good else ("🟡" if value <= warn else "🔴")
    else:
        return "🟢" if value >= good else ("🟡" if value >= warn else "🔴")


def fmt_val(key, value):
    if value is None:
        return "N/A"
    b = BENCHMARKS.get(key, {})
    if b.get("pct"):
        return f"{value*100:.1f}%"
    if key in ("arr", "mrr", "arpa", "cac", "ltv"):
        return f"{value:,.0f}"
    return f"{value:.2f}"


def print_report(m: dict):
    print(f"\n{'═'*55}")
    print("  SaaS 健康报告")
    print(f"{'═'*55}")
    print(f"  {'指标':<22} {'数值':>12}  状态")
    print(f"  {'─'*50}")
    print(f"  {'ARR':<22} {m['arr']:>12,.0f}")
    print(f"  {'MRR':<22} {m['mrr']:>12,.0f}")
    print(f"  {'ARPA':<22} {m['arpa']:>12,.0f}" if m['arpa'] else "")

    for key in ["mrr_growth_rate", "monthly_churn_rate", "mrr_churn_rate",
                "cac", "ltv", "ltv_cac_ratio", "cac_payback_months", "nrr", "gross_margin_pct"]:
        b = BENCHMARKS.get(key)
        label = b["label"] if b else key
        icon = status_icon(key, m[key])
        val = fmt_val(key, m[key])
        print(f"  {label:<22} {val:>12}  {icon}")

    # 优先问题
    critical = [(k, b) for k, b in BENCHMARKS.items()
                if status_icon(k, m.get(k)) == "🔴"]
    watch = [(k, b) for k, b in BENCHMARKS.items()
             if status_icon(k, m.get(k)) == "🟡"]

    if critical or watch:
        print(f"\n  ── 需要关注 ──")
        for k, b in critical:
            print(f"  🔴 {b['label']}：{fmt_val(k, m.get(k))} — 严重，需立即处理")
        for k, b in watch:
            print(f"  🟡 {b['label']}：{fmt_val(k, m.get(k))} — 需要关注")


def interactive_mode():
    print("SaaS 指标计算器（交互模式）")
    print("直接回车跳过可选项\n")

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

    mrr = ask("当前 MRR")
    mrr_prev = ask("上月 MRR（可选）", required=False)
    customers = ask("当前客户数")
    new_customers = ask("本月新增客户数")
    churned = ask("本月流失客户数")
    sm_spend = ask("本月销售+市场费用（可选）", required=False)
    gm = ask("毛利率 % （如 70）（可选）", required=False)
    expansion = ask("扩张 MRR（可选）", required=False) or 0
    churned_mrr = ask("流失 MRR（可选）", required=False) or 0

    m = calc_metrics(mrr, mrr_prev, customers, new_customers, churned,
                     sm_spend, gm, expansion, churned_mrr)
    print_report(m)


def main():
    parser = argparse.ArgumentParser(description="SaaS 核心指标计算器")
    parser.add_argument("--mrr", type=float)
    parser.add_argument("--mrr-prev", type=float)
    parser.add_argument("--customers", type=float)
    parser.add_argument("--new-customers", type=float, default=0)
    parser.add_argument("--churned", type=float, default=0)
    parser.add_argument("--sm-spend", type=float)
    parser.add_argument("--gross-margin", type=float)
    parser.add_argument("--expansion-mrr", type=float, default=0)
    parser.add_argument("--churned-mrr", type=float, default=0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.mrr:
        interactive_mode()
        return

    m = calc_metrics(args.mrr, args.mrr_prev, args.customers,
                     args.new_customers, args.churned,
                     args.sm_spend, args.gross_margin,
                     args.expansion_mrr, args.churned_mrr)

    if args.json:
        print(json.dumps(m, ensure_ascii=False, indent=2))
    else:
        print_report(m)


if __name__ == "__main__":
    main()

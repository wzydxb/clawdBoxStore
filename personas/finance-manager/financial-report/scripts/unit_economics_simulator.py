#!/usr/bin/env python3
"""
unit_economics_simulator.py - 12个月单位经济学前瞻模拟

用法：
  python unit_economics_simulator.py --mrr 50000 --growth 10 --churn 3 --cac 2000
  python unit_economics_simulator.py --mrr 50000 --growth 10 --churn 3 --cac 2000 --json
  python unit_economics_simulator.py --mrr 50000 --growth 10 --churn 3 --cac 2000 --scenarios
"""

import argparse
import json


def simulate(mrr, monthly_growth_rate, monthly_churn_rate, cac,
             gross_margin_pct=70, months=12, sm_spend_monthly=None, arpa=None):

    results = []
    current_mrr = mrr
    cumulative_sm = 0

    for m in range(1, months + 1):
        new_mrr = current_mrr * monthly_growth_rate / 100
        churned_mrr = current_mrr * monthly_churn_rate / 100
        current_mrr = current_mrr + new_mrr - churned_mrr

        gm = gross_margin_pct / 100
        # Use provided ARPA or fall back to initial MRR (constant proxy)
        unit_arpa = arpa or mrr
        ltv = (unit_arpa * gm) / (monthly_churn_rate / 100) if monthly_churn_rate else None
        ltv_cac = ltv / cac if (ltv and cac) else None
        payback = cac / (unit_arpa * gm) if (cac and unit_arpa and gm) else None

        sm = sm_spend_monthly or (new_mrr / (monthly_growth_rate / 100) * 0.3)
        cumulative_sm += sm

        results.append({
            "month": m,
            "mrr": round(current_mrr, 0),
            "arr": round(current_mrr * 12, 0),
            "net_new_mrr": round(new_mrr - churned_mrr, 0),
            "churned_mrr": round(churned_mrr, 0),
            "ltv": round(ltv, 0) if ltv else None,
            "ltv_cac_ratio": round(ltv_cac, 2) if ltv_cac else None,
            "cac_payback_months": round(payback, 1) if payback else None,
        })

    return results


def print_report(results, label="base"):
    print(f"\n  ── {label} ──")
    print(f"  {'月':<5} {'MRR':>10} {'ARR':>12} {'净新增MRR':>10} {'LTV:CAC':>9} {'回收期':>8}")
    for r in results:
        ltv_cac = f"{r['ltv_cac_ratio']:.2f}" if r["ltv_cac_ratio"] else "N/A"
        payback = f"{r['cac_payback_months']:.1f}mo" if r["cac_payback_months"] else "N/A"
        print(f"  {r['month']:<5} {r['mrr']:>10,.0f} {r['arr']:>12,.0f} "
              f"{r['net_new_mrr']:>10,.0f} {ltv_cac:>9} {payback:>8}")


def main():
    parser = argparse.ArgumentParser(description="单位经济学12个月模拟")
    parser.add_argument("--mrr", type=float, required=True, help="当前 MRR")
    parser.add_argument("--growth", type=float, required=True, help="月增长率（如 10 代表10%%）")
    parser.add_argument("--churn", type=float, required=True, help="月流失率（如 3 代表3%%）")
    parser.add_argument("--cac", type=float, required=True, help="CAC（客户获取成本）")
    parser.add_argument("--arpa", type=float, help="每客户月均收入（不填则用初始MRR作为代理）")
    parser.add_argument("--gross-margin", type=float, default=70, help="毛利率（默认70%%）")
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--scenarios", action="store_true", help="同时输出 bull/bear 情景")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    base = simulate(args.mrr, args.growth, args.churn, args.cac,
                    args.gross_margin, args.months, arpa=args.arpa)

    if args.json:
        out = {"base": base}
        if args.scenarios:
            out["bull"] = simulate(args.mrr, args.growth * 1.3, args.churn * 0.7,
                                   args.cac, args.gross_margin, args.months, arpa=args.arpa)
            out["bear"] = simulate(args.mrr, args.growth * 0.6, args.churn * 1.4,
                                   args.cac, args.gross_margin, args.months, arpa=args.arpa)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'═'*60}")
        print("  单位经济学 12 个月预测")
        print(f"  初始 MRR: {args.mrr:,.0f}  增长: {args.growth}%%/月  流失: {args.churn}%%/月  CAC: {args.cac:,.0f}")
        print(f"{'═'*60}")
        print_report(base, "基准情景")
        if args.scenarios:
            bull = simulate(args.mrr, args.growth * 1.3, args.churn * 0.7,
                            args.cac, args.gross_margin, args.months, arpa=args.arpa)
            bear = simulate(args.mrr, args.growth * 0.6, args.churn * 1.4,
                            args.cac, args.gross_margin, args.months, arpa=args.arpa)
            print_report(bull, f"乐观（增长×1.3，流失×0.7）")
            print_report(bear, f"悲观（增长×0.6，流失×1.4）")

        final = base[-1]
        print(f"\n  期末 ARR: {final['arr']:,.0f}")
        if final["ltv_cac_ratio"]:
            icon = "🟢" if final["ltv_cac_ratio"] >= 3 else ("🟡" if final["ltv_cac_ratio"] >= 1.5 else "🔴")
            print(f"  期末 LTV:CAC: {final['ltv_cac_ratio']:.2f}  {icon}")


if __name__ == "__main__":
    main()

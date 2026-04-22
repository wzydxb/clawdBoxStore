#!/usr/bin/env python3
"""
comp_benchmarker.py - 薪酬基准对比 + 薪资带建模 + 总薪酬分析

用法：
  python comp_benchmarker.py data.json
  python comp_benchmarker.py data.json --json
  python comp_benchmarker.py data.json --percentile 50

INPUT SCHEMA:
{
  "company_stage": "series-a",
  "location": "Beijing",
  "employees": [
    {
      "name": "张三",
      "title": "Senior Engineer",
      "level": "L5",
      "department": "Engineering",
      "base_salary": 280000,
      "equity_usd": 50000,
      "bonus_pct": 10,
      "market_p50": 300000,
      "market_p75": 360000,
      "market_p90": 420000
    }
  ]
}
"""

import argparse
import json
import sys


EQUITY_REFRESH_SCHEDULE = {
    "seed": 0.25,
    "series-a": 0.20,
    "series-b": 0.15,
    "series-c": 0.10,
    "growth": 0.08,
}


def analyze_employee(emp: dict, target_percentile: int = 50) -> dict:
    name = emp.get("name", "")
    base = emp.get("base_salary", 0)
    equity = emp.get("equity_usd", 0)
    bonus_pct = emp.get("bonus_pct", 0)
    p50 = emp.get("market_p50")
    p75 = emp.get("market_p75")
    p90 = emp.get("market_p90")

    bonus_amount = base * bonus_pct / 100
    total_cash = base + bonus_amount
    total_comp = total_cash + equity

    # Compa-ratio vs target percentile
    if target_percentile == 50:
        market_ref = p50
    elif target_percentile == 75:
        market_ref = p75
    else:
        market_ref = p90

    compa_ratio = base / market_ref if market_ref else None

    # Position in band
    if p50 and p75 and p90:
        if base < p50:
            band_position = "below-market"
            position_icon = "🔴"
        elif base <= p75:
            band_position = "market"
            position_icon = "🟢"
        elif base <= p90:
            band_position = "above-market"
            position_icon = "🟡"
        else:
            band_position = "top-of-market"
            position_icon = "🟢"
    else:
        band_position = None
        position_icon = "⚪"

    # Raise recommendation: flag if below P50 (compa < 1.0)
    raise_rec = None
    if compa_ratio and compa_ratio < 1.0 and market_ref:
        raise_rec = round((market_ref - base), 0)

    return {
        "name": name,
        "title": emp.get("title", ""),
        "level": emp.get("level", ""),
        "department": emp.get("department", ""),
        "base_salary": base,
        "bonus_amount": round(bonus_amount, 0),
        "equity_usd": equity,
        "total_cash": round(total_cash, 0),
        "total_comp": round(total_comp, 0),
        "market_p50": p50,
        "market_p75": p75,
        "market_p90": p90,
        "compa_ratio": round(compa_ratio, 2) if compa_ratio else None,
        "band_position": band_position,
        "position_icon": position_icon,
        "raise_recommendation": raise_rec,
    }


def print_report(results: list, company_stage: str, target_percentile: int):
    print(f"\n{'═'*75}")
    print(f"  薪酬基准报告  |  阶段：{company_stage}  |  目标分位：P{target_percentile}")
    print(f"{'═'*75}")
    print(f"  {'姓名':<10} {'职级':<8} {'基本薪资':>10} {'总现金':>10} {'总薪酬':>10} {'Compa':>7} {'市场位置'}")
    print(f"  {'─'*70}")

    for r in results:
        compa_s = f"{r['compa_ratio']:.2f}" if r['compa_ratio'] else "N/A"
        print(f"  {r['name']:<10} {r['level']:<8} {r['base_salary']:>10,.0f} "
              f"{r['total_cash']:>10,.0f} {r['total_comp']:>10,.0f} "
              f"{compa_s:>7}  {r['position_icon']} {r['band_position'] or ''}")

    # Raise recommendations
    needs_raise = [r for r in results if r["raise_recommendation"]]
    if needs_raise:
        print(f"\n  ── 薪酬调整建议 ──")
        for r in needs_raise:
            print(f"  🔴 {r['name']} ({r['title']})：建议调薪 +{r['raise_recommendation']:,.0f}（当前低于市场P50）")

    # Summary stats
    total_payroll = sum(r["base_salary"] for r in results)
    below_market = sum(1 for r in results if r["band_position"] == "below-market")
    print(f"\n  总基本薪资包：{total_payroll:,.0f}  |  低于市场：{below_market} 人")


def main():
    parser = argparse.ArgumentParser(description="薪酬基准对比 + 薪资带建模")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("--percentile", type=int, default=50, choices=[50, 75, 90],
                        help="目标市场分位（默认 P50）")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.input}", file=sys.stderr)
        sys.exit(1)

    company_stage = data.get("company_stage", "series-a")
    results = [analyze_employee(emp, args.percentile) for emp in data.get("employees", [])]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_report(results, company_stage, args.percentile)


if __name__ == "__main__":
    main()

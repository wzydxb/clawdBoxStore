#!/usr/bin/env python3
"""
budget_variance_analyzer.py - 预算差异分析

用法：
  python budget_variance_analyzer.py data.json
  python budget_variance_analyzer.py data.json --format json
  python budget_variance_analyzer.py data.json --threshold-pct 5 --threshold-amt 25000
"""

import json
import argparse
import sys


def safe_div(a, b):
    return a / b if (a is not None and b and b != 0) else None


def is_material(variance_amt, variance_pct, threshold_pct, threshold_amt):
    return abs(variance_pct or 0) >= threshold_pct or abs(variance_amt or 0) >= threshold_amt


def classify(item_type: str, variance_amt: float) -> str:
    """收入正差异=有利，费用正差异=不利"""
    if item_type == "revenue":
        return "有利 ✅" if variance_amt >= 0 else "不利 ❌"
    else:
        return "有利 ✅" if variance_amt <= 0 else "不利 ❌"


def analyze_item(item: dict, threshold_pct: float, threshold_amt: float) -> dict:
    actual = item.get("actual", 0)
    budget = item.get("budget", 0)
    prior = item.get("prior_year")
    item_type = item.get("type", "expense")  # revenue / expense

    var_amt = actual - budget
    var_pct = safe_div(var_amt, abs(budget))

    var_vs_prior_amt = (actual - prior) if prior is not None else None
    var_vs_prior_pct = safe_div(var_vs_prior_amt, abs(prior)) if prior else None

    material = is_material(var_amt, var_pct, threshold_pct, threshold_amt)

    return {
        "name":              item.get("name", "未命名"),
        "department":        item.get("department", ""),
        "category":          item.get("category", ""),
        "type":              item_type,
        "actual":            actual,
        "budget":            budget,
        "variance_amt":      var_amt,
        "variance_pct":      var_pct,
        "prior_year":        prior,
        "vs_prior_amt":      var_vs_prior_amt,
        "vs_prior_pct":      var_vs_prior_pct,
        "classification":    classify(item_type, var_amt),
        "material":          material,
    }


def flatten_items(data: dict) -> list:
    """支持两种输入格式：
    1. 扁平: {"items": [...]}
    2. 部门嵌套: {"departments": [{"name": "Engineering", "items": [...]}]}
    """
    if "items" in data:
        return data["items"]
    flat = []
    for dept in data.get("departments", []):
        dept_name = dept.get("name", "")
        for item in dept.get("items", []):
            item = dict(item)
            if not item.get("department"):
                item["department"] = dept_name
            flat.append(item)
    return flat


def run(data: dict, threshold_pct: float, threshold_amt: float) -> dict:
    items = flatten_items(data)
    period = data.get("period", "")

    analyzed = [analyze_item(i, threshold_pct, threshold_amt) for i in items]
    material = [a for a in analyzed if a["material"]]

    total_actual = sum(a["actual"] for a in analyzed)
    total_budget = sum(a["budget"] for a in analyzed)
    total_var = total_actual - total_budget

    # 按部门汇总
    dept_summary = {}
    for a in analyzed:
        dept = a["department"] or "其他"
        if dept not in dept_summary:
            dept_summary[dept] = {"actual": 0, "budget": 0}
        dept_summary[dept]["actual"] += a["actual"]
        dept_summary[dept]["budget"] += a["budget"]
    for dept, s in dept_summary.items():
        s["variance"] = s["actual"] - s["budget"]
        s["variance_pct"] = safe_div(s["variance"], abs(s["budget"]))

    return {
        "period": period,
        "summary": {
            "total_actual": total_actual,
            "total_budget": total_budget,
            "total_variance": total_var,
            "total_variance_pct": safe_div(total_var, abs(total_budget)),
            "material_items_count": len(material),
        },
        "material_variances": material,
        "all_items": analyzed,
        "department_summary": dept_summary,
    }


def fmt_amt(v):
    if v is None:
        return "N/A"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:,.0f}"


def fmt_pct(v):
    if v is None:
        return "N/A"
    sign = "+" if v > 0 else ""
    return f"{sign}{v*100:.1f}%"


def print_results(r: dict):
    s = r["summary"]
    print(f"\n{'═'*60}")
    print(f"  预算差异分析报告  {r['period']}")
    print(f"{'═'*60}")
    print(f"  实际合计    {s['total_actual']:>15,.0f}")
    print(f"  预算合计    {s['total_budget']:>15,.0f}")
    print(f"  总差异      {fmt_amt(s['total_variance']):>15}  ({fmt_pct(s['total_variance_pct'])})")
    print(f"  重大差异项  {s['material_items_count']} 项")

    if r["department_summary"]:
        print(f"\n{'─'*60}")
        print("  部门汇总")
        print(f"{'─'*60}")
        print(f"  {'部门':<20} {'实际':>12} {'预算':>12} {'差异':>12} {'差异%':>8}")
        for dept, ds in r["department_summary"].items():
            print(f"  {dept:<20} {ds['actual']:>12,.0f} {ds['budget']:>12,.0f} "
                  f"{fmt_amt(ds['variance']):>12} {fmt_pct(ds['variance_pct']):>8}")

    if r["material_variances"]:
        print(f"\n{'─'*60}")
        print("  重大差异明细")
        print(f"{'─'*60}")
        for item in r["material_variances"]:
            print(f"\n  {item['name']}  [{item['department']}]  {item['classification']}")
            print(f"    实际: {item['actual']:,.0f}  预算: {item['budget']:,.0f}  "
                  f"差异: {fmt_amt(item['variance_amt'])} ({fmt_pct(item['variance_pct'])})")
            if item["prior_year"] is not None:
                print(f"    同比: {fmt_amt(item['vs_prior_amt'])} ({fmt_pct(item['vs_prior_pct'])})")


def main():
    parser = argparse.ArgumentParser(description="预算差异分析")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--threshold-pct", type=float, default=10.0, help="重大差异百分比阈值（默认10%%）")
    parser.add_argument("--threshold-amt", type=float, default=50000, help="重大差异金额阈值（默认50000）")
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.input}", file=sys.stderr)
        sys.exit(1)

    result = run(data, args.threshold_pct / 100, args.threshold_amt)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_results(result)


if __name__ == "__main__":
    main()

# ── INPUT SCHEMA ──────────────────────────────────────────
# {
#   "period": "2025-Q1",
#   "items": [
#     {
#       "name": "销售收入",
#       "department": "销售部",
#       "category": "收入",
#       "type": "revenue",
#       "actual": 1200000,
#       "budget": 1000000,
#       "prior_year": 900000
#     },
#     {
#       "name": "市场费用",
#       "department": "市场部",
#       "category": "费用",
#       "type": "expense",
#       "actual": 180000,
#       "budget": 150000,
#       "prior_year": 130000
#     }
#   ]
# }

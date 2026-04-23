#!/usr/bin/env python3
"""
hiring_plan_modeler.py - 招聘计划 + 人力成本预测 + 部门编制规划

用法：
  python hiring_plan_modeler.py data.json
  python hiring_plan_modeler.py data.json --json
  python hiring_plan_modeler.py data.json --months 12

INPUT SCHEMA:
{
  "current_headcount": 25,
  "current_monthly_payroll": 300000,
  "benefits_multiplier": 1.25,
  "roles": [
    {
      "title": "Senior Engineer",
      "department": "Engineering",
      "level": "L5",
      "base_salary": 240000,
      "hire_month": 2,
      "backfill": false
    },
    {
      "title": "Account Executive",
      "department": "Sales",
      "level": "IC3",
      "base_salary": 120000,
      "ote_multiplier": 2.0,
      "hire_month": 3,
      "backfill": false
    }
  ]
}
"""

import argparse
import json
import sys


def model_hiring_plan(data: dict, months: int = 12) -> dict:
    current_hc = data.get("current_headcount", 0)
    current_payroll = data.get("current_monthly_payroll", 0)
    benefits_mult = data.get("benefits_multiplier", 1.25)
    roles = data.get("roles", [])

    # Build monthly schedule
    monthly = []
    cumulative_hc = current_hc
    cumulative_payroll = current_payroll

    hire_schedule = {}
    for role in roles:
        m = role.get("hire_month", 1)
        if m not in hire_schedule:
            hire_schedule[m] = []
        hire_schedule[m].append(role)

    total_new_hires = 0
    total_annual_cost = 0

    for m in range(1, months + 1):
        new_hires = hire_schedule.get(m, [])
        new_hc = len(new_hires)
        cumulative_hc += new_hc
        total_new_hires += new_hc

        new_monthly_cost = 0
        for role in new_hires:
            base = role.get("base_salary", 0)
            ote_mult = role.get("ote_multiplier", 1.0)
            annual_tc = base * ote_mult
            monthly_tc = annual_tc / 12 * benefits_mult
            new_monthly_cost += monthly_tc
            total_annual_cost += annual_tc * benefits_mult  # full cost including benefits

        cumulative_payroll += new_monthly_cost

        monthly.append({
            "month": m,
            "new_hires": new_hc,
            "new_roles": [r["title"] for r in new_hires],
            "cumulative_headcount": cumulative_hc,
            "monthly_payroll": round(cumulative_payroll, 0),
            "monthly_payroll_increase": round(new_monthly_cost, 0),
        })

    # Department breakdown
    dept_summary = {}
    for role in roles:
        dept = role.get("department", "Other")
        if dept not in dept_summary:
            dept_summary[dept] = {"headcount": 0, "annual_cost": 0}
        dept_summary[dept]["headcount"] += 1
        base = role.get("base_salary", 0)
        ote_mult = role.get("ote_multiplier", 1.0)
        dept_summary[dept]["annual_cost"] += base * ote_mult * benefits_mult

    return {
        "summary": {
            "current_headcount": current_hc,
            "total_new_hires": total_new_hires,
            "ending_headcount": cumulative_hc,
            "current_monthly_payroll": current_payroll,
            "ending_monthly_payroll": round(cumulative_payroll, 0),
            "total_incremental_annual_cost": round(total_annual_cost, 0),
        },
        "monthly_plan": monthly,
        "by_department": {k: {"headcount": v["headcount"],
                               "annual_cost": round(v["annual_cost"], 0)}
                          for k, v in dept_summary.items()},
    }


def print_report(result: dict):
    s = result["summary"]
    print(f"\n{'═'*60}")
    print("  招聘计划报告")
    print(f"{'═'*60}")
    print(f"  当前人数          {s['current_headcount']:>10}")
    print(f"  新增招聘          {s['total_new_hires']:>10}")
    print(f"  期末人数          {s['ending_headcount']:>10}")
    print(f"  当前月薪资包      {s['current_monthly_payroll']:>10,.0f}")
    print(f"  期末月薪资包      {s['ending_monthly_payroll']:>10,.0f}")
    print(f"  新增年度人力成本  {s['total_incremental_annual_cost']:>10,.0f}")

    print(f"\n  ── 部门分布 ──")
    print(f"  {'部门':<20} {'新增人数':>8} {'年度成本':>14}")
    for dept, info in result["by_department"].items():
        print(f"  {dept:<20} {info['headcount']:>8} {info['annual_cost']:>14,.0f}")

    print(f"\n  ── 月度招聘计划 ──")
    print(f"  {'月':<5} {'新增':>5} {'累计人数':>8} {'月薪资包':>12}  新增岗位")
    for m in result["monthly_plan"]:
        roles_str = ", ".join(m["new_roles"]) if m["new_roles"] else "—"
        print(f"  {m['month']:<5} {m['new_hires']:>5} {m['cumulative_headcount']:>8} "
              f"{m['monthly_payroll']:>12,.0f}  {roles_str}")


def main():
    parser = argparse.ArgumentParser(description="招聘计划 + 人力成本预测")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.input}", file=sys.stderr)
        sys.exit(1)

    result = model_hiring_plan(data, args.months)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_report(result)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
ops_efficiency_analyzer.py - 流程效率分析 + 成熟度评分 + 瓶颈定位

用法：
  python ops_efficiency_analyzer.py data.json
  python ops_efficiency_analyzer.py data.json --json
  python ops_efficiency_analyzer.py --interactive

INPUT SCHEMA:
{
  "processes": [
    {
      "name": "客户签约流程",
      "owner": "销售",
      "avg_cycle_time_days": 14,
      "target_cycle_time_days": 7,
      "error_rate_pct": 8,
      "automation_pct": 20,
      "steps": [
        {"name": "需求确认", "time_days": 2, "manual": true},
        {"name": "合同起草", "time_days": 5, "manual": true},
        {"name": "法务审核", "time_days": 4, "manual": true},
        {"name": "签署归档", "time_days": 3, "manual": false}
      ]
    }
  ]
}
"""

import argparse
import json
import sys


MATURITY_LEVELS = {
    1: "Ad hoc（随机应变）",
    2: "Defined（有流程文档）",
    3: "Measured（跟踪KPI）",
    4: "Managed（数据驱动改进）",
    5: "Optimized（持续优化循环）",
}


def score_maturity(proc: dict) -> int:
    """
    根据流程指标推断成熟度等级（1-5）
    """
    score = 1
    # Has defined steps
    if proc.get("steps"):
        score = max(score, 2)
    # Has measurement (cycle time vs target)
    if proc.get("avg_cycle_time_days") and proc.get("target_cycle_time_days"):
        score = max(score, 3)
    # Error rate tracked
    if proc.get("error_rate_pct") is not None:
        score = max(score, 3)
    # High automation = managed
    automation = proc.get("automation_pct", 0)
    if automation >= 50:
        score = max(score, 4)
    # Near target + low error = optimized
    cycle = proc.get("avg_cycle_time_days")
    target = proc.get("target_cycle_time_days")
    error = proc.get("error_rate_pct", 100)
    if cycle and target and cycle <= target * 1.1 and error <= 2:
        score = max(score, 5)
    return score


def analyze_process(proc: dict) -> dict:
    name = proc["name"]
    cycle = proc.get("avg_cycle_time_days")
    target = proc.get("target_cycle_time_days")
    error_rate = proc.get("error_rate_pct")
    automation = proc.get("automation_pct", 0)
    steps = proc.get("steps", [])

    # Efficiency ratio
    efficiency = None
    if cycle and target and cycle > 0:
        efficiency = target / cycle  # 1.0 = on target, <1 = behind

    # Bottleneck: longest manual step
    bottleneck = None
    if steps:
        manual_steps = [s for s in steps if s.get("manual", True)]
        if manual_steps:
            bottleneck = max(manual_steps, key=lambda s: s.get("time_days", 0))

    # Automation opportunity
    if steps:
        manual_time = sum(s.get("time_days", 0) for s in steps if s.get("manual", True))
        total_time = sum(s.get("time_days", 0) for s in steps)
        automation_opportunity = manual_time / total_time * 100 if total_time > 0 else 0
    else:
        automation_opportunity = 100 - automation

    maturity = score_maturity(proc)

    # Priority issues
    issues = []
    if efficiency and efficiency < 0.6:
        issues.append("严重超时（cycle time > 1.6× target）")
    elif efficiency and efficiency < 0.8:
        issues.append("轻微超时（cycle time > 1.2× target）")
    if error_rate and error_rate > 10:
        issues.append(f"错误率偏高（{error_rate}%）")
    if automation < 20:
        issues.append("自动化程度极低，人工成本高")

    return {
        "process": name,
        "owner": proc.get("owner", ""),
        "cycle_time_days": cycle,
        "target_days": target,
        "efficiency_ratio": round(efficiency, 2) if efficiency else None,
        "error_rate_pct": error_rate,
        "automation_pct": automation,
        "automation_opportunity_pct": round(automation_opportunity, 1),
        "maturity_level": maturity,
        "maturity_label": MATURITY_LEVELS[maturity],
        "bottleneck_step": bottleneck["name"] if bottleneck else None,
        "bottleneck_days": bottleneck.get("time_days") if bottleneck else None,
        "issues": issues,
    }


def print_report(results: list):
    print(f"\n{'═'*70}")
    print("  流程效率分析报告")
    print(f"{'═'*70}")

    for r in results:
        eff = r["efficiency_ratio"]
        if eff is None:
            eff_icon = "⚪"
        elif eff >= 0.9:
            eff_icon = "🟢"
        elif eff >= 0.7:
            eff_icon = "🟡"
        else:
            eff_icon = "🔴"

        print(f"\n  【{r['process']}】  负责人：{r['owner']}")
        print(f"  {'─'*50}")
        if r["cycle_time_days"] and r["target_days"]:
            print(f"  周期时间     {r['cycle_time_days']}天  （目标 {r['target_days']}天）  {eff_icon}")
        if r["error_rate_pct"] is not None:
            err_icon = "🟢" if r["error_rate_pct"] <= 2 else ("🟡" if r["error_rate_pct"] <= 10 else "🔴")
            print(f"  错误率       {r['error_rate_pct']}%  {err_icon}")
        print(f"  自动化程度   {r['automation_pct']}%  （可提升至 {r['automation_opportunity_pct']:.0f}%）")
        print(f"  成熟度       L{r['maturity_level']} — {r['maturity_label']}")
        if r["bottleneck_step"]:
            print(f"  瓶颈步骤     {r['bottleneck_step']}（{r['bottleneck_days']}天）")
        if r["issues"]:
            print(f"  ⚠️  问题：")
            for issue in r["issues"]:
                print(f"     • {issue}")

    # Summary
    critical = [r for r in results if r["efficiency_ratio"] and r["efficiency_ratio"] < 0.7]
    low_auto = [r for r in results if r["automation_pct"] < 20]
    if critical:
        print(f"\n  🔴 紧急处理：{', '.join(r['process'] for r in critical)}")
    if low_auto:
        print(f"  🟡 自动化优化机会：{', '.join(r['process'] for r in low_auto)}")


def interactive_mode():
    print("流程效率分析（交互模式）\n")
    processes = []
    while True:
        name = input("  流程名称（回车结束）: ").strip()
        if not name:
            break
        proc = {"name": name}
        owner = input("  负责人: ").strip()
        if owner:
            proc["owner"] = owner
        cycle = input("  平均周期（天）: ").strip()
        target = input("  目标周期（天）: ").strip()
        error = input("  错误率 % : ").strip()
        automation = input("  自动化程度 % : ").strip()
        if cycle:
            proc["avg_cycle_time_days"] = float(cycle)
        if target:
            proc["target_cycle_time_days"] = float(target)
        if error:
            proc["error_rate_pct"] = float(error)
        if automation:
            proc["automation_pct"] = float(automation)
        processes.append(proc)
        print()

    if not processes:
        print("没有输入流程数据。")
        return

    results = [analyze_process(p) for p in processes]
    print_report(results)


def main():
    parser = argparse.ArgumentParser(description="流程效率分析 + 成熟度评分")
    parser.add_argument("input", nargs="?", help="输入 JSON 文件路径")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    if args.interactive or not args.input:
        interactive_mode()
        return

    try:
        with open(args.input) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.input}", file=sys.stderr)
        sys.exit(1)

    results = [analyze_process(p) for p in data.get("processes", [])]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_report(results)


if __name__ == "__main__":
    main()

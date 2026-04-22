#!/usr/bin/env python3
"""
okr_tracker.py - OKR 级联追踪 + 进度评分 + 风险预警

用法：
  python okr_tracker.py data.json
  python okr_tracker.py data.json --json
  python okr_tracker.py data.json --week 8

INPUT SCHEMA:
{
  "quarter": "2024-Q2",
  "total_weeks": 13,
  "current_week": 6,
  "objectives": [
    {
      "id": "O1",
      "title": "成为行业领先的客户成功平台",
      "owner": "CEO",
      "key_results": [
        {
          "id": "KR1.1",
          "title": "NPS 从 42 提升到 60",
          "unit": "score",
          "baseline": 42,
          "target": 60,
          "current": 51,
          "owner": "CS团队"
        },
        {
          "id": "KR1.2",
          "title": "客户续约率达到 92%",
          "unit": "pct",
          "baseline": 85,
          "target": 92,
          "current": 88,
          "owner": "CS团队"
        }
      ]
    }
  ]
}
"""

import argparse
import json
import sys


def score_kr(kr: dict, current_week: int, total_weeks: int) -> dict:
    baseline = kr.get("baseline", 0)
    target = kr.get("target")
    current = kr.get("current")

    if target is None or current is None:
        return {**kr, "progress_pct": None, "expected_pct": None, "status": "⚪", "at_risk": False}

    total_delta = target - baseline
    if total_delta == 0:
        progress_pct = 100.0
    else:
        progress_pct = (current - baseline) / total_delta * 100

    # Expected progress based on time elapsed
    time_elapsed_pct = current_week / total_weeks * 100
    expected_pct = time_elapsed_pct  # linear expectation

    # Status
    gap = progress_pct - expected_pct
    if progress_pct >= 100:
        status = "🟢"
        at_risk = False
    elif gap >= -10:
        status = "🟢"
        at_risk = False
    elif gap >= -25:
        status = "🟡"
        at_risk = True
    else:
        status = "🔴"
        at_risk = True

    # Projected end value (linear extrapolation)
    if current_week > 0:
        rate_per_week = (current - baseline) / current_week
        projected = baseline + rate_per_week * total_weeks
        projected_pct = (projected - baseline) / total_delta * 100 if total_delta != 0 else 100
    else:
        projected = current
        projected_pct = progress_pct

    return {
        **kr,
        "progress_pct": round(progress_pct, 1),
        "expected_pct": round(expected_pct, 1),
        "gap_pct": round(gap, 1),
        "projected_end": round(projected, 2),
        "projected_pct": round(projected_pct, 1),
        "status": status,
        "at_risk": at_risk,
    }


def score_objective(obj: dict, current_week: int, total_weeks: int) -> dict:
    scored_krs = [score_kr(kr, current_week, total_weeks) for kr in obj.get("key_results", [])]

    valid = [kr for kr in scored_krs if kr["progress_pct"] is not None]
    avg_progress = sum(kr["progress_pct"] for kr in valid) / len(valid) if valid else None
    at_risk_count = sum(1 for kr in scored_krs if kr["at_risk"])

    if avg_progress is None:
        obj_status = "⚪"
    elif at_risk_count == 0:
        obj_status = "🟢"
    elif at_risk_count < len(scored_krs):
        obj_status = "🟡"
    else:
        obj_status = "🔴"

    return {
        "id": obj.get("id", obj.get("name", "")),
        "title": obj.get("title", obj.get("name", "")),
        "owner": obj.get("owner", ""),
        "avg_progress_pct": round(avg_progress, 1) if avg_progress is not None else None,
        "status": obj_status,
        "at_risk_krs": at_risk_count,
        "key_results": scored_krs,
    }


def print_report(objectives: list, quarter: str, current_week: int, total_weeks: int):
    print(f"\n{'═'*65}")
    print(f"  OKR 追踪报告 — {quarter}  第 {current_week}/{total_weeks} 周")
    print(f"{'═'*65}")

    at_risk_all = []

    for obj in objectives:
        print(f"\n  {obj['status']} [{obj['id']}] {obj['title']}")
        print(f"     负责人：{obj['owner']}  |  整体进度：{obj['avg_progress_pct']}%")
        print(f"     {'KR':<8} {'负责人':<12} {'当前':>8} {'目标':>8} {'进度':>7} {'预期':>7} {'差距':>7}")
        for kr in obj["key_results"]:
            kr_id = kr.get("id", kr.get("name", ""))
            kr_title = kr.get("title", kr.get("name", ""))
            prog = f"{kr['progress_pct']}%" if kr['progress_pct'] is not None else "N/A"
            exp = f"{kr['expected_pct']}%" if kr['expected_pct'] is not None else "N/A"
            gap = f"{kr['gap_pct']:+.1f}%" if kr.get('gap_pct') is not None else "N/A"
            curr_s = str(kr.get("current", "N/A"))
            tgt_s = str(kr.get("target", "N/A"))
            print(f"     {kr_id:<8} {kr.get('owner',''):<12} {curr_s:>8} {tgt_s:>8} "
                  f"{prog:>7} {exp:>7} {gap:>7}  {kr['status']}")
            if kr["at_risk"]:
                at_risk_all.append(f"{kr_id}: {kr_title}")

    if at_risk_all:
        print(f"\n  ── ⚠️  风险预警 ──")
        for item in at_risk_all:
            print(f"  • {item}")
    else:
        print(f"\n  ✅ 所有 KR 进度正常")


def main():
    parser = argparse.ArgumentParser(description="OKR 级联追踪 + 风险预警")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("--week", type=int, help="覆盖当前周数")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.input}", file=sys.stderr)
        sys.exit(1)

    quarter = data.get("quarter", "")
    total_weeks = data.get("total_weeks", 13)
    current_week = args.week or data.get("current_week", 1)

    objectives = [score_objective(obj, current_week, total_weeks)
                  for obj in data.get("objectives", [])]

    if args.json:
        print(json.dumps({
            "quarter": quarter,
            "current_week": current_week,
            "total_weeks": total_weeks,
            "objectives": objectives,
        }, ensure_ascii=False, indent=2))
    else:
        print_report(objectives, quarter, current_week, total_weeks)


if __name__ == "__main__":
    main()

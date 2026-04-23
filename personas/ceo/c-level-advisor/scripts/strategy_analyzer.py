#!/usr/bin/env python3
"""
strategy_analyzer.py - 战略选项加权评分 + 优先级矩阵

用法：
  python strategy_analyzer.py data.json
  python strategy_analyzer.py data.json --json
  python strategy_analyzer.py --interactive

INPUT SCHEMA:
{
  "context": "Series A SaaS，考虑是否进入企业市场",
  "criteria": [
    {"name": "市场规模", "weight": 0.25},
    {"name": "执行可行性", "weight": 0.20},
    {"name": "竞争壁垒", "weight": 0.20},
    {"name": "资源匹配度", "weight": 0.20},
    {"name": "战略契合度", "weight": 0.15}
  ],
  "options": [
    {
      "name": "深耕中小企业市场",
      "scores": {"市场规模": 6, "执行可行性": 9, "竞争壁垒": 7, "资源匹配度": 8, "战略契合度": 8},
      "pros": ["现有客户基础", "销售周期短"],
      "cons": ["ARPU低", "规模天花板"],
      "required_resources": "现有团队可执行"
    },
    {
      "name": "进入企业市场",
      "scores": {"市场规模": 9, "执行可行性": 5, "竞争壁垒": 8, "资源匹配度": 5, "战略契合度": 7},
      "pros": ["高ARPU", "强护城河"],
      "cons": ["需要企业销售团队", "18-24个月见效"],
      "required_resources": "需招聘企业销售 + 解决方案工程师"
    }
  ]
}
"""

import argparse
import json
import sys


def score_option(option: dict, criteria: list) -> dict:
    scores = option.get("scores", {})
    weighted_total = 0.0
    breakdown = []

    for c in criteria:
        name = c["name"]
        weight = c["weight"]
        raw = scores.get(name, 5)
        weighted = raw * weight
        weighted_total += weighted
        breakdown.append({
            "criterion": name,
            "weight": weight,
            "raw_score": raw,
            "weighted_score": round(weighted, 2),
        })

    return {
        "name": option["name"],
        "weighted_score": round(weighted_total, 2),
        "breakdown": breakdown,
        "pros": option.get("pros", []),
        "cons": option.get("cons", []),
        "required_resources": option.get("required_resources", ""),
    }


def rank_options(options: list, criteria: list) -> list:
    scored = [score_option(opt, criteria) for opt in options]
    scored.sort(key=lambda x: -x["weighted_score"])
    for i, opt in enumerate(scored):
        opt["rank"] = i + 1
    return scored


def print_report(ranked: list, context: str, criteria: list):
    print(f"\n{'═'*65}")
    print("  战略选项分析报告")
    if context:
        print(f"  背景：{context}")
    print(f"{'═'*65}")

    print(f"\n  ── 综合评分排名 ──")
    print(f"  {'排名':<5} {'选项':<25} {'加权得分':>10}")
    for opt in ranked:
        icon = "🥇" if opt["rank"] == 1 else ("🥈" if opt["rank"] == 2 else "🥉")
        print(f"  {icon}  {opt['name']:<25} {opt['weighted_score']:>10.2f}/10")

    for opt in ranked:
        print(f"\n  ── #{opt['rank']} {opt['name']} ──")
        print(f"  {'评估维度':<20} {'权重':>6} {'原始分':>8} {'加权分':>8}")
        for b in opt["breakdown"]:
            bar = "█" * int(b["raw_score"])
            print(f"  {b['criterion']:<20} {b['weight']:>5.0%} {b['raw_score']:>8.1f} {b['weighted_score']:>8.2f}  {bar}")
        if opt["pros"]:
            print(f"  ✅ 优势：{' | '.join(opt['pros'])}")
        if opt["cons"]:
            print(f"  ⚠️  风险：{' | '.join(opt['cons'])}")
        if opt["required_resources"]:
            print(f"  📦 资源需求：{opt['required_resources']}")

    # Recommendation
    winner = ranked[0]
    print(f"\n  ── 建议 ──")
    print(f"  推荐选项：{winner['name']}（得分 {winner['weighted_score']:.2f}）")
    if len(ranked) > 1:
        gap = winner["weighted_score"] - ranked[1]["weighted_score"]
        if gap < 0.5:
            print(f"  ⚠️  与第二选项差距仅 {gap:.2f}，建议进一步验证关键假设后决策")


def interactive_mode():
    print("战略选项分析（交互模式）\n")
    context = input("  决策背景（可选）: ").strip()

    print("\n  输入评估维度（回车结束）：")
    criteria = []
    while True:
        name = input(f"  维度 {len(criteria)+1} 名称: ").strip()
        if not name:
            break
        weight = input(f"  权重（0-1，如 0.25）: ").strip()
        try:
            criteria.append({"name": name, "weight": float(weight)})
        except ValueError:
            print("  权重格式错误，跳过")

    if not criteria:
        print("没有输入评估维度。")
        return

    # Normalize weights
    total_w = sum(c["weight"] for c in criteria)
    if total_w > 0:
        for c in criteria:
            c["weight"] /= total_w

    print("\n  输入战略选项（回车结束）：")
    options = []
    while True:
        name = input(f"\n  选项 {len(options)+1} 名称（回车结束）: ").strip()
        if not name:
            break
        scores = {}
        for c in criteria:
            s = input(f"    {c['name']} 得分（1-10）: ").strip()
            try:
                scores[c["name"]] = float(s)
            except ValueError:
                scores[c["name"]] = 5
        options.append({"name": name, "scores": scores})

    if not options:
        print("没有输入选项。")
        return

    ranked = rank_options(options, criteria)
    print_report(ranked, context, criteria)


def main():
    parser = argparse.ArgumentParser(description="战略选项加权评分")
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

    criteria = data.get("criteria", [])
    options = data.get("options", [])
    context = data.get("context", "")

    # Normalize weights to sum to 1
    total_w = sum(c.get("weight", 0) for c in criteria)
    if total_w > 0 and abs(total_w - 1.0) > 0.001:
        for c in criteria:
            c["weight"] = c.get("weight", 0) / total_w

    ranked = rank_options(options, criteria)

    if args.json:
        print(json.dumps({"context": context, "ranked_options": ranked},
                         ensure_ascii=False, indent=2))
    else:
        print_report(ranked, context, criteria)


if __name__ == "__main__":
    main()

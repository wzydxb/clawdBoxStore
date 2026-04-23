#!/usr/bin/env python3
"""
fundraising_model.py - 融资稀释 + 股权结构 + 多轮情景模型

用法：
  python fundraising_model.py data.json
  python fundraising_model.py data.json --json
  python fundraising_model.py data.json --rounds seed,series-a,series-b

INPUT SCHEMA:
{
  "company_name": "Acme Inc.",
  "founders": [
    {"name": "Alice", "shares": 5000000},
    {"name": "Bob",   "shares": 5000000}
  ],
  "option_pool_pct": 10,
  "rounds": [
    {
      "name": "Seed",
      "pre_money_valuation": 5000000,
      "raise_amount": 1000000,
      "lead_investor": "Angel Fund"
    },
    {
      "name": "Series A",
      "pre_money_valuation": 20000000,
      "raise_amount": 5000000,
      "lead_investor": "VC Fund A",
      "option_pool_increase_pct": 5
    }
  ]
}
"""

import argparse
import json
import sys


def build_cap_table(data: dict, round_filter: list = None) -> dict:
    founders = data.get("founders", [])
    option_pool_pct = data.get("option_pool_pct", 10)
    rounds = data.get("rounds", [])

    if round_filter:
        rounds = [r for r in rounds if r["name"].lower() in [x.lower() for x in round_filter]]

    # Initial shares
    total_founder_shares = sum(f["shares"] for f in founders)
    option_pool_shares = int(total_founder_shares * option_pool_pct / (100 - option_pool_pct))
    total_shares = total_founder_shares + option_pool_shares

    shareholders = {f["name"]: f["shares"] for f in founders}
    shareholders["Option Pool"] = option_pool_shares

    history = [{
        "event": "Founding",
        "pre_money": None,
        "raise": None,
        "new_shares": None,
        "post_money": None,
        "total_shares": total_shares,
        "table": {k: {"shares": v, "pct": round(v / total_shares * 100, 2)}
                  for k, v in shareholders.items()},
    }]

    for rnd in rounds:
        name = rnd["name"]
        pre_money = rnd["pre_money_valuation"]
        raise_amt = rnd["raise_amount"]
        post_money = pre_money + raise_amt
        investor = rnd.get("lead_investor", name + " Investors")

        # Option pool increase (pre-money, dilutes existing)
        pool_increase_pct = rnd.get("option_pool_increase_pct", 0)
        if pool_increase_pct:
            new_pool = int(total_shares * pool_increase_pct / 100)
            shareholders["Option Pool"] = shareholders.get("Option Pool", 0) + new_pool
            total_shares += new_pool

        # Price per share based on pre-money
        if total_shares <= 0:
            continue
        price_per_share = pre_money / total_shares
        new_shares = int(raise_amt / price_per_share)
        total_shares += new_shares
        shareholders[investor] = shareholders.get(investor, 0) + new_shares

        table = {k: {"shares": v, "pct": round(v / total_shares * 100, 2)}
                 for k, v in shareholders.items()}

        history.append({
            "event": name,
            "pre_money": pre_money,
            "raise": raise_amt,
            "post_money": post_money,
            "price_per_share": round(price_per_share, 4),
            "new_shares": new_shares,
            "total_shares": total_shares,
            "table": table,
        })

    return {
        "company": data.get("company_name", ""),
        "rounds": history,
        "final_total_shares": total_shares,
        "final_table": history[-1]["table"],
    }


def exit_scenario(cap_table: dict, exit_valuation: float) -> list:
    """Calculate proceeds per shareholder at a given exit valuation."""
    final = cap_table["final_table"]
    total_shares = cap_table["final_total_shares"]
    price = exit_valuation / total_shares

    results = []
    for name, info in final.items():
        proceeds = info["shares"] * price
        results.append({
            "shareholder": name,
            "shares": info["shares"],
            "pct": info["pct"],
            "proceeds": round(proceeds, 0),
        })
    results.sort(key=lambda x: -x["proceeds"])
    return results


def print_cap_table(cap_table: dict):
    print(f"\n{'═'*65}")
    print(f"  股权结构报告 — {cap_table['company']}")
    print(f"{'═'*65}")

    for rnd in cap_table["rounds"]:
        print(f"\n  ── {rnd['event']} ──")
        if rnd.get("pre_money"):
            pre_m = rnd["pre_money"] / 1e6
            post_m = rnd["post_money"] / 1e6
            raise_m = rnd["raise"] / 1e6
            pps = rnd["price_per_share"]
            print(f"  估值前：${pre_m:.1f}M  融资：${raise_m:.1f}M  估值后：${post_m:.1f}M  每股价格：${pps:.4f}")
        print(f"  {'股东':<20} {'股数':>12} {'占比':>8}")
        for name, info in rnd["table"].items():
            print(f"  {name:<20} {info['shares']:>12,} {info['pct']:>7.2f}%")


def print_exit_table(exit_results: list, exit_val: float):
    print(f"\n  ── 退出情景（估值 ${exit_val/1e6:.1f}M）──")
    print(f"  {'股东':<20} {'占比':>8} {'退出收益':>14}")
    for r in exit_results:
        print(f"  {r['shareholder']:<20} {r['pct']:>7.2f}% {r['proceeds']:>14,.0f}")


def main():
    parser = argparse.ArgumentParser(description="融资稀释 + 股权结构模型")
    parser.add_argument("input", help="输入 JSON 文件路径")
    parser.add_argument("--rounds", help="只模拟指定轮次，逗号分隔（如 Seed,Series A）")
    parser.add_argument("--exit", type=float, help="退出估值（用于计算各方收益）")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {args.input}", file=sys.stderr)
        sys.exit(1)

    round_filter = [r.strip() for r in args.rounds.split(",")] if args.rounds else None
    cap_table = build_cap_table(data, round_filter)

    exit_results = None
    if args.exit:
        exit_results = exit_scenario(cap_table, args.exit)

    if args.json:
        out = {"cap_table": cap_table}
        if exit_results:
            out["exit_scenario"] = {"valuation": args.exit, "proceeds": exit_results}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print_cap_table(cap_table)
        if exit_results:
            print_exit_table(exit_results, args.exit)


if __name__ == "__main__":
    main()

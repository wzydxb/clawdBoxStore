#!/usr/bin/env python3
"""
quick_ratio_calculator.py - SaaS Quick Ratio（增长效率）

Quick Ratio = (新增MRR + 扩张MRR) / (流失MRR + 收缩MRR)
> 4 优秀 | 2-4 健康 | 1-2 观察 | <1 危险

用法：
  python quick_ratio_calculator.py --new-mrr 10000 --expansion 2000 --churned 3000 --contraction 500
  python quick_ratio_calculator.py --new-mrr 10000 --expansion 2000 --churned 3000 --json
"""

import argparse
import json


def calc_quick_ratio(new_mrr, expansion_mrr, churned_mrr, contraction_mrr=0):
    gained = new_mrr + expansion_mrr
    lost = churned_mrr + contraction_mrr
    qr = gained / lost if lost > 0 else float("inf")
    return {
        "new_mrr": new_mrr,
        "expansion_mrr": expansion_mrr,
        "churned_mrr": churned_mrr,
        "contraction_mrr": contraction_mrr,
        "total_gained": gained,
        "total_lost": lost,
        "quick_ratio": round(qr, 2),
        "net_new_mrr": gained - lost,
    }


def status(qr):
    if qr == float("inf") or qr >= 4:
        return "🟢 优秀（增长效率极高）"
    elif qr >= 2:
        return "🟢 健康"
    elif qr >= 1:
        return "🟡 观察（增长在放缓）"
    else:
        return "🔴 危险（流失速度超过获取）"


def print_report(r):
    print(f"\n{'═'*45}")
    print("  SaaS Quick Ratio 报告")
    print(f"{'═'*45}")
    print(f"  新增 MRR          {r['new_mrr']:>12,.0f}")
    print(f"  扩张 MRR          {r['expansion_mrr']:>12,.0f}")
    print(f"  ─ 合计获得        {r['total_gained']:>12,.0f}")
    print(f"  流失 MRR          {r['churned_mrr']:>12,.0f}")
    print(f"  收缩 MRR          {r['contraction_mrr']:>12,.0f}")
    print(f"  ─ 合计损失        {r['total_lost']:>12,.0f}")
    print(f"\n  净新增 MRR        {r['net_new_mrr']:>12,.0f}")
    qr = r['quick_ratio']
    qr_str = f"{qr:.2f}" if qr != float("inf") else "∞"
    print(f"  Quick Ratio       {qr_str:>12}")
    print(f"\n  状态：{status(qr)}")


def main():
    parser = argparse.ArgumentParser(description="SaaS Quick Ratio 计算器")
    parser.add_argument("--new-mrr", type=float, required=True, help="新增 MRR")
    parser.add_argument("--expansion", type=float, default=0, help="扩张 MRR")
    parser.add_argument("--churned", type=float, required=True, help="流失 MRR")
    parser.add_argument("--contraction", type=float, default=0, help="收缩 MRR")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = calc_quick_ratio(args.new_mrr, args.expansion, args.churned, args.contraction)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_report(result)


if __name__ == "__main__":
    main()

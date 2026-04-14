#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自媒体爆款标题公式框架生成器

职责说明：
  本脚本负责"结构"，不负责"语义"。
  输出的是带填充提示的公式框架，由大模型完成最终的语义填充，生成贴合主题的标题。

  脚本做的事：
    - 根据平台选取匹配的标题公式
    - 将用户关键词和主题注入公式的语义提示位
    - 输出结构化 JSON，供大模型二次处理

  大模型收到输出后需要做的事：
    - 按照每条公式的 hint 字段提示，结合 topic 和 keywords 填写 [占位符]
    - 生成语义连贯、贴合主题的最终标题
    - 向用户展示最终标题，不要展示原始 JSON

调用方式（三种，任选其一，推荐方式1）：

  方式1 - 独立参数（推荐，跨平台无引号转义问题）：
    python generate_titles.py --topic 做饭教程 --keywords 家常菜,快手菜,零失败 --platform douyin --count 5

  方式2 - stdin 传入 JSON（适合程序间调用）：
    echo {"topic":"做饭教程","keywords":["家常菜","快手菜"],"platform":"douyin","count":5} | python generate_titles.py

  方式3 - JSON 字符串（CMD 环境可用，PowerShell 慎用）：
    python generate_titles.py "{\"topic\":\"做饭教程\",\"platform\":\"douyin\"}"

  注意：切换目录与执行脚本之间请使用 ; 而非 &&（PowerShell 5.x 不支持 &&）

参数说明：
    topic    : 内容主题描述（自然语言）
    keywords : 主题关键词，方式1用逗号分隔（支持中英文逗号、空格），方式2/3用JSON数组
    platform : 目标平台，可选 xiaohongshu / wechat / douyin / zhihu / bilibili / all
    count    : 每个平台输出公式数量，默认 5
"""

import sys
import io
import re
import json
import random
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# ------------------------------------------------------------------
# 跨平台编码保护：Windows CMD 默认 GBK，强制 stdout 使用 UTF-8
# ------------------------------------------------------------------
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except AttributeError:
    pass  # 某些环境（如 IDLE）stdout 无 buffer，静默跳过

# ------------------------------------------------------------------
# 路径基准：始终以脚本所在位置推算 skill 根目录，跨平台兼容
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------
# 公式库
# 每条公式包含：
#   pattern : 标题结构，[占位符] 是需要模型根据语义填写的部分
#   hint    : 对每个 [占位符] 的填写说明，指导模型如何结合 topic/keywords 填写
#   formula : 公式类型名称（便于模型理解当前公式的修辞逻辑）
# ------------------------------------------------------------------
FORMULAS: Dict[str, List[Dict]] = {
    "xiaohongshu": [
        {
            "formula": "数字+结果",
            "pattern": "[数字]个[与主题相关的方法/技巧]，[时间]内[与主题相关的具体成果]✨",
            "hint": "[数字]用3/5/7，[方法/技巧]结合keywords，[时间]用7天/30天，[成果]要具体可感",
        },
        {
            "formula": "情绪+反差",
            "pattern": "后悔没早[动作]！这个[与主题相关的事物]让我[与主题相关的收益]💖",
            "hint": "[动作]用学/试/做，[事物]结合keywords核心词，[收益]要有情绪感染力",
        },
        {
            "formula": "人群+成就",
            "pattern": "[具体人群]必看！[数字]个[与主题相关的干货]，太香了🔥",
            "hint": "[人群]结合topic受众（如宝妈/上班族/学生党），[干货]结合keywords",
        },
        {
            "formula": "对比+逆袭",
            "pattern": "从[与主题相关的困境状态]到[与主题相关的理想状态]，我只做了这[数字]件事",
            "hint": "[困境]和[理想状态]要紧扣topic，形成强烈对比，数字用3/5",
        },
        {
            "formula": "故事+数字",
            "pattern": "[城市/身份][时间经历]，我[与主题相关的具体成就]💪",
            "hint": "[城市/身份]增加真实感，[时间]用X年，[成就]要量化且贴合topic",
        },
    ],
    "wechat": [
        {
            "formula": "悬念+揭秘",
            "pattern": "为什么[与主题相关的普遍现象]？原来[与主题相关的真相/原因]",
            "hint": "[现象]是读者有共鸣的痛点，[真相]要出乎意料但合理，紧扣topic",
        },
        {
            "formula": "对比+方法",
            "pattern": "从[困境A]到[理想B]，我只做对了这[数字]件事",
            "hint": "[困境A]和[理想B]要围绕topic的核心价值主张，数字用3/5",
        },
        {
            "formula": "权威+利益",
            "pattern": "[权威来源]：[与主题相关的做法]，[与主题相关的具体收益]",
            "hint": "[权威]用研究/专家/数据，[做法]和[收益]紧扣topic和keywords",
        },
        {
            "formula": "痛点+警告",
            "pattern": "为什么你总是[与主题相关的痛点]？这[数字]个[原因/习惯]正在[负面影响]",
            "hint": "[痛点]戳中目标读者，[原因]结合topic，[影响]制造紧迫感",
        },
        {
            "formula": "利益+方法",
            "pattern": "[数字]个[与主题相关的方法]，帮你[与主题相关的具体目标]",
            "hint": "[方法]结合keywords，[目标]要具体量化，避免模糊表达",
        },
    ],
    "douyin": [
        {
            "formula": "疑问+信息差",
            "pattern": "你知道吗？[高比例]%的人都不知道[与主题相关的具体技巧/知识点]",
            "hint": "[比例]用90/95，[技巧]要真实具体且与topic直接相关，不要泛化",
        },
        {
            "formula": "反差+对比",
            "pattern": "没想到！[与主题相关的低成本/简单方案]比[与主题相关的高成本/复杂方案]还[具体效果]",
            "hint": "[低成本方案]和[高成本方案]都要紧扣topic，[效果]要具体",
        },
        {
            "formula": "指令+利益",
            "pattern": "一定要看！这个视频可能帮你[与主题相关的具体收益]",
            "hint": "[收益]要与topic强相关，具体可感，不要写泛泛的'改变人生'",
        },
        {
            "formula": "数字+结果",
            "pattern": "[数字]个[与主题相关的方法/技巧]，让你[与主题相关的具体改变]",
            "hint": "[方法]结合keywords，[改变]要量化或有画面感，贴合topic受众",
        },
        {
            "formula": "警告+后果",
            "pattern": "千万别[与主题相关的错误做法]，否则[与主题相关的具体损失/后果]",
            "hint": "[错误做法]是topic领域的常见误区，[后果]真实可信，不夸张",
        },
    ],
    "zhihu": [
        {
            "formula": "问题+路径",
            "pattern": "[目标人群]如何[与主题相关的目标]？有哪些可行的路径？",
            "hint": "[人群]结合topic受众，[目标]要具体，不要过于宽泛",
        },
        {
            "formula": "体验+共鸣",
            "pattern": "[与主题相关的具体经历/处境]是一种怎样的体验？",
            "hint": "[经历]要真实、有代入感，与topic核心场景紧密相关",
        },
        {
            "formula": "现象+思考",
            "pattern": "为什么越来越多的[人群][与主题相关的现象/选择]？",
            "hint": "[人群]贴合topic受众，[现象]是当下真实趋势，引发深度思考",
        },
        {
            "formula": "推荐+专业",
            "pattern": "有哪些[形容词]的[与主题相关的内容/工具/方法]推荐？",
            "hint": "[形容词]用相见恨晚/实用/高效，[内容]紧扣topic和keywords",
        },
    ],
    "bilibili": [
        {
            "formula": "挑战+悬念",
            "pattern": "【第[期数]期】挑战[与主题相关的具体挑战任务]，结果...",
            "hint": "[任务]要具体有趣且与topic相关，悬念结尾引导完播",
        },
        {
            "formula": "教程+成就",
            "pattern": "史上最强[与主题相关的核心技能]教程！看完你就是大神",
            "hint": "[技能]要与topic直接相关，夸张风格符合B站调性",
        },
        {
            "formula": "全程高能+成果",
            "pattern": "【全程高能】我花了[时间]，[与主题相关的具体成就]",
            "hint": "[时间]用7天/30天，[成就]具体量化，与topic强相关",
        },
        {
            "formula": "系列+攻略",
            "pattern": "从入门到精通：[与主题相关的领域]完整学习攻略",
            "hint": "[领域]直接使用topic核心词或keywords中最具代表性的词",
        },
    ],
}

# 各平台字数建议，输出给模型参考
PLATFORM_CHAR_LIMITS: Dict[str, str] = {
    "xiaohongshu": "20字以内（超出会被截断）",
    "wechat":      "24-30字最佳",
    "douyin":      "15-20字最佳（前3秒原则）",
    "zhihu":       "25-40字",
    "bilibili":    "20-30字",
}


def get_formulas(
    topic: str,
    keywords: List[str],
    platform: str,
    count: int,
) -> Dict:
    """
    输出结构化公式框架，供大模型进行语义填充。

    Args:
        topic    : 内容主题描述
        keywords : 主题关键词列表
        platform : 目标平台
        count    : 每个平台输出公式数量

    Returns:
        结构化 JSON，包含公式列表和模型处理指引
    """
    platforms = list(FORMULAS.keys()) if platform == "all" else [platform]

    platform_results: Dict[str, Dict] = {}
    for plat in platforms:
        if plat not in FORMULAS:
            continue
        pool = FORMULAS[plat]
        selected = random.sample(pool, min(count, len(pool)))
        # 若 count 超过公式数量，允许重复抽取补足
        while len(selected) < count:
            selected.append(random.choice(pool))

        platform_results[plat] = {
            "char_limit": PLATFORM_CHAR_LIMITS.get(plat, ""),
            "formulas": [
                {
                    "formula": f["formula"],
                    "pattern": f["pattern"],
                    "hint":    f["hint"],
                }
                for f in selected
            ],
        }

    return {
        "topic":    topic or "（未指定）",
        "keywords": keywords,
        "platform": platform,
        "platforms": platform_results,
        "instruction": (
            "请按以下步骤处理每条公式，生成最终标题：\n"
            "1. 阅读 pattern 中的 [占位符] 和对应的 hint 说明\n"
            "2. 结合 topic 和 keywords 的语义，将 [占位符] 替换为贴合主题的具体词句\n"
            "3. 控制字数在 char_limit 范围内\n"
            "4. 最终向用户展示标题列表，按平台分组，不要展示原始 JSON 和 hint"
        ),
    }


def _split_keywords(raw: str) -> List[str]:
    """
    切分关键词字符串，兼容英文逗号、中文逗号、空格及混合写法。
    示例：
        "健身,减脂,运动"   → ["健身", "减脂", "运动"]
        "健身，减脂，运动"  → ["健身", "减脂", "运动"]
        "健身 减脂 运动"   → ["健身", "减脂", "运动"]
    """
    parts = re.split(r"[，,\s]+", raw)
    return [p.strip() for p in parts if p.strip()]


def parse_args() -> Dict:
    """
    解析参数，按优先级依次尝试：
      1. --topic / --keywords 等独立参数（推荐，无引号转义问题）
      2. stdin 输入的 JSON（管道调用）
      3. sys.argv[1] 的 JSON 字符串（兜底）
    """
    defaults = {"topic": "", "keywords": [], "platform": "all", "count": 5}

    # --- 方式1：独立参数（--topic --keywords --platform --count）---
    if len(sys.argv) > 1 and sys.argv[1].startswith("--"):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--topic",    default="")
        parser.add_argument("--keywords", default="")
        parser.add_argument("--platform", default="all")
        parser.add_argument("--count",    type=int, default=5)
        args, _ = parser.parse_known_args()
        keywords = _split_keywords(args.keywords) if args.keywords else []
        return {
            "topic":    args.topic,
            "keywords": keywords,
            "platform": args.platform,
            "count":    args.count,
        }

    # --- 方式2：stdin JSON ---
    if len(sys.argv) == 1 and not sys.stdin.isatty():
        try:
            raw = sys.stdin.read().strip()
            params = json.loads(raw)
            return {**defaults, **params}
        except (json.JSONDecodeError, ValueError):
            return defaults

    # --- 方式3：sys.argv[1] JSON 字符串 ---
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
            return {**defaults, **params}
        except (json.JSONDecodeError, ValueError):
            return {**defaults, "topic": sys.argv[1]}

    return defaults


def main() -> None:
    params   = parse_args()
    topic    = params.get("topic", "")
    keywords = params.get("keywords", [])
    platform = params.get("platform", "all")
    count    = int(params.get("count", 5))

    result = get_formulas(topic, keywords, platform, count)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

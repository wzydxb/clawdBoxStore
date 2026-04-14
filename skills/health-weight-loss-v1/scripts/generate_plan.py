#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康减重方案生成器
根据用户身体数据和偏好生成个性化运动与饮食方案
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class HealthMetricsCalculator:
    """健康指标计算器"""

    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> float:
        """计算BMI"""
        height_m = height_cm / 100
        return round(weight_kg / (height_m ** 2), 1)

    @staticmethod
    def get_bmi_category(bmi: float) -> str:
        """获取BMI分类"""
        if bmi < 18.5:
            return "偏瘦"
        elif bmi < 24:
            return "正常"
        elif bmi < 28:
            return "超重"
        else:
            return "肥胖"

    @staticmethod
    def calculate_bmr(gender: str, weight_kg: float, height_cm: float, age: int) -> int:
        """计算基础代谢率 (Mifflin-St Jeor公式)"""
        if gender == "男":
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
        return int(bmr)

    @staticmethod
    def calculate_tdee(bmr: int, activity_level: str) -> int:
        """计算每日总能量消耗"""
        multipliers = {
            "久坐": 1.2,
            "轻度活动": 1.375,
            "中度活动": 1.55,
            "高强度活动": 1.725,
            "极高强度": 1.9
        }
        return int(bmr * multipliers.get(activity_level, 1.375))

    @staticmethod
    def calculate_target_calories(tdee: int, goal: str = "lose") -> int:
        """计算目标摄入热量"""
        if goal == "lose":
            return max(1200, tdee - 500)  # 减脂：制造500kcal缺口，不低于1200
        elif goal == "maintain":
            return tdee
        else:  # gain
            return tdee + 300

    @staticmethod
    def calculate_ideal_weight(height_cm: float, gender: str) -> tuple:
        """计算理想体重范围 (BMI 18.5-24)"""
        height_m = height_cm / 100
        min_weight = round(18.5 * (height_m ** 2), 1)
        max_weight = round(24 * (height_m ** 2), 1)
        return (min_weight, max_weight)

    @staticmethod
    def calculate_max_heart_rate(age: int) -> int:
        """计算最大心率"""
        return 220 - age


class WorkoutPlanGenerator:
    """运动计划生成器"""

    # 运动库
    EXERCISE_LIBRARY = {
        "无器械": {
            "有氧": [
                {"name": "开合跳", "difficulty": 1, "calories_per_min": 8},
                {"name": "高抬腿", "difficulty": 2, "calories_per_min": 10},
                {"name": "原地跑", "difficulty": 1, "calories_per_min": 8},
                {"name": "波比跳", "difficulty": 3, "calories_per_min": 15},
                {"name": "登山跑", "difficulty": 2, "calories_per_min": 12},
            ],
            "力量": [
                {"name": "俯卧撑", "difficulty": 2, "target": "上肢/胸部"},
                {"name": "深蹲", "difficulty": 1, "target": "下肢"},
                {"name": "弓步蹲", "difficulty": 2, "target": "下肢"},
                {"name": "平板支撑", "difficulty": 2, "target": "核心"},
                {"name": "仰卧起坐", "difficulty": 1, "target": "腹部"},
                {"name": "臀桥", "difficulty": 1, "target": "臀部"},
                {"name": "波比跳", "difficulty": 3, "target": "全身"},
            ],
            "拉伸": [
                {"name": "颈部拉伸", "difficulty": 1},
                {"name": "肩部拉伸", "difficulty": 1},
                {"name": "腿部拉伸", "difficulty": 1},
                {"name": "猫牛式", "difficulty": 1},
                {"name": "婴儿式", "difficulty": 1},
            ]
        },
        "哑铃": {
            "力量": [
                {"name": "哑铃深蹲", "difficulty": 2, "target": "下肢"},
                {"name": "哑铃划船", "difficulty": 2, "target": "背部"},
                {"name": "哑铃推举", "difficulty": 2, "target": "肩部"},
                {"name": "哑铃弯举", "difficulty": 1, "target": "手臂"},
                {"name": "哑铃硬拉", "difficulty": 2, "target": "下肢/背部"},
                {"name": "哑铃卧推", "difficulty": 2, "target": "胸部"},
            ]
        },
        "健身房": {
            "有氧": [
                {"name": "跑步机", "difficulty": 1, "calories_per_min": 10},
                {"name": "椭圆机", "difficulty": 1, "calories_per_min": 8},
                {"name": "动感单车", "difficulty": 2, "calories_per_min": 12},
                {"name": "划船机", "difficulty": 2, "calories_per_min": 11},
            ],
            "力量": [
                {"name": "杠铃深蹲", "difficulty": 3, "target": "下肢"},
                {"name": "杠铃硬拉", "difficulty": 3, "target": "全身"},
                {"name": "卧推", "difficulty": 2, "target": "胸部"},
                {"name": "引体向上", "difficulty": 3, "target": "背部"},
                {"name": "腿举", "difficulty": 2, "target": "下肢"},
                {"name": "器械划船", "difficulty": 1, "target": "背部"},
            ]
        }
    }

    def __init__(self, fitness_level: str, equipment: str, workout_days: int,
                 workout_minutes: int, target_parts: Optional[List[str]] = None):
        self.fitness_level = fitness_level
        self.equipment = equipment
        self.workout_days = workout_days
        self.workout_minutes = workout_minutes
        self.target_parts = target_parts or ["全身"]

        # 根据健身水平调整难度
        self.difficulty_map = {
            "零基础": 1,
            "偶尔运动": 2,
            "经常运动": 3
        }
        self.base_difficulty = self.difficulty_map.get(fitness_level, 1)

    def generate_4week_plan(self) -> Dict:
        """生成4周训练计划"""
        plan = {
            "第1周_适应期": self._generate_week_plan(1),
            "第2周_提升期": self._generate_week_plan(2),
            "第3周_强化期": self._generate_week_plan(3),
            "第4周_巩固期": self._generate_week_plan(4),
        }
        return plan

    def _generate_week_plan(self, week: int) -> List[Dict]:
        """生成单周计划"""
        sessions = []

        # 根据周次调整强度
        intensity_multiplier = 0.7 + (week * 0.1)  # 0.8, 0.9, 1.0, 1.1

        for day in range(1, self.workout_days + 1):
            session = self._generate_session(day, week, intensity_multiplier)
            sessions.append(session)

        return sessions

    def _generate_session(self, day: int, week: int, intensity: float) -> Dict:
        """生成单次训练"""
        # 根据天数分配训练类型
        if self.workout_days <= 3:
            # 全身训练
            session_type = "全身训练"
        elif day % 2 == 1:
            session_type = "上肢+核心"
        else:
            session_type = "下肢+有氧"

        # 构建训练内容
        warm_up = self._get_warm_up()
        main_exercises = self._get_main_exercises(session_type, week)
        cool_down = self._get_cool_down()

        return {
            "day": day,
            "type": session_type,
            "duration": self.workout_minutes,
            "warm_up": warm_up,
            "main_exercises": main_exercises,
            "cool_down": cool_down
        }

    def _get_warm_up(self) -> List[Dict]:
        """获取热身动作"""
        return [
            {"name": "关节活动", "duration": "2分钟", "description": "颈部、肩部、髋部、膝关节活动"},
            {"name": "原地踏步", "duration": "2分钟", "description": "逐渐加快节奏"},
            {"name": "动态拉伸", "duration": "3分钟", "description": "手臂画圈、腿部摆动"},
        ]

    def _get_main_exercises(self, session_type: str, week: int) -> List[Dict]:
        """获取主训练动作"""
        exercises = []

        # 根据器械选择动作库
        available_equipment = ["无器械"]
        if self.equipment in ["哑铃", "健身房"]:
            available_equipment.append("哑铃")
        if self.equipment == "健身房":
            available_equipment.append("健身房")

        # 根据训练类型选择动作
        if "全身" in session_type or "上肢" in session_type:
            # 添加上肢/胸部动作
            exercises.extend([
                {"name": "俯卧撑", "sets": 2 + week, "reps": "8-12次", "rest": "60秒"},
                {"name": "平板支撑", "sets": 3, "reps": "30-45秒", "rest": "45秒"},
            ])

        if "全身" in session_type or "下肢" in session_type:
            # 添加下肢动作
            exercises.extend([
                {"name": "深蹲", "sets": 3, "reps": "12-15次", "rest": "60秒"},
                {"name": "弓步蹲", "sets": 2, "reps": "每侧10次", "rest": "45秒"},
            ])

        if "有氧" in session_type or week >= 2:
            # 添加有氧
            cardio_time = max(10, self.workout_minutes // 3)
            exercises.append({
                "name": "有氧训练",
                "sets": 1,
                "reps": f"{cardio_time}分钟",
                "description": "开合跳、高抬腿或原地跑",
                "rest": "无"
            })

        return exercises

    def _get_cool_down(self) -> List[Dict]:
        """获取放松动作"""
        return [
            {"name": "慢走", "duration": "2分钟", "description": "逐渐降低心率"},
            {"name": "全身拉伸", "duration": "5分钟", "description": "重点拉伸训练部位"},
            {"name": "深呼吸", "duration": "1分钟", "description": "放松身心"},
        ]


class MealPlanGenerator:
    """饮食计划生成器"""

    # 食物数据库
    FOOD_DATABASE = {
        "蛋白质": [
            {"name": "鸡胸肉", "calories_per_100g": 165, "protein_per_100g": 31},
            {"name": "鸡蛋", "calories_per_100g": 155, "protein_per_100g": 13},
            {"name": "三文鱼", "calories_per_100g": 208, "protein_per_100g": 20},
            {"name": "豆腐", "calories_per_100g": 76, "protein_per_100g": 8},
            {"name": "瘦牛肉", "calories_per_100g": 250, "protein_per_100g": 26},
            {"name": "虾", "calories_per_100g": 99, "protein_per_100g": 24},
        ],
        "碳水": [
            {"name": "糙米", "calories_per_100g": 111, "carbs_per_100g": 23},
            {"name": "燕麦", "calories_per_100g": 389, "carbs_per_100g": 66},
            {"name": "红薯", "calories_per_100g": 86, "carbs_per_100g": 20},
            {"name": "全麦面包", "calories_per_100g": 247, "carbs_per_100g": 41},
            {"name": "藜麦", "calories_per_100g": 120, "carbs_per_100g": 21},
        ],
        "蔬菜": [
            {"name": "西兰花", "calories_per_100g": 34, "fiber_per_100g": 2.6},
            {"name": "菠菜", "calories_per_100g": 23, "fiber_per_100g": 2.2},
            {"name": "黄瓜", "calories_per_100g": 15, "fiber_per_100g": 0.5},
            {"name": "番茄", "calories_per_100g": 18, "fiber_per_100g": 1.2},
            {"name": "胡萝卜", "calories_per_100g": 41, "fiber_per_100g": 2.8},
        ],
        "水果": [
            {"name": "苹果", "calories_per_100g": 52, "fiber_per_100g": 2.4},
            {"name": "香蕉", "calories_per_100g": 89, "fiber_per_100g": 2.6},
            {"name": "蓝莓", "calories_per_100g": 57, "fiber_per_100g": 2.4},
            {"name": "橙子", "calories_per_100g": 47, "fiber_per_100g": 2.4},
        ],
        "健康脂肪": [
            {"name": "牛油果", "calories_per_100g": 160, "fat_per_100g": 15},
            {"name": "坚果混合", "calories_per_100g": 607, "fat_per_100g": 54},
            {"name": "橄榄油", "calories_per_100g": 884, "fat_per_100g": 100},
        ]
    }

    def __init__(self, target_calories: int, dietary_restrictions: Optional[List[str]] = None):
        self.target_calories = target_calories
        self.dietary_restrictions = dietary_restrictions or []

        # 营养素分配 (蛋白质30%, 碳水40%, 脂肪30%)
        self.protein_ratio = 0.30
        self.carb_ratio = 0.40
        self.fat_ratio = 0.30

    def generate_daily_plan(self) -> Dict:
        """生成每日饮食计划"""
        # 三餐热量分配
        breakfast_cal = int(self.target_calories * 0.30)
        lunch_cal = int(self.target_calories * 0.40)
        dinner_cal = int(self.target_calories * 0.25)
        snack_cal = int(self.target_calories * 0.05)

        return {
            "早餐": self._generate_meal("早餐", breakfast_cal),
            "午餐": self._generate_meal("午餐", lunch_cal),
            "晚餐": self._generate_meal("晚餐", dinner_cal),
            "加餐": self._generate_meal("加餐", snack_cal),
            "每日总计": {
                "热量": self.target_calories,
                "蛋白质": f"{int(self.target_calories * self.protein_ratio / 4)}g",
                "碳水": f"{int(self.target_calories * self.carb_ratio / 4)}g",
                "脂肪": f"{int(self.target_calories * self.fat_ratio / 9)}g"
            }
        }

    def _generate_meal(self, meal_type: str, calories: int) -> Dict:
        """生成单餐计划"""
        if meal_type == "早餐":
            return {
                "热量": f"{calories} kcal",
                "建议": [
                    "蛋白质：鸡蛋2个 或 牛奶250ml",
                    "碳水：全麦面包2片 或 燕麦50g",
                    "蔬果：番茄/黄瓜/苹果1个"
                ],
                "示例": "燕麦牛奶粥(燕麦50g+牛奶250ml) + 水煮蛋1个 + 苹果1个"
            }
        elif meal_type == "午餐":
            return {
                "热量": f"{calories} kcal",
                "建议": [
                    "蛋白质：鸡胸肉/鱼/瘦牛肉 150g",
                    "碳水：糙米/红薯 150g",
                    "蔬菜：绿叶蔬菜 200g",
                    "油脂：橄榄油 1茶匙"
                ],
                "示例": "香煎鸡胸肉150g + 糙米饭1碗 + 蒜蓉西兰花"
            }
        elif meal_type == "晚餐":
            return {
                "热量": f"{calories} kcal",
                "建议": [
                    "蛋白质：豆腐/鱼虾 100g",
                    "碳水：少量杂粮 100g",
                    "蔬菜：蔬菜汤/凉拌菜 200g"
                ],
                "示例": "清蒸鱼100g + 蔬菜豆腐汤 + 少量杂粮饭"
            }
        else:  # 加餐
            return {
                "热量": f"{calories} kcal",
                "建议": [
                    "下午：坚果10g 或 水果1个",
                    "运动前（如需要）：香蕉半根"
                ],
                "示例": "无糖酸奶1杯 或 核桃2-3个"
            }

    def generate_shopping_list(self) -> List[str]:
        """生成购物清单"""
        return [
            "蛋白质类：鸡胸肉、鸡蛋、三文鱼、豆腐、瘦牛肉",
            "碳水类：糙米、燕麦、红薯、全麦面包",
            "蔬菜类：西兰花、菠菜、黄瓜、番茄、胡萝卜",
            "水果类：苹果、香蕉、蓝莓",
            "其他：坚果、橄榄油、无糖酸奶"
        ]


class WeightLossPlanGenerator:
    """减重方案主生成器"""

    def __init__(self, user_data: Dict):
        self.user_data = user_data
        self.calculator = HealthMetricsCalculator()
        self.metrics = self._calculate_all_metrics()

    def _calculate_all_metrics(self) -> Dict:
        """计算所有健康指标"""
        w = self.user_data

        bmi = self.calculator.calculate_bmi(w["current_weight_kg"], w["height_cm"])
        bmr = self.calculator.calculate_bmr(
            w["gender"], w["current_weight_kg"], w["height_cm"], w["age"]
        )

        # 根据运动基础确定活动系数
        activity_map = {
            "零基础": "轻度活动",
            "偶尔运动": "中度活动",
            "经常运动": "高强度活动"
        }
        activity_level = activity_map.get(w["fitness_level"], "中度活动")

        tdee = self.calculator.calculate_tdee(bmr, activity_level)
        target_calories = self.calculator.calculate_target_calories(tdee, "lose")
        ideal_weight = self.calculator.calculate_ideal_weight(w["height_cm"], w["gender"])
        max_hr = self.calculator.calculate_max_heart_rate(w["age"])

        weight_to_lose = w["current_weight_kg"] - w["target_weight_kg"]
        weeks_needed = int(weight_to_lose / 0.75)  # 按每周0.75kg计算

        return {
            "bmi": bmi,
            "bmi_category": self.calculator.get_bmi_category(bmi),
            "bmr": bmr,
            "tdee": tdee,
            "target_calories": target_calories,
            "ideal_weight_range": ideal_weight,
            "max_heart_rate": max_hr,
            "weight_to_lose": weight_to_lose,
            "estimated_weeks": weeks_needed
        }

    def generate_full_plan(self) -> str:
        """生成完整方案文档"""
        # 生成运动计划
        workout_gen = WorkoutPlanGenerator(
            fitness_level=self.user_data["fitness_level"],
            equipment=self.user_data.get("equipment", "无器械"),
            workout_days=self.user_data.get("weekly_workout_days", 3),
            workout_minutes=self.user_data.get("daily_workout_minutes", 30),
            target_parts=self.user_data.get("target_body_parts", ["全身"])
        )
        workout_plan = workout_gen.generate_4week_plan()

        # 生成饮食计划
        meal_gen = MealPlanGenerator(
            target_calories=self.metrics["target_calories"],
            dietary_restrictions=self.user_data.get("dietary_restrictions", [])
        )
        meal_plan = meal_gen.generate_daily_plan()
        shopping_list = meal_gen.generate_shopping_list()

        # 生成Markdown文档
        return self._format_plan_as_markdown(workout_plan, meal_plan, shopping_list)

    def _format_plan_as_markdown(self, workout_plan: Dict, meal_plan: Dict,
                                  shopping_list: List[str]) -> str:
        """格式化为Markdown文档"""
        w = self.user_data
        m = self.metrics

        md = f"""# 🎯 个性化健康减重方案

**生成日期**: {datetime.now().strftime('%Y年%m月%d日')}
**方案周期**: 4周（建议连续执行3-4个周期）

---

## 📋 个人档案

| 项目 | 内容 |
|------|------|
| 性别 | {w['gender']} |
| 年龄 | {w['age']}岁 |
| 身高 | {w['height_cm']}cm |
| 当前体重 | {w['current_weight_kg']}kg |
| 目标体重 | {w['target_weight_kg']}kg |
| 运动基础 | {w['fitness_level']} |
| 可用器械 | {w.get('equipment', '无器械')} |
| 每周运动 | {w.get('weekly_workout_days', 3)}天 |
| 每次时长 | {w.get('daily_workout_minutes', 30)}分钟 |

---

## 📊 身体数据分析

| 指标 | 数值 | 说明 |
|------|------|------|
| **BMI** | {m['bmi']} | {m['bmi_category']} |
| **理想体重范围** | {m['ideal_weight_range'][0]}-{m['ideal_weight_range'][1]} kg | 基于BMI 18.5-24 |
| **需减重量** | {m['weight_to_lose']} kg | 从当前到目标 |
| **基础代谢率(BMR)** | {m['bmr']} kcal/天 | 静息消耗 |
| **每日总消耗(TDEE)** | {m['tdee']} kcal/天 | 含活动消耗 |
| **建议每日摄入** | {m['target_calories']} kcal/天 | 制造热量缺口 |
| **最大心率** | {m['max_heart_rate']} bpm | 220-年龄 |
| **预计达成时间** | 约{m['estimated_weeks']}周 | 按每周减0.5-1kg |

---

## 🏃 4周运动计划

**训练原则**：
- 每周{w.get('weekly_workout_days', 3)}次训练，每次{w.get('daily_workout_minutes', 30)}分钟
- 循序渐进，第1周适应，第4周强化
- 有氧+力量结合，保留肌肉同时减脂
- 心率控制在最大心率的60-75%（{int(m['max_heart_rate']*0.6)}-{int(m['max_heart_rate']*0.75)} bpm）

"""

        # 添加每周计划
        for week_name, sessions in workout_plan.items():
            md += f"\n### {week_name.replace('_', ' ')}\n\n"
            for session in sessions:
                md += f"**第{session['day']}次训练** - {session['type']} ({session['duration']}分钟)\n\n"

                md += "**热身** (7分钟)\n"
                for item in session['warm_up']:
                    md += f"- {item['name']}: {item['duration']} - {item['description']}\n"

                md += "\n**主训练**\n"
                for ex in session['main_exercises']:
                    if 'description' in ex:
                        md += f"- {ex['name']}: {ex['reps']} - {ex['description']}\n"
                    else:
                        md += f"- {ex['name']}: {ex['sets']}组 x {ex['reps']}, 休息{ex['rest']}\n"

                md += "\n**放松** (8分钟)\n"
                for item in session['cool_down']:
                    md += f"- {item['name']}: {item['duration']} - {item['description']}\n"
                md += "\n---\n\n"

        # 添加饮食计划
        md += """\n## 🥗 饮食指导方案

### 营养原则
- **蛋白质**: 占总热量30%，维持肌肉量
- **碳水**: 占总热量40%，优选复合碳水
- **脂肪**: 占总热量30%，优选不饱和脂肪
- **膳食纤维**: 每日25-30g

### 每日食谱框架

"""

        for meal_type, details in meal_plan.items():
            if meal_type == "每日总计":
                md += f"\n### {meal_type}\n\n"
                md += f"| 营养素 | 摄入量 |\n|--------|--------|\n"
                md += f"| 热量 | {details['热量']} kcal |\n"
                md += f"| 蛋白质 | {details['蛋白质']} |\n"
                md += f"| 碳水 | {details['碳水']} |\n"
                md += f"| 脂肪 | {details['脂肪']} |\n"
            else:
                md += f"\n### {meal_type} ({details['热量']})\n\n"
                md += "**建议搭配**:\n"
                for suggestion in details['建议']:
                    md += f"- {suggestion}\n"
                md += f"\n**示例**: {details['示例']}\n"

        # 添加购物清单
        md += "\n## 🛒 推荐购物清单\n\n"
        for item in shopping_list:
            md += f"- {item}\n"

        # 添加执行建议
        md += """
---

## ✅ 执行检查清单

### 每日必做
- [ ] 完成当日运动计划
- [ ] 记录饮食（前2周建议详细记录）
- [ ] 饮水2000ml以上
- [ ] 睡眠7-8小时

### 每周必做
- [ ] 称重1次（固定时间，如周一早晨空腹）
- [ ] 回顾本周完成情况
- [ ] 准备下周食材

### 每两周必做
- [ ] 测量腰围
- [ ] 拍照对比
- [ ] 评估方案是否需要调整

---

## ⚠️ 重要提醒

### 安全原则
1. **循序渐进**：不要突然增加运动量或大幅减少热量
2. **倾听身体**：疼痛时停止，区分正常肌肉酸痛和受伤
3. **充足睡眠**：睡眠不足会影响代谢和恢复
4. **保持水分**：运动时额外补充水分

### 以下情况请咨询医生
- 有心血管疾病、糖尿病等慢性病
- BMI ≥ 28
- 关节或骨骼问题
- 长期未运动且年龄>40岁
- 孕期/哺乳期

### 危险信号（立即停止运动）
- 胸痛或胸闷
- 头晕或昏厥感
- 呼吸困难（非正常运动喘息）
- 心悸或心律不齐

---

## 📈 进度追踪表

| 周次 | 日期 | 体重(kg) | 腰围(cm) | 完成情况 | 备注 |
|------|------|----------|----------|----------|------|
| 初始 | - | {w['current_weight_kg']} | - | - | 开始记录 |
| 第1周 | | | | | |
| 第2周 | | | | | |
| 第3周 | | | | | |
| 第4周 | | | | | |

---

## 📝 免责声明

本方案基于一般性健康原则生成，仅供参考。每个人的身体状况不同，效果因人而异。开始任何运动或饮食计划前，建议咨询医生或专业营养师。如有任何不适，请立即停止并寻求专业医疗建议。

**祝你减重成功，健康生活！** 💪
"""

        return md


def main():
    """主函数 - CLI入口"""
    parser = argparse.ArgumentParser(description='生成个性化健康减重方案')
    parser.add_argument('--gender', required=True, choices=['男', '女'], help='性别')
    parser.add_argument('--age', type=int, required=True, help='年龄')
    parser.add_argument('--height', type=float, required=True, help='身高(cm)')
    parser.add_argument('--current-weight', type=float, required=True, help='当前体重(kg)')
    parser.add_argument('--target-weight', type=float, required=True, help='目标体重(kg)')
    parser.add_argument('--fitness-level', default='零基础',
                       choices=['零基础', '偶尔运动', '经常运动'], help='运动基础')
    parser.add_argument('--workout-days', type=int, default=3, help='每周运动天数')
    parser.add_argument('--workout-minutes', type=int, default=30, help='每次运动分钟数')
    parser.add_argument('--equipment', default='无器械', help='可用器械')
    parser.add_argument('--output', required=True, help='输出文件路径')

    args = parser.parse_args()

    # 构建用户数据
    user_data = {
        "gender": args.gender,
        "age": args.age,
        "height_cm": args.height,
        "current_weight_kg": args.current_weight,
        "target_weight_kg": args.target_weight,
        "fitness_level": args.fitness_level,
        "weekly_workout_days": args.workout_days,
        "daily_workout_minutes": args.workout_minutes,
        "equipment": args.equipment
    }

    # 生成方案
    generator = WeightLossPlanGenerator(user_data)
    plan_content = generator.generate_full_plan()

    # 保存文件
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(plan_content)

    print(f"[OK] 方案已生成: {output_path}")

    # 输出关键指标摘要
    m = generator.metrics
    print(f"\n[数据] 关键指标:")
    print(f"  BMI: {m['bmi']} ({m['bmi_category']})")
    print(f"  建议每日摄入: {m['target_calories']} kcal")
    print(f"  预计达成时间: 约{m['estimated_weeks']}周")


if __name__ == "__main__":
    main()

# health-weight-loss-v1

## 简介

个性化科学减重方案生成器。根据用户的身体状况、时间安排、运动基础和减重目标，量身定制运动计划与饮食指导。

## 主要功能

- 根据身高、体重、年龄、性别计算基础代谢率（BMR）和目标热量缺口
- 生成个性化每周运动计划，匹配用户运动基础和可用时间
- 提供饮食结构建议，包括三餐热量分配和食物选择
- 阶段性目标拆解，支持 4 周、8 周、12 周等不同周期
- 参考运动库（exercise_library）和营养指南（nutrition_guide）生成科学依据说明

## 使用方式

通过 OpenClaw 对话界面直接描述需求，例如：

```
我现在体重 80kg，身高 175cm，每周能运动 3 次，目标 3 个月减 10kg，帮我制定计划。
```

也可以直接调用脚本：

```bash
python scripts/generate_plan.py \
  --weight 80 --height 175 --age 30 --gender male \
  --weekly-sessions 3 --goal-kg 10 --weeks 12
```

## 依赖 / 前置条件

- Python 3.8+
- 无需外部 API Key
- 参考资料位于 `references/` 目录：
  - `exercise_library/`：运动动作库
  - `nutrition_guide/`：营养指南
  - `scientific_basis/`：科学依据文献

## 注意事项

- 本工具提供的方案仅供参考，不构成医疗建议
- 有基础疾病（心脏病、糖尿病等）的用户，执行计划前请咨询医生
- 减重速度建议控制在每周 0.5~1kg，过快减重有健康风险

---
name: ppt-studio
description: 模板优先的一体化 PPT 生成技能。用于根据主题、调研结果或资料自动完成三步流程：内容与结构规划、视觉与组件资产生成、PPTX 组装导出。适合做汇报、方案、市场分析、演讲 Deck、商业演示。
---

# PPT Studio

## 默认执行方式

`ppt-studio` 是新的 PPT 主入口。默认按 3 步执行：
1. **内容与结构规划**
2. **视觉与组件资产生成**
3. **PPTX 组装导出**

默认策略：
- 模板优先
- 没有模板时走 scratch
- 再失败时才允许 `ppt-nano-master` 兜底
- 最多只问一次，且问题要短

## Step 1：内容与结构规划

运行：

```bash
python {baseDir}/scripts/step1_plan.py \
  --theme "{主题}" \
  --research-file "{调研文件}" \
  --output-dir "{workspace}/ppt_studio/{任务名}"
```

输出：
- `deck_plan.json`
- `slide_outline.json`

## Step 2：视觉与组件资产生成

运行：

```bash
python {baseDir}/scripts/step2_generate_assets.py \
  --plan "{workspace}/ppt_studio/{任务名}/deck_plan.json" \
  --output-dir "{workspace}/ppt_studio/{任务名}"
```

输出：
- `style_resolution.json`
- `slide_specs.json`
- `slide_assets_manifest.json`
- 可选 `assets/*.png`

## Step 3：PPTX 组装导出

运行：

```bash
PPT_STUDIO_PYTHON=/root/.openclaw/venvs/ppt/bin/python python {baseDir}/scripts/step3_render_pptx.py \
  --plan "{workspace}/ppt_studio/{任务名}/deck_plan.json" \
  --specs "{workspace}/ppt_studio/{任务名}/slide_specs.json" \
  --assets "{workspace}/ppt_studio/{任务名}/slide_assets_manifest.json" \
  --output "{workspace}/ppt_studio/{任务名}/presentation.pptx"
```

输出：
- `presentation.pptx`
- `render_report.json`

## 一键总入口

```bash
PPT_STUDIO_PYTHON=/root/.openclaw/venvs/ppt/bin/python python {baseDir}/scripts/run_pipeline.py \
  --theme "{主题}" \
  --research-file "{调研文件}" \
  --output-dir "{workspace}/ppt_studio/{任务名}"
```

## 复用说明

- 内容与质量规则：看 `references/INTAKE.md`、`WORKFLOW.md`、`TEMPLATES.md`、`RUBRIC.md`
- 模板模式：看 `references/template-workflow.md`
- 组件与视觉：看 `references/VIS-GUIDE.md`、`STYLE-GUIDE.md`
- 本 skill 第一版以模板优先为主，会根据主题从 `assets/templates/templates.json` 自动选择模板；`ppt-nano-master` 暂时只作兜底，不再作为主入口。

---
name: footage-first-render
description: >-
  Render clip-heavy topics with real footage first, original audio first, and cards only as fallback.
---

# 素材优先渲染

当 strategist 需要为重素材选题准备或校验渲染行为时，使用这个 skill。

## 规则
- 重素材选题必须默认优先使用真实源素材。
- 只要存在真实片段，就尽量保留原始音频。
- Cards 只作为兜底方案。
- 如果某个重素材选题的 package 缺少真实 clip assets，则将 `ready_for_synthesis: false`。
- 不允许使用 script-only render payload。

## 规范输出路径
- `outputs/analysis/production_package.json`
- `outputs/analysis/execution.json`
- `outputs/render/video.mp4`
- `outputs/render/render_report.json`

## 推荐渲染请求
- `production_package.path=/home/node/.clawbox/workspace-content-strategist-1/outputs/analysis/production_package.json`
- `output_dir=/home/node/.clawbox/workspace-content-strategist-1/outputs/render`

## 脚本
- `scripts/video-synth-bridge.mjs`

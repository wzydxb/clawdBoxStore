---
name: footage-first-render
description: >-
  Render clip-heavy topics with real footage first, original audio first, and cards only as fallback.
---

# Footage-First Render

Use this skill when the strategist is preparing or validating render behavior for clip-heavy topics.

## Rules
- Clip-heavy topics must default to real source footage first.
- Preserve original audio whenever real clips are present.
- Cards are fallback only.
- If the package lacks real clip assets for a clip-heavy topic, set `ready_for_synthesis: false`.
- Do not allow script-only render payloads.

## Canonical Output Paths
- `outputs/analysis/production_package.json`
- `outputs/analysis/execution.json`
- `outputs/render/video.mp4`
- `outputs/render/render_report.json`

## Preferred Render Request
- `production_package.path=/home/node/.clawbox/workspace-content-strategist-1/outputs/analysis/production_package.json`
- `output_dir=/home/node/.clawbox/workspace-content-strategist-1/outputs/render`

## Scripts
- `scripts/video-synth-bridge.mjs`

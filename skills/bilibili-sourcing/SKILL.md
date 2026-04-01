---
name: bilibili-sourcing
description: >-
  Collect candidate Bilibili videos, comments, and source clips for topic analysis and asset planning.
---

# Bilibili Sourcing

Use this skill when the strategist needs to source Bilibili candidate videos, collect comments, and identify source clips.

## Rules
- Prefer real Bilibili videos and real comments when available.
- For clip-heavy topics, produce canonical `asset_requirements[]` items with:
  - `type: "clip"`
  - `source: "BV..."`
  - `start_time`
  - `end_time`
  - `desc`
- If comments are unavailable, record a structured degraded reason instead of pretending evidence exists.

## Scripts
- `scripts/opencli-host-bridge.mjs`

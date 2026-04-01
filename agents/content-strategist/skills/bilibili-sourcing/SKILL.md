---
name: bilibili-sourcing
description: >-
  Collect candidate Bilibili videos, comments, and source clips for topic analysis and asset planning.
---

# Bilibili 选材

当 strategist 需要收集 Bilibili 候选视频、评论和源片段时，使用这个 skill。

## 规则
- 在可用时，优先使用真实的 Bilibili 视频和真实评论。
- 对于重素材选题，产出规范的 `asset_requirements[]` 条目，包含：
  - `type: "clip"`
  - `source: "BV..."`
  - `start_time`
  - `end_time`
  - `desc`
- 如果拿不到评论，记录结构化的 degraded reason，不要假装已经有证据。

## 脚本
- `scripts/opencli-host-bridge.mjs`

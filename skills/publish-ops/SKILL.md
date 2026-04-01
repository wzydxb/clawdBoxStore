---
name: publish-ops
description: >-
  Define the publish, monitor, reply, and ledger rules for the strategist-owned closure path.
---

# Publish Ops

Use this skill when the strategist is responsible for the phase-2 closure path.

## Rules
- If render succeeds and publish metadata is present, continue into publish.
- Persist `aid` / `bvid` as the canonical identity.
- Initialize monitor/reply through `bilibili_publisher`.
- Record status in the workspace ledger.
- Do not treat dynamic posts as the main closure path.

## Scripts
- `scripts/bilibili-publisher-bridge.mjs`
- `scripts/bilibili_api_ops.py`

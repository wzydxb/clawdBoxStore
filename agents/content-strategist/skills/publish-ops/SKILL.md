---
name: publish-ops
description: >-
  Define the publish, monitor, reply, and ledger rules for the strategist-owned closure path.
---

# 发布操作

当 strategist 负责 phase-2 closure path 时，使用这个 skill。

## 规则
- 如果 render 成功且存在 publish metadata，则继续进入 publish。
- 将 `aid` / `bvid` 作为规范身份标识持久化。
- 通过 `bilibili_publisher` 初始化 monitor / reply。
- 在 workspace ledger 中记录状态。
- 不要将动态帖子视为主要 closure path。

## 脚本
- `scripts/bilibili-publisher-bridge.mjs`
- `scripts/bilibili_api_ops.py`

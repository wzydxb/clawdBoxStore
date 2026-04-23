---
name: system-setup
description: 系统环境前置初始化。执行 env-init.sh 一键检测并补齐所有运行依赖：Python、opencli、搜索适配器、网盘。在任何 agent 功能使用前完成，与 agent 业务逻辑完全分离。触发词：环境初始化、环境没好、第一次用、setup、python没有、网盘没挂、opencli装了吗
version: 2.1.0
---

# 系统环境初始化

## 执行

```bash
bash ~/.hermes/scripts/env-init.sh
```

脚本自动完成：
1. Python 3.8+ 检查 / 安装，persona 脚本语法验证
2. opencli 检查 / 安装
3. 搜索适配器部署（baidu / bing / so / sogou / sohu）
4. Samba 服务检查，workspace 软链修复

## 如果某项失败

| 失败项 | 详细指引 |
|--------|---------|
| Python 安装失败 | `skill_view("system-setup/python-env")` |
| opencli 安装失败（无 npm/bun） | `skill_view("system-setup/opencli")` |
| 网盘未部署（首次） | `skill_view("system-setup/network-drive")` |

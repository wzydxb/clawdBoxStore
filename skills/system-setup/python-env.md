---
name: python-env
description: Python 运行时环境检查与初始化。确认 python3 版本、pip 可用性，以及 hermes-opc 所有 persona 脚本所需的标准库完整性。
version: 1.1.0
---

# Python 环境初始化

## 诊断

```bash
echo "=== Python 版本 ===" && python3 --version 2>/dev/null || echo "MISSING"
echo "=== pip ===" && python3 -m pip --version 2>/dev/null || echo "PIP_MISSING"
echo "=== 标准库 ===" && python3 -c "import json,argparse,sys,statistics,math,datetime; print('STD_OK')" 2>/dev/null || echo "STD_BROKEN"
```

| 状态 | 行动 |
|------|------|
| `MISSING` | → [安装 Python](#install) |
| 版本 < 3.8 | → [升级 Python](#install) |
| `PIP_MISSING` | → [安装 pip](#pip) |
| `STD_BROKEN` | → 重装 Python（标准库损坏） |
| 全部 OK | ✅ Python 就绪 |

---

## 安装 Python {#install}

**macOS**
```bash
brew install python3
# 验证
python3 --version   # 期望 3.8+
```

**Debian / Ubuntu（盒子端）**
```bash
apt-get update
apt-get install -y python3 python3-pip
```

---

## 安装 pip {#pip}

```bash
python3 -m ensurepip --upgrade
# 或
curl -sS https://bootstrap.pypa.io/get-pip.py | python3
```

---

## hermes-opc 脚本依赖说明

所有 `personas/*/scripts/*.py` **只使用 Python 标准库，无需 pip install 任何包**。

| 模块 | 用途 | 使用脚本 |
|------|------|---------|
| `json` | 数据输入输出 | 全部 |
| `argparse` | CLI 参数解析 | 全部 |
| `sys` | 退出码 | 全部 |
| `statistics` | 均值、标准差 | forecast_builder, unit_economics |
| `math` | 数学运算 | dcf_valuation, ratio_calculator |
| `datetime` | 日期处理 | okr_tracker, hiring_plan |

Python **3.8+** 即可运行全部脚本。

### 快速验证所有脚本可运行

```bash
# 在 hermes-opc 根目录执行
find personas -name "*.py" | while read f; do
  python3 -m py_compile "$f" && echo "OK: $f" || echo "FAIL: $f"
done
```

期望全部输出 `OK`，无 `FAIL`。

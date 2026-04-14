# stock-price-checker

## 简介

使用 yfinance 库获取股票实时价格和基础行情数据，无需注册账号或配置 API Key，开箱即用。

## 主要功能

- 查询股票当前价格（支持美股、港股等 yfinance 覆盖的市场）
- 获取基础行情：开盘价、收盘价、最高价、最低价、成交量
- 支持批量查询多只股票

## 使用方式

通过 OpenClaw 对话触发，示例：

```
查一下苹果公司（AAPL）现在的股价
查询特斯拉、英伟达、微软的最新价格
```

核心脚本：
- `stock-price.py`：Python 主逻辑，调用 yfinance 获取数据
- `stock-price.sh`：Shell 包装脚本，便于命令行直接调用

股票代码格式：
- 美股：`AAPL`、`TSLA`、`NVDA`
- 港股：`0700.HK`
- A 股：`600519.SS`（上交所）、`000001.SZ`（深交所）

## 依赖 / 前置条件

- Python 3.8+
- `yfinance` 库（`pip install yfinance`）
- 无需 API Key

## 注意事项

- 数据来源为 Yahoo Finance，A 股数据可能存在延迟或不完整
- 网络需能访问 Yahoo Finance（国内网络可能需要代理）
- 仅供参考，不构成投资建议

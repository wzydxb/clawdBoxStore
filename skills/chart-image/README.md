# 图表图像生成

## 简介

通过 Node.js 脚本生成 PNG 格式图表图像，支持多种常见图表类型，适合在不依赖前端环境的场景下生成可直接使用的图表文件。

## 主要功能

支持以下图表类型：
- 线图（Line Chart）
- 柱状图（Bar Chart）
- 面积图（Area Chart）
- 点图/散点图（Scatter Chart）
- 烛形图（Candlestick Chart）
- 饼图 / 甜甜圈图（Pie / Donut Chart）
- 热力图（Heatmap）

## 使用方式

核心脚本：`scripts/chart.mjs`（Node.js ESM 模块）

基本调用方式：

```bash
node scripts/chart.mjs --type line --data '[{"x":1,"y":2},{"x":2,"y":4}]' --output chart.png
```

也可以通过对话描述你的数据和图表需求，助手会自动调用脚本生成图像并返回文件路径。

示例提示：
- "用这份销售数据生成一张柱状图"
- "把以下月度数据画成面积图，输出 PNG"

## 依赖/前置条件

- Node.js >= 18
- 安装依赖：`npm install`（在 skill 目录下执行）
- 无需 API Key

## 注意事项

- 输出格式固定为 PNG，不支持 SVG 或 PDF
- 数据量过大时生成速度会变慢，建议单次不超过 1000 个数据点
- 烛形图需要提供 open/high/low/close 四个字段

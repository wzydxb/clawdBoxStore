---
name: clawdbox-image-gen
description: 使用龙虾智盒内置 AI 绘画能力，支持千问图像生成模型，无需额外 API Key。
homepage: https://api.clawdbox.cn
metadata:
  {
    "openclaw":
      {
        "emoji": "🎨",
        "requires": { "bins": ["python3"] },
        "install":
          [
            {
              "id": "python-brew",
              "kind": "brew",
              "formula": "python",
              "bins": ["python3"],
              "label": "Install Python (brew)",
            },
          ],
      },
  }
---

# 龙虾智盒 AI 绘画

使用龙虾智盒内置的 AI 图片生成能力，基于千问图像模型，无需额外配置 API Key。

## 可用模型

| 模型名 | 说明 |
|--------|------|
| `Qwen-Image-2.0` | 千问图像生成（加速版，速度快） |
| `Qwen-Image-2.0-Prod` | 千问图像生成（专业版，质量更高） |

## Run

```bash
python3 {baseDir}/scripts/gen.py --prompt "画一只可爱的橘猫"
```

### 常用参数

```bash
# 基本用法
python3 {baseDir}/scripts/gen.py --prompt "赛博朋克风格的城市夜景"

# 指定模型和数量
python3 {baseDir}/scripts/gen.py --prompt "水彩风格的山水画" --model Qwen-Image-2.0-Prod --count 4

# 指定尺寸（宽*高）
python3 {baseDir}/scripts/gen.py --prompt "一只宇航员龙虾" --size 1024x1536

# 横版图片
python3 {baseDir}/scripts/gen.py --prompt "日落下的海滩" --size 1536x1024

# 关闭水印
python3 {baseDir}/scripts/gen.py --prompt "产品展示图" --no-watermark

# 关闭提示词自动扩展
python3 {baseDir}/scripts/gen.py --prompt "极简线条画" --no-extend

# 自定义输出目录
python3 {baseDir}/scripts/gen.py --prompt "可爱的猫咪" --out-dir ./my-images
```

### 图片编辑

```bash
# 基于图片 URL 编辑
python3 {baseDir}/scripts/gen.py --edit --image "https://example.com/photo.png" --prompt "把背景换成星空"

# 基于本地图片编辑
python3 {baseDir}/scripts/gen.py --edit --image ./input.png --prompt "添加一顶帽子"
```

## 尺寸支持

| 尺寸 | 用途 |
|------|------|
| `1024x1024` | 正方形（默认） |
| `1024x1536` | 竖版（手机壁纸） |
| `1536x1024` | 横版（桌面壁纸） |
| `768x768` | 小尺寸快速预览 |

## Output

- `*.png` 图片文件
- `prompts.json`（提示词 → 文件映射）
- `index.html`（缩略图画廊）

## 认证说明

脚本自动从 `~/.hermes/config.yaml` 读取 API 认证凭据，无需手动配置。该 token 在设备绑定时由龙虾助手自动下发。

也可以通过环境变量覆盖：
```bash
export CLAWDBOX_API_KEY="your-token"
export CLAWDBOX_API_URL="https://api.clawdbox.cn"
```

## 注意事项

- 图片下载地址有效期 24 小时，请及时保存
- 使用龙虾智盒积分，无需额外 API Key
- 生成耗时约 5-15 秒，请耐心等待

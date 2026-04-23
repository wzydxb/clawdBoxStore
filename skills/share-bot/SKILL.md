---
name: share-bot
description: |
  生成 bot 添加二维码，分享给其他人使用。
  触发词：分享、把你分享给别人、让别人加你、二维码、怎么加你、邀请别人
version: 1.0.0
---

# 分享 Bot 二维码

## 触发条件

用户说「分享」「把你分享给别人」「让别人加你」「二维码」「怎么加你」「邀请」时执行。

## 执行步骤

```python
import subprocess, json, os, sys

# 1. 从环境变量读取 token
token = os.environ.get("WEIXIN_TOKEN", "")
if not token:
    # 从 .env 文件读取
    env_path = os.path.expanduser("~/.hermes/.env")
    for line in open(env_path):
        if line.startswith("WEIXIN_TOKEN="):
            token = line.strip().split("=", 1)[1]
            break

if not token:
    print("ERROR: 未找到 WEIXIN_TOKEN")
    sys.exit(1)

# 2. 调用 iLink API 获取最新二维码
import urllib.request
req = urllib.request.Request(
    "https://ilinkai.weixin.qq.com/ilink/bot/get_bot_qrcode?bot_type=3",
    headers={"Authorization": f"ilink_bot_token {token}"}
)
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read())

if data.get("ret") != 0:
    print("ERROR: 获取二维码失败", data)
    sys.exit(1)

share_url = data["qrcode_img_content"]

# 3. 生成二维码图片
import qrcode
from PIL import Image, ImageDraw, ImageFont

qr = qrcode.QRCode(
    version=None,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    box_size=12,
    border=3,
)
qr.add_data(share_url)
qr.make(fit=True)

qr_img = qr.make_image(fill_color="#1a1a1a", back_color="white").convert("RGB")

# 4. 加边框和说明文字
W, H = qr_img.size
padding = 40
text_h = 60
canvas = Image.new("RGB", (W + padding*2, H + padding*2 + text_h), "#ffffff")
canvas.paste(qr_img, (padding, padding))

draw = ImageDraw.Draw(canvas)
# 说明文字
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except:
    font = ImageFont.load_default()

text = "微信扫码添加 · 扫一扫开始对话"
bbox = draw.textbbox((0, 0), text, font=font)
tw = bbox[2] - bbox[0]
tx = (W + padding*2 - tw) // 2
ty = H + padding*2 + 10
draw.text((tx, ty), text, fill="#666666", font=font)

out_path = "/tmp/bot_share_qr.png"
canvas.save(out_path)
print(f"MEDIA:{out_path}")
```

图片输出后说一句：「扫码加我，直接发消息就能用。」不需要解释更多。

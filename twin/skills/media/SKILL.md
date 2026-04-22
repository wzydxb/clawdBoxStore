---
name: media
description: |
  图片和视频生成/编辑/理解能力。通过 clawdbox-media-tools 插件直接调用，无需 MCP。
  触发词：画图、生成图片、做视频、分析图片、改图、图生视频
version: 1.0.0
---

# 多媒体能力

通过 `clawdbox-media-tools` 插件的 4 个工具实现图片/视频能力。

## 可用工具

| 工具 | 用途 | 参数 |
|------|------|------|
| `generate_image(prompt, [model])` | 文生图 | prompt 用英文效果更好 |
| `edit_image(image, instruction, [model])` | 编辑图片 | image 支持本地路径/URL/base64 |
| `understand_image(image, question, [model])` | 图片内容理解 | 返回文字分析 |
| `generate_video(prompt, [seconds], [size], [image], [last_frame], [model])` | 文生视频 | seconds 是字符串 "4"/"6"/"8" |

## 触发场景

| 用户说 | 执行 |
|--------|------|
| 画图/生成图片/帮我画 | `generate_image(prompt=...)` |
| 改图/编辑图片/把这张图... | `edit_image(image=..., instruction=...)` |
| 分析图片/这张图是什么/看看这图 | `understand_image(image=..., question=...)` |
| 做视频/生成视频/图生视频 | `generate_video(prompt=..., [image=...])` |

## 重要规则

- **不要**把图片 base64 输出到对话——直接把用户消息里的图片路径/URL/base64 传给工具参数
- 图片/视频落盘在 `~/.hermes/media/{images,videos}/`，重启不丢
- 生成完成后通过 MEDIA:/路径 发送给用户（微信环境：先 curl 下载到本地再发）
- `last_frame` 和 `reference_images` 不要同时传（语义冲突）

## 典型工作流

### 文生图
```
generate_image(prompt="a white cat wearing a chef hat")
→ {"file_path": "/root/.hermes/media/images/xxx.png"}
→ 发送 MEDIA:/root/.hermes/media/images/xxx.png
```

### 图片编辑
```
用户传来图片后：
edit_image(image=<用户图路径或URL>, instruction="把背景改成蓝天白云")
→ 返回新图路径 → 发送
```

### 图生视频
```
generate_image(prompt="...")      → 得到图片路径
generate_video(prompt="...", image=图片路径, seconds="4")
→ {"file_path": "...mp4"} → 发送
```

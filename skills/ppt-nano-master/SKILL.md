---
name: ppt-nano-master
description: 生成多风格 PPT（白板/光辉/医疗/年度总结/开学第一课/林地/湿壁画/画架/立体/黑胶风），用户说「ppt-nano-master」「生成 PPT」「做 PPT」等关键词时
---

# PPT-Nano 技能

## 1. 默认模式

默认进入草稿直出模式：
- 最多只问一次，而且问题要短
- 不等回复也先做一版
- 先做首页主视觉，再做正文页
- 对外回复只保留极简说明

只有用户明确要求逐步确认时，才切换到严格确认流程。

## 2. 核心生成原则

1. **首页优先**
   - 先根据主题和调研后的核心主题集合生成首页主视觉提示词
   - 先生成首页主视觉图，并把它作为首页背景图
   - 没有首页主视觉图，不进入正文页生成

2. **风格统一**
   - 后续页的色板、卡片、图表、图标、标题层级都跟首页保持一致
   - 风格由主题决定，不是固定套模板
   - 如果首页主视觉无法生成，允许降级为联网搜索一张与主题强相关的背景图，再用它统一后续页面风格

3. **组件由内容决定**
   - 数据类内容 → 图表 / 表格 + 简短结论
   - 趋势类内容 → 折线图
   - 对比类内容 → 柱状图 / 对照表
   - 场景分类 / 应用分层 → 卡片矩阵
   - 流程 / 路径 / 步骤 → 流程图 / 时间轴
   - 结论页 → 结论卡片
   - 尾页 → 致谢页

4. **真实数据优先**
   - 图表和表格只允许用当次输入或当次检索得到的数据
   - 没有真实数据时，必须明确标注“示意数据 / 待补数据”
   - 不允许复用假数据模板

## 3. 总入口（推荐）

当用户已经给出主题、调研结果或大纲时，优先用总入口脚本跑完整闭环：

```bash
/root/.openclaw/venvs/ppt/bin/python {baseDir}/scripts/run_pipeline.py \
  --theme "{主题}" \
  --research-file "{调研文件或整理后的文本文件}" \
  --slides 8 \
  --style whiteboard \
  --output-dir "{workspace}/ppt_outputs/{任务名}" \
  --output-pptx "{workspace}/ppt_outputs/{任务名}/final.pptx"
```

这个总入口会自动完成：
1. 主题提炼
2. 页面规划
3. 组件选择
4. 逐页生图
5. 合成 PPT

执行要求：
- 总入口按阶段执行并落盘状态，不再靠长会话一路续跑
- 某一页生图失败时，整单立即停在该阶段并返回结构化错误，不允许无界续跑
- fallback 必须收敛，不能把失败消息再当成下一轮输入继续放大

如果只想试某一页，再退回单页命令模式。

## 4. 单页命令模式

```bash
/root/.openclaw/venvs/ppt/bin/python {baseDir}/scripts/generate_image.py \
  --prompt "{页面提示词}" \
  --filename "{输出文件名}.jpg" \
  --resolution 2K \
  --aspect-ratio 16:9 \
  -i "{参考图绝对路径}"
```

### 页型与参考图映射
- 首页 → `cover.jpg`
- 数据页 → `chart.jpg`
- 流程页 → `navigation.jpg`
- 普通内容页 → `content.jpg`
- 文字页 → `text.jpg`
- 尾页 → `closing.jpg`

不同页型严禁混用参考图。

## 5. 合成命令

```bash
/root/.openclaw/venvs/ppt/bin/python {baseDir}/scripts/build_pptx.py \
  -i "slide1.jpg" "slide2.jpg" "slide3.jpg" \
  -o "{workspace}/你的文件名.pptx"
```

## 6. 依赖

当前页面生成走系统底层 `clawdbox-image-gen`，不再直连外部 OpenAI 兼容图片 API。

检查：

```bash
/root/.openclaw/venvs/ppt/bin/python -c "import PIL, pptx; print('ok')" && test -f /root/.openclaw/workspace/skills/clawdbox-image-gen/scripts/gen.py
```

## 7. 输出约定

- 单页生成脚本输出：`MEDIA:/abs/path/to/file.jpg`
- 合成脚本输出：`PPTX:/abs/path/to/file.pptx`
- 对用户最终回复要短：
  - 例如：`已先做一版，重点放进 PPT 里了。`

## 8. 禁止事项

- ❌ 没有首页主视觉或明确降级背景图就直接做正文页
- ❌ 首页和正文风格割裂
- ❌ 数据页只有大段文字，没有图表/表格
- ❌ 流程页不用流程图，只用段落硬写
- ❌ 不同题材复用同一套组件模板和假数据
- ❌ 长篇追问或长篇过程汇报

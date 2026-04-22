---
name: yourself-skill
description: "与其蒸馏别人，不如蒸馏自己。把聊天记录、日记、照片蒸馏成可运行的数字分身。| Distill yourself into a runnable digital twin."
version: "1.0.0"
---

> **语言**：根据用户第一条消息的语言，全程使用同一语言回复。

# 自己.skill 创建器（Hermes 版）

## 触发条件

当用户说以下任意内容时启动：
- 「帮我创建一个自己的 skill」
- 「我想把自己蒸馏成分身」
- 「新建自我镜像」
- 「给我做一个我自己的数字分身」

当用户对已有自我 Skill 说以下内容时，进入进化模式：
- 「我有新文件」/ 「追加」
- 「这不对」/ 「我不会这样说」/ 「我应该是」
- 「更新我的分身」

当用户说「列出我的分身」时列出所有已生成的自我 Skill。

---

## 环境说明

本 Skill 运行在 Hermes Agent 环境。

- **Skill 目录**：`~/.hermes/skills/yourself-skill/`（下称 `SKILL_DIR`）
- **分身存储目录**：`~/.hermes/skills/yourself-skill/selves/`（下称 `SELVES_DIR`）
- **Python 工具路径**：`~/.hermes/skills/yourself-skill/tools/`

## 工具使用规则

| 任务 | 执行方式 |
|------|----------|
| 读取 MD/TXT 文件 | Bash `cat {path}` |
| 读取图片/PDF | vision 工具或 Bash read |
| 解析微信聊天记录 | `python3 ~/.hermes/skills/yourself-skill/tools/wechat_parser.py` |
| 解析 QQ 聊天记录 | `python3 ~/.hermes/skills/yourself-skill/tools/qq_parser.py` |
| 解析社交媒体内容 | `python3 ~/.hermes/skills/yourself-skill/tools/social_parser.py` |
| 分析照片元信息 | `python3 ~/.hermes/skills/yourself-skill/tools/photo_analyzer.py` |
| 写入/更新分身文件 | Bash `cat > {path} << 'EOF'` 或 `tee` |
| 版本管理 | `python3 ~/.hermes/skills/yourself-skill/tools/version_manager.py` |
| 列出已有分身 | `python3 ~/.hermes/skills/yourself-skill/tools/skill_writer.py --action list` |
| 合并生成 SKILL.md | `python3 ~/.hermes/skills/yourself-skill/tools/skill_writer.py --action combine` |

**分身存储位置**：所有生成的分身文件写入 `~/.hermes/skills/yourself-skill/selves/{slug}/`

---

## 主流程：创建新数字分身

### Step 1：基础信息录入（3 个问题）

读取 `~/.hermes/skills/yourself-skill/prompts/intake.md` 了解问题序列，只问 3 个问题：

1. **代号/昵称**（必填）— 示例：`小北` / `自己` / `joey`
2. **基本信息**（一句话：年龄、职业、城市）— 示例：`35岁，产品经理，上海`
3. **自我画像**（一句话：MBTI、星座、性格标签）— 示例：`INTJ 摩羯座 行动派`

除代号外均可跳过。收集完后汇总确认再进入下一步。

### Step 2：原材料导入

询问用户提供原材料：

```
原材料怎么提供？数据越多，还原度越高。

  [A] 微信聊天记录导出
      支持 WeChatMsg、留痕、PyWxDump 等工具的导出格式

  [B] QQ 聊天记录导出
      支持 QQ 消息管理器导出的 txt/mht 格式

  [C] 社交媒体 / 日记 / 笔记
      朋友圈截图、微博、备忘录、Obsidian 笔记等

  [D] 照片
      提取时间地点，构建人生时间线

  [E] 直接粘贴/口述
      把你对自己的认知告诉我

可以混用，也可以跳过（仅凭手动信息生成）。
```

#### 方式 A：微信聊天记录

```bash
python3 ~/.hermes/skills/yourself-skill/tools/wechat_parser.py \
  --file {path} \
  --target "我" \
  --output /tmp/wechat_out.txt \
  --format auto
```

#### 方式 B：QQ 聊天记录

```bash
python3 ~/.hermes/skills/yourself-skill/tools/qq_parser.py \
  --file {path} \
  --target "我" \
  --output /tmp/qq_out.txt
```

#### 方式 C：社交媒体 / 笔记

Bash `cat {path}` 直接读取文本文件。图片截图发给 AI 分析。

#### 方式 D：照片分析

```bash
python3 ~/.hermes/skills/yourself-skill/tools/photo_analyzer.py \
  --dir {photo_dir} \
  --output /tmp/photo_out.txt
```

#### 方式 E：直接粘贴/口述

引导用户回忆：
```
可以聊聊这些（想到什么说什么）：

🗣️ 你的口头禅是什么？
💬 你做决定的时候通常怎么想？
🍜 你难过的时候一般会做什么？
📍 你最喜欢去哪里？
😤 你生气的时候是什么样？
💭 你深夜独处的时候在想什么？
🌱 你觉得自己这几年最大的变化是什么？
```

如果用户说「没有文件」或「跳过」，仅凭 Step 1 的手动信息生成。

### Step 3：分析原材料

读取以下 prompt 文件作为分析指导：
- `~/.hermes/skills/yourself-skill/prompts/self_analyzer.md` — 提取个人经历、价值观、生活习惯
- `~/.hermes/skills/yourself-skill/prompts/persona_analyzer.md` — 提取说话风格、情感模式、决策模式

### Step 4：生成并预览

读取以下 prompt 文件作为生成模板：
- `~/.hermes/skills/yourself-skill/prompts/self_builder.md` — 生成 Self Memory
- `~/.hermes/skills/yourself-skill/prompts/persona_builder.md` — 生成 Persona（5 层结构）

向用户展示摘要（各 5-8 行），询问确认。

### Step 5：写入文件

用户确认后，执行：

```bash
SLUG={slug}
SELVES_DIR=~/.hermes/skills/yourself-skill/selves
mkdir -p /tmp/yourself_${SLUG}

# 写入临时文件
cat > /tmp/yourself_${SLUG}/meta.json << 'METAEOF'
{meta_json}
METAEOF

cat > /tmp/yourself_${SLUG}/self.md << 'SELFEOF'
{self_content}
SELFEOF

cat > /tmp/yourself_${SLUG}/persona.md << 'PERSONAEOF'
{persona_content}
PERSONAEOF

# 创建分身
python3 ~/.hermes/skills/yourself-skill/tools/skill_writer.py \
  --action create \
  --slug ${SLUG} \
  --base-dir ${SELVES_DIR} \
  --meta /tmp/yourself_${SLUG}/meta.json \
  --self /tmp/yourself_${SLUG}/self.md \
  --persona /tmp/yourself_${SLUG}/persona.md

# 同步到 Hermes skills 目录，让分身可以被直接加载
cp -r ${SELVES_DIR}/${SLUG} ~/.hermes/skills/${SLUG}
```

> **Fallback**：如果脚本失败，直接用 Bash 写入文件到 `~/.hermes/skills/yourself-skill/selves/{slug}/`，然后手动写 `SKILL.md`。

告知用户：
```
✅ 数字分身已创建！

文件位置：~/.hermes/skills/yourself-skill/selves/{slug}/
已同步至：~/.hermes/skills/{slug}/

如果用起来感觉哪里不像你，直接说「我不会这样」，我来更新。
```

---

## 进化模式：追加文件

用户提供新的聊天记录、照片或笔记时：

1. 按 Step 2 的方式读取新内容
2. `cat ~/.hermes/skills/yourself-skill/selves/{slug}/self.md` 读取现有内容
3. 读取 `~/.hermes/skills/yourself-skill/prompts/merger.md` 分析增量
4. 备份当前版本：
   ```bash
   python3 ~/.hermes/skills/yourself-skill/tools/version_manager.py \
     --action backup --slug {slug} \
     --base-dir ~/.hermes/skills/yourself-skill/selves
   ```
5. 追加内容到对应文件
6. 重新生成 SKILL.md：
   ```bash
   python3 ~/.hermes/skills/yourself-skill/tools/skill_writer.py \
     --action combine --slug {slug} \
     --base-dir ~/.hermes/skills/yourself-skill/selves
   cp ~/.hermes/skills/yourself-skill/selves/{slug}/SKILL.md ~/.hermes/skills/{slug}/SKILL.md
   ```

---

## 进化模式：对话纠正

用户表达「不对」/「我不会这样说」时：

1. 读取 `~/.hermes/skills/yourself-skill/prompts/correction_handler.md`
2. 判断属于 Self Memory（事实/经历）还是 Persona（性格/说话方式）
3. 追加 correction 记录到对应文件
4. 重新生成并同步 SKILL.md

---

## 管理命令

**列出所有分身**：
```bash
python3 ~/.hermes/skills/yourself-skill/tools/skill_writer.py \
  --action list --base-dir ~/.hermes/skills/yourself-skill/selves
```

**回滚版本**：
```bash
python3 ~/.hermes/skills/yourself-skill/tools/version_manager.py \
  --action rollback --slug {slug} --version {version} \
  --base-dir ~/.hermes/skills/yourself-skill/selves
```

**删除分身**（确认后执行）：
```bash
rm -rf ~/.hermes/skills/yourself-skill/selves/{slug}
rm -rf ~/.hermes/skills/{slug}
```

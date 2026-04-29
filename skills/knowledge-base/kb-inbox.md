---
name: kb-inbox
description: 上传资料整理归档：用户通过SMB上传新文件后的自动整理与分类流程
version: 1.0.0
---

# 上传资料整理流程

用户通过 SMB/网盘上传文件时，**必须放到 `$MOUNT/上传原始资料/` 目录**，watcher 检测到后触发本流程。

---

## 核心规则

### 1. 必须处理 上传原始资料 内所有文件

收到通知时，**完整扫描 上传原始资料 根目录**，不能只处理第一个文件：

```bash
ls "$MOUNT/上传原始资料/"   # 先列出所有文件，再逐一处理
```

### 2. zip/压缩包：解压到主目录，不在 上传原始资料 内解压

```bash
# 错误做法：在 上传原始资料 内解压（会被 watcher 二次触发）
cd "$MOUNT/上传原始资料" && unzip file.zip

# 正确做法：解压到主目录临时区
unzip "$MOUNT/上传原始资料/file.zip" -d "$MOUNT/tmp_unzip/"
```

### 3. 处理完成后清空 上传原始资料

每个文件处理完后立即从 上传原始资料 移走，处理完所有文件后 上传原始资料 应为空：

```bash
mv "$MOUNT/上传原始资料/file.zip" "$MOUNT/档案库/对应分类/"
# 或者 rm（如果原始文件不需要保留）
```

### 5. 处理子目录
- `kb_organize.py` 默认仅扫描根目录文件。
- 若 `上传原始资料/` 中包含子目录，需先递归列出所有文件，或在脚本中显式处理子目录内容，确保无遗漏。
- 建议：使用 `find $MOUNT/上传原始资料 -type f` 来确保覆盖所有深层文件。

---

## 标准整理流程（必须严格按顺序执行，不得跳步）

收到 kb_notify 推送时，执行以下步骤：

### Step 1：扫描 上传原始资料 根目录
```bash
ls $MOUNT/上传原始资料/
```

### Step 2：**强制解压所有压缩包**（关键步骤，禁止跳过）

凡是 .zip / .tar.gz / .rar / .7z 后缀的文件，**必须先解压**，再处理解压出来的内容；**绝不能把压缩包当作其他类直接归档**。

```bash
mkdir -p $MOUNT/.tmp_extract
for f in $MOUNT/上传原始资料/*.zip $MOUNT/上传原始资料/*.tar.gz $MOUNT/上传原始资料/*.rar $MOUNT/上传原始资料/*.7z; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  mkdir -p "$MOUNT/.tmp_extract/${base%.*}"
  case "$f" in
    *.zip) unzip -o "$f" -d "$MOUNT/.tmp_extract/${base%.*}" ;;
    *.tar.gz) tar -xzf "$f" -C "$MOUNT/.tmp_extract/${base%.*}" ;;
    *.rar) unrar x -o+ "$f" "$MOUNT/.tmp_extract/${base%.*}/" ;;
    *.7z) 7z x "$f" -o"$MOUNT/.tmp_extract/${base%.*}" ;;
  esac
  # 解压后把压缩包本身归档到 档案库/原始压缩包/
  mkdir -p $MOUNT/档案库/原始压缩包/
  mv "$f" $MOUNT/档案库/原始压缩包/
done

# 把解压出来的内容递归移到 上传原始资料/，让后续步骤继续处理
find $MOUNT/.tmp_extract -type f -exec mv {} $MOUNT/上传原始资料/ \;
rm -rf $MOUNT/.tmp_extract
```

### Step 3：识别文件类型并准备归类
- .xlsx / .csv / .json → 数据类
- .docx / .pdf → 文档类
- .pptx → 演示类
- 视频/图片 → 媒体类
- 其他 → 其他类

### Step 4：归类到 档案库/ 对应分类
```bash
python3 /root/.hermes/skills/knowledge-base/scripts/kb_organize.py $MOUNT --execute
```

### Step 5：更新索引
```bash
python3 /root/.hermes/skills/knowledge-base/scripts/kb_index.py $MOUNT
```

### Step 6：**强制更新 Wiki 知识库**（关键步骤，禁止跳过）

按 `skill_view("knowledge-base/kb-wiki")` 的规则，必须完成：

1. **更新 `$MOUNT/.hermes-index/wiki/_index.md`**：为每个新文件追加条目（路径、类型、标签、一句话摘要、关联主题）
2. **生成/更新 `$MOUNT/.hermes-index/wiki/concepts/<主题>.md`**：根据本批文件涉及的业务主题（如湖南高校教师数据、BIM造价等），把多个文件的核心信息综合成主题知识页
3. **追加 `$MOUNT/.hermes-index/wiki/log.md`** 一行：`- YYYY-MM-DD HH:MM：新增 N 个文件，涉及主题：[主题列表]`



### Step 6.5：**Wiki 格式校验（关键步骤，禁止跳过）**

生成 wiki 后必须立即运行校验：

```bash
python3 /root/.hermes/skills/knowledge-base/scripts/kb_wiki_check.py $MOUNT
```

- **校验通过**（exit 0）：继续 Step 7
- **校验失败**（exit 1）：根据输出的问题列表逐一修复，然后**再次运行校验**，直到通过为止

常见问题及修复方法：
- 「wiki link 未闭合」→  改成 （双方括号）
- 「摘要是占位符」→ 把「关于xxx的文档」替换为实际内容摘要（读文件后写一句话）
- 「缺少核心内容」→ 读取相关文件内容，补充 concept 页的核心内容章节
- 「引用了 [[X]] 但 concepts/X.md 不存在」→ 创建对应的 concept 页，或修改关联指向已有主题

### Step 7：确认 上传原始资料 已清空
```bash
ls $MOUNT/上传原始资料/   # 应为空
```

### Step 8：向用户报告处理结果
格式：
```
📂 已处理 N 个文件：
· [文件名] → [归档路径]（[一句话摘要]）
...

📚 已更新 wiki 主题：
· [[主题1]]、[[主题2]]

要我[具体建议动作]吗？
```

---

## ⚠️ 完整性检查（执行前后核对）

执行前必读：
- 压缩包**必须先解压再处理**，不能直接归类到其他
- wiki 内容**必须实际写入文件**，不能只口头说已生成

执行后核对：
- `ls $MOUNT/上传原始资料/` 应为空
- `ls $MOUNT/.hermes-index/wiki/concepts/` 应有新主题页
- `tail $MOUNT/.hermes-index/wiki/_index.md` 应有新增条目

---

## 解压规范

```bash
# zip
unzip "$MOUNT/上传原始资料/xxx.zip" -d "$MOUNT/.上传原始资料_tmp/"

# 解压完成后，把内容物归类到主目录
# .上传原始资料_tmp/ 只是临时中转，处理完立即删除
rm -rf "$MOUNT/.上传原始资料_tmp/"
```

解压出来的文件按内容类型分别走 Step 2-4，不直接放在主目录根下。

---

## 注意事项

- 上传原始资料 watcher **只监听根目录**（非递归），agent 在 `上传原始资料/temp/` 或 `上传原始资料/` 子目录操作不会触发二次推送
- 如果 上传原始资料 里有 `._` 开头的 Mac 元数据文件，直接忽略删除
- 处理失败的文件移到 `$MOUNT/上传原始资料/failed/`，并告知用户原因

---
name: kb-inbox
description: inbox 文件接收与 ETL 流程：用户上传新文件后的标准处理规范
version: 1.0.0
---

# Inbox ETL 流程

用户通过 SMB/网盘上传文件时，**必须放到 `$MOUNT/inbox/` 目录**，watcher 检测到后触发本流程。

---

## 核心规则

### 1. 必须处理 inbox 内所有文件

收到通知时，**完整扫描 inbox 根目录**，不能只处理第一个文件：

```bash
ls "$MOUNT/inbox/"   # 先列出所有文件，再逐一处理
```

### 2. zip/压缩包：解压到主目录，不在 inbox 内解压

```bash
# 错误做法：在 inbox 内解压（会被 watcher 二次触发）
cd "$MOUNT/inbox" && unzip file.zip

# 正确做法：解压到主目录临时区
unzip "$MOUNT/inbox/file.zip" -d "$MOUNT/tmp_unzip/"
```

### 3. 处理完成后清空 inbox

每个文件处理完后立即从 inbox 移走，处理完所有文件后 inbox 应为空：

```bash
mv "$MOUNT/inbox/file.zip" "$MOUNT/归档目标路径/"
# 或者 rm（如果原始文件不需要保留）
```

### 4. agent 不往 inbox 写任何文件

inbox 只接收用户上传的原始文件。agent 的输出（报告、清洗后的数据、索引等）一律写到主目录。

---

## 标准 ETL 步骤

收到 kb_notify 推送时，执行以下步骤：

```
Step 1：扫描 inbox 根目录，列出所有待处理文件
         ls $MOUNT/inbox/ | grep -v '^\.''

Step 2：逐一识别文件类型
         - .zip / .tar.gz → 解压到主目录，然后递归处理解压出来的文件
         - .xlsx / .csv   → 数据清洗入库
         - .docx / .pdf   → 提取内容，更新知识库索引
         - .pptx          → 提取文本，建索引
         - 视频/图片       → 只记录元数据，不提取内容

Step 3：归类到主目录合适位置
         python3 kb_organize.py $MOUNT --file <文件路径> --dest <目标路径>

Step 4：更新索引
         python3 kb_index.py $MOUNT

Step 5：清空 inbox（所有文件已移走）

Step 6：向用户报告处理结果
         格式：
         📂 已处理 N 个文件：
         · [文件名] → [归档路径]（[一句话内容摘要]）
         · ...
         要我[具体建议动作]吗？
```

---

## 解压规范

```bash
# zip
unzip "$MOUNT/inbox/xxx.zip" -d "$MOUNT/.inbox_tmp/"

# 解压完成后，把内容物归类到主目录
# .inbox_tmp/ 只是临时中转，处理完立即删除
rm -rf "$MOUNT/.inbox_tmp/"
```

解压出来的文件按内容类型分别走 Step 2-4，不直接放在主目录根下。

---

## 注意事项

- inbox watcher **只监听根目录**（非递归），agent 在 `inbox/temp/` 或 `inbox/` 子目录操作不会触发二次推送
- 如果 inbox 里有 `._` 开头的 Mac 元数据文件，直接忽略删除
- 处理失败的文件移到 `$MOUNT/inbox/failed/`，并告知用户原因

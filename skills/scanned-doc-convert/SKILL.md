---
name: scanned-doc-convert
description: 当用户要求把扫描 PDF、拍照页、截图页或其他图片型文档转换为 TXT、可编辑 PDF 或 DOCX 时，使用这个 skill。固定入口是当前目录下的 `run.py`；不要搜索脚本位置，不要阅读脚本源码。
metadata: { "openclaw": { "emoji": "🧾", "requires": { "anyBins": ["python3", "python"] } } }
---

# scanned-doc-convert

把扫描 PDF、拍照页、截图页或其他图片型文档转换为 TXT、可编辑 PDF 或 DOCX 时，直接使用这个 skill。

## 低 token 执行规则

- 当前 `SKILL.md` 所在目录就是 `<skill-root>`。
- 固定入口为 `<skill-root>/run.py`。
- `run.py` 会在内部定位并执行 `<skill-root>/scripts/run_scanned_doc_convert.py`。
- `run.py` 允许直接写：
  - `python run.py --input "..." --output "..."`
  - `python run.py "input" "output"`
- 当只提供输入和输出时，入口会自动按 `auto-convert` 处理。
- 不要搜索别的脚本路径，不要拼 `baseDir`，不要猜 `../`，不要读取 `scripts/` 源码。
- 默认直接执行 `auto-convert`。只有用户明确要求中间产物时，才执行 `upload`、`convert`、`pdf2docx`、`ocr2txt`。
- 只有脚本真实报错且明确提示缺依赖时，才安装依赖并重试。

## 平台命令

- Linux / macOS：优先 `python3`，不存在时回退 `python`
- Windows：统一使用 `python`

Linux / macOS：

```bash
cd "<skill-root>"
python3 run.py --input "/path/to/input.pdf" --output "/path/to/output.docx"
```

Windows PowerShell：

```powershell
Set-Location "<skill-root>"
python .\run.py --input "D:\path\to\input.pdf" --output "D:\path\to\output.docx"
```

## 中文路径规则

- 输入路径、输出路径、目录名可以包含中文、空格、括号。
- 路径必须整体加引号，作为单个参数传入。
- 不要手动转码，不要拆分路径，不要用 glob 搜文件。

## 默认命令

- 输出 `.txt`：使用 `auto-convert`
- 输出 `.pdf`：使用 `auto-convert`
- 输出 `.docx`：使用 `auto-convert`

示例：

```bash
python3 run.py --input "/path/to/input.pdf" --output "/path/to/output.txt"
python3 run.py --input "/path/to/input.png" --output "/path/to/output.pdf"
python3 run.py --input "/path/to/input.pdf" --output "/path/to/output.docx"
```

内部行为：

- `.txt`：走 `ocr2txt`
- `.pdf`：走 `upload + convert`
- `.docx`：走 `upload + convert + pdf2docx`

## 分步命令

仅在用户明确要求中间产物时使用：

- `upload`

```bash
python3 run.py upload --input "/path/to/input.pdf" --output "/path/to/01.upload.json"
```

- `convert`

```bash
python3 run.py convert --upload-meta "/path/to/01.upload.json" --output "/path/to/02.output.pdf"
```

- `pdf2docx`

```bash
python3 run.py pdf2docx --input "/path/to/02.output.pdf" --output "/path/to/03.output.docx"
```

- `ocr2txt`

```bash
python3 run.py ocr2txt --input "/path/to/input.pdf" --output "/path/to/output.txt"
```

## 默认配置来源

- `--base-url` 默认优先读取环境变量 `OPENCLAW_RELEASE_BASE_URL`，否则回退到 `~/.openclaw/openclaw.json`
- `--auth-uid`、`--auth-token` 默认读取 `~/.openclaw/identity/openclaw-userinfo.json`
- `--state-dir` 默认 `~/.openclaw`
- `--poll-interval` 默认 `1.0`
- `--max-wait-time` 默认 `180`
- `--pdf-page-max-side` 默认 `2048`

## 依赖处理

- 需要 `requests`
- 处理 PDF 输入时可能需要 `PyMuPDF`
- 默认不要预装依赖
- 只有当脚本真实报错指向缺依赖时，才安装后重试

## 不要做的事

- 不要搜索 skill 外的脚本
- 不要搜索 `run.py`
- 不要主动打开 `scripts/run_scanned_doc_convert.py` 阅读源码
- 当 `run.py --input ... --output ...` 已经能表达需求时，不要再额外补写子命令
- 不要把路径拆成多段再拼接
- 不要在没有报错时先安装依赖

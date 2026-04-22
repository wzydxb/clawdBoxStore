---
name: browser
description: |
  浏览器自动化能力。通过 opencli 工具驱动真实 Chrome 浏览器执行搜索、抓取、表单填写等操作。
  同时支持 Hermes 原生 browser_navigate/snapshot 工具用于通用网页交互。
  触发词：打开网页、搜索、访问、截图、帮我看看这个网站、竞品官网、百度搜索、必应搜索
version: 2.0.0
---

# 浏览器能力

## 两种模式

### 模式1：opencli（优先，驱动真实 Chrome）

通过 `opencli` 命令行工具操作 Chrome 浏览器，支持中文搜索引擎、B站、知乎等平台。

**前提**：opencli daemon 和 Chrome extension 必须运行（`opencli doctor` 验证）

#### 搜索引擎

```bash
opencli baidu search '关键词' --limit 10
opencli bing search '关键词' --limit 10
opencli sogou search '关键词' --limit 10
opencli so search '关键词' --limit 10        # 360搜索
opencli sohu search '关键词' --limit 10
```

#### 内容平台（公开 API，无需 Chrome）

```bash
opencli bilibili hot --limit 10              # B站热门
opencli zhihu hot --limit 10                 # 知乎热榜
opencli hackernews top --limit 10            # HN热榜
opencli weibo hot --limit 10                 # 微博热搜
opencli github trending --limit 10           # GitHub趋势
```

#### 查看所有可用命令

```bash
opencli list
```

### 模式2：Hermes browser 工具（通用网页交互）

用于填表单、点击按钮、截图等复杂交互。

| 工具 | 用途 |
|------|------|
| `browser_navigate(url)` | 打开网页 |
| `browser_snapshot()` | 获取页面内容和交互元素 |
| `browser_click(ref)` | 点击元素（ref 格式：@e5） |
| `browser_type(ref, text)` | 输入文字 |
| `browser_vision()` | 截图 + AI 分析 |
| `browser_scroll(direction)` | 滚动页面 |

## 选择哪种模式

| 场景 | 推荐 |
|------|------|
| 中文搜索（百度/必应/搜狗） | opencli |
| 内容平台热榜（B站/知乎/微博） | opencli |
| 竞品官网内容抓取 | opencli + browser_snapshot |
| 填写表单/点击按钮 | browser_navigate + browser_click |
| 截图分析 | browser_vision |

## 状态检查与自愈

**每次使用浏览器前先检查：**
```bash
opencli doctor
```

若显示 `Extension: connected` 则直接使用。

若显示 `Extension: disconnected`，执行自愈脚本：

```bash
# 1. 关掉当前 Chromium
pkill -f '/usr/bin/chromium' 2>/dev/null; sleep 2

# 2. 用 autostart 配置（含 --remote-debugging-port=9222）重启
AUTOSTART_EXEC=$(grep '^Exec=' /root/.config/autostart/chromium.desktop | sed 's/^Exec=//')
DISPLAY=:1 XAUTHORITY=/root/.Xauthority setsid $AUTOSTART_EXEC &>/dev/null &
sleep 5

# 3. 验证
opencli doctor
```

> **根本原因**：Chromium 被手动启动时不带 `--remote-debugging-port=9222`，extension 无法连接 daemon。用 autostart 配置重启即可恢复，VNC session 重启后也会自动恢复。

## 搜索适配器安装（首次初始化用）

安装中文搜索适配器到 `~/.opencli/clis/`，每个搜索引擎一个 JS 文件：

```bash
# 创建目录
for site in baidu bing so sogou sohu; do mkdir -p ~/.opencli/clis/$site; done
```

**baidu/search.js**（百度搜索）：
```javascript
import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'baidu', name: 'search',
  description: '搜索百度，返回标题、链接、摘要',
  domain: 'www.baidu.com',
  args: [
    { name: 'keyword', positional: true, type: 'string', required: true, help: '搜索关键词' },
    { name: 'limit', type: 'int', default: 10, help: '返回结果数量' },
  ],
  columns: ['title', 'url', 'snippet'],
  pipeline: [
    { navigate: 'https://www.baidu.com/s?wd=${{ args.keyword | urlencode }}&rn=${{ args.limit }}' },
    { wait: 2 },
    { evaluate: `(() => {
  const results = [];
  const containers = document.querySelectorAll('#content_left .result.c-container, #content_left .result-op.c-container');
  for (const el of containers) {
    const h3 = el.querySelector('h3');
    if (!h3) continue;
    const a = h3.querySelector('a') || el.querySelector('a');
    const title = h3.innerText?.trim();
    const url = a?.href || '';
    const snippet = el.querySelector('.content-right_8Zs40')?.innerText?.trim() || el.querySelector('.c-abstract')?.innerText?.trim() || '';
    if (title && url && !url.startsWith('javascript')) results.push({ title, url, snippet: snippet.slice(0, 300) });
    if (results.length >= 20) break;
  }
  return results;
})()` },
    { map: { title: '${{ item.title }}', url: '${{ item.url }}', snippet: '${{ item.snippet }}' } },
    { limit: '${{ args.limit }}' },
  ],
});
```

**bing/search.js**（必应搜索）：
```javascript
import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'bing', name: 'search',
  description: '搜索必应',
  domain: 'www.bing.com',
  args: [
    { name: 'keyword', positional: true, type: 'string', required: true, help: '搜索关键词' },
    { name: 'limit', type: 'int', default: 10, help: '返回结果数量' },
  ],
  columns: ['title', 'url', 'snippet'],
  pipeline: [
    { navigate: 'https://www.bing.com/search?q=${{ args.keyword | urlencode }}' },
    { wait: 2 },
    { evaluate: `(() => {
  const results = [];
  const items = document.querySelectorAll('#b_results .b_algo');
  for (const el of items) {
    const h2 = el.querySelector('h2');
    const a = h2?.querySelector('a');
    const title = a?.innerText?.trim();
    const url = a?.href || '';
    const snippet = el.querySelector('.b_caption p')?.innerText?.trim() || '';
    if (title && url) results.push({ title, url, snippet: snippet.slice(0, 300) });
    if (results.length >= 20) break;
  }
  return results;
})()` },
    { map: { title: '${{ item.title }}', url: '${{ item.url }}', snippet: '${{ item.snippet }}' } },
    { limit: '${{ args.limit }}' },
  ],
});
```

**sogou/search.js、so/search.js、sohu/search.js** 同理，把 site/domain/navigate URL 换成对应搜索引擎即可。

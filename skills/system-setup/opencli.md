---
name: opencli
description: opencli 工具链初始化。安装 opencli、部署搜索适配器、启动 Chrome daemon，确保浏览器自动化能力就绪。
version: 1.0.0
---

# opencli + 浏览器环境初始化

## 诊断

```bash
opencli --version 2>/dev/null || echo "MISSING"
opencli doctor 2>/dev/null
ls ~/.opencli/clis/ 2>/dev/null || echo "ADAPTERS_MISSING"
```

| 状态 | 行动 |
|------|------|
| opencli MISSING | → [安装 opencli](#install) |
| daemon 未起 / extension 未连接 | → [启动 Chrome daemon](#chrome) |
| 适配器目录为空 | → [部署搜索适配器](#adapters) |

---

## 安装 opencli {#install}

```bash
npm install -g @jackwener/opencli
# 或
bun add -g @jackwener/opencli
```

验证：
```bash
opencli --version
```

---

## Extension 断开自愈 {#chrome}

**每次使用浏览器前先检查：**
```bash
opencli doctor
```

如果显示 `Extension: disconnected`，按以下步骤自愈：

**步骤 1：检查 Chromium 是否缺少调试端口**
```bash
CHROM_PID=$(pgrep -f '/usr/bin/chromium' | head -1)
[ -n "$CHROM_PID" ] && cat /proc/$CHROM_PID/cmdline | tr '\0' ' ' | grep -o 'remote-debugging-port=[0-9]*' || echo "缺少 --remote-debugging-port"
```

**步骤 2：用正确参数重启 Chromium（VNC 环境）**
```bash
pkill -f '/usr/bin/chromium' 2>/dev/null; sleep 2
AUTOSTART_EXEC=$(grep '^Exec=' /root/.config/autostart/chromium.desktop | sed 's/^Exec=//')
DISPLAY=:1 XAUTHORITY=/root/.Xauthority setsid $AUTOSTART_EXEC &>/dev/null &
sleep 5
opencli doctor   # 期望：Extension: connected
```

autostart 配置里已包含 `--remote-debugging-port=9222`，直接复用即可，不需要手动拼参数。

**步骤 3：如果 autostart 配置不存在**
```bash
DISPLAY=:1 XAUTHORITY=/root/.Xauthority setsid /usr/bin/chromium \
  --remote-debugging-port=9222 --start-fullscreen \
  --load-extension=/root/opencli-extension \
  --no-sandbox --password-store=basic &>/dev/null &
sleep 5
opencli doctor
```

**macOS**
```bash
opencli daemon start
opencli doctor   # 期望：daemon ✅  extension ✅
```

> **根本原因**：Chromium 被手动启动时不会带 `--remote-debugging-port=9222`，extension 无法连接 daemon。VNC session 重启后 GNOME autostart 会用正确参数重新拉起，自动恢复。

---

## 部署搜索适配器 {#adapters}

将 `hermes-opc/opencli-adapters/` 下的适配器复制到 `~/.opencli/clis/`：

```bash
for site in baidu bing so sogou sohu; do
  mkdir -p ~/.opencli/clis/$site
done

# 从 hermes-opc 仓库复制（路径按实际调整）
REPO=~/.hermes   # 或 hermes-opc 实际路径
cp "$REPO/opencli-adapters/baidu/search.js"  ~/.opencli/clis/baidu/search.js
cp "$REPO/opencli-adapters/bing/search.js"   ~/.opencli/clis/bing/search.js
cp "$REPO/opencli-adapters/so/search.js"     ~/.opencli/clis/so/search.js
cp "$REPO/opencli-adapters/sogou/search.js"  ~/.opencli/clis/sogou/search.js
cp "$REPO/opencli-adapters/sohu/search.js"   ~/.opencli/clis/sohu/search.js
```

验证：
```bash
opencli list   # 应看到 baidu search、bing search 等
opencli baidu search '测试' --limit 3
```

---

## 适配器源文件（备用手动创建）

如果仓库路径不可用，手动创建各文件：

<details>
<summary>baidu/search.js</summary>

```javascript
import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'baidu', name: 'search',
  description: '搜索百度，返回标题、链接、摘要（使用真实浏览器，无需代理）',
  domain: 'www.baidu.com',
  args: [
    { name: 'keyword', positional: true, type: 'string', required: true, help: '搜索关键词' },
    { name: 'limit', type: 'int', default: 10, help: '返回结果数量（最多 20）' },
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
    const snippet =
      el.querySelector('.content-right_8Zs40')?.innerText?.trim() ||
      el.querySelector('.c-abstract')?.innerText?.trim() ||
      el.querySelector('[class*="content"]')?.innerText?.trim() || '';
    if (title && url && !url.startsWith('javascript'))
      results.push({ title, url, snippet: snippet.slice(0, 300) });
    if (results.length >= 20) break;
  }
  return results;
})()` },
    { map: { title: '${{ item.title }}', url: '${{ item.url }}', snippet: '${{ item.snippet }}' } },
    { limit: '${{ args.limit }}' },
  ],
});
```
</details>

<details>
<summary>bing/search.js</summary>

```javascript
import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'bing', name: 'search',
  description: '搜索必应，返回标题、链接、摘要',
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
</details>

<details>
<summary>so/search.js（360搜索）</summary>

```javascript
import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'so', name: 'search',
  description: '搜索360搜索，返回标题、链接、摘要',
  domain: 'www.so.com',
  args: [
    { name: 'keyword', positional: true, type: 'string', required: true, help: '搜索关键词' },
    { name: 'limit', type: 'int', default: 10, help: '返回结果数量' },
  ],
  columns: ['title', 'url', 'snippet'],
  pipeline: [
    { navigate: 'https://www.so.com/s?q=${{ args.keyword | urlencode }}' },
    { wait: 2 },
    { evaluate: `(() => {
  const results = [];
  const items = document.querySelectorAll('#results .res-list');
  for (const el of items) {
    const h3 = el.querySelector('h3');
    const a = h3?.querySelector('a') || el.querySelector('a');
    const title = h3?.innerText?.trim();
    const url = a?.href || '';
    const snippet = el.querySelector('.res-desc, .res-summary')?.innerText?.trim() || '';
    if (title && url && !url.startsWith('javascript'))
      results.push({ title, url, snippet: snippet.slice(0, 300) });
    if (results.length >= 20) break;
  }
  return results;
})()` },
    { map: { title: '${{ item.title }}', url: '${{ item.url }}', snippet: '${{ item.snippet }}' } },
    { limit: '${{ args.limit }}' },
  ],
});
```
</details>

<details>
<summary>sogou/search.js</summary>

```javascript
import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'sogou', name: 'search',
  description: '搜索搜狗，返回标题、链接、摘要',
  domain: 'www.sogou.com',
  args: [
    { name: 'keyword', positional: true, type: 'string', required: true, help: '搜索关键词' },
    { name: 'limit', type: 'int', default: 10, help: '返回结果数量' },
  ],
  columns: ['title', 'url', 'snippet'],
  pipeline: [
    { navigate: 'https://www.sogou.com/web?query=${{ args.keyword | urlencode }}' },
    { wait: 2 },
    { evaluate: `(() => {
  const results = [];
  const items = document.querySelectorAll('.results .rb, .results .vrwrap');
  for (const el of items) {
    const h3 = el.querySelector('h3');
    const a = h3?.querySelector('a') || el.querySelector('a');
    const title = h3?.innerText?.trim() || a?.innerText?.trim();
    const url = a?.href || '';
    const snippet = el.querySelector('.space-txt, .ft')?.innerText?.trim() || '';
    if (title && url && !url.startsWith('javascript'))
      results.push({ title, url, snippet: snippet.slice(0, 300) });
    if (results.length >= 20) break;
  }
  return results;
})()` },
    { map: { title: '${{ item.title }}', url: '${{ item.url }}', snippet: '${{ item.snippet }}' } },
    { limit: '${{ args.limit }}' },
  ],
});
```
</details>

<details>
<summary>sohu/search.js</summary>

```javascript
import { cli } from '@jackwener/opencli/registry';
cli({
  site: 'sohu', name: 'search',
  description: '搜索搜狐，返回标题、链接、摘要',
  domain: 'www.sohu.com',
  args: [
    { name: 'keyword', positional: true, type: 'string', required: true, help: '搜索关键词' },
    { name: 'limit', type: 'int', default: 10, help: '返回结果数量' },
  ],
  columns: ['title', 'url', 'snippet'],
  pipeline: [
    { navigate: 'https://www.sohu.com/a/search?keyword=${{ args.keyword | urlencode }}' },
    { wait: 2 },
    { evaluate: `(() => {
  const results = [];
  const items = document.querySelectorAll('.search-result-item, .article-item');
  for (const el of items) {
    const a = el.querySelector('a[href*="sohu.com"]') || el.querySelector('a');
    const title = a?.innerText?.trim() || el.querySelector('h3,h2')?.innerText?.trim();
    const url = a?.href || '';
    const snippet = el.querySelector('.summary, .desc, p')?.innerText?.trim() || '';
    if (title && url && !url.startsWith('javascript'))
      results.push({ title, url, snippet: snippet.slice(0, 300) });
    if (results.length >= 20) break;
  }
  return results;
})()` },
    { map: { title: '${{ item.title }}', url: '${{ item.url }}', snippet: '${{ item.snippet }}' } },
    { limit: '${{ args.limit }}' },
  ],
});
```
</details>

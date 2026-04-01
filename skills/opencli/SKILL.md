---
name: opencli
description: Make websites or Electron apps operable from a CLI while reusing the current Chrome login state. Use when working with OpenCLI commands, generating or modifying OpenCLI adapters, browsing supported site commands, or operating browser/Electron targets through the opencli tool.
---

# OpenCLI

> Make any website or Electron App your CLI. Reuse Chrome login, zero risk, AI-powered discovery.

> [!CAUTION]
> **AI Agent 必读：创建或修改任何适配器之前，你必须先阅读 `CLI-EXPLORER.md`。**
> 该文档包含 API 发现工作流、认证策略决策树、平台 SDK 速查表、`tap` 步骤调试流程、分页 API 模板、级联请求模式以及常见陷阱。
> 本文件主要提供命令参考和简化模板。

> [!IMPORTANT]
> 创建或修改 adapter 时，遵守 3 条规则：
> 1. 主参数优先用 positional arg，不要默认做成 `--query` / `--id` / `--url`
> 2. 预期中的 adapter 失败优先抛 `CliError` 子类，不要直接抛原始 `Error`
> 3. 新增 adapter 或新增用户可发现命令时，同步更新 adapter docs、`docs/adapters/index.md`、sidebar，以及 README / README.zh-CN 中受影响的入口

## Install & Run

```bash
# npm global install (recommended)
npm install -g @jackwener/opencli
opencli <command>

# Or from source
cd ~/code/opencli && npm install
npx tsx src/main.ts <command>

# Update to latest
npm update -g @jackwener/opencli
```

## Prerequisites

Browser commands require:
1. Chrome browser running and already logged into target sites
2. `opencli Browser Bridge` Chrome extension installed
3. No extra setup beyond the daemon auto-start

Public API commands like `hackernews` and部分 `v2ex` 功能不需要浏览器。

## Common command groups

### Content / social platforms

```bash
opencli bilibili hot --limit 10
opencli zhihu hot --limit 10
opencli xiaohongshu search "美食"
opencli weibo hot --limit 10
opencli twitter search "AI"
opencli reddit hot --limit 10
opencli jike feed --limit 10
opencli douban top250
opencli facebook feed --limit 10
opencli instagram explore
opencli tiktok explore
```

### Developer / information tools

```bash
opencli gh repo list
opencli hackernews top --limit 10
opencli stackoverflow search "typescript"
opencli wikipedia summary "Python"
opencli arxiv search "attention"
opencli google news --limit 10
```

### Productivity / desktop adapters

```bash
opencli antigravity status
opencli cursor ask "question"
opencli codex ask "question"
opencli chatgpt ask "question"
opencli chatwise ask "question"
opencli notion read
opencli discord-app read
opencli doubao-app ask "question"
```

### Commerce / jobs / finance

```bash
opencli boss search "AI agent"
opencli ctrip search "三亚"
opencli smzdm search "耳机"
opencli xueqiu stock --symbol SH600519
opencli yahoo-finance quote --symbol AAPL
opencli barchart quote --symbol AAPL
opencli jd item 100291143898
opencli coupang search "耳机"
```

## Management commands

```bash
opencli list
opencli list --json
opencli install <name>
opencli register <name>
opencli validate
opencli doctor
```

## AI agent workflow

```bash
opencli explore <url> --site <name>
opencli synthesize <site>
opencli generate <url> --goal "hot"
opencli record <url>
opencli cascade <api-url>
```

## Output formats

All built-in commands support `--format` / `-f`:
- `table`
- `json`
- `yaml`
- `md`
- `csv`

## Creating adapters

### YAML pipeline example

```yaml
site: mysite
name: hot
description: Hot topics
domain: www.mysite.com
strategy: cookie
browser: true

args:
  limit:
    type: int
    default: 20
    description: Number of items

pipeline:
  - navigate: https://www.mysite.com
  - evaluate: |
      (async () => {
        const res = await fetch('/api/hot', { credentials: 'include' });
        const d = await res.json();
        return d.data.items.map(item => ({
          title: item.title,
          score: item.score,
        }));
      })()
  - map:
      rank: ${{ index + 1 }}
      title: ${{ item.title }}
      score: ${{ item.score }}
  - limit: ${{ args.limit }}

columns: [rank, title, score]
```

### TypeScript adapter example

```typescript
import { cli, Strategy } from '../../registry.js';

cli({
  site: 'mysite',
  name: 'search',
  strategy: Strategy.INTERCEPT,
  args: [{ name: 'query', required: true, positional: true }],
  columns: ['rank', 'title', 'url'],
  func: async (page, kwargs) => {
    await page.goto('https://www.mysite.com/search');
    await page.installInterceptor('/api/search');
    await page.autoScroll({ times: 3, delayMs: 2000 });
    const requests = await page.getInterceptedRequests();
    let results = [];
    for (const req of requests) results.push(...req.data.items);
    return results.map((item, i) => ({ rank: i + 1, title: item.title, url: item.url }));
  },
});
```

## Authentication tiers

| Tier | Name | Method |
|------|------|--------|
| 1 | `public` | No auth, Node.js fetch |
| 2 | `cookie` | Browser fetch with credentials |
| 3 | `header` | Custom headers |
| 4 | `intercept` | XHR interception + state extraction |
| 5 | `ui` | Full UI automation |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `npx not found` | Install Node.js |
| `Extension not connected` | Keep Chrome open and install the Browser Bridge extension |
| `Target page context` error | Add `navigate:` before `evaluate:` |
| Empty table data | Check returned JSON path |
| Daemon issues | Use `curl localhost:19825/status` and `curl localhost:19825/logs` |

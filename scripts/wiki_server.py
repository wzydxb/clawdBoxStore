#!/usr/bin/env python3
"""
Wiki Server — 渲染 ~/.hermes-index/wiki/ 目录，支持 SSE 动态更新
端口：8788
"""
import os, re, json, time, threading
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote

WIKI_DIR = Path(os.path.expanduser("~/.hermes-index/wiki"))
PORT = 8788
SMB_HOST = "192.168.10.30"
SMB_SHARE = "龙虾智盒网盘"
MOUNT_ROOT = Path("/data/龙虾智盒网盘")

def _smb_url(rel_dir):
    from urllib.parse import quote
    smb = f"smb://{SMB_HOST}/{quote(SMB_SHARE)}/{quote(rel_dir, safe='/')}"
    win = f"\\\\{SMB_HOST}\\{SMB_SHARE}\\{rel_dir}".replace('/', '\\')
    return smb, win

# ── 查找文件所在文件夹，返回 SMB URL ────────────────────────
def _find_file_folder(filename):
    db_path = MOUNT_ROOT / '.hermes-index' / 'index.db'
    if not db_path.exists():
        return None
    try:
        import sqlite3
        db = sqlite3.connect(str(db_path))
        row = db.execute("SELECT path FROM meta WHERE path LIKE ?", (f'%/{filename}',)).fetchone()
        db.close()
        if row:
            fpath = row[0]
            rel_dir = os.path.dirname(fpath).replace(str(MOUNT_ROOT), '').lstrip('/')
            smb, win = _smb_url(rel_dir)
            return smb, win
    except Exception:
        pass
    return None

# ── Markdown → HTML（轻量实现，无外部依赖）──────────────────
def md_to_html(text):
    text = re.sub(r'^#{6}\s+(.+)$', r'<h6>\1</h6>', text, flags=re.M)
    text = re.sub(r'^#{5}\s+(.+)$', r'<h5>\1</h5>', text, flags=re.M)
    text = re.sub(r'^#{4}\s+(.+)$', r'<h4>\1</h4>', text, flags=re.M)
    text = re.sub(r'^#{3}\s+(.+)$', r'<h3>\1</h3>', text, flags=re.M)
    text = re.sub(r'^#{2}\s+(.+)$', r'<h2>\1</h2>', text, flags=re.M)
    text = re.sub(r'^#{1}\s+(.+)$', r'<h1>\1</h1>', text, flags=re.M)
    # code blocks
    text = re.sub(r'```[\w]*\n(.*?)```', lambda m: '<pre><code>' + m.group(1).replace('<','&lt;').replace('>','&gt;') + '</code></pre>', text, flags=re.DOTALL)
    # inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # 路径字段 → SMB 文件夹链接
    def _path_link(m):
        rel_path = m.group(1).strip()
        rel_dir = os.path.dirname(rel_path)
        smb, win = _smb_url(rel_dir)
        return f'- 路径：<a class="fileref" href="{smb}" data-win="file:///{win}" onclick="return openFolder(this)">📂 {rel_path}</a>'
    text = re.sub(r'^- 路径：(.+)$', _path_link, text, flags=re.M)
    # wiki links [[X]] — 仅当 concepts/X.md 存在时渲染为超链接，否则渲染为文件引用（可打开所在文件夹）
    def _wikilink(m):
        name = m.group(1)
        if (WIKI_DIR / 'concepts' / f'{name}.md').exists():
            return f'<a class="wikilink" href="/concepts/{name}.md">{name}</a>'
        result = _find_file_folder(name)
        if result:
            smb, win = result
            return f'<a class="fileref" href="{smb}" data-win="file:///{win}" onclick="return openFolder(this)">📎 {name}</a>'
        return f'<span class="fileref">📎 {name}</span>'
    text = re.sub(r'\[\[(.+?)\]\]', _wikilink, text)
    # links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    # hr
    text = re.sub(r'^---+$', '<hr>', text, flags=re.M)
    # tables
    lines = text.split('\n')
    out, in_table = [], False
    for line in lines:
        if re.match(r'^\|.+\|$', line):
            if not in_table:
                out.append('<table>')
                in_table = True
            if re.match(r'^\|[-| :]+\|$', line):
                continue
            cells = [c.strip() for c in line.strip('|').split('|')]
            tag = 'th' if not any('<td>' in l for l in out[-3:]) else 'td'
            out.append('<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>')
        else:
            if in_table:
                out.append('</table>')
                in_table = False
            out.append(line)
    if in_table:
        out.append('</table>')
    text = '\n'.join(out)
    # lists
    text = re.sub(r'((?:^[-*]\s.+\n?)+)', lambda m: '<ul>' + re.sub(r'^[-*]\s(.+)', r'<li>\1</li>', m.group(1), flags=re.M) + '</ul>', text, flags=re.M)
    text = re.sub(r'((?:^\d+\.\s.+\n?)+)', lambda m: '<ol>' + re.sub(r'^\d+\.\s(.+)', r'<li>\1</li>', m.group(1), flags=re.M) + '</ol>', text, flags=re.M)
    # paragraphs
    paras = re.split(r'\n{2,}', text)
    result = []
    for p in paras:
        p = p.strip()
        if not p:
            continue
        if re.match(r'^<(h[1-6]|ul|ol|pre|table|hr|blockquote)', p):
            result.append(p)
        else:
            result.append(f'<p>{p}</p>')
    return '\n'.join(result)

# ── 构建侧边栏树 ─────────────────────────────────────────────
def build_sidebar():
    items = []
    index = WIKI_DIR / '_index.md'
    if index.exists():
        items.append('<li class="nav-index"><a href="/_index.md">📋 文档总览</a></li>')
    log = WIKI_DIR / 'log.md'
    if log.exists():
        items.append('<li><a href="/log.md">📝 更新记录</a></li>')

    concepts = sorted((WIKI_DIR / 'concepts').glob('*.md')) if (WIKI_DIR / 'concepts').is_dir() else []
    if concepts:
        items.append('<li class="nav-section">📚 专题文档</li>')
        for f in concepts:
            items.append(f'<li><a href="/concepts/{f.name}">{f.stem}</a></li>')

    insights = sorted((WIKI_DIR / 'insights').glob('*.md')) if (WIKI_DIR / 'insights').is_dir() else []
    if insights:
        items.append('<li class="nav-section">💡 分析沉淀</li>')
        for f in insights:
            items.append(f'<li><a href="/insights/{f.name}">{f.stem}</a></li>')

    return '\n'.join(items)

# ── 页面模板 ─────────────────────────────────────────────────
PAGE_TMPL = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — 知识库</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f6fa;color:#1a1a2e;display:flex;height:100vh;overflow:hidden}}
#sidebar{{width:240px;min-width:240px;background:#1e1e2e;color:#cdd6f4;display:flex;flex-direction:column;overflow-y:auto;padding:0}}
#sidebar-header{{padding:20px 16px 12px;font-size:18px;font-weight:700;color:#cba6f7;border-bottom:1px solid #313244;letter-spacing:.5px}}
#sidebar-header span{{font-size:11px;font-weight:400;color:#6c7086;display:block;margin-top:2px}}
#nav{{padding:8px 0;flex:1}}
#nav ul{{list-style:none}}
#nav li a{{display:block;padding:7px 20px;color:#cdd6f4;text-decoration:none;font-size:13px;border-left:3px solid transparent;transition:all .15s}}
#nav li a:hover,#nav li a.active{{background:#313244;color:#cba6f7;border-left-color:#cba6f7}}
#nav li.nav-section{{padding:12px 20px 4px;font-size:11px;font-weight:600;color:#6c7086;text-transform:uppercase;letter-spacing:.8px}}
#nav li.nav-index a{{color:#89b4fa}}
#main{{flex:1;display:flex;flex-direction:column;overflow:hidden}}
#topbar{{background:#fff;border-bottom:1px solid #e2e8f0;padding:12px 28px;display:flex;align-items:center;gap:12px}}
#topbar h1{{font-size:16px;font-weight:600;color:#1a1a2e;flex:1}}
#live-badge{{font-size:11px;padding:3px 10px;border-radius:20px;background:#d1fae5;color:#065f46;font-weight:600}}
#live-badge.stale{{background:#fee2e2;color:#991b1b}}
#content{{flex:1;overflow-y:auto;padding:32px 40px}}
#content-inner{{max-width:860px;margin:0 auto}}
h1{{font-size:26px;font-weight:700;margin-bottom:20px;color:#1a1a2e;padding-bottom:12px;border-bottom:2px solid #e2e8f0}}
h2{{font-size:20px;font-weight:600;margin:28px 0 12px;color:#1e1e2e}}
h3{{font-size:16px;font-weight:600;margin:20px 0 8px;color:#374151}}
p{{line-height:1.75;margin-bottom:14px;color:#374151}}
code{{background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:13px;font-family:'JetBrains Mono',monospace}}
pre{{background:#1e1e2e;color:#cdd6f4;padding:16px 20px;border-radius:8px;overflow-x:auto;margin:16px 0}}
pre code{{background:none;padding:0;color:inherit}}
table{{width:100%;border-collapse:collapse;margin:16px 0;font-size:14px}}
th{{background:#f8fafc;padding:10px 14px;text-align:left;font-weight:600;border-bottom:2px solid #e2e8f0}}
td{{padding:9px 14px;border-bottom:1px solid #f1f5f9}}
tr:hover td{{background:#f8fafc}}
ul,ol{{padding-left:24px;margin-bottom:14px;line-height:1.75}}
li{{margin-bottom:4px}}
hr{{border:none;border-top:1px solid #e2e8f0;margin:24px 0}}
a{{color:#6366f1;text-decoration:none}}
a:hover{{text-decoration:underline}}
a.wikilink{{color:#8b5cf6;background:#f5f3ff;padding:1px 5px;border-radius:3px}}
.fileref{{color:#6b7280;background:#f1f5f9;padding:1px 5px;border-radius:3px;font-size:13px;text-decoration:none}}
a.fileref{{color:#0369a1;background:#f0f9ff;cursor:pointer}}
a.fileref:hover{{text-decoration:underline}}
.empty-state{{text-align:center;padding:80px 20px;color:#9ca3af}}
.empty-state .icon{{font-size:48px;margin-bottom:16px}}
.empty-state h2{{font-size:20px;color:#6b7280;margin-bottom:8px}}
</style>
</head>
<body>
<div id="sidebar">
  <div id="sidebar-header">📖 知识库<span>智能文档中心</span></div>
  <div id="nav"><ul id="nav-list">{sidebar}</ul></div>
</div>
<div id="main">
  <div id="topbar">
    <h1 id="page-title">{title}</h1>
    <span id="live-badge">● 已同步</span>
  </div>
  <div id="content"><div id="content-inner">{body}</div></div>
</div>
<script>
const path = '{path}';
// 跨平台打开 SMB 文件夹
function openFolder(el) {{
  const isWin = navigator.userAgent.indexOf('Windows') > -1;
  if (isWin) {{
    const winPath = (el.dataset.win || '').replace('file:///', '');
    // 弹出气泡
    const old = document.getElementById('smb-popup');
    if (old) old.remove();
    const popup = document.createElement('div');
    popup.id = 'smb-popup';
    popup.innerHTML = `
      <div style="font-size:14px;font-weight:600;margin-bottom:8px">📂 文件夹路径</div>
      <div style="background:#f1f5f9;padding:8px 12px;border-radius:6px;font-family:monospace;font-size:13px;word-break:break-all;margin-bottom:12px;user-select:all">${{winPath}}</div>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button onclick="document.getElementById('smb-popup').remove()" style="padding:6px 16px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer;font-size:13px">取消</button>
        <button id="smb-copy-btn" style="padding:6px 16px;border:none;border-radius:6px;background:#6366f1;color:#fff;cursor:pointer;font-size:13px">复制路径</button>
      </div>
    `;
    popup.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#fff;padding:20px 24px;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.2);z-index:9999;min-width:360px;max-width:500px';
    // 遮罩
    const mask = document.createElement('div');
    mask.id = 'smb-mask';
    mask.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.3);z-index:9998';
    mask.onclick = () => {{ mask.remove(); popup.remove(); }};
    document.body.appendChild(mask);
    document.body.appendChild(popup);
    document.getElementById('smb-copy-btn').onclick = () => {{
      const ta = document.createElement('textarea');
      ta.value = winPath;
      ta.style.cssText = 'position:fixed;left:-9999px';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      popup.innerHTML = `
        <div style="text-align:center;padding:10px 0">
          <div style="font-size:32px;margin-bottom:8px">✅</div>
          <div style="font-size:15px;font-weight:600;margin-bottom:6px">路径已复制</div>
          <div style="font-size:13px;color:#6b7280">请打开「此电脑」，在地址栏粘贴并回车即可打开文件夹</div>
        </div>
      `;
      setTimeout(() => {{ popup.remove(); mask.remove(); }}, 2500);
    }};
    return false;
  }}
  // Mac/Linux: smb:// 直接跳转
  window.location.href = el.href;
  return false;
}}
// SSE 动态更新
const es = new EventSource('/events');
es.onmessage = e => {{
  const d = JSON.parse(e.data);
  if (d.type === 'reload') {{
    fetch('/render?path=' + encodeURIComponent(path))
      .then(r => r.json())
      .then(d => {{
        document.getElementById('content-inner').innerHTML = d.body;
        document.getElementById('nav-list').innerHTML = d.sidebar;
        document.getElementById('page-title').textContent = d.title;
        document.getElementById('live-badge').className = 'live-badge';
        document.getElementById('live-badge').textContent = '● 已同步';
        // re-highlight active
        document.querySelectorAll('#nav a').forEach(a => {{
          a.classList.toggle('active', a.getAttribute('href') === path);
        }});
      }});
  }}
}};
es.onerror = () => {{
  document.getElementById('live-badge').className = 'stale';
  document.getElementById('live-badge').textContent = '○ 连接中断';
}};
// highlight active nav
document.querySelectorAll('#nav a').forEach(a => {{
  a.classList.toggle('active', a.getAttribute('href') === path);
}});
</script>
</body>
</html>"""

# ── SSE 广播 ─────────────────────────────────────────────────
_clients = []
_clients_lock = threading.Lock()

def broadcast(msg):
    with _clients_lock:
        dead = []
        for q in _clients:
            try:
                q.append(msg)
            except:
                dead.append(q)
        for q in dead:
            _clients.remove(q)

# ── 文件监视线程 ─────────────────────────────────────────────
def watch_wiki():
    mtimes = {}
    while True:
        changed = False
        for f in WIKI_DIR.rglob('*.md'):
            mt = f.stat().st_mtime
            if mtimes.get(str(f)) != mt:
                mtimes[str(f)] = mt
                changed = True
        if changed:
            broadcast(json.dumps({'type': 'reload'}))
        time.sleep(2)

# ── HTTP Handler ─────────────────────────────────────────────
class WikiHandler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        path = unquote(self.path.split('?')[0])

        if path == '/events':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            q = []
            with _clients_lock:
                _clients.append(q)
            try:
                while True:
                    if q:
                        msg = q.pop(0)
                        self.wfile.write(f'data: {msg}\n\n'.encode())
                        self.wfile.flush()
                    else:
                        self.wfile.write(b': ping\n\n')
                        self.wfile.flush()
                        time.sleep(3)
            except:
                with _clients_lock:
                    if q in _clients:
                        _clients.remove(q)
            return

        if path == '/render':
            qs = self.path.split('?', 1)[1] if '?' in self.path else ''
            params = dict(p.split('=', 1) for p in qs.split('&') if '=' in p)
            fpath = unquote(params.get('path', '/_index.md'))
            title, body = self._render_md(fpath)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'title': title, 'body': body, 'sidebar': build_sidebar()}).encode())
            return

        if path == '/' or path == '':
            path = '/_index.md'

        if path.endswith('.md'):
            title, body = self._render_md(path)
            html = PAGE_TMPL.format(title=title, body=body, sidebar=build_sidebar(), path=path)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode())
            return

        self.send_response(404)
        self.end_headers()

    def _render_md(self, url_path):
        # url_path like /_index.md or /concepts/foo.md
        rel = url_path.lstrip('/')
        fpath = WIKI_DIR / rel
        if not fpath.exists() or not str(fpath.resolve()).startswith(str(WIKI_DIR.resolve())):
            return '404', '<div class="empty-state"><div class="icon">📄</div><h2>文档不存在</h2><p>该文档尚未生成，请上传相关文件后由系统自动建立索引。</p></div>'
        text = fpath.read_text(encoding='utf-8')
        # extract title from first h1
        m = re.search(r'^#\s+(.+)$', text, re.M)
        title = m.group(1) if m else fpath.stem
        body = md_to_html(text)
        return title, body

if __name__ == '__main__':
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    t = threading.Thread(target=watch_wiki, daemon=True)
    t.start()
    print(f'Wiki server running on http://0.0.0.0:{PORT}')
    ThreadingHTTPServer(('0.0.0.0', PORT), WikiHandler).serve_forever()

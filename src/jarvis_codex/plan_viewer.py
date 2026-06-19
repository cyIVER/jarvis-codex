from __future__ import annotations

import argparse
import html
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Jarvis Codex Local Plan</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0e1116;
      --panel: #151a22;
      --panel-2: #10151d;
      --text: #eef2f7;
      --muted: #98a2b3;
      --line: #273142;
      --accent: #5eead4;
      --accent-2: #7dd3fc;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--text); }
    .shell { min-height: 100dvh; display: grid; grid-template-columns: 320px minmax(0, 1fr); }
    aside { border-right: 1px solid var(--line); background: var(--panel-2); padding: 22px; position: sticky; top: 0; height: 100dvh; overflow: auto; }
    main { padding: 28px clamp(18px, 4vw, 56px); max-width: 1180px; width: 100%; min-width: 0; }
    h1, h2, h3 { letter-spacing: 0; line-height: 1.08; }
    h1 { margin: 0 0 14px; font-size: clamp(32px, 5vw, 66px); max-width: 880px; }
    h2 { margin-top: 36px; border-top: 1px solid var(--line); padding-top: 24px; font-size: 26px; }
    h3 { margin-top: 24px; font-size: 19px; color: var(--accent-2); }
    p, li { color: #d6dde8; line-height: 1.65; }
    a { color: var(--accent); }
    code { background: #0a0d12; border: 1px solid var(--line); border-radius: 6px; padding: 2px 6px; color: #b9f6ea; }
    pre { background: #0a0d12; border: 1px solid var(--line); border-radius: 8px; padding: 16px; overflow: auto; max-width: 100%; }
    pre code { border: 0; padding: 0; background: transparent; }
    .diagram {
      margin: 22px 0;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, #151c27 0%, #10151d 100%);
      border-radius: 8px;
      padding: 18px;
      overflow: auto;
    }
    .diagram-title {
      color: var(--muted);
      font-size: 12px;
      letter-spacing: .12em;
      text-transform: uppercase;
      margin-bottom: 14px;
    }
    .diagram-flow {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
      gap: 12px;
      align-items: stretch;
      min-width: 0;
    }
    .diagram-level {
      display: grid;
      align-content: start;
      gap: 10px;
      position: relative;
    }
    .diagram-level:not(:last-child)::after {
      content: "";
      position: absolute;
      top: 24px;
      right: -10px;
      width: 8px;
      height: 8px;
      border-top: 2px solid var(--accent);
      border-right: 2px solid var(--accent);
      transform: rotate(45deg);
      opacity: .8;
    }
    .diagram-node {
      border: 1px solid #314056;
      background: #0d141d;
      color: var(--text);
      border-radius: 7px;
      padding: 12px 14px;
      min-width: 0;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.04);
    }
    .diagram-node strong { display: block; font-size: 13px; line-height: 1.25; }
    .diagram-node small { display: block; margin-top: 5px; color: var(--muted); font-size: 11px; }
    .diagram-links { margin-top: 9px; display: flex; flex-wrap: wrap; gap: 5px; }
    .diagram-link {
      color: var(--accent);
      background: rgba(94, 234, 212, .08);
      border: 1px solid rgba(94, 234, 212, .18);
      border-radius: 999px;
      padding: 2px 7px;
      font-size: 10.5px;
      line-height: 1.35;
    }
    .diagram-stack {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 14px;
    }
    .diagram-class {
      border: 1px solid #314056;
      background: #0d141d;
      border-radius: 8px;
      overflow: hidden;
    }
    .diagram-class h4 {
      margin: 0;
      padding: 11px 13px;
      background: #172231;
      color: var(--accent-2);
      font-size: 14px;
    }
    .diagram-class ul { list-style: none; margin: 0; padding: 10px 13px 13px; }
    .diagram-class li { color: #d6dde8; font-size: 13px; line-height: 1.5; }
    table { border-collapse: collapse; display: block; width: 100%; max-width: 100%; margin: 18px 0; background: var(--panel); border: 1px solid var(--line); overflow-x: auto; }
    th, td { border-bottom: 1px solid var(--line); padding: 11px 12px; text-align: left; vertical-align: top; }
    th { color: var(--text); background: #1a2130; }
    .brand { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; }
    .mark { width: 13px; height: 13px; background: var(--accent); box-shadow: 0 0 24px rgba(94, 234, 212, .45); }
    .title { font-weight: 700; }
    .meta { color: var(--muted); font-size: 13px; line-height: 1.5; margin-bottom: 20px; }
    .tabs { display: grid; gap: 8px; }
    button {
      border: 1px solid var(--line);
      color: var(--text);
      background: #111720;
      min-height: 42px;
      padding: 0 12px;
      text-align: left;
      border-radius: 7px;
      cursor: pointer;
      font: inherit;
    }
    button.active { border-color: var(--accent); background: #14242a; }
    button:active { transform: translateY(1px); }
    .status { margin-top: 20px; padding-top: 18px; border-top: 1px solid var(--line); color: var(--muted); font-size: 13px; }
    .doc { padding-bottom: 48px; min-width: 0; overflow-wrap: anywhere; }
    .doc blockquote { margin-left: 0; border-left: 3px solid var(--accent); padding-left: 14px; color: var(--muted); }
    @media (max-width: 860px) {
      .shell { display: block; }
      aside { position: static; height: auto; }
      main { padding-top: 20px; }
      .diagram-flow { grid-template-columns: 1fr; }
      .diagram-level:not(:last-child)::after {
        top: auto;
        right: 50%;
        bottom: -11px;
        transform: translateX(50%) rotate(135deg);
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand"><span class="mark"></span><span class="title">Jarvis Plan</span></div>
      <div class="meta">Local-only review surface. Files are served from this repo over localhost.</div>
      <div id="tabs" class="tabs"></div>
      <div id="status" class="status">Loading local plan files...</div>
    </aside>
    <main><article id="doc" class="doc"></article></main>
  </div>
  <script>
    const tabs = document.getElementById('tabs');
    const doc = document.getElementById('doc');
    const status = document.getElementById('status');

    function escapeHtml(value) {
      return value.replace(/[&<>"']/g, (ch) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[ch]));
    }

    function inline(text) {
      return escapeHtml(text)
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>');
    }

    function renderMarkdown(src) {
      const lines = src.split(/\\r?\\n/);
      let out = [];
      let inCode = false;
      let codeLang = '';
      let code = [];
      let inTable = false;
      let table = [];
      let inList = false;
      let inOrderedList = false;

      function flushCode() {
        if (code.length) {
          const raw = code.join('\\n');
          if (codeLang === 'mermaid') out.push(renderMermaid(raw));
          else out.push('<pre><code>' + escapeHtml(raw) + '</code></pre>');
        }
        code = [];
        codeLang = '';
      }
      function flushList() {
        if (inList) out.push('</ul>');
        if (inOrderedList) out.push('</ol>');
        inList = false;
        inOrderedList = false;
      }
      function flushTable() {
        if (!table.length) return;
        const rows = table.filter((row) => !/^\\s*\\|?\\s*-+/.test(row));
        out.push('<table>' + rows.map((row, idx) => {
          const cells = row.split('|').map((cell) => cell.trim()).filter(Boolean);
          const tag = idx === 0 ? 'th' : 'td';
          return '<tr>' + cells.map((cell) => `<${tag}>${inline(cell)}</${tag}>`).join('') + '</tr>';
        }).join('') + '</table>');
        table = [];
        inTable = false;
      }

      for (const line of lines) {
        if (line.startsWith('```')) {
          flushTable(); flushList();
          if (inCode) { flushCode(); inCode = false; } else { inCode = true; codeLang = line.slice(3).trim().toLowerCase(); }
          continue;
        }
        if (inCode) { code.push(line); continue; }
        if (line.includes('|') && /^\\s*\\|?.+\\|.+/.test(line)) {
          flushList(); inTable = true; table.push(line); continue;
        }
        flushTable();
        if (/^# /.test(line)) { flushList(); out.push('<h1>' + inline(line.slice(2)) + '</h1>'); continue; }
        if (/^## /.test(line)) { flushList(); out.push('<h2>' + inline(line.slice(3)) + '</h2>'); continue; }
        if (/^### /.test(line)) { flushList(); out.push('<h3>' + inline(line.slice(4)) + '</h3>'); continue; }
        if (/^- /.test(line)) {
          if (inOrderedList) { out.push('</ol>'); inOrderedList = false; }
          if (!inList) { out.push('<ul>'); inList = true; }
          out.push('<li>' + inline(line.slice(2)) + '</li>');
          continue;
        }
        if (/^\\d+\\. /.test(line)) {
          if (inList) { out.push('</ul>'); inList = false; }
          if (!inOrderedList) { out.push('<ol>'); inOrderedList = true; }
          out.push('<li>' + inline(line.replace(/^\\d+\\. /, '')) + '</li>');
          continue;
        }
        if (!line.trim()) { flushList(); continue; }
        flushList();
        out.push('<p>' + inline(line) + '</p>');
      }
      flushCode(); flushTable(); flushList();
      return out.join('\\n');
    }

    function parseNode(raw) {
      const trimmed = raw.trim();
      const match = trimmed.match(/^([A-Za-z0-9_]+)(?:\\[([^\\]]+)\\])?/);
      if (!match) return null;
      return { id: match[1], label: match[2] || match[1] };
    }

    function renderMermaid(src) {
      if (/^\\s*classDiagram/m.test(src)) return renderClassDiagram(src);
      return renderFlowDiagram(src);
    }

    function renderFlowDiagram(src) {
      const nodes = new Map();
      const edges = [];
      for (const rawLine of src.split(/\\r?\\n/)) {
        const line = rawLine.trim();
        if (!line || line.startsWith('flowchart') || line.startsWith('graph')) continue;
        if (line.includes('-->')) {
          const parts = line.split(/-->/).map((part) => part.trim());
          for (const part of parts) {
            const node = parseNode(part);
            if (node && !nodes.has(node.id)) nodes.set(node.id, node.label);
          }
          for (let i = 0; i < parts.length - 1; i++) {
            const from = parseNode(parts[i]);
            const to = parseNode(parts[i + 1]);
            if (from && to) edges.push([from.id, to.id]);
          }
          continue;
        }
        const node = parseNode(line);
        if (node && !nodes.has(node.id)) nodes.set(node.id, node.label);
      }

      if (!edges.length) {
        return '<pre><code>' + escapeHtml(src) + '</code></pre>';
      }

      const incoming = new Map();
      const outgoing = new Map();
      for (const id of nodes.keys()) {
        incoming.set(id, []);
        outgoing.set(id, []);
      }
      for (const [from, to] of edges) {
        if (!outgoing.has(from)) outgoing.set(from, []);
        if (!incoming.has(to)) incoming.set(to, []);
        outgoing.get(from).push(to);
        incoming.get(to).push(from);
      }

      const levels = new Map();
      for (const id of nodes.keys()) levels.set(id, 0);
      for (let pass = 0; pass < nodes.size + edges.length; pass++) {
        let changed = false;
        for (const [from, to] of edges) {
          const nextLevel = (levels.get(from) || 0) + 1;
          if (nextLevel > (levels.get(to) || 0)) {
            levels.set(to, nextLevel);
            changed = true;
          }
        }
        if (!changed) break;
      }

      const columns = [];
      for (const id of nodes.keys()) {
        const level = levels.get(id) || 0;
        if (!columns[level]) columns[level] = [];
        columns[level].push(id);
      }

      const htmlColumns = columns.filter(Boolean).map((ids) => {
        const cards = ids.map((id) => {
        const label = nodes.get(id) || id;
          const links = (outgoing.get(id) || [])
            .map((target) => `<span class="diagram-link">to ${escapeHtml(nodes.get(target) || target)}</span>`)
            .join('');
          return `<div class="diagram-node"><strong>${inline(label)}</strong><small>${escapeHtml(id)}</small>${links ? `<div class="diagram-links">${links}</div>` : ''}</div>`;
        }).join('');
        return `<div class="diagram-level">${cards}</div>`;
      }).join('');
      return '<section class="diagram"><div class="diagram-title">Mermaid Flow</div><div class="diagram-flow">' + htmlColumns + '</div></section>';
    }

    function renderClassDiagram(src) {
      const classes = [];
      let active = null;
      for (const rawLine of src.split(/\\r?\\n/)) {
        const line = rawLine.trim();
        if (!line || line === 'classDiagram' || line.includes('-->')) continue;
        const classMatch = line.match(/^class\\s+([A-Za-z0-9_]+)\\s*\\{?/);
        if (classMatch) {
          active = { name: classMatch[1], fields: [] };
          classes.push(active);
          continue;
        }
        if (line === '}') { active = null; continue; }
        if (active) active.fields.push(line);
      }
      if (!classes.length) {
        return '<pre><code>' + escapeHtml(src) + '</code></pre>';
      }
      const body = classes.map((item) => {
        const fields = item.fields.map((field) => '<li>' + inline(field) + '</li>').join('');
        return `<div class="diagram-class"><h4>${escapeHtml(item.name)}</h4><ul>${fields}</ul></div>`;
      }).join('');
      return '<section class="diagram"><div class="diagram-title">Mermaid Class Map</div><div class="diagram-stack">' + body + '</div></section>';
    }

    async function loadFile(file, button) {
      for (const item of tabs.querySelectorAll('button')) item.classList.remove('active');
      button.classList.add('active');
      const res = await fetch('/api/file/' + encodeURIComponent(file));
      const text = await res.text();
      doc.innerHTML = renderMarkdown(text);
      status.textContent = file + ' loaded from localhost';
    }

    async function boot() {
      const res = await fetch('/api/files');
      const files = await res.json();
      tabs.innerHTML = '';
      for (const file of files) {
        const button = document.createElement('button');
        button.textContent = file;
        button.addEventListener('click', () => loadFile(file, button));
        tabs.appendChild(button);
      }
      if (files[0]) await loadFile(files[0], tabs.querySelector('button'));
      else status.textContent = 'No MDX files found.';
    }
    boot().catch((err) => { status.textContent = err.message; });
  </script>
</body>
</html>
"""


class PlanViewerHandler(BaseHTTPRequestHandler):
    plan_dir: Path

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self._send(200, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if parsed.path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
            return
        if parsed.path == "/api/files":
            files = sorted(path.name for path in self.plan_dir.glob("*.mdx"))
            self._send(200, json.dumps(files).encode("utf-8"), "application/json")
            return
        if parsed.path.startswith("/api/file/"):
            name = unquote(parsed.path.removeprefix("/api/file/"))
            if "/" in name or "\\" in name:
                self._send(400, b"invalid file name", "text/plain")
                return
            path = self.plan_dir / name
            if path.suffix != ".mdx" or not path.exists():
                self._send(404, b"not found", "text/plain")
                return
            self._send(200, path.read_bytes(), mimetypes.types_map.get(".md", "text/markdown"))
            return
        self._send(404, b"not found", "text/plain")

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(prog="jarvis-plan-viewer")
    parser.add_argument("--dir", default="plans/jarvis-codex-swarm", help="Plan directory containing .mdx files")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8765, help="Bind port")
    args = parser.parse_args()

    plan_dir = Path(args.dir).resolve()
    if not plan_dir.exists():
        parser.error(f"plan directory does not exist: {html.escape(str(plan_dir))}")
    PlanViewerHandler.plan_dir = plan_dir
    server = ThreadingHTTPServer((args.host, args.port), PlanViewerHandler)
    print(f"Jarvis local plan viewer: http://{args.host}:{args.port}")
    print(f"Serving: {plan_dir}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

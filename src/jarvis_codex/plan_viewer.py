from __future__ import annotations

import argparse
import html
import json
import mimetypes
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


SAFE_STEP_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}$")


def next_steps_state_path(state_dir: Path) -> Path:
    return state_dir / "next-steps" / "selection.json"


def load_next_steps_selection(state_dir: Path) -> dict[str, object]:
    path = next_steps_state_path(state_dir)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"selected": [], "brief": "", "updated_at": None}
    selected = raw.get("selected", [])
    if not isinstance(selected, list):
        selected = []
    safe_selected = [item for item in selected if isinstance(item, str) and SAFE_STEP_ID.match(item)]
    brief = raw.get("brief", "")
    return {
        "selected": safe_selected,
        "brief": brief if isinstance(brief, str) else "",
        "updated_at": raw.get("updated_at") if isinstance(raw.get("updated_at"), int) else None,
    }


def save_next_steps_selection(state_dir: Path, selected: list[object], brief: object = "") -> dict[str, object]:
    safe_selected = [item for item in selected if isinstance(item, str) and SAFE_STEP_ID.match(item)]
    data = {
        "selected": safe_selected,
        "brief": brief if isinstance(brief, str) else "",
        "updated_at": int(time.time()),
    }
    path = next_steps_state_path(state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data


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
      --warn: #fbbf24;
      --danger: #fb7185;
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
    button.primary {
      border-color: rgba(94, 234, 212, .7);
      background: var(--accent);
      color: #061014;
      font-weight: 700;
      text-align: center;
    }
    button.secondary { text-align: center; }
    button.filter {
      min-height: 34px;
      padding: 0 10px;
      font-size: 13px;
      text-align: center;
    }
    button.filter.active { color: #061014; background: var(--accent); }
    .status { margin-top: 20px; padding-top: 18px; border-top: 1px solid var(--line); color: var(--muted); font-size: 13px; }
    .doc { padding-bottom: 48px; min-width: 0; overflow-wrap: anywhere; }
    .doc blockquote { margin-left: 0; border-left: 3px solid var(--accent); padding-left: 14px; color: var(--muted); }
    .next-shell { display: grid; gap: 24px; padding-bottom: 48px; }
    .next-header { display: grid; gap: 14px; max-width: 900px; }
    .next-header h1 { margin-bottom: 0; }
    .next-header p { margin: 0; max-width: 68ch; }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }
    .metric {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 14px;
      min-width: 0;
    }
    .metric strong { display: block; font-size: 25px; line-height: 1; }
    .metric span { display: block; margin-top: 7px; color: var(--muted); font-size: 12px; line-height: 1.35; }
    .toolbar {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
      border-top: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      padding: 14px 0;
    }
    .step-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(280px, .8fr);
      gap: 18px;
      align-items: start;
    }
    .step-list {
      display: grid;
      gap: 10px;
      min-width: 0;
    }
    .step-row {
      display: grid;
      grid-template-columns: 28px minmax(0, 1fr) auto;
      gap: 12px;
      align-items: start;
      border: 1px solid var(--line);
      background: #111720;
      border-radius: 8px;
      padding: 14px;
    }
    .step-row.selected { border-color: rgba(94, 234, 212, .75); background: #122126; }
    .step-row input {
      width: 18px;
      height: 18px;
      margin-top: 3px;
      accent-color: var(--accent);
    }
    .step-body { min-width: 0; }
    .step-title { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
    .step-title strong { font-size: 15px; line-height: 1.3; }
    .step-body p { margin: 7px 0 0; color: #c5cedb; font-size: 13px; line-height: 1.5; }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 0 8px;
      color: var(--muted);
      font-size: 11px;
      line-height: 1;
      white-space: nowrap;
    }
    .badge.ready { border-color: rgba(94, 234, 212, .35); color: var(--accent); }
    .badge.gated { border-color: rgba(251, 191, 36, .35); color: var(--warn); }
    .badge.risk { border-color: rgba(251, 113, 133, .35); color: var(--danger); }
    .step-meta { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
    .priority { color: var(--accent-2); font-size: 12px; line-height: 1.4; white-space: nowrap; }
    .proceed-panel {
      position: sticky;
      top: 24px;
      display: grid;
      gap: 12px;
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 16px;
      min-width: 0;
    }
    .proceed-panel h2 {
      margin: 0;
      border: 0;
      padding: 0;
      font-size: 21px;
    }
    .proceed-panel p { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.5; }
    .brief {
      width: 100%;
      min-height: 230px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #0a0d12;
      color: var(--text);
      padding: 12px;
      font: 13px/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .empty-note {
      border: 1px dashed #3a4659;
      border-radius: 8px;
      padding: 18px;
      color: var(--muted);
      background: #10151d;
    }
    @media (max-width: 860px) {
      .shell { display: block; }
      aside { position: static; height: auto; }
      main { padding-top: 20px; }
      .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .step-grid { grid-template-columns: 1fr; }
      .proceed-panel { position: static; }
      .step-row { grid-template-columns: 28px minmax(0, 1fr); }
      .priority { grid-column: 2; }
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
    const STORAGE_KEY = 'jarvis-next-step-selection';
    let serverSelected = new Set();
    const NEXT_STEPS = [
      {
        id: 'commit-push-baseline',
        title: 'Push Gate 2 baseline',
        category: 'Git',
        status: 'gated',
        priority: 'P0',
        summary: 'Push the committed local viewer baseline after confirming the remote target and branch policy.',
        owner: 'main thread',
        command: 'git push origin main'
      },
      {
        id: 'refresh-worktrunk-lanes',
        title: 'Refresh Worktrunk lanes',
        category: 'Worktrunk',
        status: 'gated',
        priority: 'P0',
        summary: 'Inspect each lane worktree, decide hold or abandon, then refresh only after explicit approval.',
        owner: 'worktree coordinator',
        command: 'git worktree list'
      },
      {
        id: 'voice-notification-hardening',
        title: 'Harden voice notification hooks',
        category: 'Voice',
        status: 'ready',
        priority: 'P1',
        summary: 'Move the hook classification helpers toward reusable tests and document the speech defaults.',
        owner: 'local AI OS hooks',
        command: 'python3 ~/.codex/bin/codex_notify_jarvis.py --test'
      },
      {
        id: 'viewer-selection-persistence',
        title: 'Persist selected next steps',
        category: 'UI',
        status: 'ready',
        priority: 'P1',
        summary: 'Promote browser-only selections into a local state file when a durable queue is approved.',
        owner: 'viewer UI',
        command: 'uv run jarvis-plan-viewer --dir plans/jarvis-codex-swarm'
      },
      {
        id: 'hardware-runtime-gate',
        title: 'Define hardware runtime gates',
        category: 'Hardware',
        status: 'ready',
        priority: 'P1',
        summary: 'Turn CUDA, Docker, and NPU detection into explicit workload gate checks before heavy local runs.',
        owner: 'runtime boundary',
        command: 'uv run jarvis-codex hardware --workload video'
      },
      {
        id: 'remotion-review-gate',
        title: 'Plan Remotion review assets',
        category: 'Remotion',
        status: 'gated',
        priority: 'P2',
        summary: 'Define local-only video review assets, storage boundaries, and browser verification before generation.',
        owner: 'visual review lane',
        command: 'pending local-only Remotion gate'
      },
      {
        id: 'codex-bridge-contract',
        title: 'Revisit Codex bridge contract',
        category: 'Bridge',
        status: 'risk',
        priority: 'P2',
        summary: 'Review bridge scope before adding execution adapters so tool use remains approval-aware.',
        owner: 'codex bridge lane',
        command: 'uv run jarvis-codex handoff --objective "Review Codex bridge contract"'
      }
    ];

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

    function selection() {
      if (serverSelected.size) return new Set(serverSelected);
      try {
        const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        return new Set(Array.isArray(parsed) ? parsed : []);
      } catch {
        return new Set();
      }
    }

    async function loadServerSelection() {
      try {
        const res = await fetch('/api/next-steps');
        if (!res.ok) throw new Error('selection unavailable');
        const data = await res.json();
        const selected = Array.isArray(data.selected) ? data.selected : [];
        serverSelected = new Set(selected);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(selected));
      } catch {
        serverSelected = selection();
      }
    }

    async function saveSelection(ids, brief = '') {
      const selected = [...ids];
      serverSelected = new Set(selected);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(selected));
      try {
        const res = await fetch('/api/next-steps', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ selected, brief }),
        });
        if (!res.ok) throw new Error('save failed');
        status.textContent = 'Next steps saved locally';
      } catch {
        status.textContent = 'Next steps saved in this browser';
      }
    }

    function selectedSteps() {
      const ids = selection();
      return NEXT_STEPS.filter((step) => ids.has(step.id));
    }

    function categoryCounts() {
      const selected = selectedSteps();
      return {
        selected: selected.length,
        gated: selected.filter((step) => step.status === 'gated').length,
        ready: selected.filter((step) => step.status === 'ready').length,
        risk: selected.filter((step) => step.status === 'risk').length,
      };
    }

    function buildProceedBrief(steps) {
      if (!steps.length) return 'Select one or more next steps to build a proceed brief.';
      return [
        '# Proceed Brief',
        '',
        'Selected next steps:',
        ...steps.map((step, index) => `${index + 1}. ${step.title} [${step.priority}, ${step.status}]`),
        '',
        'Execution notes:',
        ...steps.map((step) => `- ${step.title}: ${step.summary} Owner: ${step.owner}. Check: ${step.command}`),
        '',
        'Boundaries:',
        '- Ask before push, merge, rebase, branch deletion, worktree removal, hook edits, shell integration, or GPU/Docker execution.',
        '- Keep generated runtime state out of Git.',
      ].join('\\n');
    }

    function renderNextSteps(activeCategory = 'All') {
      for (const item of tabs.querySelectorAll('button')) item.classList.remove('active');
      const nextButton = tabs.querySelector('[data-view="next-steps"]');
      if (nextButton) nextButton.classList.add('active');
      const ids = selection();
      const categories = ['All', ...new Set(NEXT_STEPS.map((step) => step.category))];
      const steps = activeCategory === 'All' ? NEXT_STEPS : NEXT_STEPS.filter((step) => step.category === activeCategory);
      const counts = categoryCounts();
      doc.innerHTML = `
        <section class="next-shell">
          <div class="next-header">
            <h1>Next Steps</h1>
            <p>Select the work you want to proceed with and use the generated brief as the handoff for the next Codex pass.</p>
          </div>
          <div class="summary-grid" aria-live="polite">
            <div class="metric"><strong>${counts.selected}</strong><span>selected</span></div>
            <div class="metric"><strong>${counts.ready}</strong><span>ready</span></div>
            <div class="metric"><strong>${counts.gated}</strong><span>approval gated</span></div>
            <div class="metric"><strong>${counts.risk}</strong><span>needs review</span></div>
          </div>
          <div class="toolbar">
            ${categories.map((category) => `<button class="filter ${category === activeCategory ? 'active' : ''}" data-category="${escapeHtml(category)}">${escapeHtml(category)}</button>`).join('')}
          </div>
          <div class="step-grid">
            <div class="step-list">
              ${steps.map((step) => `
                <label class="step-row ${ids.has(step.id) ? 'selected' : ''}">
                  <input type="checkbox" data-step="${escapeHtml(step.id)}" ${ids.has(step.id) ? 'checked' : ''} />
                  <span class="step-body">
                    <span class="step-title"><strong>${escapeHtml(step.title)}</strong><span class="badge ${escapeHtml(step.status)}">${escapeHtml(step.status)}</span></span>
                    <p>${escapeHtml(step.summary)}</p>
                    <span class="step-meta">
                      <span class="badge">${escapeHtml(step.category)}</span>
                      <span class="badge">${escapeHtml(step.owner)}</span>
                    </span>
                  </span>
                  <span class="priority">${escapeHtml(step.priority)}</span>
                </label>
              `).join('') || '<div class="empty-note">No steps match this filter.</div>'}
            </div>
            <aside class="proceed-panel">
              <h2>Proceed Brief</h2>
              <p>${counts.selected ? `${counts.selected} step${counts.selected === 1 ? '' : 's'} selected.` : 'No steps selected.'}</p>
              <textarea class="brief" id="proceedBrief" readonly>${escapeHtml(buildProceedBrief(selectedSteps()))}</textarea>
              <button class="primary" id="copyBrief">Copy Brief</button>
              <button class="secondary" id="clearSelection">Clear Selection</button>
            </aside>
          </div>
        </section>
      `;
      status.textContent = 'Next steps ready';
      for (const button of doc.querySelectorAll('[data-category]')) {
        button.addEventListener('click', () => renderNextSteps(button.dataset.category || 'All'));
      }
      for (const input of doc.querySelectorAll('[data-step]')) {
        input.addEventListener('change', () => {
          const next = selection();
          if (input.checked) next.add(input.dataset.step);
          else next.delete(input.dataset.step);
          saveSelection(next, buildProceedBrief(NEXT_STEPS.filter((step) => next.has(step.id))));
          renderNextSteps(activeCategory);
        });
      }
      doc.querySelector('#clearSelection').addEventListener('click', () => {
        saveSelection(new Set());
        renderNextSteps(activeCategory);
      });
      doc.querySelector('#copyBrief').addEventListener('click', async () => {
        const brief = doc.querySelector('#proceedBrief').value;
        try {
          await navigator.clipboard.writeText(brief);
          status.textContent = 'Proceed brief copied';
        } catch {
          status.textContent = 'Proceed brief ready to copy';
        }
      });
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
      await loadServerSelection();
      tabs.innerHTML = '';
      const nextSteps = document.createElement('button');
      nextSteps.textContent = 'Next steps';
      nextSteps.dataset.view = 'next-steps';
      nextSteps.addEventListener('click', () => renderNextSteps());
      tabs.appendChild(nextSteps);
      for (const file of files) {
        const button = document.createElement('button');
        button.textContent = file;
        button.dataset.view = 'file';
        button.addEventListener('click', () => loadFile(file, button));
        tabs.appendChild(button);
      }
      renderNextSteps();
    }
    boot().catch((err) => { status.textContent = err.message; });
  </script>
</body>
</html>
"""


class PlanViewerHandler(BaseHTTPRequestHandler):
    plan_dir: Path
    state_dir: Path

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
        if parsed.path == "/api/next-steps":
            data = load_next_steps_selection(self.state_dir)
            self._send(200, json.dumps(data).encode("utf-8"), "application/json")
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

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/next-steps":
            self._send(404, b"not found", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length > 20000:
            self._send(413, b"payload too large", "text/plain")
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send(400, b"invalid json", "text/plain")
            return
        if not isinstance(payload, dict):
            self._send(400, b"invalid payload", "text/plain")
            return
        selected = payload.get("selected", [])
        if not isinstance(selected, list):
            self._send(400, b"selected must be a list", "text/plain")
            return
        try:
            data = save_next_steps_selection(self.state_dir, selected, payload.get("brief", ""))
        except OSError:
            self._send(500, b"could not save selection", "text/plain")
            return
        self._send(200, json.dumps(data).encode("utf-8"), "application/json")

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
    parser.add_argument("--state", default="state", help="State directory for local viewer selections")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8765, help="Bind port")
    args = parser.parse_args()

    plan_dir = Path(args.dir).resolve()
    if not plan_dir.exists():
        parser.error(f"plan directory does not exist: {html.escape(str(plan_dir))}")
    PlanViewerHandler.plan_dir = plan_dir
    PlanViewerHandler.state_dir = Path(args.state).resolve()
    server = ThreadingHTTPServer((args.host, args.port), PlanViewerHandler)
    print(f"Jarvis local plan viewer: http://{args.host}:{args.port}")
    print(f"Serving: {plan_dir}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

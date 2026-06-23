from __future__ import annotations


HUD_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "connect-src 'self' ws: wss:; "
    "media-src 'self' blob:; "
    "object-src 'none'; "
    "base-uri 'none'; "
    "frame-ancestors 'none'"
)


HUD_MANIFEST = """{
  "name": "Jarvis Harness",
  "short_name": "Jarvis",
  "description": "Private-network Jarvis harness for Codex, Antigravity, voice, approvals, and telemetry.",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "background_color": "#02050a",
  "theme_color": "#06131d",
  "icons": [
    {
      "src": "/assets/icon.svg",
      "sizes": "any",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    }
  ]
}
"""


HUD_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="96" fill="#02050a"/>
  <circle cx="256" cy="256" r="180" fill="none" stroke="#4cdcff" stroke-width="16"/>
  <circle cx="256" cy="256" r="112" fill="none" stroke="#64f2af" stroke-width="12" stroke-dasharray="24 18"/>
  <circle cx="256" cy="256" r="48" fill="#4cdcff"/>
  <path d="M256 76v62M256 374v62M76 256h62M374 256h62" stroke="#e7faff" stroke-width="18" stroke-linecap="round"/>
</svg>
"""


HUD_SERVICE_WORKER = r"""const CACHE_NAME = "jarvis-hud-v1";
const PRECACHE = ["/", "/assets/hud.js", "/manifest.webmanifest", "/assets/icon.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.pathname === "/rpc" || url.pathname === "/ws") {
    return;
  }
  if (!PRECACHE.includes(url.pathname)) {
    return;
  }
  event.respondWith(caches.match(request).then((cached) => cached || fetch(request)));
});
"""


HUD_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#06131d">
  <meta name="jarvis-runtime-token" content="__JARVIS_RUNTIME_TOKEN__">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="Jarvis">
  <link rel="manifest" href="/manifest.webmanifest">
  <link rel="icon" href="/assets/icon.svg" type="image/svg+xml">
  <title>Jarvis Harness</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #03070d;
      --panel: rgba(8, 24, 34, 0.82);
      --panel-strong: rgba(6, 48, 68, 0.86);
      --line: rgba(76, 220, 255, 0.42);
      --line-soft: rgba(76, 220, 255, 0.2);
      --text: #e7faff;
      --muted: #86aebc;
      --cyan: #4cdcff;
      --green: #64f2af;
      --amber: #ffc65c;
      --red: #ff6b7a;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      height: 100vh;
      overflow: hidden;
      background:
        radial-gradient(circle at 50% 18%, rgba(44, 188, 255, 0.2), transparent 24%),
        radial-gradient(circle at 80% 70%, rgba(65, 255, 197, 0.1), transparent 22%),
        linear-gradient(145deg, #02050a 0%, #06131d 52%, #02050a 100%);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }

    .scan {
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(76, 220, 255, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(76, 220, 255, 0.04) 1px, transparent 1px);
      background-size: 38px 38px;
      mask-image: radial-gradient(circle, black 18%, transparent 78%);
    }

    .shell {
      position: relative;
      z-index: 1;
      width: min(1680px, calc(100% - 24px));
      height: 100vh;
      margin: 0 auto;
      padding: 12px 0;
      display: grid;
      grid-template-rows: auto auto minmax(0, 1fr);
      gap: 12px;
    }

    header {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      align-items: center;
      border-bottom: 1px solid var(--line);
      padding-bottom: 10px;
    }

    h1 {
      margin: 0;
      color: var(--cyan);
      font-size: clamp(28px, 3vw, 48px);
      line-height: 0.92;
      text-transform: uppercase;
    }

    .subtitle {
      margin: 6px 0 0;
      color: var(--muted);
      max-width: 820px;
      line-height: 1.35;
      font-size: 14px;
    }

    .core {
      width: 96px;
      aspect-ratio: 1;
      border: 1px solid var(--line);
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: radial-gradient(circle, rgba(76, 220, 255, 0.22), transparent 64%);
      position: relative;
    }

    .core:before,
    .core:after {
      content: "";
      position: absolute;
      border-radius: 50%;
      border: 1px dashed rgba(76, 220, 255, 0.48);
    }

    .core:before { inset: 18px; }
    .core:after { inset: 44px; border-style: solid; border-color: rgba(100, 242, 175, 0.55); }

    .core span {
      position: relative;
      text-align: center;
      color: var(--green);
      text-transform: uppercase;
      font-size: 12px;
      line-height: 1.45;
    }

    .core strong {
      display: block;
      color: var(--text);
      font-size: 18px;
    }

    .app-layout {
      display: grid;
      grid-template-columns: 214px minmax(0, 1fr);
      gap: 12px;
      min-height: 0;
    }

    .nav-pane {
      border: 1px solid var(--line);
      background: rgba(1, 13, 20, 0.84);
      padding: 10px;
      display: grid;
      grid-template-rows: auto 1fr auto;
      gap: 10px;
      min-height: 0;
    }

    .nav-title {
      color: var(--cyan);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .nav-list {
      display: grid;
      align-content: start;
      gap: 8px;
      min-height: 0;
    }

    .nav-button {
      width: 100%;
      min-height: 44px;
      text-align: left;
      display: grid;
      gap: 2px;
    }

    .nav-button small {
      display: block;
      color: var(--muted);
      font-weight: 600;
    }

    .nav-button.active {
      border-color: rgba(100, 242, 175, 0.8);
      background: rgba(100, 242, 175, 0.14);
      color: var(--green);
    }

    .nav-help {
      min-height: 0;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.45;
      border-top: 1px solid var(--line-soft);
      padding-top: 10px;
    }

    .operator-command {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) auto auto auto;
      gap: 8px;
      align-items: center;
      border: 1px solid var(--line);
      background: rgba(1, 13, 20, 0.86);
      padding: 10px;
      min-width: 0;
    }

    .operator-command label {
      color: var(--green);
      font-weight: 900;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      white-space: nowrap;
    }

    .operator-command input {
      min-width: 0;
    }

    .operator-command-status {
      grid-column: 2 / -1;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }

    .page-stack {
      min-height: 0;
      overflow: hidden;
    }

    .page {
      display: none;
      height: 100%;
      min-height: 0;
      overflow: auto;
      padding-right: 6px;
    }

    .page.active {
      display: grid;
      gap: 12px;
      align-content: start;
    }

    .page-grid {
      display: grid;
      grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
      gap: 12px;
      min-height: 0;
      align-items: start;
    }

    .flow-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      align-items: start;
    }

    .control-grid {
      display: grid;
      gap: 10px;
    }

    .panel {
      border: 1px solid var(--line);
      background: var(--panel);
      box-shadow: 0 0 34px rgba(76, 220, 255, 0.07);
      min-width: 0;
      min-height: 0;
    }

    .panel h2 {
      margin: 0;
      padding: 13px 14px;
      border-bottom: 1px solid var(--line-soft);
      color: var(--cyan);
      font-size: 14px;
      text-transform: uppercase;
    }

    .panel-body {
      padding: 14px;
      min-height: 0;
    }

    .status-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .metric {
      border: 1px solid var(--line-soft);
      padding: 12px;
      min-height: 86px;
      background: rgba(1, 13, 20, 0.74);
    }

    .metric small {
      color: var(--muted);
      text-transform: uppercase;
      font-size: 11px;
    }

    .metric strong {
      display: block;
      margin-top: 6px;
      font-size: 22px;
      color: var(--text);
    }

    .pane-list {
      display: grid;
      gap: 10px;
    }

    .agent-pane {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      align-items: center;
      border: 1px solid var(--line-soft);
      background: rgba(1, 13, 20, 0.72);
      padding: 12px;
    }

    .agent-pane strong {
      display: block;
      color: var(--text);
      font-size: 15px;
    }

    .agent-pane span {
      color: var(--muted);
      font-size: 12px;
    }

    button {
      appearance: none;
      border: 1px solid var(--line);
      background: rgba(76, 220, 255, 0.08);
      color: var(--text);
      min-height: 38px;
      padding: 0 14px;
      font-weight: 650;
      cursor: pointer;
    }

    button:hover { background: rgba(76, 220, 255, 0.16); }
    button.danger { border-color: rgba(255, 107, 122, 0.5); }

    .console {
      max-height: 42vh;
      overflow: auto;
      padding: 14px;
      background: #02070d;
      border-top: 1px solid var(--line-soft);
      font: 13px/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      color: #c6f7ff;
      white-space: pre-wrap;
    }

    .terminal-board {
      display: grid;
      gap: 10px;
    }

    .terminal-panel {
      grid-column: 1 / -1;
    }

    .terminal-pane {
      border: 1px solid rgba(100, 242, 175, 0.34);
      background: #01060a;
      min-height: 178px;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
    }

    .terminal-pane header {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      padding: 10px 12px;
      border-bottom: 1px solid var(--line-soft);
      align-items: center;
    }

    .terminal-pane strong {
      color: var(--green);
      font-size: 13px;
      overflow-wrap: anywhere;
    }

    .terminal-pane small {
      color: var(--muted);
      overflow-wrap: anywhere;
    }

    .terminal-output {
      min-height: 140px;
      max-height: 42vh;
      overflow: auto;
      margin: 0;
      padding: 12px;
      color: #d9faff;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font: 13px/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }

    .voice {
      display: grid;
      gap: 12px;
    }

    .voice-button {
      min-height: 74px;
      border-radius: 50%;
      aspect-ratio: 1;
      justify-self: center;
      width: 120px;
      border: 1px solid rgba(100, 242, 175, 0.7);
      background: radial-gradient(circle, rgba(100, 242, 175, 0.18), rgba(76, 220, 255, 0.08));
      color: var(--green);
      text-transform: uppercase;
    }

    .voice-button.active {
      color: var(--amber);
      border-color: rgba(255, 198, 92, 0.85);
    }

    .log {
      min-height: 86px;
      max-height: 34vh;
      overflow: auto;
      border: 1px solid var(--line-soft);
      padding: 12px;
      color: var(--muted);
      background: rgba(1, 13, 20, 0.74);
      line-height: 1.5;
    }

    select,
    input,
    textarea {
      width: 100%;
      min-height: 38px;
      border: 1px solid var(--line-soft);
      background: rgba(1, 13, 20, 0.88);
      color: var(--text);
      padding: 9px 10px;
      font: inherit;
    }

    textarea {
      resize: vertical;
    }

    .quick-start {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }

    .quick-step {
      border: 1px solid var(--line-soft);
      background: rgba(1, 13, 20, 0.74);
      padding: 12px;
      color: var(--muted);
      line-height: 1.4;
    }

    .quick-step strong {
      display: block;
      color: var(--text);
      margin-bottom: 6px;
    }

    @media (max-width: 1000px) {
      header,
      .app-layout,
      .operator-command,
      .page-grid,
      .flow-grid,
      .quick-start {
        grid-template-columns: 1fr;
      }

      .operator-command-status {
        grid-column: 1;
      }

      .shell {
        height: 100vh;
      }

      .nav-pane {
        position: sticky;
        top: 0;
        z-index: 3;
      }

      .nav-list {
        display: flex;
        gap: 8px;
        overflow-x: auto;
      }

      .nav-button {
        min-width: 148px;
      }

      .core {
        width: 108px;
      }
    }
  </style>
</head>
<body>
  <div class="scan"></div>
  <main class="shell">
    <header>
      <div>
        <h1>Jarvis Harness</h1>
        <p class="subtitle">
          Local command center for Codex, Antigravity, Codeburn, approvals, voice input, and runtime-supervised PTY panes.
          Commands are routed through the Jarvis runtime policy layer before execution.
        </p>
      </div>
      <div class="core" aria-label="runtime core status"><span><strong>ONLINE</strong>Runtime Core</span></div>
    </header>

    <section class="operator-command" aria-label="Jarvis operator command line">
      <label for="shell-command-input">Jarvis&gt;</label>
      <input id="shell-command-input" type="text" autocomplete="off" placeholder="Type intent. Enter records; no execution.">
      <button id="shell-command-record" type="button">Record Intent</button>
      <button id="shell-command-create" type="button">New Session</button>
      <button id="shell-command-voice" type="button">Voice</button>
      <div id="shell-command-status" class="operator-command-status">Shell input is state-only. Create or select a session, then record intent or use Voice for microphone input.</div>
    </section>

    <section class="app-layout" aria-label="Jarvis workspace">
      <nav class="nav-pane" aria-label="Jarvis pages">
        <div class="nav-title">Operator Navigation</div>
        <div class="nav-list" role="tablist" aria-label="Jarvis page tabs">
          <button class="nav-button active" type="button" role="tab" aria-selected="true" data-page-target="overview">Overview<small>Status and panes</small></button>
          <button class="nav-button" type="button" role="tab" aria-selected="false" data-page-target="voice">Voice<small>Mic and speech</small></button>
          <button class="nav-button" type="button" role="tab" aria-selected="false" data-page-target="session">Session<small>Prompt history</small></button>
          <button class="nav-button" type="button" role="tab" aria-selected="false" data-page-target="swarm">Swarm<small>Plans and launches</small></button>
          <button class="nav-button" type="button" role="tab" aria-selected="false" data-page-target="loop">Loop<small>Lifecycle and commands</small></button>
          <button class="nav-button" type="button" role="tab" aria-selected="false" data-page-target="release">Release<small>Gates and evidence</small></button>
        </div>
        <div class="nav-help">Use pages like a shell workspace: speak or type an intent, record state, request approvals, then launch only through approved runtime controls.</div>
      </nav>

      <div class="page-stack">
        <section id="page-overview" class="page active" data-page="overview" aria-label="Overview page">
          <div class="quick-start">
            <div class="quick-step"><strong>1. Create or select a session</strong>Session state keeps prompts, approvals, and lifecycle records together.</div>
            <div class="quick-step"><strong>2. Speak or type intent</strong>Voice and prompt records do not execute commands by themselves.</div>
            <div class="quick-step"><strong>3. Approve exact actions</strong>Only approval-gated runtime controls can launch supervised PTYs.</div>
          </div>
          <div class="page-grid">
            <div class="panel">
              <h2>Runtime Status</h2>
              <div class="panel-body status-grid">
                <div class="metric"><small>Socket</small><strong id="socket-status">offline</strong></div>
                <div class="metric"><small>Policy</small><strong>gated</strong></div>
                <div class="metric"><small>Voice</small><strong id="voice-status">idle</strong></div>
                <div class="metric"><small>Approvals</small><strong id="approval-count">0</strong></div>
                <div class="metric"><small>Agents</small><strong id="agent-provider-status">unknown</strong></div>
                <div class="metric"><small>Codeburn</small><strong id="codeburn-status">unknown</strong></div>
                <div class="metric"><small>PWA</small><strong id="pwa-status">checking</strong></div>
                <div class="metric"><small>Readiness</small><strong id="readiness-status">unknown</strong></div>
                <div class="metric"><small>Mobile</small><strong id="mobile-access-status">unknown</strong></div>
                <div class="metric"><small>Release Gates</small><strong id="release-gate-status">unknown</strong></div>
                <div class="metric"><small>Release Plan</small><strong id="release-checklist-status">unknown</strong></div>
              </div>
            </div>

            <div class="panel">
              <h2>Harness Panes</h2>
              <div class="panel-body pane-list">
                <div class="agent-pane"><div><strong>Codex</strong><span>Implementation and verification lane</span></div><button data-pane="codex">Prepare</button></div>
                <div class="agent-pane"><div><strong>Antigravity</strong><span>Architecture and adversarial review lane</span></div><button data-pane="antigravity">Prepare</button></div>
                <div class="agent-pane"><div><strong>AG Challenge</strong><span>Approval-only adversarial review brief</span></div><button id="request-ag-challenge-approval" type="button">Challenge</button></div>
                <div class="agent-pane"><div><strong>Codeburn</strong><span>Fixed no-shell usage telemetry lane</span></div><button id="refresh-codeburn" type="button">Status</button></div>
              </div>
              <div id="agent-provider-list" class="log">Agent provider readiness pending. Status checks do not launch providers.</div>
              <textarea id="ag-challenge-brief" rows="3" placeholder="Antigravity challenge brief. Example: Review this plan for hidden release, safety, and architecture risks."></textarea>
              <div id="ag-challenge-status" class="log">Antigravity challenge requests are approval-only. They do not launch AG, Codex, PTYs, Worktrunk, shell commands, services, or workflows.</div>
              <div id="console" class="console" aria-live="polite">Jarvis runtime console ready.</div>
            </div>

            <div class="panel terminal-panel">
              <h2>Live Backend Terminal</h2>
              <div id="terminal-panes" class="panel-body terminal-board" aria-live="polite">
                <div class="log">Runtime-supervised PTY output will appear here by channel after an approved launch.</div>
              </div>
            </div>
          </div>
        </section>

        <section id="page-voice" class="page" data-page="voice" aria-label="Voice page">
          <div class="panel">
            <h2>Voice Control</h2>
            <div class="panel-body voice">
              <button id="mic-toggle" class="voice-button" type="button">Mic</button>
              <button id="speak-status" type="button">Speak Status</button>
              <input id="stt-model-id" type="text" value="tiny.en" aria-label="Local STT model id">
              <button id="request-transcription-approval" type="button">Request Audio Transcription Approval</button>
              <input id="stt-approval-id" type="text" placeholder="Paste approved audio transcription approval id">
              <button id="transcribe-captured-audio" type="button">Transcribe Approved Audio</button>
              <div id="voice-log" class="log">Microphone is disabled until you click the button and approve browser permission.</div>
              <div id="proposal-preview" class="log">Voice intent proposals will appear here. They do not execute commands.</div>
              <button id="request-proposal-approval" type="button">Request Proposal Approval</button>
              <button id="refresh-approvals" type="button">Refresh Approvals</button>
              <div id="approvals-list" class="log">No pending approvals loaded.</div>
              <div id="approved-launches" class="log">Approved pane launches will appear here after approval.</div>
            </div>
          </div>
        </section>

        <section id="page-session" class="page" data-page="session" aria-label="Session page">
          <div class="panel">
            <h2>Session Continuity</h2>
            <div class="panel-body control-grid">
              <div class="agent-pane">
                <div><strong id="active-session">No active session selected</strong><span>Session context is local to this HUD until selected or created.</span></div>
                <div>
                  <select id="session-profile" aria-label="Session policy profile"></select>
                  <button id="create-session" type="button">Create HUD Session</button>
                  <button id="set-session-profile" type="button">Set Profile</button>
                </div>
              </div>
              <div id="sessions-list" class="log">Active sessions will appear here.</div>
              <textarea id="prompt-text" class="log" rows="4" placeholder="Record a prompt in session history. This does not execute Codex, Antigravity, PTY, or Worktrunk."></textarea>
              <button id="send-prompt" type="button">Record Prompt</button>
              <input id="history-search" type="search" placeholder="Search semantic history">
              <button id="search-history" type="button">Search History</button>
              <div id="history-search-results" class="log">Search results will appear here. Search is read-only.</div>
              <button id="refresh-session-history" type="button">Refresh Session History</button>
              <div id="session-history" class="log">Semantic session history will appear here. This is not an execution queue.</div>
            </div>
          </div>
        </section>

        <section id="page-swarm" class="page" data-page="swarm" aria-label="Swarm page">
          <div class="flow-grid">
            <div class="panel">
              <h2>Swarm Planning</h2>
              <div class="panel-body control-grid">
                <textarea id="swarm-objective" class="log" rows="4" placeholder="Record a planning-only swarm objective. This does not launch agents, Worktrunk, PTYs, or commands."></textarea>
                <button id="record-swarm-plan" type="button">Record Swarm Plan</button>
                <button id="request-swarm-start-approval" type="button">Request Swarm Start Approval</button>
                <input id="swarm-lifecycle-approval-id" type="text" placeholder="Paste approved swarm lifecycle approval id">
                <button id="record-swarm-start" type="button">Record Approved Swarm Start</button>
                <button id="request-swarm-stop-approval" type="button">Request Swarm Stop Approval</button>
                <button id="record-swarm-stop" type="button">Record Approved Swarm Stop</button>
                <div id="swarm-plan-status" class="log">Swarm planning is semantic state only. No agents are launched from this control.</div>
              </div>
            </div>
            <div class="panel">
              <h2>Swarm Role Launch</h2>
              <div class="panel-body control-grid">
                <div class="agent-pane">
                  <div><strong>Swarm Role Launch</strong><span>Approval-gated role-labeled PTY launch. Runtime policy still applies.</span></div>
                  <div>
                    <input id="swarm-launch-role-id" type="text" value="codex-executor" aria-label="Swarm launch role id">
                    <input id="swarm-launch-profile" type="text" value="swarm" aria-label="Swarm launch policy profile">
                  </div>
                </div>
                <input id="swarm-launch-cwd" type="text" placeholder="Optional cwd; leave blank for runtime default">
                <textarea id="swarm-launch-command" class="log" rows="2" placeholder="Exact role command to launch after matching approval. Example: pwd"></textarea>
                <button id="request-swarm-launch-approval" type="button">Request Swarm Launch Approval</button>
                <input id="swarm-launch-approval-id" type="text" placeholder="Paste approved swarm.launch approval id">
                <button id="launch-approved-swarm" type="button">Launch Approved Swarm Role</button>
                <div id="swarm-launch-status" class="log">Swarm role launch is disabled until a swarm lifecycle start is recorded and a matching approval is consumed. Displayed commands are not execution authority.</div>
              </div>
            </div>
          </div>
        </section>

        <section id="page-loop" class="page" data-page="loop" aria-label="Loop page">
          <div class="flow-grid">
            <div class="panel">
              <h2>Loop Lifecycle</h2>
              <div class="panel-body control-grid">
                <textarea id="loop-objective" class="log" rows="3" placeholder="Record a loop lifecycle objective. This does not launch agents, PTYs, Worktrunk, shell, or workflows."></textarea>
                <button id="request-loop-start-approval" type="button">Request Loop Start Approval</button>
                <input id="loop-lifecycle-approval-id" type="text" placeholder="Paste approved loop lifecycle approval id">
                <button id="record-loop-start" type="button">Record Approved Loop Start</button>
                <button id="request-loop-pause-approval" type="button">Request Loop Pause Approval</button>
                <button id="record-loop-pause" type="button">Record Approved Loop Pause</button>
                <button id="request-loop-resume-approval" type="button">Request Loop Resume Approval</button>
                <button id="record-loop-resume" type="button">Record Approved Loop Resume</button>
                <button id="request-loop-stop-approval" type="button">Request Loop Stop Approval</button>
                <button id="record-loop-stop" type="button">Record Approved Loop Stop</button>
                <div id="loop-lifecycle-status" class="log">Loop lifecycle controls record approved state only. They do not start autonomous execution.</div>
              </div>
            </div>
            <div class="panel">
              <h2>Command Proposal</h2>
              <div class="panel-body control-grid">
                <textarea id="command-proposal" class="log" rows="3" placeholder="Propose a command for policy review. This records a proposal only; it does not request approval or execute."></textarea>
                <button id="record-command-proposal" type="button">Record Command Proposal</button>
                <div id="command-proposal-status" class="log">Command proposals are classified and stored as planning state only.</div>
              </div>
            </div>
          </div>
        </section>

        <section id="page-release" class="page" data-page="release" aria-label="Release page">
          <div class="flow-grid">
            <div class="panel">
              <h2>Release Gates</h2>
              <div class="panel-body control-grid">
                <div id="readiness-gaps" class="log">Readiness summary pending.</div>
                <div id="mobile-access-panel" class="log">Mobile access readiness pending. Displayed commands are proposals only.</div>
                <div id="mobile-evidence-panel" class="log">Mobile evidence brief pending. No runtime is launched from this panel.</div>
                <div id="gemini-evidence-panel" class="log">Gemini evidence brief pending. No OAuth, WebSocket, or network probe is launched from this panel.</div>
                <div id="packaging-evidence-panel" class="log">Packaging evidence brief pending. No install, build, signing, copy, upload, or publish runs from this panel.</div>
                <div id="security-evidence-panel" class="log">External security evidence brief pending. No scanner, service, network, build, signing, copy, or publish action runs from this panel.</div>
                <div id="release-gate-panel" class="log">Release gate status pending. Evidence records do not close gates.</div>
                <div id="release-acceptance-brief-panel" class="log">Release acceptance brief pending. Proposed commands are display-only.</div>
                <div id="release-checklist-panel" class="log">Release readiness checklist pending. Displayed commands are proposals only.</div>
                <button id="refresh-readiness" type="button">Refresh Readiness</button>
              </div>
            </div>
            <div class="panel">
              <h2>Evidence Metadata</h2>
              <div class="panel-body control-grid">
                <select id="release-evidence-gate" aria-label="Release evidence gate">
                  <option value="actual_mobile_device_validation">actual_mobile_device_validation</option>
                  <option value="networked_gemini_live_validation">networked_gemini_live_validation</option>
                  <option value="electron_packaging_and_signing">electron_packaging_and_signing</option>
                  <option value="release_packaging_and_signing">release_packaging_and_signing</option>
                  <option value="external_security_review">external_security_review</option>
                  <option value="unattended_loop_scheduling">unattended_loop_scheduling</option>
                </select>
                <input id="release-evidence-reviewer" placeholder="Reviewer/operator" value="operator">
                <textarea id="release-evidence-summary" rows="2" placeholder="Evidence summary. This does not close the gate."></textarea>
                <button id="record-release-evidence" type="button">Record Evidence Metadata</button>
                <div id="release-evidence-status" class="log">Evidence metadata is state-only and does not authorize release.</div>
                <select id="release-accept-gate" aria-label="Release gate acceptance gate">
                  <option value="actual_mobile_device_validation">actual_mobile_device_validation</option>
                  <option value="networked_gemini_live_validation">networked_gemini_live_validation</option>
                  <option value="electron_packaging_and_signing">electron_packaging_and_signing</option>
                  <option value="release_packaging_and_signing">release_packaging_and_signing</option>
                  <option value="external_security_review">external_security_review</option>
                  <option value="unattended_loop_scheduling">unattended_loop_scheduling</option>
                </select>
                <input id="release-accept-evidence-id" placeholder="Evidence id to accept">
                <input id="release-accept-reviewer" placeholder="Acceptance reviewer/operator" value="operator">
                <textarea id="release-accept-summary" rows="2" placeholder="Acceptance summary. This closes only the selected local gate and grants no execution authority."></textarea>
                <button id="accept-release-gate" type="button">Accept Gate Evidence</button>
                <div id="release-accept-status" class="log">Gate acceptance requires an existing evidence id for the same gate.</div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </section>
  </main>
  <script src="/assets/hud.js"></script>
</body>
</html>
"""


HUD_JS = r"""(() => {
  const consoleEl = document.getElementById("console");
  const socketStatus = document.getElementById("socket-status");
  const voiceStatus = document.getElementById("voice-status");
  const voiceLog = document.getElementById("voice-log");
  const proposalPreview = document.getElementById("proposal-preview");
  const micToggle = document.getElementById("mic-toggle");
  const speakStatus = document.getElementById("speak-status");
  const sttModelId = document.getElementById("stt-model-id");
  const requestTranscriptionApproval = document.getElementById("request-transcription-approval");
  const sttApprovalId = document.getElementById("stt-approval-id");
  const transcribeCapturedAudio = document.getElementById("transcribe-captured-audio");
  const requestProposalApproval = document.getElementById("request-proposal-approval");
  const approvalCount = document.getElementById("approval-count");
  const agentProviderStatus = document.getElementById("agent-provider-status");
  const agentProviderList = document.getElementById("agent-provider-list");
  const terminalPanes = document.getElementById("terminal-panes");
  const agChallengeBrief = document.getElementById("ag-challenge-brief");
  const requestAgChallengeApproval = document.getElementById("request-ag-challenge-approval");
  const agChallengeStatus = document.getElementById("ag-challenge-status");
  const approvalsList = document.getElementById("approvals-list");
  const approvedLaunches = document.getElementById("approved-launches");
  const activeSession = document.getElementById("active-session");
  const sessionsList = document.getElementById("sessions-list");
  const sessionHistory = document.getElementById("session-history");
  const refreshSessionHistoryButton = document.getElementById("refresh-session-history");
  const createSession = document.getElementById("create-session");
  const sessionProfile = document.getElementById("session-profile");
  const setSessionProfile = document.getElementById("set-session-profile");
  const promptText = document.getElementById("prompt-text");
  const sendPrompt = document.getElementById("send-prompt");
  const swarmObjective = document.getElementById("swarm-objective");
  const recordSwarmPlan = document.getElementById("record-swarm-plan");
  const requestSwarmStartApproval = document.getElementById("request-swarm-start-approval");
  const swarmLifecycleApprovalId = document.getElementById("swarm-lifecycle-approval-id");
  const recordSwarmStart = document.getElementById("record-swarm-start");
  const requestSwarmStopApproval = document.getElementById("request-swarm-stop-approval");
  const recordSwarmStop = document.getElementById("record-swarm-stop");
  const swarmPlanStatus = document.getElementById("swarm-plan-status");
  const swarmLaunchRoleId = document.getElementById("swarm-launch-role-id");
  const swarmLaunchProfile = document.getElementById("swarm-launch-profile");
  const swarmLaunchCwd = document.getElementById("swarm-launch-cwd");
  const swarmLaunchCommand = document.getElementById("swarm-launch-command");
  const requestSwarmLaunchApproval = document.getElementById("request-swarm-launch-approval");
  const swarmLaunchApprovalId = document.getElementById("swarm-launch-approval-id");
  const launchApprovedSwarm = document.getElementById("launch-approved-swarm");
  const swarmLaunchStatus = document.getElementById("swarm-launch-status");
  const loopObjective = document.getElementById("loop-objective");
  const requestLoopStartApproval = document.getElementById("request-loop-start-approval");
  const loopLifecycleApprovalId = document.getElementById("loop-lifecycle-approval-id");
  const recordLoopStart = document.getElementById("record-loop-start");
  const requestLoopPauseApproval = document.getElementById("request-loop-pause-approval");
  const recordLoopPause = document.getElementById("record-loop-pause");
  const requestLoopResumeApproval = document.getElementById("request-loop-resume-approval");
  const recordLoopResume = document.getElementById("record-loop-resume");
  const requestLoopStopApproval = document.getElementById("request-loop-stop-approval");
  const recordLoopStop = document.getElementById("record-loop-stop");
  const loopLifecycleStatus = document.getElementById("loop-lifecycle-status");
  const commandProposal = document.getElementById("command-proposal");
  const recordCommandProposal = document.getElementById("record-command-proposal");
  const commandProposalStatus = document.getElementById("command-proposal-status");
  const historySearch = document.getElementById("history-search");
  const searchHistory = document.getElementById("search-history");
  const historySearchResults = document.getElementById("history-search-results");
  const codeburnStatus = document.getElementById("codeburn-status");
  const refreshCodeburn = document.getElementById("refresh-codeburn");
  const pwaStatus = document.getElementById("pwa-status");
  const readinessStatus = document.getElementById("readiness-status");
  const readinessGaps = document.getElementById("readiness-gaps");
  const mobileAccessStatus = document.getElementById("mobile-access-status");
  const mobileAccessPanel = document.getElementById("mobile-access-panel");
  const mobileEvidencePanel = document.getElementById("mobile-evidence-panel");
  const geminiEvidencePanel = document.getElementById("gemini-evidence-panel");
  const packagingEvidencePanel = document.getElementById("packaging-evidence-panel");
  const securityEvidencePanel = document.getElementById("security-evidence-panel");
  const releaseGateStatus = document.getElementById("release-gate-status");
  const releaseGatePanel = document.getElementById("release-gate-panel");
  const releaseAcceptanceBriefPanel = document.getElementById("release-acceptance-brief-panel");
  const releaseChecklistStatus = document.getElementById("release-checklist-status");
  const releaseChecklistPanel = document.getElementById("release-checklist-panel");
  const releaseEvidenceGate = document.getElementById("release-evidence-gate");
  const releaseEvidenceReviewer = document.getElementById("release-evidence-reviewer");
  const releaseEvidenceSummary = document.getElementById("release-evidence-summary");
  const recordReleaseEvidence = document.getElementById("record-release-evidence");
  const releaseEvidenceStatus = document.getElementById("release-evidence-status");
  const releaseAcceptGate = document.getElementById("release-accept-gate");
  const releaseAcceptEvidenceId = document.getElementById("release-accept-evidence-id");
  const releaseAcceptReviewer = document.getElementById("release-accept-reviewer");
  const releaseAcceptSummary = document.getElementById("release-accept-summary");
  const acceptReleaseGate = document.getElementById("accept-release-gate");
  const releaseAcceptStatus = document.getElementById("release-accept-status");
  const refreshReadiness = document.getElementById("refresh-readiness");
  const shellCommandInput = document.getElementById("shell-command-input");
  const shellCommandRecord = document.getElementById("shell-command-record");
  const shellCommandCreate = document.getElementById("shell-command-create");
  const shellCommandVoice = document.getElementById("shell-command-voice");
  const shellCommandStatus = document.getElementById("shell-command-status");
  const navButtons = Array.from(document.querySelectorAll("[data-page-target]"));
  const pages = Array.from(document.querySelectorAll("[data-page]"));
  let socket;
  let requestSeq = 0;
  const requestIndex = new Map();
  let activeSessionId = "hud";
  let micStream = null;
  let recognition = null;
  let mediaRecorder = null;
  let audioSequence = 0;
  let utteranceId = null;
  let lastAudioPath = "";
  let lastAudioUtteranceId = "";
  let stoppingRecorder = false;
  let lastVoiceProposal = null;
  let lastReadiness = null;
  let lastSwarmPlanEventId = "";
  let lastSwarmLifecycleEventId = "";
  let lastSwarmLaunchRoles = [];
  let lastLoopLifecycleEventId = "";
  const terminalChannels = new Map();
  const runtimeToken = document.querySelector('meta[name="jarvis-runtime-token"]')?.content || "";
  const PANE_LAUNCHES = {
    codex: {
      label: "Codex",
      command: "codex",
      risk: "high",
      summary: "Launch Codex in a runtime-supervised PTY pane"
    },
    antigravity: {
      label: "Antigravity",
      command: "agy",
      risk: "high",
      summary: "Launch Antigravity in a runtime-supervised PTY pane"
    },
  };

  function log(line) {
    const stamp = new Date().toLocaleTimeString();
    consoleEl.textContent += `\n[${stamp}] ${line}`;
    consoleEl.scrollTop = consoleEl.scrollHeight;
  }

  function terminalLabel(metadata) {
    const command = metadata.command ? `Command: ${metadata.command}` : "Command pending";
    const profile = metadata.profile ? `Profile: ${metadata.profile}` : "Profile pending";
    const pid = metadata.pid ? `PID: ${metadata.pid}` : "PID pending";
    return `${command} | ${profile} | ${pid}`;
  }

  function ensureTerminalPane(channelId, metadata = {}) {
    const existing = terminalChannels.get(channelId);
    if (existing) {
      Object.assign(existing.metadata, metadata);
      existing.meta.textContent = terminalLabel(existing.metadata);
      return existing;
    }
    if (terminalPanes.querySelector(".log")) {
      terminalPanes.textContent = "";
    }
    const pane = document.createElement("article");
    pane.className = "terminal-pane";
    pane.dataset.terminalChannel = channelId;

    const header = document.createElement("header");
    const title = document.createElement("strong");
    title.textContent = `PTY ${channelId}`;
    const meta = document.createElement("small");
    meta.textContent = terminalLabel(metadata);
    header.append(title, meta);

    const output = document.createElement("pre");
    output.className = "terminal-output";
    output.textContent = "";

    pane.append(header, output);
    terminalPanes.appendChild(pane);

    const state = { pane, output, meta, metadata: { ...metadata } };
    terminalChannels.set(channelId, state);
    return state;
  }

  function registerPtyChannel(result, source = "pty.create") {
    if (!result || !result.channel_id) return;
    ensureTerminalPane(result.channel_id, {
      command: result.command || "",
      profile: result.profile || "",
      pid: result.pid || "",
      source
    });
  }

  function handlePtyStream(frame) {
    const state = ensureTerminalPane(frame.channel_id, {
      stream_type: frame.stream_type || "stdout",
      sequence: frame.sequence || 0
    });
    state.output.textContent += frame.chunk || "";
    if (state.output.textContent.length > 50000) {
      state.output.textContent = state.output.textContent.slice(-50000);
    }
    state.output.scrollTop = state.output.scrollHeight;
  }

  function observePtyOutputEvent(frame) {
    const payload = frame.payload || {};
    if (!payload.channel_id) return;
    ensureTerminalPane(payload.channel_id, {
      command: payload.command || "",
      profile: payload.profile || "",
      pid: payload.pid || "",
      stream_type: payload.stream_type || "",
      sequence: payload.pty_sequence || ""
    });
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    }[ch]));
  }

  function request(method, params = {}) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      log(`Socket is not connected. Cannot send ${method}.`);
      return;
    }
    requestSeq += 1;
    const requestId = `hud_${requestSeq}`;
    requestIndex.set(requestId, { method, params });
    socket.send(JSON.stringify({ type: "request", id: requestId, method, params }));
  }

  function privilegedParams(params = {}) {
    return { ...params, runtime_token: runtimeToken };
  }

  function currentSessionId() {
    return activeSessionId || "hud";
  }

  function selectedProfileId() {
    return sessionProfile.value || "observe";
  }

  function hasActiveOperatorSession() {
    return Boolean(activeSessionId && activeSessionId !== "hud");
  }

  function showPage(name) {
    for (const page of pages) {
      page.classList.toggle("active", page.dataset.page === name);
    }
    for (const button of navButtons) {
      const active = button.dataset.pageTarget === name;
      button.classList.toggle("active", active);
      button.setAttribute("aria-selected", active ? "true" : "false");
    }
    log(`Page selected: ${name}.`);
  }

  for (const button of navButtons) {
    button.addEventListener("click", () => showPage(button.dataset.pageTarget));
  }

  function createHudSession() {
    request("session.create", {
      title: `HUD session ${new Date().toLocaleString()}`,
      profile_id: selectedProfileId(),
      source_client: "hud",
      actor_id: "user"
    });
    shellCommandStatus.textContent = "Session creation requested. Recording intent remains state-only.";
    log("HUD session creation requested.");
  }

  function recordPromptText(text, sourceClient) {
    const cleanText = text.trim();
    if (!cleanText) {
      shellCommandStatus.textContent = "Nothing recorded. Type an intent first.";
      log("Prompt text is empty; nothing recorded.");
      return false;
    }
    if (!hasActiveOperatorSession()) {
      shellCommandStatus.textContent = "Create or select a HUD session before recording shell input. No command was executed.";
      showPage("session");
      log("Shell input requires an active session. Nothing executed.");
      return false;
    }
    request("prompt.send", {
      session_id: currentSessionId(),
      text: cleanText,
      target: "planning",
      source_client: sourceClient,
      actor_id: "user"
    });
    shellCommandStatus.textContent = "Intent record requested. This does not execute Codex, Antigravity, PTYs, Worktrunk, or shell commands.";
    log("Prompt record requested. This does not execute a command or agent.");
    return true;
  }

  function swarmLaunchRoles() {
    const command = swarmLaunchCommand.value.trim();
    if (!command) {
      return [];
    }
    return [
      {
        role_id: (swarmLaunchRoleId.value.trim() || "codex-executor"),
        command,
        profile: (swarmLaunchProfile.value.trim() || "swarm"),
        cwd: swarmLaunchCwd.value.trim()
      }
    ];
  }

  function connect() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${protocol}//${location.host}/ws`);
    socket.addEventListener("open", () => {
      socketStatus.textContent = "online";
      log("Connected to Jarvis runtime.");
      request("initialize");
      request("session.list", { status: "active", limit: 25 });
      request("profile.list");
      refreshSessionHistory();
      request("approval.list", { status: "pending" });
      request("approval.list", { status: "approved" });
      request("voice.provider_status");
      request("agent.provider_status");
      request("telemetry.codeburn_status");
      request("runtime.readiness");
      request("mobile.evidence_brief");
      request("gemini.evidence_brief");
      request("release.packaging_evidence_brief");
      request("release.security_evidence_brief");
      request("release.gate_status");
      request("release.gate_acceptance_brief");
      request("release.readiness_checklist");
    });
    socket.addEventListener("close", () => {
      socketStatus.textContent = "offline";
      log("Runtime socket closed.");
      setTimeout(connect, 1500);
    });
    socket.addEventListener("message", (event) => {
      const frame = JSON.parse(event.data);
      if (frame.type === "stream") {
        handlePtyStream(frame);
        log(`PTY ${frame.channel_id}: ${frame.chunk.trimEnd()}`);
        return;
      }
      if (frame.type === "event") {
        log(`Event: ${frame.event_type}`);
        if (frame.event_type === "pty.output") {
          observePtyOutputEvent(frame);
        }
        if (frame.event_type && frame.event_type.startsWith("approval.")) {
          request("approval.list", { status: "pending" });
          request("approval.list", { status: "approved" });
        }
        if (frame.event_type && frame.event_type.startsWith("session.")) {
          request("session.list", { status: "active", limit: 25 });
        }
        if (frame.session_id === currentSessionId()) {
          refreshSessionHistory();
        }
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.resumed_session_id) {
        activeSessionId = frame.result.resumed_session_id;
        activeSession.textContent = `Active session: ${activeSessionId}`;
        renderSessionHistory(frame.result.messages || [], frame.result.current_sequence);
        log(`Resumed session ${activeSessionId}. No execution authority granted.`);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && Array.isArray(frame.result.messages)) {
        renderSessionHistory(frame.result.messages, frame.result.current_sequence);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.archived_session_id) {
        log(`Archived session ${frame.result.archived_session_id}.`);
        request("session.list", { status: "active", limit: 25 });
        refreshSessionHistory();
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && Array.isArray(frame.result.profiles)) {
        renderProfiles(frame.result.profiles, frame.result.default_profile || "observe");
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.profile_id && frame.result.session) {
        log(`Session ${frame.result.session_id} profile set to ${frame.result.profile_id}.`);
        request("session.list", { status: "active", limit: 25 });
        refreshSessionHistory();
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.prompt_event_id) {
        log(`Prompt recorded for ${frame.result.session_id}. No execution authority granted.`);
        promptText.value = "";
        shellCommandInput.value = "";
        shellCommandStatus.textContent = `Intent recorded for ${frame.result.session_id}. No execution authority granted.`;
        refreshSessionHistory();
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.swarm_plan_event_id) {
        lastSwarmPlanEventId = frame.result.swarm_plan_event_id;
        log(`Swarm plan recorded for ${frame.result.session_id}. No agents launched; no Worktrunk mutation occurred.`);
        swarmPlanStatus.textContent = `Swarm plan recorded at sequence ${frame.result.sequence}. Plan event: ${lastSwarmPlanEventId}. This is planning state only.`;
        swarmObjective.value = "";
        refreshSessionHistory();
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.swarm_lifecycle_event_id) {
        lastSwarmLifecycleEventId = frame.result.swarm_lifecycle_event_id;
        log(`Swarm lifecycle ${frame.result.lifecycle_state} recorded for ${frame.result.session_id}. No agents, PTYs, Worktrunk, commands, or workflows executed.`);
        swarmPlanStatus.textContent = `Swarm lifecycle ${frame.result.lifecycle_state} recorded at sequence ${frame.result.sequence}. Event: ${lastSwarmLifecycleEventId}. State only.`;
        refreshSessionHistory();
        request("approval.list", { status: "approved" });
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.swarm_launch_event_id) {
        const roles = Array.isArray(frame.result.roles) ? frame.result.roles : [];
        for (const role of roles) {
          registerPtyChannel(role, "swarm.launch");
        }
        const channels = roles.map((role) => role.channel_id).filter(Boolean).join(", ");
        log(`Swarm launched ${frame.result.role_count || roles.length} approved role-labeled PTY pane(s). Channels: ${channels || "none"}.`);
        swarmLaunchStatus.textContent = `Swarm launched ${frame.result.role_count || roles.length} approved role-labeled PTY pane(s). Event: ${frame.result.swarm_launch_event_id}. Runtime policy gate still applies.`;
        refreshSessionHistory();
        request("approval.list", { status: "approved" });
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.loop_lifecycle_event_id) {
        lastLoopLifecycleEventId = frame.result.loop_lifecycle_event_id;
        log(`Loop lifecycle ${frame.result.lifecycle_state} recorded for ${frame.result.session_id}. No agents, PTYs, Worktrunk, shell, or workflows executed.`);
        loopLifecycleStatus.textContent = `Loop lifecycle ${frame.result.lifecycle_state} recorded at sequence ${frame.result.sequence}. Event: ${lastLoopLifecycleEventId}. State only.`;
        refreshSessionHistory();
        request("approval.list", { status: "approved" });
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.command_proposal_event_id) {
        const policy = frame.result.policy || {};
        log(`Command proposal recorded for ${frame.result.session_id}. Policy: ${policy.status || "unknown"}. No approval was created and nothing executed.`);
        commandProposalStatus.textContent = `Proposal ${frame.result.proposal_id} recorded. Policy: ${policy.status || "unknown"} (${policy.reason || "no reason"}). No approval created.`;
        commandProposal.value = "";
        refreshSessionHistory();
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && Array.isArray(frame.result.results)) {
        renderSearchResults(frame.result.results, frame.result.query || "");
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.child_session_id) {
        activeSessionId = frame.result.child_session_id;
        activeSession.textContent = `Active session: ${activeSessionId}`;
        log(`Forked session ${frame.result.parent_session_id} to ${frame.result.child_session_id}. No execution authority granted.`);
        request("session.list", { status: "active", limit: 25 });
        refreshSessionHistory();
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.sessions) {
        renderSessions(frame.result.sessions);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.session_id) {
        activeSessionId = frame.result.session_id;
        activeSession.textContent = `Active session: ${activeSessionId}`;
        shellCommandStatus.textContent = `Active session ${activeSessionId}. Shell input records planning context only.`;
        log(`HUD session active: ${activeSessionId}.`);
        request("session.list", { status: "active", limit: 25 });
        refreshSessionHistory();
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.codeburn) {
        renderCodeburnStatus(frame.result.codeburn);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && Array.isArray(frame.result.providers)) {
        renderAgentProviders(frame.result);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && Object.prototype.hasOwnProperty.call(frame.result, "production_complete")) {
        renderReadiness(frame.result);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.release_evidence_command && frame.result.target_url) {
        renderMobileEvidenceBrief(frame.result);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.release_evidence_command && frame.result.recommended_path) {
        renderGeminiEvidenceBrief(frame.result);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && Array.isArray(frame.result.release_evidence_commands)) {
        renderPackagingEvidenceBrief(frame.result);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.security_review_plan_status && frame.result.release_evidence_command) {
        renderSecurityEvidenceBrief(frame.result);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && Array.isArray(frame.result.acceptance_items)) {
        renderReleaseAcceptanceBrief(frame.result);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && Object.prototype.hasOwnProperty.call(frame.result, "open_gate_count")) {
        renderReleaseGateStatus(frame.result);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && Array.isArray(frame.result.checklist)) {
        renderReleaseChecklist(frame.result);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.evidence && frame.result.state_write_performed) {
        releaseEvidenceStatus.textContent = `Evidence metadata recorded for ${frame.result.evidence.gate}. Gate closed: ${frame.result.release_gate_closed ? "yes" : "no"}.`;
        request("release.gate_status");
        request("release.gate_acceptance_brief");
        request("release.readiness_checklist");
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.acceptance && frame.result.state_write_performed) {
        releaseAcceptStatus.textContent = `Gate accepted for ${frame.result.acceptance.gate} using ${frame.result.acceptance.evidence_id}. This grants no execution authority.`;
        request("release.gate_status");
        request("release.gate_acceptance_brief");
        request("release.readiness_checklist");
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.audio && frame.result.audio.path) {
        lastAudioPath = frame.result.audio.path;
        lastAudioUtteranceId = frame.result.audio.utterance_id || "";
        voiceLog.textContent = `Captured local audio chunk ${lastAudioUtteranceId || ""}. Transcription requires approval.`;
        log(`Audio chunk stored locally at ${lastAudioPath}. No transcription ran.`);
        refreshSessionHistory();
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.transcription) {
        const eventPayload = frame.result.event && frame.result.event.payload ? frame.result.event.payload : {};
        const text = eventPayload.text || frame.result.transcription.transcript || "";
        voiceLog.textContent = `Approved local STT transcript: ${text}`;
        log("Approved local STT transcription completed. Transcript event recorded without execution authority.");
        request("approval.list", { status: "approved" });
        refreshSessionHistory();
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.approvals) {
        const indexed = requestIndex.get(frame.id);
        const status = indexed && indexed.params ? indexed.params.status : "pending";
        if (status === "approved") {
          renderApprovedLaunches(frame.result.approvals);
        } else {
          approvalCount.textContent = String(frame.result.approvals.length);
          renderApprovals(frame.result.approvals);
        }
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.channel_id) {
        registerPtyChannel(frame.result, "pty.create");
        log(`PTY channel launched: ${frame.result.channel_id}. Approval: ${frame.result.approval_id || "none"}.`);
        requestIndex.delete(frame.id);
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.proposal) {
        const proposal = frame.result.proposal;
        lastVoiceProposal = proposal;
        renderVoiceProposal(proposal);
        log(`Voice intent proposal: ${proposal.intent_type} -> ${proposal.summary}`);
        voiceLog.textContent = `Intent proposal: ${proposal.intent_type}. ${proposal.execution_authority ? "Execution authority present" : "No execution authority"}.`;
        return;
      }
      if (frame.type === "response" && frame.error) {
        log(`Error: ${frame.error.code} - ${frame.error.message}`);
        return;
      }
      log(`Frame: ${JSON.stringify(frame)}`);
    });
  }

  async function registerPwa() {
    if (!("serviceWorker" in navigator)) {
      pwaStatus.textContent = "unavailable";
      return;
    }
    try {
      await navigator.serviceWorker.register("/service-worker.js");
      pwaStatus.textContent = "ready";
      log("PWA service worker registered for HUD shell assets.");
    } catch (error) {
      pwaStatus.textContent = "failed";
      log(`PWA service worker registration failed: ${error.message}`);
    }
  }

  document.querySelectorAll("[data-pane]").forEach((button) => {
    button.addEventListener("click", () => {
      const pane = button.getAttribute("data-pane");
      const launch = PANE_LAUNCHES[pane];
      if (!launch) {
        log(`${pane} pane is not configured.`);
        return;
      }
      request("approval.request", {
        session_id: currentSessionId(),
        summary: launch.summary,
        operation: launch.command,
        risk: launch.risk,
        scope: {
          source: "hud.pane.prepare",
          pane,
          command: launch.command,
          runtime_supervised: true,
          execution_authority: false
        }
      });
      log(`${launch.label} pane launch approval requested. No PTY was started.`);
    });
  });

  requestAgChallengeApproval.addEventListener("click", () => {
    const brief = agChallengeBrief.value.trim() || "Review the current Jarvis plan for hidden release, safety, and architecture risks.";
    request("approval.request", {
      session_id: currentSessionId(),
      summary: `Launch Antigravity challenge pane: ${brief.slice(0, 96)}`,
      operation: "agy",
      risk: "high",
      scope: {
        source: "hud.pane.prepare",
        pane: "antigravity",
        mode: "challenge",
        command: "agy",
        profile: "observe",
        challenge_brief: brief,
        runtime_supervised: true,
        execution_authority: false
      },
      source_client: "hud",
      actor_id: "user"
    });
    agChallengeStatus.textContent = "Antigravity challenge approval requested. No PTY was launched; approved launch still requires the separate approved-launch control.";
    log("Antigravity challenge approval requested. No AG process, PTY, shell command, Worktrunk, or workflow was launched.");
  });

  createSession.addEventListener("click", createHudSession);

  setSessionProfile.addEventListener("click", () => {
    request("profile.set", {
      session_id: currentSessionId(),
      profile_id: selectedProfileId(),
      reason: "HUD profile selection",
      source_client: "hud",
      actor_id: "user"
    });
    log(`Session profile update requested: ${selectedProfileId()}. This changes metadata only.`);
  });

  sendPrompt.addEventListener("click", () => {
    recordPromptText(promptText.value, "hud");
  });

  shellCommandRecord.addEventListener("click", () => {
    recordPromptText(shellCommandInput.value, "hud.command_bar");
  });

  shellCommandInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      recordPromptText(shellCommandInput.value, "hud.command_bar");
    }
  });

  shellCommandCreate.addEventListener("click", () => {
    showPage("session");
    createHudSession();
  });

  shellCommandVoice.addEventListener("click", () => {
    showPage("voice");
    micToggle.focus();
    shellCommandStatus.textContent = "Voice page selected. Click Mic to request browser microphone permission.";
  });

  recordSwarmPlan.addEventListener("click", () => {
    const objective = swarmObjective.value.trim();
    if (!objective) {
      log("Swarm objective is empty; nothing recorded.");
      return;
    }
    request("swarm.plan", {
      session_id: currentSessionId(),
      objective,
      profile_id: selectedProfileId(),
      lanes: [
        {
          lane_id: "planning",
          title: "Planning lane",
          task: objective,
          agent: "unassigned"
        }
      ],
      source_client: "hud",
      actor_id: "user"
    });
    swarmPlanStatus.textContent = "Swarm plan record requested. This does not start agents, Worktrunk, PTYs, or commands.";
    log("Swarm plan record requested. Planning state only; no agents launched.");
  });

  requestSwarmStartApproval.addEventListener("click", () => {
    if (!lastSwarmPlanEventId) {
      log("Record a swarm plan before requesting swarm start approval.");
      swarmPlanStatus.textContent = "Start approval requires a recorded swarm plan event id.";
      return;
    }
    request("approval.request", {
      session_id: currentSessionId(),
      summary: "Record approved swarm lifecycle start",
      operation: "swarm.start",
      risk: "medium",
      scope: {
        source: "swarm.start",
        session_id: currentSessionId(),
        plan_event_id: lastSwarmPlanEventId,
        execution_authority: false
      },
      source_client: "hud",
      actor_id: "user"
    });
    swarmPlanStatus.textContent = "Swarm start approval requested. Approval does not launch agents or commands.";
    log("Swarm start approval requested for recorded plan. No lifecycle state changed yet.");
  });

  recordSwarmStart.addEventListener("click", () => {
    const approvalId = swarmLifecycleApprovalId.value.trim();
    if (!lastSwarmPlanEventId || !approvalId) {
      log("Swarm start requires a recorded plan event and an approved lifecycle approval id.");
      return;
    }
    request("swarm.start", privilegedParams({
      session_id: currentSessionId(),
      plan_event_id: lastSwarmPlanEventId,
      approval_id: approvalId,
      source_client: "hud",
      actor_id: "user"
    }));
    swarmLifecycleApprovalId.value = "";
    swarmPlanStatus.textContent = "Approved swarm start record requested. This records lifecycle state only.";
    log("Approved swarm start record requested. No agents, PTYs, Worktrunk, shell, or workflows launched.");
  });

  requestSwarmStopApproval.addEventListener("click", () => {
    if (!lastSwarmLifecycleEventId) {
      log("Record a swarm lifecycle event before requesting stop approval.");
      swarmPlanStatus.textContent = "Stop approval requires a recorded swarm lifecycle event id.";
      return;
    }
    request("approval.request", {
      session_id: currentSessionId(),
      summary: "Record approved swarm lifecycle stop",
      operation: "swarm.stop",
      risk: "medium",
      scope: {
        source: "swarm.stop",
        session_id: currentSessionId(),
        swarm_event_id: lastSwarmLifecycleEventId,
        execution_authority: false
      },
      source_client: "hud",
      actor_id: "user"
    });
    swarmPlanStatus.textContent = "Swarm stop approval requested. Approval does not stop running processes.";
    log("Swarm stop approval requested for lifecycle record. No runtime process was stopped.");
  });

  recordSwarmStop.addEventListener("click", () => {
    const approvalId = swarmLifecycleApprovalId.value.trim();
    if (!lastSwarmLifecycleEventId || !approvalId) {
      log("Swarm stop requires a recorded lifecycle event and an approved lifecycle approval id.");
      return;
    }
    request("swarm.stop", privilegedParams({
      session_id: currentSessionId(),
      swarm_event_id: lastSwarmLifecycleEventId,
      approval_id: approvalId,
      source_client: "hud",
      actor_id: "user"
    }));
    swarmLifecycleApprovalId.value = "";
    swarmPlanStatus.textContent = "Approved swarm stop record requested. This records lifecycle state only.";
    log("Approved swarm stop record requested. No agents, PTYs, Worktrunk, shell, or workflows stopped.");
  });

  requestSwarmLaunchApproval.addEventListener("click", () => {
    if (!lastSwarmLifecycleEventId) {
      log("Record an approved swarm start before requesting swarm role launch approval.");
      swarmLaunchStatus.textContent = "Swarm launch approval requires a recorded swarm lifecycle start event id.";
      return;
    }
    const roles = swarmLaunchRoles();
    if (roles.length === 0) {
      log("Swarm launch command is empty; no approval requested.");
      swarmLaunchStatus.textContent = "Enter an exact role command before requesting swarm.launch approval.";
      return;
    }
    lastSwarmLaunchRoles = roles;
    request("approval.request", {
      session_id: currentSessionId(),
      summary: "Launch approved swarm role-labeled PTY pane",
      operation: "swarm.launch",
      risk: "high",
      scope: {
        source: "swarm.launch",
        session_id: currentSessionId(),
        swarm_event_id: lastSwarmLifecycleEventId,
        roles
      },
      source_client: "hud",
      actor_id: "user"
    });
    swarmLaunchStatus.textContent = "swarm.launch approval requested. Launch approval does not start PTYs until the approved id is submitted.";
    log("swarm.launch approval requested for exact role scope. No PTY was started.");
  });

  launchApprovedSwarm.addEventListener("click", () => {
    const approvalId = swarmLaunchApprovalId.value.trim();
    const roles = lastSwarmLaunchRoles.length ? lastSwarmLaunchRoles : swarmLaunchRoles();
    if (!lastSwarmLifecycleEventId || !approvalId || roles.length === 0) {
      log("Swarm role launch requires a started swarm event, an exact role command, and an approved swarm.launch approval id.");
      swarmLaunchStatus.textContent = "Approved swarm launch requires started swarm event, role command, and approval id.";
      return;
    }
    request("swarm.launch", privilegedParams({
      session_id: currentSessionId(),
      swarm_event_id: lastSwarmLifecycleEventId,
      roles,
      approval_id: approvalId,
      source_client: "hud",
      actor_id: "user"
    }));
    swarmLaunchApprovalId.value = "";
    swarmLaunchStatus.textContent = "Approved swarm launch requested. Runtime policy gate still applies.";
    log("Approved swarm.launch requested. This can start role-labeled PTYs only for the exact approved role scope.");
  });

  function requestLoopApproval(operation) {
    const objective = loopObjective.value.trim() || "Record approved loop lifecycle state";
    if (operation !== "loop.start" && !lastLoopLifecycleEventId) {
      log("Record a loop start before requesting pause, resume, or stop approval.");
      loopLifecycleStatus.textContent = "Loop pause/resume/stop approval requires a recorded loop lifecycle event id.";
      return;
    }
    request("approval.request", {
      session_id: currentSessionId(),
      summary: `Record approved ${operation} lifecycle state`,
      operation,
      risk: "medium",
      scope: {
        source: operation,
        session_id: currentSessionId(),
        execution_authority: false
      },
      metadata: {
        objective,
        loop_event_id: lastLoopLifecycleEventId
      },
      source_client: "hud",
      actor_id: "user"
    });
    loopLifecycleStatus.textContent = `${operation} approval requested. Approval does not launch agents, PTYs, Worktrunk, shell, or workflows.`;
    log(`${operation} approval requested. No loop lifecycle state changed yet.`);
  }

  function recordLoopLifecycle(operation) {
    const approvalId = loopLifecycleApprovalId.value.trim();
    if (!approvalId) {
      log("Loop lifecycle record requires an approved loop lifecycle approval id.");
      return;
    }
    if (operation !== "loop.start" && !lastLoopLifecycleEventId) {
      log("Loop pause/resume/stop requires an existing loop lifecycle event id.");
      return;
    }
    request(operation, privilegedParams({
      session_id: currentSessionId(),
      objective: loopObjective.value.trim(),
      loop_event_id: operation === "loop.start" ? "" : lastLoopLifecycleEventId,
      approval_id: approvalId,
      source_client: "hud",
      actor_id: "user"
    }));
    loopLifecycleApprovalId.value = "";
    loopLifecycleStatus.textContent = `Approved ${operation} record requested. This records lifecycle state only.`;
    log(`Approved ${operation} record requested. No agents, PTYs, Worktrunk, shell, or workflows launched.`);
  }

  requestLoopStartApproval.addEventListener("click", () => requestLoopApproval("loop.start"));
  recordLoopStart.addEventListener("click", () => recordLoopLifecycle("loop.start"));
  requestLoopPauseApproval.addEventListener("click", () => requestLoopApproval("loop.pause"));
  recordLoopPause.addEventListener("click", () => recordLoopLifecycle("loop.pause"));
  requestLoopResumeApproval.addEventListener("click", () => requestLoopApproval("loop.resume"));
  recordLoopResume.addEventListener("click", () => recordLoopLifecycle("loop.resume"));
  requestLoopStopApproval.addEventListener("click", () => requestLoopApproval("loop.stop"));
  recordLoopStop.addEventListener("click", () => recordLoopLifecycle("loop.stop"));

  recordCommandProposal.addEventListener("click", () => {
    const command = commandProposal.value.trim();
    if (!command) {
      log("Command proposal is empty; nothing recorded.");
      return;
    }
    request("command.propose", {
      session_id: currentSessionId(),
      command,
      profile: selectedProfileId(),
      summary: `HUD command proposal: ${command}`,
      source_client: "hud",
      actor_id: "user"
    });
    commandProposalStatus.textContent = "Command proposal record requested. This does not request approval, launch a PTY, or execute.";
    log("Command proposal record requested. Classification and semantic state only.");
  });

  searchHistory.addEventListener("click", () => {
    const query = historySearch.value.trim();
    request("message.search", {
      query,
      session_id: currentSessionId(),
      limit: 20
    });
    log(`History search requested for "${query}". Search is read-only.`);
  });

  refreshCodeburn.addEventListener("click", () => {
    request("telemetry.codeburn_status");
    log("Codeburn telemetry refresh requested.");
  });

  refreshReadiness.addEventListener("click", () => {
    request("runtime.readiness");
    request("mobile.evidence_brief");
    request("gemini.evidence_brief");
    request("release.packaging_evidence_brief");
    request("release.security_evidence_brief");
    request("release.gate_status");
    request("release.gate_acceptance_brief");
    request("release.readiness_checklist");
    log("Runtime readiness refresh requested.");
  });

  recordReleaseEvidence.addEventListener("click", () => {
    const gate = releaseEvidenceGate.value;
    const summary = releaseEvidenceSummary.value.trim();
    const reviewer = releaseEvidenceReviewer.value.trim() || "operator";
    if (!summary) {
      releaseEvidenceStatus.textContent = "Evidence summary is required. No state was written.";
      return;
    }
    request("release.evidence_add", {
      gate,
      summary,
      reviewer,
      runtime_token: runtimeToken
    });
    releaseEvidenceStatus.textContent = "Release evidence metadata recording requested. This does not close the gate.";
    log(`Release evidence metadata requested for ${gate}. No gate closure authority granted.`);
  });

  acceptReleaseGate.addEventListener("click", () => {
    const gate = releaseAcceptGate.value;
    const evidenceId = releaseAcceptEvidenceId.value.trim();
    const summary = releaseAcceptSummary.value.trim();
    const reviewer = releaseAcceptReviewer.value.trim() || "operator";
    if (!evidenceId || !summary) {
      releaseAcceptStatus.textContent = "Evidence id and acceptance summary are required. No gate was accepted.";
      return;
    }
    request("release.gate_accept", {
      gate,
      evidence_id: evidenceId,
      summary,
      reviewer,
      runtime_token: runtimeToken
    });
    releaseAcceptStatus.textContent = "Release gate acceptance requested. This writes state only and grants no execution authority.";
    log(`Release gate acceptance requested for ${gate} using evidence ${evidenceId}. No commands, signing, publication, or validation launched.`);
  });

  refreshSessionHistoryButton.addEventListener("click", () => {
    refreshSessionHistory();
    log("Session history refresh requested.");
  });

  speakStatus.addEventListener("click", () => {
    speakRuntimeStatus();
  });

  sessionsList.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) return;
    const archiveSessionId = target.dataset.archiveSessionId;
    if (archiveSessionId) {
      request("session.archive", {
        session_id: archiveSessionId,
        reason: "HUD archive request",
        source_client: "hud",
        actor_id: "user"
      });
      log(`Session archive requested for ${archiveSessionId}.`);
      return;
    }
    const forkSessionId = target.dataset.forkSessionId;
    if (forkSessionId) {
      request("session.fork", {
        session_id: forkSessionId,
        profile_id: selectedProfileId(),
        source_client: "hud",
        actor_id: "user"
      });
      log(`Session fork requested for ${forkSessionId}. This creates state only.`);
      return;
    }
    const sessionId = target.dataset.sessionId;
    if (!sessionId) return;
    request("session.resume", { session_id: sessionId, limit: 25 });
    log(`Session resume requested for ${sessionId}.`);
  });

  document.getElementById("refresh-approvals").addEventListener("click", () => {
    request("approval.list", { status: "pending" });
    request("approval.list", { status: "approved" });
  });

  approvalsList.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) return;
    const approvalId = target.dataset.approvalId;
    const action = target.dataset.approvalAction;
    if (!approvalId || !action) return;
    request("approval.respond", privilegedParams({
      approval_id: approvalId,
      status: action,
      reason: `HUD ${action} click`
    }));
    log(`Approval ${action} requested for ${approvalId}.`);
  });

  approvedLaunches.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLButtonElement)) return;
    const voiceApprovalId = target.dataset.voiceTranscribeApprovalId;
    if (voiceApprovalId) {
      runApprovedAudioTranscription(voiceApprovalId);
      return;
    }
    const approvalId = target.dataset.approvalId;
    const command = target.dataset.command;
    const profile = target.dataset.profile || "observe";
    if (!approvalId || !command) return;
    request("pty.create", privilegedParams({
      command,
      profile,
      approval_id: approvalId,
      session_id: currentSessionId()
    }));
    log(`Approved launch requested for ${approvalId}. Runtime policy gate still applies.`);
  });

  requestProposalApproval.addEventListener("click", () => {
    if (!lastVoiceProposal) {
      log("No voice intent proposal is available for approval.");
      return;
    }
    const operation = lastVoiceProposal.command
      ? lastVoiceProposal.command
      : `${lastVoiceProposal.intent_type}:${lastVoiceProposal.target}:${lastVoiceProposal.summary}`;
    const risk = lastVoiceProposal.policy && lastVoiceProposal.policy.risk
      ? lastVoiceProposal.policy.risk
      : (lastVoiceProposal.intent_type === "command_proposal" ? "high" : "medium");
    request("approval.request", {
      session_id: currentSessionId(),
      summary: `Review voice proposal: ${lastVoiceProposal.summary}`,
      operation,
      risk,
      scope: {
        source: "voice.intent_propose",
        proposal_id: lastVoiceProposal.proposal_id,
        intent_type: lastVoiceProposal.intent_type,
        target: lastVoiceProposal.target,
        command: lastVoiceProposal.command || "",
        execution_authority: false
      }
    });
    log("Approval requested for voice intent proposal. No command was executed.");
  });

  function selectedSttModelId() {
    return (sttModelId.value || "tiny.en").trim() || "tiny.en";
  }

  function requestAudioTranscriptionApproval() {
    if (!lastAudioPath) {
      voiceLog.textContent = "Record a local audio chunk before requesting transcription approval.";
      log("Audio transcription approval requires a captured runtime audio path.");
      return;
    }
    const modelId = selectedSttModelId();
    request("approval.request", {
      session_id: currentSessionId(),
      summary: `Transcribe captured local audio ${lastAudioUtteranceId || ""}`.trim(),
      operation: "voice.transcribe_audio",
      risk: "medium",
      scope: {
        source: "voice.transcribe_audio",
        audio_file: lastAudioPath,
        model_id: modelId,
        execution_authority: false
      }
    });
    voiceLog.textContent = `Audio transcription approval requested for model id ${modelId}. No transcription has run.`;
    log("Audio transcription approval requested. No local STT adapter was started.");
  }

  function runApprovedAudioTranscription(approvalId = "") {
    const effectiveApprovalId = (approvalId || sttApprovalId.value || "").trim();
    if (!lastAudioPath) {
      voiceLog.textContent = "No captured local audio path is available for transcription.";
      log("Approved audio transcription requires a captured runtime audio path.");
      return;
    }
    if (!effectiveApprovalId) {
      voiceLog.textContent = "Paste or select an approved audio transcription approval id first.";
      log("Approved audio transcription requires an approval id.");
      return;
    }
    sttApprovalId.value = effectiveApprovalId;
    const modelId = selectedSttModelId();
    request("voice.transcribe_audio", privilegedParams({
      session_id: currentSessionId(),
      audio_file: lastAudioPath,
      model_id: modelId,
      approval_id: effectiveApprovalId,
      provider: "local-stt-adapter",
      timeout_seconds: 120
    }));
    voiceLog.textContent = `Approved local STT requested with model id ${modelId}.`;
    log("Approved local STT transcription requested through runtime policy gates.");
  }

  requestTranscriptionApproval.addEventListener("click", requestAudioTranscriptionApproval);
  transcribeCapturedAudio.addEventListener("click", () => runApprovedAudioTranscription());

  micToggle.addEventListener("click", async () => {
    if (micStream) {
      if (recognition) {
        recognition.stop();
        recognition = null;
      }
      if (mediaRecorder && mediaRecorder.state !== "inactive") {
        stoppingRecorder = true;
        mediaRecorder.stop();
      }
      micStream.getTracks().forEach((track) => track.stop());
      micStream = null;
      mediaRecorder = null;
      micToggle.classList.remove("active");
      voiceStatus.textContent = "idle";
      voiceLog.textContent = "Microphone stopped. No further audio is sent to the Jarvis runtime.";
      request("voice.stop", { session_id: currentSessionId(), provider: "browser-web-speech" });
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      voiceLog.textContent = "Browser microphone API is unavailable.";
      voiceStatus.textContent = "unavailable";
      return;
    }
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micToggle.classList.add("active");
      voiceStatus.textContent = "permission granted";
      voiceLog.textContent = "Microphone permission granted. Browser speech recognition will be used when available.";
      log("Microphone permission granted by browser.");
      request("voice.start", { session_id: currentSessionId(), provider: "browser-web-speech" });
      startSpeechRecognition();
    } catch (error) {
      voiceStatus.textContent = "blocked";
      voiceLog.textContent = `Microphone permission failed: ${error.name}`;
      log(`Microphone permission failed: ${error.name}`);
    }
  });

  function startSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      voiceStatus.textContent = "mic only";
      voiceLog.textContent = "Microphone is active. Browser SpeechRecognition is unavailable, so audio chunks will be stored locally for later STT.";
      log("Browser SpeechRecognition unavailable. Starting local audio chunk capture.");
      startMediaRecorderFallback();
      return;
    }
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognition.onstart = () => {
      voiceStatus.textContent = "listening";
      voiceLog.textContent = "Listening. Final transcripts are sent to Jarvis as voice.submit events.";
    };
    recognition.onerror = (event) => {
      voiceStatus.textContent = "stt error";
      voiceLog.textContent = `Speech recognition error: ${event.error}`;
      log(`Speech recognition error: ${event.error}`);
    };
    recognition.onend = () => {
      if (micStream) {
        voiceStatus.textContent = "mic active";
      }
    };
    recognition.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const text = event.results[i][0].transcript.trim();
        if (event.results[i].isFinal && text) {
          voiceLog.textContent = `Final transcript: ${text}`;
          request("voice.submit", {
            session_id: currentSessionId(),
            provider: "browser-web-speech",
            transcript: text
          });
          request("voice.intent_propose", {
            session_id: currentSessionId(),
            profile: "observe",
            transcript: text
          });
          log(`Voice transcript submitted: ${text}`);
        } else if (text) {
          interim += `${text} `;
        }
      }
      if (interim.trim()) {
        voiceLog.textContent = `Interim transcript: ${interim.trim()}`;
      }
    };
    recognition.start();
  }

  function renderVoiceProposal(proposal) {
    const command = proposal.command ? `\nCommand proposal: ${proposal.command}` : "";
    const policy = proposal.policy ? `\nPolicy: ${proposal.policy.status} (${proposal.policy.reason})` : "";
    proposalPreview.textContent = [
      `Intent: ${proposal.intent_type}`,
      `Target: ${proposal.target}`,
      `Summary: ${proposal.summary}`,
      `Approval required: ${proposal.approval_required}`,
      `Execution authority: ${proposal.execution_authority}`,
      command.trim(),
      policy.trim()
    ].filter(Boolean).join("\n");
  }

  function renderApprovals(approvals) {
    if (!approvals.length) {
      approvalsList.textContent = "No pending approvals.";
      return;
    }
    approvalsList.innerHTML = approvals.map((approval) => {
      const scope = JSON.stringify(approval.scope || {}, null, 2);
      return `
        <section class="approval-item">
          <strong>${escapeHtml(approval.summary || approval.id)}</strong>
          <div>Risk: ${escapeHtml(approval.risk || "medium")}</div>
          <div>Operation: ${escapeHtml(approval.operation || "")}</div>
          <pre>Scope: ${escapeHtml(scope)}</pre>
          <button type="button" data-approval-id="${escapeHtml(approval.id)}" data-approval-action="approved">Approve</button>
          <button type="button" class="danger" data-approval-id="${escapeHtml(approval.id)}" data-approval-action="rejected">Reject</button>
        </section>
      `;
    }).join("");
  }

  function renderSessions(sessions) {
    if (!sessions.length) {
      sessionsList.textContent = "No active sessions yet. Create one to bind approvals and voice events to a durable session.";
      return;
    }
    sessionsList.innerHTML = sessions.map((session) => `
      <section class="approval-item">
        <strong>${escapeHtml(session.title || session.id)}</strong>
        <div>ID: ${escapeHtml(session.id)}</div>
        <div>Profile: ${escapeHtml(session.profile_id || "observe")} | Updated: ${escapeHtml(session.updated_at || "")}</div>
        <button type="button" data-session-id="${escapeHtml(session.id)}">Use Session</button>
        <button type="button" data-fork-session-id="${escapeHtml(session.id)}">Fork Session</button>
        <button type="button" class="danger" data-archive-session-id="${escapeHtml(session.id)}">Archive Session</button>
      </section>
    `).join("");
  }

  function renderProfiles(profiles, defaultProfile) {
    sessionProfile.innerHTML = profiles.map((profile) => `
      <option value="${escapeHtml(profile.id)}">${escapeHtml(profile.label || profile.id)}</option>
    `).join("");
    sessionProfile.value = defaultProfile || "observe";
    log(`Loaded ${profiles.length} policy profiles. Profile selection changes session metadata only.`);
  }

  function refreshSessionHistory() {
    request("message.list", { session_id: currentSessionId(), limit: 25 });
  }

  function renderSessionHistory(messages, currentSequence) {
    if (!messages.length) {
      sessionHistory.textContent = `No semantic history for ${currentSessionId()} yet. Current sequence: ${currentSequence || 0}.`;
      return;
    }
    sessionHistory.innerHTML = messages.map((message) => {
      const payload = JSON.stringify(message.payload || {}, null, 2);
      return `
        <section class="approval-item">
          <strong>${escapeHtml(message.event_type || "event")}</strong>
          <div>Sequence: ${escapeHtml(message.sequence || "")} | Session: ${escapeHtml(message.session_id || "")}</div>
          <pre>${escapeHtml(payload)}</pre>
        </section>
      `;
    }).join("");
  }

  function renderSearchResults(results, query) {
    if (!query) {
      historySearchResults.textContent = "Enter a search query to search semantic history.";
      return;
    }
    if (!results.length) {
      historySearchResults.textContent = `No read-only history matches for "${query}".`;
      return;
    }
    historySearchResults.innerHTML = results.map((result) => {
      const payload = JSON.stringify(result.payload || {}, null, 2);
      return `
        <section class="approval-item">
          <strong>${escapeHtml(result.event_type || "event")}</strong>
          <div>Sequence: ${escapeHtml(result.sequence || "")} | Session: ${escapeHtml(result.session_id || "")}</div>
          <pre>${escapeHtml(payload)}</pre>
        </section>
      `;
    }).join("");
  }

  function renderCodeburnStatus(status) {
    if (!status || !status.available) {
      codeburnStatus.textContent = "unavailable";
      log(`Codeburn status unavailable: ${status && status.error ? status.error : "unknown"}.`);
      return;
    }
    codeburnStatus.textContent = `$${status.month_cost} / ${status.month_calls}`;
    log(`Codeburn month usage: $${status.month_cost} across ${status.month_calls} calls.`);
  }

  function renderAgentProviders(status) {
    const providers = Array.isArray(status.providers) ? status.providers : [];
    agentProviderStatus.textContent = `${providers.filter((provider) => provider.command_available).length}/${providers.length}`;
    if (!providers.length) {
      agentProviderList.textContent = "No agent providers reported. No launch performed.";
      return;
    }
    agentProviderList.innerHTML = providers.map((provider) => `
      <section class="approval-item">
        <strong>${escapeHtml(provider.label || provider.id)}</strong>
        <div>Role: ${escapeHtml(provider.role || "")}</div>
        <div>Command: ${escapeHtml(provider.command || "")} | Available: ${provider.command_available ? "yes" : "no"}</div>
        <div>Boundary: ${escapeHtml(provider.execution_boundary || "")}</div>
        <div>Launch performed: ${provider.launch_performed ? "yes" : "no"} | Writes state: ${provider.writes_state ? "yes" : "no"}</div>
      </section>
    `).join("");
    log(`Agent provider status loaded for ${providers.length} providers. No agents launched.`);
  }

  function renderReadiness(readiness) {
    lastReadiness = readiness;
    readinessStatus.textContent = readiness.status || "unknown";
    const gaps = Array.isArray(readiness.remaining_gaps) ? readiness.remaining_gaps : [];
    readinessGaps.textContent = gaps.length
      ? `Remaining release gaps: ${gaps.join(", ")}`
      : "No remaining release gaps reported.";
    renderMobileAccess(readiness.mobile_access || {});
    log(`Runtime readiness: ${readiness.status || "unknown"}; production complete: ${Boolean(readiness.production_complete)}.`);
  }

  function renderMobileAccess(mobileAccess) {
    const candidate = mobileAccess.recommended_candidate || null;
    mobileAccessStatus.textContent = mobileAccess.status || "unknown";
    if (!candidate) {
      const warnings = Array.isArray(mobileAccess.warnings) && mobileAccess.warnings.length
        ? mobileAccess.warnings.join(" ")
        : "No private-network candidate reported.";
      mobileAccessPanel.textContent = `Mobile access is ${mobileAccess.status || "unknown"}. ${warnings} No runtime was launched, no network probe ran, and no approval was granted.`;
      return;
    }
    mobileAccessPanel.innerHTML = `
      <section class="approval-item">
        <strong>Private mobile candidate</strong>
        <div>URL: ${escapeHtml(candidate.url || "")}</div>
        <div>Interface: ${escapeHtml(candidate.interface || "")} | Host class: ${escapeHtml(candidate.host_class || "")}</div>
        <div>Runtime command proposal: <code>${escapeHtml(candidate.runtime_command || "")}</code></div>
        <div>Preflight command: <code>${escapeHtml(candidate.preflight_command || "")}</code></div>
        <div>Validation plan: <code>${escapeHtml(candidate.validation_plan_command || "")}</code></div>
        <div>No runtime was launched, no browser opened, no network probe ran, and displayed commands are not execution authority.</div>
      </section>
    `;
  }

  function renderMobileEvidenceBrief(brief) {
    const evidence = Array.isArray(brief.required_operator_evidence) ? brief.required_operator_evidence : [];
    const unsafe = Array.isArray(brief.unsafe_actions) ? brief.unsafe_actions : [];
    mobileEvidencePanel.innerHTML = `
      <section class="approval-item">
        <strong>${escapeHtml(brief.label || "Mobile evidence brief")}</strong>
        <div>Status: ${escapeHtml(brief.status || "unknown")} | Target: ${escapeHtml(brief.target_url || "")}</div>
        <div>Runtime command proposal: <code>${escapeHtml(brief.runtime_command || "")}</code></div>
        <div>Release evidence command: <code>${escapeHtml(brief.release_evidence_command || "")}</code></div>
        <div>Required evidence: ${escapeHtml(evidence.slice(0, 3).join("; ") || "none reported")}</div>
        <div>Unsafe actions not authorized: ${escapeHtml(unsafe.slice(0, 3).join("; ") || "none reported")}</div>
        <div>No runtime was launched, no browser opened, no network probe ran, no state was written, and the mobile gate remains open.</div>
      </section>
    `;
    log(`Mobile evidence brief loaded for ${brief.target_url || "unknown target"}. It does not prove iPhone validation or close the gate.`);
  }

  function renderGeminiEvidenceBrief(brief) {
    const evidence = Array.isArray(brief.required_operator_evidence) ? brief.required_operator_evidence : [];
    const unsafe = Array.isArray(brief.unsafe_actions) ? brief.unsafe_actions : [];
    const authModes = Array.isArray(brief.auth_modes_present) && brief.auth_modes_present.length
      ? brief.auth_modes_present.join(", ")
      : "none";
    geminiEvidencePanel.innerHTML = `
      <section class="approval-item">
        <strong>${escapeHtml(brief.label || "Gemini evidence brief")}</strong>
        <div>Status: ${escapeHtml(brief.status || "unknown")} | Auth signals: ${escapeHtml(authModes)}</div>
        <div>Recommended path: ${escapeHtml(brief.recommended_path || "")}</div>
        <div>Network test proposal: <code>${escapeHtml(brief.network_test_command || "")}</code></div>
        <div>Release evidence command: <code>${escapeHtml(brief.release_evidence_command || "")}</code></div>
        <div>Required evidence: ${escapeHtml(evidence.slice(0, 3).join("; ") || "none reported")}</div>
        <div>Unsafe actions not authorized: ${escapeHtml(unsafe.slice(0, 3).join("; ") || "none reported")}</div>
        <div>No OAuth flow started, no WebSocket opened, no network probe ran, no secret was exposed, no cloud spend was approved, and the Gemini gate remains open.</div>
      </section>
    `;
    log(`Gemini evidence brief loaded: ${brief.status || "unknown"}. It does not prove Gemini Live validation or close the gate.`);
  }

  function renderPackagingEvidenceBrief(brief) {
    const required = Array.isArray(brief.required_operator_evidence) ? brief.required_operator_evidence : [];
    const commands = Array.isArray(brief.release_evidence_commands) ? brief.release_evidence_commands : [];
    const unsafe = Array.isArray(brief.unsafe_actions) ? brief.unsafe_actions : [];
    packagingEvidencePanel.innerHTML = `
      <section class="approval-item">
        <strong>${escapeHtml(brief.label || "Packaging evidence brief")}</strong>
        <div>Status: ${escapeHtml(brief.status || "unknown")} | Preflight: ${escapeHtml(brief.packaging_preflight_status || "unknown")} | Artifact evidence: ${escapeHtml(brief.artifact_evidence_status || "unknown")}</div>
        <div>Required evidence: ${escapeHtml(required.slice(0, 3).join("; ") || "none reported")}</div>
        <div>Release evidence command: <code>${escapeHtml(commands[0] || "Record accepted packaging/signing evidence after human review.")}</code></div>
        <div>Unsafe actions not authorized: ${escapeHtml(unsafe.slice(0, 3).join("; ") || "none reported")}</div>
        <div>No install, package build, signing, copy, upload, publish, service launch, or gate closure was performed.</div>
      </section>
    `;
    log(`Packaging evidence brief loaded: ${brief.status || "unknown"}. It does not build, sign, publish, or close release gates.`);
  }

  function renderSecurityEvidenceBrief(brief) {
    const required = Array.isArray(brief.required_operator_evidence) ? brief.required_operator_evidence : [];
    const unsafe = Array.isArray(brief.unsafe_actions) ? brief.unsafe_actions : [];
    securityEvidencePanel.innerHTML = `
      <section class="approval-item">
        <strong>${escapeHtml(brief.label || "External security evidence brief")}</strong>
        <div>Status: ${escapeHtml(brief.status || "unknown")} | Plan: ${escapeHtml(brief.security_review_plan_status || "unknown")}</div>
        <div>Release evidence command: <code>${escapeHtml(brief.release_evidence_command || "")}</code></div>
        <div>Required evidence: ${escapeHtml(required.slice(0, 3).join("; ") || "none reported")}</div>
        <div>Unsafe actions not authorized: ${escapeHtml(unsafe.slice(0, 3).join("; ") || "none reported")}</div>
        <div>No scanner, service launch, network probe, build, signing, copy, publish, state write, or gate closure was performed.</div>
      </section>
    `;
    log(`External security evidence brief loaded: ${brief.status || "unknown"}. It does not complete external review or close the gate.`);
  }

  function renderReleaseGateStatus(status) {
    const gates = Array.isArray(status.gates) ? status.gates : [];
    releaseGateStatus.textContent = `${status.open_gate_count ?? gates.length} open`;
    if (!gates.length) {
      releaseGatePanel.textContent = "No release gates reported. No state was written and no approval was granted.";
      return;
    }
    releaseGatePanel.innerHTML = gates.map((gate) => `
      <section class="approval-item">
        <strong>${escapeHtml(gate.gate || "release_gate")}</strong>
        <div>Status: ${escapeHtml(gate.status || "open")} | Evidence records: ${Number(gate.evidence_count || 0)} | Acceptances: ${Number(gate.acceptance_count || 0)}</div>
        <div>Latest reviewer: ${escapeHtml(gate.latest_reviewer || "none")} | Latest evidence: ${escapeHtml(gate.latest_evidence_id || "none")}</div>
        <div>Latest acceptance: ${escapeHtml(gate.latest_acceptance_id || "none")} | Accepted evidence: ${escapeHtml(gate.accepted_evidence_id || "none")}</div>
        <div>Human acceptance required: ${gate.requires_human_acceptance ? "yes" : "no"} | Gate closed: ${gate.release_gate_closed ? "yes" : "no"}</div>
      </section>
    `).join("");
    log(`Release gate status loaded: ${status.open_gate_count ?? gates.length} open gate(s). Evidence records do not close gates.`);
  }

  function renderReleaseAcceptanceBrief(brief) {
    const items = Array.isArray(brief.acceptance_items) ? brief.acceptance_items : [];
    const ready = Array.isArray(brief.ready_for_acceptance) ? brief.ready_for_acceptance : [];
    if (!items.length) {
      releaseAcceptanceBriefPanel.textContent = "No acceptance brief items reported. No state was written and no approval was granted.";
      return;
    }
    releaseAcceptanceBriefPanel.innerHTML = items.slice(0, 6).map((item) => {
      const command = item.acceptance_command || "Record matching evidence before acceptance.";
      return `
        <section class="approval-item">
          <strong>${escapeHtml(item.gate || "release_gate")}</strong>
          <div>Status: ${escapeHtml(item.status || "needs-evidence")} | Evidence records: ${Number(item.evidence_count || 0)} | Acceptances: ${Number(item.acceptance_count || 0)}</div>
          <div>Latest evidence: ${escapeHtml(item.latest_evidence_id || "none")} | Accepted evidence: ${escapeHtml(item.accepted_evidence_id || "none")}</div>
          <div>Display-only acceptance command: <code>${escapeHtml(command)}</code></div>
          <div>Gate closed: ${item.release_gate_closed ? "yes" : "no"} | Human acceptance required: ${item.requires_human_acceptance ? "yes" : "no"}</div>
        </section>
      `;
    }).join("");
    log(`Release acceptance brief loaded: ${ready.length} gate(s) ready for human acceptance. Displayed commands are not execution authority.`);
  }

  function renderReleaseChecklist(checklist) {
    const items = Array.isArray(checklist.checklist) ? checklist.checklist : [];
    const blocked = Array.isArray(checklist.blocked_by) ? checklist.blocked_by : [];
    releaseChecklistStatus.textContent = `${blocked.length || items.length} blocked`;
    if (!items.length) {
      releaseChecklistPanel.textContent = "No release checklist items reported. No state was written and no approval was granted.";
      return;
    }
    releaseChecklistPanel.innerHTML = items.slice(0, 6).map((item) => {
      const command = item.read_only_command || "";
      const evidenceCount = Number(item.evidence_count || 0);
      return `
        <section class="approval-item">
          <strong>${escapeHtml(item.gate || "release_gate")}</strong>
          <div>Status: ${escapeHtml(item.status || "open")} | Evidence records: ${evidenceCount}</div>
          <div>Next action: ${escapeHtml(item.next_action || "")}</div>
          <div>Display-only command: <code>${escapeHtml(command)}</code></div>
          <div>Gate closed: ${item.release_gate_closed ? "yes" : "no"} | Human acceptance required: ${item.requires_human_acceptance ? "yes" : "no"}</div>
        </section>
      `;
    }).join("");
    log(`Release readiness checklist loaded: ${blocked.length || items.length} blocked item(s). Displayed commands are not execution authority.`);
  }

  function speakRuntimeStatus() {
    if (!("speechSynthesis" in window) || typeof SpeechSynthesisUtterance === "undefined") {
      voiceLog.textContent = "Browser speech synthesis is unavailable. No local TTS command was run.";
      log("Browser speech synthesis unavailable.");
      return;
    }
    const readiness = lastReadiness || { status: "unknown", remaining_gaps: [] };
    const gaps = Array.isArray(readiness.remaining_gaps) ? readiness.remaining_gaps : [];
    const summary = gaps.length
      ? `Jarvis runtime is ${readiness.status || "unknown"}. Remaining release gaps: ${gaps.slice(0, 4).join(", ")}.`
      : `Jarvis runtime is ${readiness.status || "unknown"}. No remaining release gaps reported.`;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(summary);
    utterance.rate = 0.95;
    utterance.pitch = 0.85;
    window.speechSynthesis.speak(utterance);
    voiceLog.textContent = "Speaking browser-managed runtime status. This does not run local TTS or execute commands.";
    log("Browser-managed voice output requested. No local TTS command was run.");
  }

  function approvedLaunchCommand(approval) {
    if (!approval || approval.status !== "approved") return "";
    const scope = approval.scope || {};
    if (scope.source !== "hud.pane.prepare") return "";
    const command = scope.command || approval.operation || "";
    if (!command || command !== approval.operation) return "";
    return command;
  }

  function renderApprovedLaunches(approvals) {
    const launches = approvals
      .map((approval) => ({ approval, command: approvedLaunchCommand(approval) }))
      .filter((item) => item.command);
    const voiceTranscriptions = approvals.filter((approval) => {
      const scope = approval.scope || {};
      return approval.status === "approved"
        && approval.operation === "voice.transcribe_audio"
        && scope.source === "voice.transcribe_audio";
    });
    if (!launches.length && !voiceTranscriptions.length) {
      approvedLaunches.textContent = "No approved pane launches or voice transcriptions are ready.";
      return;
    }
    const launchMarkup = launches.map(({ approval, command }) => {
      const profile = approval.scope && approval.scope.profile ? approval.scope.profile : "observe";
      return `
        <section class="approval-item">
          <strong>${escapeHtml(approval.summary || approval.id)}</strong>
          <div>Approved operation: ${escapeHtml(command)}</div>
          <div>Execution remains runtime-gated and command-matched to this approval.</div>
          <button type="button" data-approval-id="${escapeHtml(approval.id)}" data-command="${escapeHtml(command)}" data-profile="${escapeHtml(profile)}">Launch Approved PTY</button>
        </section>
      `;
    });
    const voiceMarkup = voiceTranscriptions.map((approval) => {
      const scope = approval.scope || {};
      return `
        <section class="approval-item">
          <strong>${escapeHtml(approval.summary || approval.id)}</strong>
          <div>Approved voice audio: ${escapeHtml(scope.audio_file || "")}</div>
          <div>Model id: ${escapeHtml(scope.model_id || selectedSttModelId())}</div>
          <div>Transcription remains runtime-token gated and does not grant command execution authority.</div>
          <button type="button" data-voice-transcribe-approval-id="${escapeHtml(approval.id)}">Transcribe Approved Audio</button>
        </section>
      `;
    });
    approvedLaunches.innerHTML = [...launchMarkup, ...voiceMarkup].join("");
  }

  function startMediaRecorderFallback() {
    if (!window.MediaRecorder || !micStream) {
      voiceStatus.textContent = "mic only";
      voiceLog.textContent = "MediaRecorder is unavailable. No audio chunks are sent.";
      return;
    }
    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";
    audioSequence = 0;
    utteranceId = `utt_${Date.now().toString(36)}`;
    stoppingRecorder = false;
    mediaRecorder = new MediaRecorder(micStream, { mimeType });
    mediaRecorder.onstart = () => {
      voiceStatus.textContent = "recording";
      voiceLog.textContent = "Recording local audio chunks. Transcription remains approval-gated.";
    };
    mediaRecorder.ondataavailable = async (event) => {
      if (!event.data || event.data.size === 0) {
        return;
      }
      const chunkB64 = await blobToBase64(event.data);
      request("voice.audio_chunk", {
        session_id: currentSessionId(),
        utterance_id: utteranceId,
        sequence: audioSequence,
        mime_type: mimeType,
        chunk_b64: chunkB64,
        final: stoppingRecorder
      });
      audioSequence += 1;
    };
    mediaRecorder.onerror = (event) => {
      voiceStatus.textContent = "recording error";
      voiceLog.textContent = `MediaRecorder error: ${event.error.name}`;
      log(`MediaRecorder error: ${event.error.name}`);
    };
    mediaRecorder.start(1000);
  }

  function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const value = String(reader.result || "");
        resolve(value.includes(",") ? value.split(",")[1] : value);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  connect();
  registerPwa();
})();
"""

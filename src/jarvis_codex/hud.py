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
      min-height: 100vh;
      overflow-x: hidden;
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
      width: min(1420px, calc(100% - 32px));
      margin: 0 auto;
      padding: 22px 0 34px;
      display: grid;
      gap: 18px;
    }

    header {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 18px;
      align-items: center;
      border-bottom: 1px solid var(--line);
      padding-bottom: 18px;
    }

    h1 {
      margin: 0;
      color: var(--cyan);
      font-size: clamp(34px, 5vw, 80px);
      line-height: 0.9;
      text-transform: uppercase;
    }

    .subtitle {
      margin: 10px 0 0;
      color: var(--muted);
      max-width: 820px;
      line-height: 1.55;
    }

    .core {
      width: 210px;
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
      font-size: 30px;
    }

    .topology {
      display: grid;
      grid-template-columns: 0.9fr 1.2fr 0.9fr;
      gap: 16px;
      align-items: stretch;
    }

    .panel {
      border: 1px solid var(--line);
      background: var(--panel);
      box-shadow: 0 0 34px rgba(76, 220, 255, 0.07);
      min-width: 0;
    }

    .panel h2 {
      margin: 0;
      padding: 13px 14px;
      border-bottom: 1px solid var(--line-soft);
      color: var(--cyan);
      font-size: 14px;
      text-transform: uppercase;
    }

    .panel-body { padding: 14px; }

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
      height: 360px;
      overflow: auto;
      padding: 14px;
      background: #02070d;
      border-top: 1px solid var(--line-soft);
      font: 13px/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      color: #c6f7ff;
      white-space: pre-wrap;
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
      min-height: 120px;
      border: 1px solid var(--line-soft);
      padding: 12px;
      color: var(--muted);
      background: rgba(1, 13, 20, 0.74);
      line-height: 1.5;
    }

    @media (max-width: 1000px) {
      header,
      .topology {
        grid-template-columns: 1fr;
      }

      .core {
        width: 160px;
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

    <section class="topology">
      <div class="panel">
        <h2>Runtime Status</h2>
        <div class="panel-body status-grid">
          <div class="metric"><small>Socket</small><strong id="socket-status">offline</strong></div>
          <div class="metric"><small>Policy</small><strong>gated</strong></div>
          <div class="metric"><small>Voice</small><strong id="voice-status">idle</strong></div>
          <div class="metric"><small>Approvals</small><strong id="approval-count">0</strong></div>
          <div class="metric"><small>Codeburn</small><strong id="codeburn-status">unknown</strong></div>
          <div class="metric"><small>PWA</small><strong id="pwa-status">checking</strong></div>
          <div class="metric"><small>Readiness</small><strong id="readiness-status">unknown</strong></div>
        </div>
        <div id="readiness-gaps" class="log">Readiness summary pending.</div>
        <button id="refresh-readiness" type="button">Refresh Readiness</button>
      </div>

      <div class="panel">
        <h2>Harness Panes</h2>
        <div class="panel-body pane-list">
          <div class="agent-pane"><div><strong>Codex</strong><span>Implementation and verification lane</span></div><button data-pane="codex">Prepare</button></div>
          <div class="agent-pane"><div><strong>Antigravity</strong><span>Architecture and adversarial review lane</span></div><button data-pane="antigravity">Prepare</button></div>
          <div class="agent-pane"><div><strong>Codeburn</strong><span>Fixed no-shell usage telemetry lane</span></div><button id="refresh-codeburn" type="button">Status</button></div>
        </div>
        <div id="console" class="console" aria-live="polite">Jarvis runtime console ready.</div>
      </div>

      <div class="panel">
        <h2>Voice Control</h2>
        <div class="panel-body voice">
          <button id="mic-toggle" class="voice-button" type="button">Mic</button>
          <button id="speak-status" type="button">Speak Status</button>
          <div id="voice-log" class="log">Microphone is disabled until you click the button and approve browser permission.</div>
          <div id="proposal-preview" class="log">Voice intent proposals will appear here. They do not execute commands.</div>
          <button id="request-proposal-approval" type="button">Request Proposal Approval</button>
          <button id="refresh-approvals" type="button">Refresh Approvals</button>
          <div id="approvals-list" class="log">No pending approvals loaded.</div>
          <div id="approved-launches" class="log">Approved pane launches will appear here after approval.</div>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>Session Continuity</h2>
      <div class="panel-body">
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
        <button id="refresh-session-history" type="button">Refresh Session History</button>
        <div id="session-history" class="log">Semantic session history will appear here. This is not an execution queue.</div>
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
  const requestProposalApproval = document.getElementById("request-proposal-approval");
  const approvalCount = document.getElementById("approval-count");
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
  const codeburnStatus = document.getElementById("codeburn-status");
  const refreshCodeburn = document.getElementById("refresh-codeburn");
  const pwaStatus = document.getElementById("pwa-status");
  const readinessStatus = document.getElementById("readiness-status");
  const readinessGaps = document.getElementById("readiness-gaps");
  const refreshReadiness = document.getElementById("refresh-readiness");
  let socket;
  let requestSeq = 0;
  const requestIndex = new Map();
  let activeSessionId = "hud";
  let micStream = null;
  let recognition = null;
  let mediaRecorder = null;
  let audioSequence = 0;
  let utteranceId = null;
  let stoppingRecorder = false;
  let lastVoiceProposal = null;
  let lastReadiness = null;
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
      request("telemetry.codeburn_status");
      request("runtime.readiness");
    });
    socket.addEventListener("close", () => {
      socketStatus.textContent = "offline";
      log("Runtime socket closed.");
      setTimeout(connect, 1500);
    });
    socket.addEventListener("message", (event) => {
      const frame = JSON.parse(event.data);
      if (frame.type === "stream") {
        log(`PTY ${frame.channel_id}: ${frame.chunk.trimEnd()}`);
        return;
      }
      if (frame.type === "event") {
        log(`Event: ${frame.event_type}`);
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
        refreshSessionHistory();
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
      if (frame.type === "response" && frame.result && Object.prototype.hasOwnProperty.call(frame.result, "production_complete")) {
        renderReadiness(frame.result);
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
        log(`PTY channel launched: ${frame.result.channel_id}. Approval: ${frame.result.approval_id || "none"}.`);
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

  createSession.addEventListener("click", () => {
    request("session.create", {
      title: `HUD session ${new Date().toLocaleString()}`,
      profile_id: selectedProfileId(),
      source_client: "hud",
      actor_id: "user"
    });
    log("HUD session creation requested.");
  });

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
    const text = promptText.value.trim();
    if (!text) {
      log("Prompt text is empty; nothing recorded.");
      return;
    }
    request("prompt.send", {
      session_id: currentSessionId(),
      text,
      target: "planning",
      source_client: "hud",
      actor_id: "user"
    });
    log("Prompt record requested. This does not execute a command or agent.");
  });

  refreshCodeburn.addEventListener("click", () => {
    request("telemetry.codeburn_status");
    log("Codeburn telemetry refresh requested.");
  });

  refreshReadiness.addEventListener("click", () => {
    request("runtime.readiness");
    log("Runtime readiness refresh requested.");
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
    activeSessionId = sessionId;
    activeSession.textContent = `Active session: ${sessionId}`;
    log(`Selected session ${sessionId}.`);
    refreshSessionHistory();
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
    const approvalId = target.dataset.approvalId;
    const command = target.dataset.command;
    const profile = target.dataset.profile || "observe";
    if (!approvalId || !command) return;
    request("pty.create", privilegedParams({
      command,
      profile,
      approval_id: approvalId
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

  function renderCodeburnStatus(status) {
    if (!status || !status.available) {
      codeburnStatus.textContent = "unavailable";
      log(`Codeburn status unavailable: ${status && status.error ? status.error : "unknown"}.`);
      return;
    }
    codeburnStatus.textContent = `$${status.month_cost} / ${status.month_calls}`;
    log(`Codeburn month usage: $${status.month_cost} across ${status.month_calls} calls.`);
  }

  function renderReadiness(readiness) {
    lastReadiness = readiness;
    readinessStatus.textContent = readiness.status || "unknown";
    const gaps = Array.isArray(readiness.remaining_gaps) ? readiness.remaining_gaps : [];
    readinessGaps.textContent = gaps.length
      ? `Remaining release gaps: ${gaps.join(", ")}`
      : "No remaining release gaps reported.";
    log(`Runtime readiness: ${readiness.status || "unknown"}; production complete: ${Boolean(readiness.production_complete)}.`);
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
    if (!launches.length) {
      approvedLaunches.textContent = "No approved pane launches are ready.";
      return;
    }
    approvedLaunches.innerHTML = launches.map(({ approval, command }) => {
      const profile = approval.scope && approval.scope.profile ? approval.scope.profile : "observe";
      return `
        <section class="approval-item">
          <strong>${escapeHtml(approval.summary || approval.id)}</strong>
          <div>Approved operation: ${escapeHtml(command)}</div>
          <div>Execution remains runtime-gated and command-matched to this approval.</div>
          <button type="button" data-approval-id="${escapeHtml(approval.id)}" data-command="${escapeHtml(command)}" data-profile="${escapeHtml(profile)}">Launch Approved PTY</button>
        </section>
      `;
    }).join("");
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

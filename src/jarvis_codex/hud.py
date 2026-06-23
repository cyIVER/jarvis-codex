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


HUD_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
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
        </div>
      </div>

      <div class="panel">
        <h2>Harness Panes</h2>
        <div class="panel-body pane-list">
          <div class="agent-pane"><div><strong>Codex</strong><span>Implementation and verification lane</span></div><button data-pane="codex">Prepare</button></div>
          <div class="agent-pane"><div><strong>Antigravity</strong><span>Architecture and adversarial review lane</span></div><button data-pane="antigravity">Prepare</button></div>
          <div class="agent-pane"><div><strong>Codeburn</strong><span>Usage and cost telemetry lane</span></div><button data-pane="codeburn">Prepare</button></div>
        </div>
        <div id="console" class="console" aria-live="polite">Jarvis runtime console ready.</div>
      </div>

      <div class="panel">
        <h2>Voice Control</h2>
        <div class="panel-body voice">
          <button id="mic-toggle" class="voice-button" type="button">Mic</button>
          <div id="voice-log" class="log">Microphone is disabled until you click the button and approve browser permission.</div>
          <div id="proposal-preview" class="log">Voice intent proposals will appear here. They do not execute commands.</div>
          <button id="request-proposal-approval" type="button">Request Proposal Approval</button>
          <button id="refresh-approvals" type="button">Refresh Approvals</button>
        </div>
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
  const requestProposalApproval = document.getElementById("request-proposal-approval");
  const approvalCount = document.getElementById("approval-count");
  let socket;
  let requestSeq = 0;
  let micStream = null;
  let recognition = null;
  let mediaRecorder = null;
  let audioSequence = 0;
  let utteranceId = null;
  let stoppingRecorder = false;
  let lastVoiceProposal = null;

  function log(line) {
    const stamp = new Date().toLocaleTimeString();
    consoleEl.textContent += `\n[${stamp}] ${line}`;
    consoleEl.scrollTop = consoleEl.scrollHeight;
  }

  function request(method, params = {}) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      log(`Socket is not connected. Cannot send ${method}.`);
      return;
    }
    requestSeq += 1;
    socket.send(JSON.stringify({ type: "request", id: `hud_${requestSeq}`, method, params }));
  }

  function connect() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(`${protocol}//${location.host}/ws`);
    socket.addEventListener("open", () => {
      socketStatus.textContent = "online";
      log("Connected to Jarvis runtime.");
      request("initialize");
      request("approval.list", { status: "pending" });
      request("voice.provider_status");
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
        }
        return;
      }
      if (frame.type === "response" && frame.result && frame.result.approvals) {
        approvalCount.textContent = String(frame.result.approvals.length);
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

  document.querySelectorAll("[data-pane]").forEach((button) => {
    button.addEventListener("click", () => {
      const pane = button.getAttribute("data-pane");
      log(`${pane} pane prepared. Execution requires an explicit runtime command and policy decision.`);
    });
  });

  document.getElementById("refresh-approvals").addEventListener("click", () => {
    request("approval.list", { status: "pending" });
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
      session_id: "hud",
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
      request("voice.stop", { session_id: "hud", provider: "browser-web-speech" });
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
      request("voice.start", { session_id: "hud", provider: "browser-web-speech" });
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
            session_id: "hud",
            provider: "browser-web-speech",
            transcript: text
          });
          request("voice.intent_propose", {
            session_id: "hud",
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
        session_id: "hud",
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
})();
"""

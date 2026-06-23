# Research Log

This log records the research grounding for the Jarvis harness production plan.

## 2026-06-22 Overnight Planning Loop

### ACP

Source: [Agent Client Protocol introduction](https://agentclientprotocol.com/get-started/introduction)

Findings:

- ACP standardizes communication between code editors and coding agents.
- Local agents commonly communicate through JSON-RPC over stdio.
- Remote agents can use HTTP or WebSocket.
- ACP includes agentic coding UX concepts such as diffs and Markdown user-facing text.

Jarvis decision:

- Use ACP-style JSON-RPC everywhere, including Electron, PWA, CLI, and future editor adapters.
- Keep PTY byte streams separate from semantic events.

### Gemini Live

Source: [Gemini Live API capabilities](https://ai.google.dev/gemini-api/docs/live-api/capabilities)

Findings:

- Gemini Live is documented as preview.
- It supports audio input and audio output.
- Audio input is raw little-endian 16-bit PCM with sample-rate metadata.
- The docs include session-management and ephemeral-token sections.

Jarvis decision:

- Gemini realtime voice is primary only if OAuth-compatible auth can support it.
- Do not silently switch to paid API-key usage.
- Keep local `faster-whisper` GPU and local TTS fallback.

### Gemini Live Feasibility Refresh

Sources:

- [Gemini Live API overview](https://ai.google.dev/gemini-api/docs/live-api)
- [Gemini Live API WebSocket guide](https://ai.google.dev/gemini-api/docs/live-api/get-started-websocket)
- [Gemini API OAuth quickstart](https://ai.google.dev/gemini-api/docs/oauth)
- [Gemini API key guidance](https://ai.google.dev/gemini-api/docs/api-key)

Findings:

- Gemini Live is still a stateful WebSocket API for low-latency voice and vision interaction.
- Browser-direct Live API should use ephemeral tokens rather than exposing long-lived API keys.
- OAuth is available for stricter access control, but the quickstart is testing-oriented.
- API-key behavior is changing in 2026, so unrestricted standard keys are not a production-safe default.

Jarvis decision:

- Add a read-only `jarvis-codex gemini feasibility --json` check that reports credential signals without showing secrets or connecting to Gemini.
- Keep actual Gemini Live network validation behind a separate approval gate.
- Prefer a server-mediated runtime adapter first; browser-direct Gemini Live waits for an ephemeral-token backend design.

### Electron Security

Source: [Electron security tutorial](https://www.electronjs.org/docs/latest/tutorial/security)

Findings:

- Electron apps require explicit hardening because they combine browser and desktop privileges.
- The renderer must not receive direct dangerous host capabilities.

Jarvis decision:

- Electron is a client. The runtime owns command execution, PTYs, policy, and approvals.
- UI clients render state and request actions through the runtime protocol.

### SQLite WAL

Source: [SQLite Write-Ahead Logging](https://sqlite.org/wal.html)

Findings:

- WAL allows readers and writers to proceed concurrently in common local-app workflows.
- WAL keeps changes in a separate log before checkpointing back into the database.

Jarvis decision:

- Use SQLite/WAL as the production event store.
- Keep append-only event discipline and rebuildable projections.

### Hermes Pattern Review

Sources:

- Hermes sessions, security, TUI, CLI, architecture, and rollback docs reviewed during planning.

Findings:

- Hermes uses durable sessions, profiles, terminal UX, checkpoints, and security gates.
- Its strongest transferable pattern is one runtime serving multiple clients.

Jarvis decision:

- Borrow Hermes patterns, but keep Jarvis independent and ACP-compatible.
- Add optional Hermes interop later.

### Local Harness Engineering

Sources:

- `harness-engineering` skill.
- `autoresearch` native wrapper and source docs.
- Project docs under `docs/`.

Findings:

- Autonomous loops need locked evaluators, append-only logs, explicit keep/discard states, and human-controlled surfaces.
- Current Jarvis already has local state, governance, voice ingress, hardware gates, plan viewer, and release docs.

Jarvis decision:

- Formalize loop runbook, Codeburn monitoring, AG challenge review, and phase commits.

### Browser STT And Audio Capture

Sources:

- MDN Web Speech API: `https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API`
- MDN SpeechRecognition: `https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition`
- MDN MediaRecorder: `https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder`
- FastAPI WebSockets: `https://fastapi.tiangolo.com/advanced/websockets/`

Findings:

- `SpeechRecognition` can provide browser-side speech-to-text, but MDN marks it limited availability, so Jarvis must detect it at runtime.
- `MediaRecorder` is broadly available and is the right next step for server-side audio chunk streaming to local STT.
- Browser STT must be visibly labeled as browser-managed because privacy behavior depends on the browser implementation.
- FastAPI WebSockets are suitable for the bidirectional control channel already used by the HUD.

Jarvis decision:

- Implement immediate click-to-mic browser STT through `SpeechRecognition` when available.
- Persist final browser transcripts through runtime `voice.submit` events with no execution authority.
- Keep server audio streaming via `MediaRecorder` as the next local STT adapter slice.

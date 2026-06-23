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


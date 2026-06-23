---
title: Jarvis Harness Decisions
tags:
  - jarvis-harness
  - decisions
status: active
---

# Jarvis Harness Decisions

## Locked Decisions

- Default harness shape: CLI-style command harness plus animated HUD.
- Runtime: Python FastAPI.
- Protocol: ACP-style JSON-RPC everywhere.
- State: SQLite/WAL append-only event store with FTS projections.
- Desktop: Electron, React, TypeScript, xterm.js, WebGL/Canvas HUD.
- Mobile v1: private-network PWA.
- Native iOS: future feature.
- Voice primary: Gemini realtime if OAuth-compatible auth permits it.
- Voice fallback: local `faster-whisper` GPU plus original cinematic local TTS.
- PTY model: runtime-managed PTY panes.
- Execution authority: policy-gated executor.
- Policy profiles: Observe, Dev Loop, Swarm, High-Risk Runtime.
- Swarm: dynamic risk-scaled roles.
- Git flow: validate, commit coherent groups, push to main, monitor status.

## Open Feasibility Gates

- Gemini realtime voice through available OAuth auth.
- Electron packaging route and installer format.
- Tailscale/WireGuard mobile endpoint details.
- Local cinematic TTS backend.


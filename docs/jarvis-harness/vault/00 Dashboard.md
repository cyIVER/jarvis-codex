---
title: Jarvis Harness Dashboard
tags:
  - jarvis-harness
  - dashboard
status: active
updated: 2026-06-23 04:47 EDT
---

# Jarvis Harness Dashboard

## Current Objective

Build a Claude Code style JARVIS harness that coordinates Codex, Antigravity, Codeburn, voice, swarm loops, desktop HUD, and private mobile PWA through a governed local runtime.

## Current State

- Specs created under `docs/jarvis-harness/`.
- Spec slice committed and pushed as `5bcd036`.
- Runtime event store and protocol frames committed and pushed as `5442ab5`.
- Policy classifier committed and pushed as `faa97b3`.
- Runtime FastAPI app slice committed and pushed as `6a9d518`.
- Managed PTY supervision committed and pushed as `21ef4ab`.
- Approval lifecycle committed and pushed as `1332552`.
- Live WebSocket PTY stream multiplexing committed and pushed as `276b5ab`.
- Runtime-served HUD shell committed and pushed as `7cbc5c5`.
- Browser STT transcript submission committed and pushed as `11aa08b`.
- Server-side MediaRecorder audio chunk ingestion committed and pushed as `162b9b6`.
- Approval-gated local STT transcription job wiring committed and pushed as `b8be669`.
- Plan-viewer harness route and queue-safety package committed and pushed as `13f2b06`.
- Voice intent proposal layer committed and pushed as `dc9eb7f`.
- Live semantic runtime event push committed and pushed as `479aeda`.
- Voice proposal approval UI committed and pushed as `29c3c65`.
- Approval-matched PTY launch boundary is validated and awaiting commit.
- Runtime foundation selected: [[02 Architecture#Runtime]].
- Event store selected: [[02 Architecture#Event Store]].
- Mobile v1 selected: private-network PWA.
- Native iOS moved to future scope.
- Voice selected: Gemini realtime primary if OAuth permits, local fallback otherwise.

## Active Work

- [[04 Phase Plan#Phase 1 Runtime Foundation And HUD Shell]]
- [[06 Morning Report]]

## Watchpoints

- Plan-viewer package must stay display-only and planning-only; commands and harness routes must not gain execution authority.
- Voice-origin command proposals must remain non-executing until an explicit runtime approval path is added.
- Gemini realtime OAuth feasibility is unproven.
- Electron security model must keep shell execution in runtime, not renderer.
- Rezun gap coverage must remain explicit: voice, memory, tools, and mobile continuity.

## Next

1. Commit and push approval-matched PTY launch boundary.
2. Continue into Codex/Antigravity pane launch UX and approval response controls.
3. Keep voice/STT feasibility, plan-viewer, and HUD design tied to the runtime API contract.

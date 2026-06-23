---
title: Jarvis Harness Dashboard
tags:
  - jarvis-harness
  - dashboard
status: active
updated: 2026-06-23 02:28 EDT
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
- Approval-matched PTY launch boundary committed and pushed as `6923200`.
- HUD approval response controls committed and pushed as `4ce3839`.
- Approved PTY launch controls committed and pushed as `b6f5fbf`.
- Session continuity controls committed and pushed as `2405333`.
- Live Codeburn telemetry committed and pushed as `fa1d8b1`.
- Mobile/PWA shell affordances committed and pushed as `b70ad56`.
- Production readiness runbook is committed with current implementation state, safety invariants, validation, and mobile gates.
- AG challenge review triggered safety hardening: one-shot approvals, server-configured STT adapter, narrowed dev-loop execution, and Codeburn telemetry-only HUD path.
- AG-triggered runtime safety hardening committed and pushed as `89b09fc`.
- Final integrated validation passed: governance PASS, 165 tests, and HUD/PWA browser smoke.
- Runtime readiness RPC committed and pushed as `c176976`.
- Runtime boundary hardening committed and pushed as `7d3e0b5`.
- HUD readiness panel committed and pushed as `495e7a9`.
- Browser-managed voice status output committed and pushed as `7d8685f`.
- Runtime policy profile catalog committed and pushed as `0b23f80`.
- Runtime semantic message history committed and pushed as `efe573e`.
- HUD semantic session history panel committed and pushed as `3e46529`.
- State-only session archive controls committed and pushed as `49f6fe9`.
- State-only session profile updates committed and pushed as `e08dbac`.
- Semantic prompt history composer committed and pushed as `8b893ed`.
- State-only session fork controls committed and pushed as `59b30f8`.
- Read-only session resume committed and pushed as `9d581a4`.
- Read-only semantic history search committed and pushed as `e8ca6e4`.
- Planning-only swarm plan recording committed and pushed as `f315583`.
- Current Codeburn snapshot: month `$577.58`, 6252 calls.
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
- Runtime message history is a semantic event/history view; it is not an execution queue.
- HUD session history renders event history only; it does not authorize command execution.
- Session archive is state lifecycle only; it does not execute shell, PTY, Worktrunk, or runtime workflows.
- Session profile changes are metadata only; they do not grant execution or approval authority.
- Prompt composer records semantic intent only; it does not launch Codex, Antigravity, PTY, Worktrunk, shell, or workflows.
- Session forks create lineage state only; they do not launch agents or commands.
- Session resume is read-only context rehydration; it does not write state or grant approval authority.
- History search is read-only semantic lookup over the event store; blank or missing state returns no results without writes.
- Swarm plans are semantic planning records only; they do not launch agents, Worktrunk, PTYs, shell commands, or workflows.
- Gemini realtime OAuth feasibility is unproven.
- Electron security model must keep shell execution in runtime, not renderer.
- Rezun gap coverage must remain explicit: voice, memory, tools, and mobile continuity.

## Next

1. Continue with remaining production gaps: Electron packaging, actual iPhone private-network validation, Gemini OAuth feasibility, local TTS, safe swarm start/stop design, and release packaging.
2. Keep final dashboard current if additional overnight slices land.
3. Keep voice/STT feasibility, plan-viewer, and HUD design tied to the runtime API contract.

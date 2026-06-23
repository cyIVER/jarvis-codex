---
title: Jarvis Harness Phase Plan
tags:
  - jarvis-harness
  - phases
status: active
---

# Jarvis Harness Phase Plan

## Phase 0 Spec Writeout

Status: committed and pushed.

Deliver:

- Modular specs.
- Obsidian vault.
- Morning HTML dashboard.
- Validation and commit.

## Phase 1 Runtime Foundation And HUD Shell

Status: in progress.

Deliver:

- SQLite event store.
- ACP runtime skeleton.
- Electron shell.
- Ten modes.

Completed:

- SQLite/WAL event store with FTS search projection.
- ACP-style protocol frame utilities.
- Runtime policy classifier with hardline block, approval, and allow decisions.
- FastAPI runtime app with `/health`, `/rpc`, WebSocket RPC, session creation, command classification, and planned-method stubs.
- Policy-gated PTY supervisor with create, input, resize, kill, cleanup, and runtime RPC wiring.
- Approval lifecycle service with persistent request/respond events, approval projections, runtime RPC methods, and `event.subscribe` replay framing.
- Live WebSocket PTY stream frames multiplexed with request/response traffic.

In progress:

- HUD shell and client runtime adapter.

## Phase 2 Managed PTYs

Status: implementation started.

Deliver:

- Runtime-supervised Codex, AG, shell, and Codeburn panes.

Completed:

- PTY supervisor module.
- Runtime RPC wiring for `pty.create`, `pty.input`, `pty.resize`, and `pty.kill`.
- Policy block and approval-required responses before process spawn.
- PTY output stream frames over WebSocket.

## Phase 3 Permissions

Status: implementation started.

Deliver:

- Policy profiles.
- Approval lifecycle.
- Hardline blocklist.

Completed:

- Persistent approval request and response events.
- One-shot approval response guard.
- Runtime `approval.request`, `approval.list`, and `approval.respond`.
- Runtime `event.subscribe` replay framing.

## Phase 4 Voice

Deliver:

- Gemini OAuth feasibility.
- Local faster-whisper fallback.
- Cinematic TTS adapter boundary.

## Phase 5 Swarm And Loops

Deliver:

- `/loop`.
- `/swarm`.
- Dynamic adversarial review.

## Phase 6 Mobile PWA

Deliver:

- Private-network iPhone PWA.

## Phase 7 Production Readiness

Deliver:

- End-to-end validation and release readiness report.

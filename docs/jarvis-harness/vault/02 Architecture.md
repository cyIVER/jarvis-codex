---
title: Jarvis Harness Architecture
tags:
  - jarvis-harness
  - architecture
status: active
---

# Jarvis Harness Architecture

## Runtime

Python FastAPI owns:

- ACP-style JSON-RPC.
- Session lifecycle.
- PTY supervision.
- Voice routing.
- Permissions.
- Swarms and loops.
- Event store writes.

## Event Store

SQLite/WAL stores canonical append-only events.

Projections provide:

- Search.
- HUD state.
- Markdown handoffs.
- JSONL exports.
- Readiness reports.

## Clients

- Electron HUD.
- Private mobile PWA.
- CLI controller.
- Future editor adapters.

## Agent Lanes

- Codex: execution and tests.
- Antigravity: planning, review, adversarial challenge.
- Codeburn: telemetry and usage monitoring.

## Related Specs

- [[../runtime-acp]]
- [[../event-store]]
- [[../api-contract]]
- [[../data-model]]
- [[../hud-electron-pwa]]


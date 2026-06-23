---
title: Jarvis Harness Research Notes
tags:
  - jarvis-harness
  - research
status: active
---

# Jarvis Harness Research Notes

## ACP

ACP supports local JSON-RPC and remote HTTP/WebSocket style agent-client communication. Jarvis uses ACP-style JSON-RPC across all clients.

## Gemini Live

Gemini Live supports realtime audio, but Jarvis requires OAuth-only feasibility before enabling cloud realtime voice.

## Electron

Electron renderer code must not own shell execution. Jarvis keeps command authority in the runtime.

## SQLite WAL

SQLite WAL supports the local concurrent read/write pattern needed for HUD queries while PTYs and voice append events.

## Harness Engineering

Autonomous loops need:

- Locked evaluators.
- Append-only logs.
- Explicit keep/discard states.
- Human-controlled side effects.

## Rezun Article

The article frames the missing Jarvis layer as architectural:

- real-time voice conversation,
- memory systems,
- tool/MCP integration through conversational context,
- and mobile creative flow.

Jarvis harness treats those as first-class product requirements, not polish items.

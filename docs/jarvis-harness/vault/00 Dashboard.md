---
title: Jarvis Harness Dashboard
tags:
  - jarvis-harness
  - dashboard
status: active
updated: 2026-06-22 23:35 EDT
---

# Jarvis Harness Dashboard

## Current Objective

Build a Claude Code style JARVIS harness that coordinates Codex, Antigravity, Codeburn, voice, swarm loops, desktop HUD, and private mobile PWA through a governed local runtime.

## Current State

- Specs created under `docs/jarvis-harness/`.
- Runtime foundation selected: [[02 Architecture#Runtime]].
- Event store selected: [[02 Architecture#Event Store]].
- Mobile v1 selected: private-network PWA.
- Native iOS moved to future scope.
- Voice selected: Gemini realtime primary if OAuth permits, local fallback otherwise.

## Active Work

- [[04 Phase Plan#Phase 0 Spec Writeout]]
- [[06 Morning Report]]

## Watchpoints

- Existing held-out repo changes in `src/jarvis_codex/plan_viewer.py` and `tests/test_plan_viewer.py`.
- Gemini realtime OAuth feasibility is unproven.
- Electron security model must keep shell execution in runtime, not renderer.
- Rezun gap coverage must remain explicit: voice, memory, tools, and mobile continuity.

## Next

1. Validate spec files.
2. Commit and push spec slice.
3. Continue into runtime foundation planning.

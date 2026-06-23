---
title: Jarvis Harness Risks
tags:
  - jarvis-harness
  - risks
status: active
---

# Jarvis Harness Risks

## High Risk

- Renderer command execution bypasses runtime policy.
- Cloud realtime voice cannot use OAuth-only auth.
- Public network exposure happens accidentally.
- Managed PTYs execute destructive commands without approval.
- Event projections drift from canonical event store.

## Medium Risk

- Electron animation affects terminal readability.
- PWA voice capture behaves differently on iOS.
- Dynamic swarms create too much pane noise or cost.
- Codeburn telemetry is incomplete for some providers.

## Low Risk

- Markdown spec drift before implementation.
- Existing static plan viewer overlaps with future HUD concepts.

## Mitigations

- Keep command execution in runtime.
- Add policy tests before PTY automation.
- Use private-network-only mobile defaults.
- Add cloud voice feasibility gate.
- Keep JSONL/Markdown exports from event sequence ranges.


# Jarvis Codex

Local-first voice and memory layer for Codex.

This project turns the "JARVIS for coding agents" idea into a practical system:

- **Voice loop**: capture spoken or typed intent and turn it into structured work.
- **Persistent memory**: preserve project facts, preferences, decisions, and task episodes outside chat history.
- **Tool boundary**: prepare Codex-ready handoffs while keeping execution, commits, deployments, and destructive actions behind explicit approval.

The first version is intentionally small. It does not replace Codex; it gives Codex a durable inbox and memory substrate that can later be connected to speech recognition, Codex App Server, Worktrunk, and notifications.

## Quick Start

```bash
uv run jarvis-codex capture "Add voice-driven Codex task intake for my local AI OS"
uv run jarvis-codex memory add project_name "Jarvis Codex"
uv run jarvis-codex handoff
```

By default, state is stored in `./state`.

## Commands

```bash
jarvis-codex capture "task text"          # create an inbox episode
jarvis-codex memory add KEY VALUE         # add durable memory
jarvis-codex memory list                  # print memory records
jarvis-codex approve request "summary"    # create an approval request
jarvis-codex handoff                      # generate a Codex handoff brief
jarvis-codex doctor                       # inspect local state
```

## Safety Boundary

This project prepares work for Codex. It does not execute tools, modify repositories, push branches, create PRs, deploy software, or spend money unless a future integration adds that behavior behind an approval gate.

## Roadmap

1. Local state and handoff CLI.
2. Speech-to-text adapter.
3. Codex App Server bridge.
4. Approval-aware tool execution.
5. Worktrunk-powered parallel coding sessions.
6. Desktop/mobile UI.


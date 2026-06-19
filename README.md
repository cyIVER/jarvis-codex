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
jarvis-codex hardware --workload llm      # inspect CPU/GPU/NPU/Docker capabilities
jarvis-codex doctor                       # inspect local state
jarvis-plan-viewer                        # serve the local plan and next-step selector
```

## Safety Boundary

This project prepares work for Codex. It does not execute tools, modify repositories, push branches, create PRs, deploy software, or spend money unless a future integration adds that behavior behind an approval gate.

## Local Acceleration

Jarvis Codex can inspect local CPU, NVIDIA CUDA GPU, Windows NPU, WSL GPU bridge, and Docker Desktop availability:

```bash
uv run jarvis-codex hardware --workload voice
uv run jarvis-codex hardware --workload video
```

NPU use is routed conservatively. In WSL, NPUs are usually accessed through Windows runtimes such as ONNX Runtime DirectML or OpenVINO rather than as a normal Linux device. Jarvis reports that boundary instead of assuming NPU access.

## Local Review UI

`jarvis-plan-viewer` serves the Gate 2 plan and a local next-step selector from `127.0.0.1`.

```bash
uv run jarvis-plan-viewer --dir plans/jarvis-codex-swarm --state state
```

Selected next steps are written to `state/next-steps/selection.json`, which is ignored by Git. The tracked `state/next-steps/.gitkeep` file only preserves the local state directory.

## Gate Docs

- `docs/VOICE_NOTIFICATIONS.md`
- `docs/RUNTIME_GATES.md`
- `docs/REMOTION_REVIEW.md`
- `docs/WORKTRUNK_LANES.md`

## Roadmap

1. Local state and handoff CLI.
2. Speech-to-text adapter.
3. Codex App Server bridge.
4. Approval-aware tool execution.
5. Worktrunk-powered parallel coding sessions.
6. Local browser UI and Remotion video review surface.
7. Hardware-aware GPU/NPU acceleration adapters.

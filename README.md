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
jarvis-codex handoff --queue-summary      # print a read-only safe planning-queue handoff
jarvis-codex hardware --workload llm      # inspect CPU/GPU/NPU/Docker capabilities
jarvis-codex doctor                       # inspect local state
jarvis-codex doctor --governance          # include compact Codex governance validation
jarvis-plan-viewer                        # serve the local plan and next-step selector
```

## Safety Boundary

This project prepares work for Codex. It does not execute tools, modify repositories, push branches, create PRs, deploy software, or spend money unless a future integration adds that behavior behind an approval gate.

## Codex Governance

Jarvis Codex includes project-local Codex governance files for read-only planning, review, docs research, and Worktrunk lane planning.

Validate the local governance state manually:

```bash
python3 scripts/validate-jarvis-codex-phase1.py
```

The validator is stdout-only and does not write reports. It checks the project-local `.codex/config.toml`, `.codex/agents/*.toml`, and `.agents/skills/*/SKILL.md` files.

`jarvis-codex doctor` does not run governance validation by default.

Use the opt-in governance check when needed:

```bash
jarvis-codex doctor --governance
```

This adds a compact `codex_governance` summary to doctor output. The standalone validator remains available:

```bash
python3 scripts/validate-jarvis-codex-phase1.py
```

The governance validator is stdout-only and does not write reports. It checks project-local Codex governance files; it is not a replacement for unit tests, browser checks, hardware checks, or runtime validation.

Governance validation does not approve installs, migrations, service launches, runtime workflows, Worktrunk mutation, or git mutation.

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
- `docs/PRODUCT_READINESS.md`
- `docs/SAFE_HANDOFF_GATEWAY_PRD.md`
- `docs/WORKTRUNK_LANES.md`
- `docs/JARVIS_WHITE_PAPER.md`

## Roadmap

1. Local state, handoff CLI, and read-only doctor.
2. Project-local Codex governance and validator integration.
3. Local browser UI and Remotion video review surface.
4. Hardware-aware GPU/NPU inspection and approval gates.
5. Speech-to-text adapter.
6. Codex App Server bridge.
7. Approval-aware tool execution.
8. Worktrunk-powered parallel coding sessions.

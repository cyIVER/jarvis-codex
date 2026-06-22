# Runtime Gates

Jarvis Codex can detect local CPU, NVIDIA CUDA GPU, Windows NPU, WSL GPU bridge, and Docker availability, but detection is not permission to run heavy work.

Use hardware detection as a gate before any local workload that may consume GPU, NPU, Docker, or long-running CPU resources.

## Workload Checks

```bash
uv run jarvis-codex hardware --workload llm
uv run jarvis-codex hardware --workload video
uv run jarvis-codex hardware --workload voice
```

## Gate Rules

- Docker/GPU execution needs explicit approval before running containers or heavy render/model jobs.
- NPU routing remains a Windows runtime boundary through ONNX Runtime DirectML or OpenVINO adapters.
- CUDA is preferred for `llm`, `vision`, and `video` only when an available CUDA accelerator is detected.
- Docker GPU containers are recommended only when Docker is reachable and CUDA is available.
- Runtime probes should not write generated state into Git-tracked files.

## Codex Governance Gate

Before Phase 2 governance changes, run:

```bash
python3 scripts/validate-jarvis-codex-phase1.py
```

The validator must report `Status: PASS` with zero warnings and zero failures before changing project-local Codex governance files.

This validator checks Codex governance only. It is not a replacement for unit tests, browser checks, hardware checks, or runtime validation.

Do not run installs, migrations, service launches, daemons, runtime workflows, Worktrunk mutation, or git mutation without explicit approval.

`jarvis-codex doctor` does not run this validator by default.

Use the opt-in governance check when a doctor summary should include project-local Codex governance status:

```bash
jarvis-codex doctor --governance
```

The standalone manual validator remains:

```bash
python3 scripts/validate-jarvis-codex-phase1.py
```

The validator remains stdout-only and does not write reports.

Governance validation does not approve installs, migrations, service launches, runtime workflows, Worktrunk mutation, or git mutation.

## Current Acceptance

For a video workload, the accepted backend should be one of:

- `cuda through Docker GPU containers` when CUDA and Docker are available.
- `cuda on the host runtime` when CUDA is available but Docker is not.
- `dockerized CPU render; enable NVIDIA container runtime for GPU rendering` when only Docker is available.
- `cpu` when no acceleration path is available.

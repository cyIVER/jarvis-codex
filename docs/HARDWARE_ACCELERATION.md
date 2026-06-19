# Hardware Acceleration

Jarvis Codex should use local hardware when it improves latency, privacy, or cost, while keeping execution behind explicit approval gates.

## Detected Host Shape

The current WSL host exposes:

- NVIDIA CUDA path through `nvidia-smi` and `/dev/dxg`
- Docker Desktop
- 24 CPU cores from an Intel Core Ultra class processor
- Windows-side graphics devices visible through PowerShell

NPU access is different from GPU access. Intel/Windows NPUs are commonly consumed through Windows runtimes such as ONNX Runtime DirectML, OpenVINO, or vendor SDKs. WSL may not expose the NPU as a Linux device even when Windows can use it.

## Runtime Policy

- Use CUDA for heavy local LLM, vision, embedding, transcription, and video rendering workloads when the model or renderer supports it.
- Use the NPU for low-power or background inference when a Windows ONNX Runtime DirectML or OpenVINO adapter is configured.
- Use Docker Desktop for repeatable GPU-capable services when container isolation is worth the overhead.
- Use CPU fallback for deterministic behavior and tests.
- Do not send local project data to hosted services just to gain acceleration.

## CLI

```bash
uv run jarvis-codex hardware
uv run jarvis-codex hardware --workload llm
uv run jarvis-codex hardware --workload voice
uv run jarvis-codex hardware --workload video
```

The command reports detected accelerators and a workload-specific backend recommendation.

## NPU Adapter Boundary

Future NPU-backed features should use a narrow adapter boundary:

```text
Jarvis workload
  -> capability detection
  -> backend selection
  -> Windows NPU adapter
  -> ONNX Runtime DirectML or OpenVINO
  -> result returned to local state
```

The adapter should accept explicit model paths and input files. It should not download models, index private state, or start background services without approval.

## Docker GPU Path

Docker is useful for repeatable local services:

```bash
docker run --rm --gpus all nvidia/cuda:12.9.0-base-ubuntu24.04 nvidia-smi
```

If Docker GPU access fails while host `nvidia-smi` works, fix Docker Desktop GPU integration before relying on containerized acceleration.

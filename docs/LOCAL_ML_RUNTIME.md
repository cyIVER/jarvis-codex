# Local ML Runtime Architecture

Jarvis Codex should use local acceleration as an implementation detail behind explicit approval gates. The runtime should never turn hardware detection into implicit background execution, model downloads, repository mutation, or cloud fallback.

## Direction

The current hardware direction in main introduces a `hardware` CLI that detects CPU, NVIDIA CUDA, WSL `/dev/dxg`, Docker Desktop, and Windows-side NPU candidates. This lane should not duplicate that code. Treat hardware detection as an input to a narrow runtime policy:

```text
user intent
  -> episode capture
  -> approval check
  -> workload request
  -> capability profile
  -> local backend selection
  -> explicit adapter invocation
  -> filesystem-backed result
```

Every adapter takes local input paths and local model paths. Adapters may read and write project state only through the documented state directories. They must not download models, start persistent services, index private state, invoke Codex, mutate repositories, or call hosted APIs without a pending approval being accepted by the user.

## Workload Routing

| Workload | First local backend | Accelerated backend | Output state | Approval required |
| --- | --- | --- | --- | --- |
| Voice capture | Transcript text or explicit local STT adapter | CUDA transcription or Windows NPU ONNX/OpenVINO adapter | `state/inbox/*.json` episode | Microphone access, model path, long-running listener |
| Summarization | CPU local LLM | CUDA local LLM, preferably containerized when reproducibility matters | handoff or episode summary file | Model path, source files to summarize |
| Memory extraction | CPU local LLM or deterministic rules | CUDA local LLM for batch extraction | `state/memory/memory.jsonl` append | Any automatic memory write |
| Embeddings | CPU embedding model | CUDA embedding model; Windows NPU only after adapter proof | future local vector files under `state/memory/` | New index creation, re-embedding existing memory |
| Video | CPU render | CUDA renderer in Docker when available | local render artifact outside append-only logs | Rendering job, input media paths, container execution |

Use CPU as the deterministic fallback for tests and dry runs. Prefer CUDA for heavy throughput workloads: local LLMs, vision, embeddings, transcription, and video. Prefer the Windows NPU only for narrow, low-power inference after a DirectML, OpenVINO, or ONNX Runtime adapter proves it can run a pinned local model.

The current STT path is file-based: `jarvis-codex voice ingest --audio-file ... --model ... --stt-command ... --allow-audio-processing --json`. The adapter is a local executable that receives `--audio-file` and `--model`, writes the transcript to stdout, and exits. Jarvis does not download models, start listeners, access microphones, or choose a hidden cloud fallback.

## Adapter Contracts

Adapters should be small process boundaries rather than ambient services:

- `name`: stable backend name, such as `cuda-llm`, `cuda-embedding`, `windows-npu-onnx`, or `docker-video`.
- `workloads`: supported workload names.
- `inputs`: explicit local file paths or text payloads.
- `model`: explicit local model path or configured model identifier that resolves to a local path.
- `outputs`: explicit local artifact path or structured JSON returned to the caller.
- `requires_approval`: true for model downloads, microphone access, container execution, indexing, background listeners, and any automatic memory write.

Adapter failures should return structured errors and fall back to CPU only when the fallback does not change privacy, cost, or side-effect behavior.

## Approval Gates

The existing approval ledger is the right boundary. Add approval requests before these actions:

- Starting a microphone listener or desktop hotkey listener.
- Downloading, converting, quantizing, or updating a model.
- Running Docker containers, especially with `--gpus all` or mounted project directories.
- Creating or refreshing embedding indexes over project memory.
- Automatically extracting and appending durable memories from episode text.
- Rendering video from local media or plan files.
- Crossing from WSL into Windows runtimes through PowerShell, DirectML, OpenVINO, or ONNX Runtime.

Hardware inspection itself can remain a read-only command. Backend invocation is not read-only.

## Windows NPU Boundary

Do not model the Windows NPU as a normal Linux accelerator in WSL. Route it through a Windows adapter with an explicit contract:

```text
Jarvis Codex WSL process
  -> approval checked
  -> local input serialized
  -> Windows adapter invoked
  -> ONNX Runtime DirectML or OpenVINO executes pinned model
  -> result returned to WSL
  -> local state append or artifact write
```

The first NPU proof should be a single pinned ONNX model with deterministic test input. Avoid tying core Jarvis state to any vendor SDK until the adapter proves measurable latency or power benefit over CPU.

## Merge Guidance For Hardware CLI Work

The main-side `hardware` CLI can merge independently if it stays read-only and covered by tests. After that, runtime work should land in this order:

1. Add a workload/backend interface with CPU-only test doubles.
2. Add approval checks before every non-read-only adapter invocation.
3. Add CUDA adapter tests using mocked capability profiles, not host-dependent GPU assertions.
4. Add Docker GPU smoke documentation, but keep actual container execution manual.
5. Add Windows NPU proof as an optional adapter with pinned model paths and skipped tests when Windows runtimes are absent.

This keeps execution local, auditable, and reversible while still allowing hardware-specific acceleration to evolve.

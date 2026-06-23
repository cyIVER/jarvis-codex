# Runtime And ACP Protocol

Jarvis runtime owns session control, ACP-style messaging, PTY supervision, voice routing, permissions, jobs, and state persistence.

## Runtime Shape

- Use Python FastAPI as the runtime service.
- Bind to loopback by default.
- Expose a private-network mobile endpoint only when explicitly configured.
- Keep Electron, PWA, CLI, and future editor integrations as clients of the same runtime.
- Do not let UI clients execute shell commands directly.

`jarvis-codex runtime serve` is the operator entrypoint for the local HUD runtime. It binds to `127.0.0.1:8765` by default. Binding to a non-loopback host requires `--allow-non-loopback` and is intended only for explicitly approved private-network use.

## ACP-Style Protocol

Jarvis uses ACP-style JSON-RPC for all runtime interactions.

Required v1 capabilities:

- `initialize`
- `session.create`
- `session.list`
- `session.load`
- `session.resume`
- `session.fork`
- `session.cancel`
- `prompt.send`
- `event.subscribe`
- `approval.request`
- `approval.respond`
- `pty.create`
- `pty.input`
- `pty.resize`
- `pty.kill`
- `job.list`
- `job.cancel`
- `profile.set`
- `voice.start`
- `voice.stop`
- `voice.submit`
- `voice.audio_chunk`
- `voice.transcribe_audio`
- `voice.intent_propose`
- `swarm.start`
- `swarm.launch`
- `loop.start`
- `loop.pause`
- `loop.resume`
- `loop.stop`

Loop lifecycle methods record approved state only. They do not launch agents, start PTYs, execute shell commands, mutate Worktrunk, run runtime workflows, or grant execution authority.

`swarm.launch` is the exception that starts role-labeled PTY panes. It requires an approved `swarm.launch` scope that exactly names each role command, profile, and cwd, plus the HUD runtime token. It uses the same runtime policy and PTY supervisor path as `pty.create`; hardline blocks still win and Worktrunk/Git mutation is not performed by the launch method itself.

The CLI also exposes `jarvis-codex loop run-once --allow-validation --json` for one bounded loop iteration. It runs only fixed validators/readiness collectors plus fixed no-shell Codeburn telemetry and records evidence under the selected `--state` directory. It is not a generic command runner and does not launch services, agents, PTYs, Worktrunk, Git mutation, network probes, or runtime workflows.

`jarvis-codex loop schedule --allow-validation --max-iterations <n> --interval-seconds <seconds> --json` runs a bounded foreground schedule of those fixed loop iterations. It caps iterations at 12, caps the sleep interval at 3600 seconds, writes schedule evidence under `--state`, and does not start a daemon, background itself, accept arbitrary command strings, launch services, agents, PTYs, Worktrunk, Git mutation, network probes, or runtime workflows.

The wire model should separate:

- JSON-RPC request and response frames.
- Streaming event frames.
- PTY byte streams.
- Voice transcript, intent, and audio status events.
- Approval prompts and decisions.

`voice.transcribe_audio` is approval-gated. The client may provide a runtime-owned `model_path` or a safe `model_id`. When `model_id` is used, the runtime resolves it under server-configured `JARVIS_LOCAL_STT_MODELS_DIR` or the runtime model directory. Clients must not provide adapter commands or arbitrary filesystem model paths.

Implemented WebSocket runtime streams currently include:

- `stream` frames for PTY output.
- `event` frames for semantic persisted events such as approvals, sessions, voice transcripts, audio receipts, and voice intent classifications.

## Session Model

Each session has:

- Stable session ID.
- Profile ID.
- Source client: CLI, Electron, PWA, editor, automation, or system.
- Model and provider route metadata.
- Parent session ID when forked.
- Current policy profile.
- Active panes and jobs.
- Event sequence number.
- Created, updated, archived timestamps.

## Process Supervision

Jarvis manages PTYs for:

- Codex.
- Antigravity through `agy`.
- AG adversary instances.
- Shell.
- Codeburn.

Each process must have:

- Pane ID.
- Role label.
- Working directory.
- Policy profile.
- Environment allowlist.
- Start command record.
- Kill/restart controls.
- Event log.

## Implementation Rules

- Runtime clients request actions; the runtime enforces policy.
- PTY input is never trusted as approval by itself.
- High-risk commands require explicit approval events before execution.
- `pty.create` may consume an approved approval record only when the approval operation or scoped command exactly matches the requested command.
- Hardline-blocked commands remain blocked even if an approval ID is supplied.
- Runtime state writes go through the event store.
- UI clients may render commands but must not execute them locally.

## Acceptance Criteria

- Electron, PWA, and CLI can all create or resume sessions through the same protocol.
- A PTY pane can stream output without blocking the runtime.
- A high-risk action creates an approval request instead of executing silently.
- Session replay can reconstruct pane, approval, voice, and job history from persisted events.
- Semantic runtime events are delivered separately from PTY byte streams.

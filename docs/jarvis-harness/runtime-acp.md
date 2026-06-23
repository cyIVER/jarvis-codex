# Runtime And ACP Protocol

Jarvis runtime owns session control, ACP-style messaging, PTY supervision, voice routing, permissions, jobs, and state persistence.

## Runtime Shape

- Use Python FastAPI as the runtime service.
- Bind to loopback by default.
- Expose a private-network mobile endpoint only when explicitly configured.
- Keep Electron, PWA, CLI, and future editor integrations as clients of the same runtime.
- Do not let UI clients execute shell commands directly.

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
- `swarm.start`
- `loop.start`
- `loop.pause`
- `loop.resume`
- `loop.stop`

The wire model should separate:

- JSON-RPC request and response frames.
- Streaming event frames.
- PTY byte streams.
- Voice transcript and audio status events.
- Approval prompts and decisions.

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
- Runtime state writes go through the event store.
- UI clients may render commands but must not execute them locally.

## Acceptance Criteria

- Electron, PWA, and CLI can all create or resume sessions through the same protocol.
- A PTY pane can stream output without blocking the runtime.
- A high-risk action creates an approval request instead of executing silently.
- Session replay can reconstruct pane, approval, voice, and job history from persisted events.


# API Contract

Jarvis clients communicate with the runtime through ACP-style JSON-RPC over WebSocket.

HTTP endpoints are allowed only for health checks, static assets, auth/bootstrap, and simple export downloads.

## Transport

Desktop Electron:

- Connects to loopback runtime.
- Opens a WebSocket for JSON-RPC frames.
- Opens PTY streams through runtime-managed channel IDs.

Mobile PWA:

- Connects over private VPN only.
- Uses the same JSON-RPC method names.
- Receives reduced-bandwidth event streams when the client declares mobile mode.

CLI:

- May call runtime through stdio or loopback JSON-RPC.
- Must not bypass runtime policy when running commands.

## Frame Types

Use four frame types:

- `request`: JSON-RPC request with `id`, `method`, and `params`.
- `response`: success or error response matching `id`.
- `event`: async runtime event with `type`, `session_id`, and payload.
- `stream`: chunked payload for PTY output, transcript partials, or audio status.

PTY byte payloads should be framed separately from semantic tool and approval events.

## Required Methods

Session:

- `initialize`
- `session.create`
- `session.list`
- `session.get`
- `session.resume`
- `session.fork`
- `session.archive`
- `session.cancel`

`session.archive` is implemented as a state-only lifecycle operation. It appends `session.archived`, updates the session projection, and does not execute shell, PTY, Worktrunk, or runtime workflow commands.

`session.fork` is implemented as a state-only lineage operation. It creates a child session with `parent_session_id`, inherited route/profile defaults, and no execution authority.

`session.resume` is implemented as read-only context rehydration. It returns session metadata plus recent semantic history and does not create state, execute commands, or grant approval authority.

Messaging:

- `prompt.send`
- `prompt.cancel`
- `message.list`
- `message.search`
- `event.subscribe`

`prompt.send` is implemented as a semantic prompt-history write. It appends `prompt.sent` for an existing session and explicitly does not execute Codex, Antigravity, PTY, Worktrunk, shell, or runtime workflows.

`message.list` is implemented as a semantic event/history view. If runtime state has not been initialized yet, it returns an empty list without creating state.

`message.search` is implemented as read-only semantic history search over the event-store FTS projection. Missing state and blank queries return empty results without writing files.

PTY:

- `pty.create`
- `pty.input`
- `pty.resize`
- `pty.kill`
- `pty.restart`

`pty.create` accepts an optional `approval_id`. The approval must already be approved and must exactly match the requested command through its operation or scoped command. Matching approvals are consumed atomically on use and cannot be replayed. Approved launch consumption requires the runtime HUD token. This does not bypass hardline policy blocks.

Approval:

- `approval.list`
- `approval.request`
- `approval.respond`

`approval.respond` is a privileged HUD action. It requires the per-runtime HUD token served from the same-origin HUD document and must not be accepted from untrusted clients.

Policy:

- `agent.provider_status`
- `profile.list`
- `profile.set`
- `command.classify`
- `command.propose`

`agent.provider_status` is implemented as a non-writing provider matrix for Codex, Antigravity, and Codeburn. It reports role, command availability, and execution boundary only; it does not launch providers, start PTYs, write state, or grant execution authority.

`profile.list` is implemented as a non-writing profile catalog. `profile.set` is implemented as a state-only session metadata update that appends `session.profile_set` and updates the session projection. Setting a profile does not by itself execute commands or grant approval authority.

`command.propose` is implemented as a semantic proposal record. It classifies a proposed command, appends `command.proposed`, and explicitly does not create approval, launch PTYs, run shell commands, mutate Worktrunk, or grant execution authority.

Voice:

- `voice.start`
- `voice.stop`
- `voice.submit`
- `voice.provider_status`
- `voice.audio_chunk`
- `voice.transcribe_audio`
- `voice.synthesize_audio`
- `voice.intent_propose`

`voice.transcribe_audio` requires a matching approved audio-processing approval id, the runtime HUD token, a server-configured STT adapter command, an audio file under the runtime audio directory, and a model path under the runtime model directory.

`voice.synthesize_audio` requires a matching approved audio-processing approval id bound to the requested text SHA-256, the runtime HUD token, and a server-configured TTS adapter command. The runtime chooses the output path under its audio directory; clients cannot supply adapter commands or output paths.

Loop and swarm:

- `loop.start`
- `loop.pause`
- `loop.resume`
- `loop.stop`
- `swarm.plan`
- `swarm.start`
- `swarm.stop`
- `swarm.launch`

`swarm.plan` is implemented as a planning-only semantic event. It appends `swarm.planned` for an existing session and records proposed lane assignments without launching agents, starting PTYs, mutating Worktrunk, running shell commands, or granting execution authority.

`swarm.start` and `swarm.stop` are implemented as approval-gated lifecycle records. They require a matching scoped approval and the HUD runtime token, consume that approval on use, and append `swarm.started` or `swarm.stopped`. They do not launch agents, start PTYs, mutate Worktrunk, run shell commands, execute runtime workflows, or grant execution authority.

`swarm.launch` is implemented as an approval-gated role launch. It requires a matching scoped approval, exact role command/profile/cwd matching, and the HUD runtime token before launching role-labeled PTY panes. Hardline policy blocks still override approvals. It can start PTYs and execute the approved role commands, but it does not mutate Worktrunk, mutate Git, or execute runtime workflows.

CLI loop execution:

- `jarvis-codex loop verify --json`
- `jarvis-codex loop run-once --allow-validation --json`

`loop run-once` runs only fixed validators/readiness collectors plus fixed no-shell Codeburn telemetry. It writes a loop-run JSON record under the selected `--state` directory and appends `logs/loop-runs.jsonl`. It does not accept arbitrary command strings, launch services, probe the network, mutate Git, mutate Worktrunk, start agents, start PTYs, or execute runtime workflows.

Telemetry:

- `telemetry.codeburn_status`
- `runtime.health`
- `runtime.readiness`

## Error Model

Every error response must include:

- `code`
- `message`
- `retryable`
- `policy_blocked`
- `approval_required`
- `details`

Policy blocks are not runtime crashes. They are successful safety outcomes and should render as actionable approvals or denials.

## Compatibility Rules

- Additive fields are allowed.
- Removing or renaming methods requires a protocol version bump.
- Client capabilities must be declared during `initialize`.
- The runtime may downgrade features for mobile clients.
- Unknown event types must be ignored by clients unless marked `critical`.

## Acceptance Criteria

- Desktop, PWA, and CLI use the same method namespace.
- A client can reconnect and resume a session event stream.
- Policy-blocked commands produce structured errors.
- PTY chunks cannot be confused with approval decisions.
- Semantic `event` frames carry persisted runtime events and must not be treated as PTY bytes or command execution.
- Browser WebSocket clients must pass same-origin validation before the runtime accepts the connection.
- Approval response and approval-consuming execution paths must require the per-runtime HUD token.

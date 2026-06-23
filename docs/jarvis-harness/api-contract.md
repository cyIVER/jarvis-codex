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

Messaging:

- `prompt.send`
- `prompt.cancel`
- `message.list`
- `event.subscribe`

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

- `profile.list`
- `profile.set`
- `command.classify`

`profile.list` is implemented as a non-writing profile catalog. `profile.set` remains planned because changing a session profile is stateful and requires a separate event/projection decision.

Voice:

- `voice.start`
- `voice.stop`
- `voice.submit`
- `voice.provider_status`
- `voice.audio_chunk`
- `voice.transcribe_audio`
- `voice.intent_propose`

`voice.transcribe_audio` requires a matching approved audio-processing approval id, the runtime HUD token, a server-configured STT adapter command, an audio file under the runtime audio directory, and a model path under the runtime model directory.

Loop and swarm:

- `loop.start`
- `loop.pause`
- `loop.resume`
- `loop.stop`
- `swarm.plan`
- `swarm.start`
- `swarm.stop`

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

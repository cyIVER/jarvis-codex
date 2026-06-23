# Phase Roadmap

This roadmap converts the Jarvis harness architecture into shippable phases.

Each phase should end with targeted validation, docs updates if needed, coherent commits, push to main, and a readiness note.

## Phase 0: Spec Writeout

Deliver:

- `docs/jarvis-harness/` spec set.

Acceptance:

- Specs record runtime, event store, HUD, voice, permissions, swarm, mobile, and phase gates.
- Existing uncommitted work is not mixed into the spec commit.

## Phase 1: Runtime Foundation And HUD Shell

Deliver:

- SQLite/WAL event store.
- Projection interfaces.
- ACP-style JSON-RPC models.
- FastAPI runtime skeleton.
- Electron React shell.
- Ten mode navigation.
- HUD connection status.

Acceptance:

- Runtime starts locally.
- Empty event store bootstraps in configured state dir.
- Electron shell connects to runtime.
- Mobile PWA shell can load from runtime in private mode.
- Tests cover event append, projection rebuild, and protocol frame validation.

## Phase 2: Managed PTYs

Deliver:

- PTY manager.
- Codex pane.
- Antigravity pane.
- Shell pane.
- Codeburn pane.
- Pane event persistence.

Acceptance:

- PTY output streams to HUD.
- PTY input goes through runtime.
- Kill/restart controls work.
- Policy profile is visible per pane.
- Tests prove UI clients do not spawn shell commands directly.

## Phase 3: Permissions And Approvals

Deliver:

- Observe, Dev Loop, Swarm, and High-Risk Runtime profiles.
- Command classification.
- Approval event flow.
- Hardline blocklist.

Acceptance:

- High-risk commands create approval prompts.
- Approved actions are scoped and logged.
- Rejected actions do not execute.
- Policy decisions persist in the event store.

## Phase 4: Voice

Deliver:

- Click-to-arm mic flow.
- Transcript preview.
- Gemini OAuth realtime feasibility gate.
- Local `faster-whisper` GPU fallback adapter.
- Local cinematic TTS adapter boundary.

Acceptance:

- Mic activation requires click.
- Cloud voice cannot use API-key fallback silently.
- Local fallback can transcribe and route a prompt.
- Risky spoken commands require confirmation.

## Phase 5: Swarm And Loops

Deliver:

- `/loop` delivery loop.
- `/swarm` dynamic orchestrator-worker flow.
- AG adversary panes.
- Codeburn telemetry integration.
- Commit/push phase gate.

Acceptance:

- Risk-scaled swarm roles spawn deterministically.
- Adversary review is required for high-risk commits.
- Loop state is durable and resumable.
- Phase push flow validates before pushing.

## Phase 6: Mobile PWA

Deliver:

- Private-network mobile route.
- PWA voice/chat/approval/status UI.
- Mobile session identity.

Acceptance:

- iPhone can use the PWA over private VPN.
- Mobile approvals include complete action detail.
- Runtime remains private by default.

## Phase 7: Production Readiness

Deliver:

- End-to-end smoke tests.
- Browser/mobile tests.
- Voice tests with mocked providers.
- PTY safety tests.
- Release readiness report.

Acceptance:

- Core tests pass.
- UI smoke tests pass.
- Safety gates pass.
- Docs match implemented behavior.
- Remaining native iOS work is tracked as future scope.


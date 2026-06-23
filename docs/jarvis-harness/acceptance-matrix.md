# Acceptance Matrix

This matrix defines production-readiness checks for the harness.

Current implementation note: the local FastAPI runtime, browser HUD, approval-gated PTY/swarm/loop surfaces, release-readiness review surfaces, and local STT path are validated. Actual iPhone validation, networked Gemini Live validation, Electron/release signing, external security attestation, and unattended/background scheduling remain release gates.

| Area | V1 Acceptance | Current validation | Boundary |
| --- | --- | --- | --- |
| Runtime | FastAPI runtime starts locally and exposes ACP-style JSON-RPC. | Runtime integration tests and HUD browser smoke tests. | Loopback by default; non-loopback serving requires explicit operator approval. |
| Event store | SQLite/WAL event store appends canonical events and rebuilds projections. | Event-store unit tests. | State writes stay under the selected state directory. |
| Sessions | Sessions can create, resume, fork, archive, and replay. | Protocol and projection tests. | Replay is local evidence, not external execution authority. |
| PTYs | Runtime-managed panes stream output and accept gated input. | PTY integration tests. | High-risk commands remain blocked by policy even with approval records. |
| Policy | Observe, Dev Loop, Swarm, and High-Risk Runtime profiles enforce gates. | Policy unit and safety tests. | Hardline blocks apply to git mutation, Worktrunk mutation, services, daemons, installs, secrets, and destructive actions. |
| Approvals | High-risk actions create structured approval prompts. | Approval lifecycle tests. | Approvals are scoped records, not blanket permission to run adjacent commands. |
| HUD | Browser HUD surfaces runtime, voice, swarm, release gate, release evidence, release checklist, mobile, and loop state. | HUD unit tests and browser smoke tests. | Displayed commands and release checklists are proposals/evidence only. |
| Mobile | Mobile HUD access plan, private URL discovery, viewport checks, preflight evidence, and operator evidence brief are available. | Mobile viewport, private-network planning, evidence-brief, and runtime readiness tests. | Actual iPhone private-network validation remains an open release gate until human evidence is accepted. |
| Voice | File-based local STT and approved browser-audio transcription controls work through local adapters. | Mock provider, local adapter, whisper.cpp wrapper, runtime, and HUD tests. | Microphone capture, audio storage, and transcription remain separately approved steps. |
| Swarm | Operator can plan swarm lanes, record lifecycle, and launch approved role-labeled PTY panes. | Swarm planner, lifecycle, launch, runtime, and HUD tests. | `swarm.launch` requires exact scoped approval, HUD token, and policy clearance; no Worktrunk or Git mutation. |
| Loop | Bounded run-once and foreground schedule execute fixed validators/readiness collectors and write local evidence; unattended policy is reportable. | Loop readiness, unattended policy, and autonomous-loop tests. | No daemon/background scheduling, arbitrary commands, agent fanout, or unattended mutation. |
| Release review | Manifest, artifact evidence, gate status, readiness checklist, external security packet, and evidence ledger are available. | Release, CLI, runtime, HUD, and browser smoke tests. | Review-only; no signing, copying, publishing, gate closure, or external acceptance. |
| Codeburn | Usage snapshots are captured at phase boundaries. | CLI smoke and readiness note checks. | Missing telemetry should be reported as a warning, not treated as release proof. |
| AG review | High-risk phases receive read-only AG challenge review when useful. | HUD challenge approval request coverage and explicit challenge passes. | AG output is advisory; approved AG panes remain runtime-gated and do not become execution authority. |
| Git flow | Coherent phase commits are pushed after validation. | Git log, status checks, and CI. | Commit/push may occur only after scoped validation; no destructive git commands. |
| Safety | Destructive, secret, money, public exposure, and high-risk runtime actions are gated. | Hardline blocklist tests and release readiness checks. | Evidence and UI display never close gates automatically. |

## Release Blocking Failures

- Runtime or HUD can execute commands outside policy or without required approvals.
- UI can bypass runtime policy to execute commands.
- Voice can trigger audio capture, transcription, or high-risk action without confirmation.
- Mobile endpoint binds publicly by default.
- Release evidence, gate status, or checklist output closes gates automatically.
- Event store cannot replay session history.
- PTY logs are not persisted.
- Git, Worktrunk, service, install, migration, or destructive mutation bypasses hardline policy.
- External/device/signing gates are reported complete without accepted evidence.
- Commit/push happens after failing required tests.

## Release Warnings

- Networked Gemini Live validation has not been run with operator approval.
- Actual iPhone private-network validation has not been run with accepted evidence.
- Electron/release artifacts are local and unsigned unless a separate signing/distribution gate is approved.
- External security reviewer attestation has not been accepted.
- Unattended/background operation remains gated beyond the read-only policy report.
- Cloud realtime remains unavailable through OAuth-only assumptions.
- Local TTS quality is below target.
- Mobile HUD is functional but less cinematic than desktop.
- Codeburn telemetry unavailable or incomplete.
- AG challenge still requires explicit operator approval before any `agy` pane launch.

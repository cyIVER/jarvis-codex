# Acceptance Matrix

This matrix defines production-readiness checks for the harness.

Current implementation note: the local FastAPI runtime and browser HUD foundation are validated, but Electron packaging, full mobile-device validation, full swarm commands, and release packaging remain future gates.

| Area | V1 Acceptance | Validation |
| --- | --- | --- |
| Runtime | FastAPI runtime starts locally and exposes ACP-style JSON-RPC. | Runtime integration tests. |
| Event store | SQLite/WAL event store appends canonical events and rebuilds projections. | Event-store unit tests. |
| Sessions | Sessions can create, resume, fork, archive, and replay. | Protocol and projection tests. |
| PTYs | Runtime-managed panes stream output and accept gated input. | PTY integration tests. |
| Policy | Observe, Dev Loop, Swarm, and High-Risk Runtime profiles enforce gates. | Policy unit and safety tests. |
| Approvals | High-risk actions create structured approval prompts. | Approval lifecycle tests. |
| HUD | Electron HUD renders ten modes with no layout overlap. | Browser/UI smoke tests. |
| Mobile | iPhone PWA connects over private VPN and can submit prompts and approvals. | Mobile viewport and private-network tests. |
| Voice | Cloud realtime uses OAuth-only feasibility; local fallback works. | Mock provider and local adapter tests. |
| Swarm | Dynamic role selection scales with risk. | Swarm planner tests. |
| Loop | Delivery loop can plan, implement, test, review, commit, push, and continue. | End-to-end rehearsal. |
| Codeburn | Usage snapshots are captured at phase boundaries. | CLI smoke and readiness note check. |
| AG review | High-risk phases receive read-only AG challenge review. | Readiness note evidence. |
| Git flow | Coherent phase commits are pushed after validation. | Git log and status checks. |
| Safety | Destructive, secret, money, public exposure, and high-risk runtime actions are gated. | Hardline blocklist tests. |

## Release Blocking Failures

- Runtime can execute commands outside policy.
- UI can bypass runtime to execute commands.
- Voice can trigger high-risk action without confirmation.
- Mobile endpoint binds publicly by default.
- Event store cannot replay session history.
- PTY logs are not persisted.
- Commit/push happens after failing required tests.

## Release Warnings

- Cloud realtime unavailable through OAuth.
- Local TTS quality below target.
- Mobile HUD is functional but less cinematic than desktop.
- Codeburn telemetry unavailable or incomplete.
- AG challenge unavailable; replace with local adversary review.

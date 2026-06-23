# Production Readiness Runbook

This runbook summarizes the current Jarvis harness readiness state and the checks required before treating a build as production-ready.

## Current Implemented Surface

Implemented and validated in the local FastAPI runtime:

- ACP-style JSON-RPC request, response, event, and stream frames.
- SQLite/WAL runtime event store with session and approval projections.
- Runtime policy classification and hardline command blocking.
- State-only session archive lifecycle through `session.archive`.
- State-only session lineage creation through `session.fork`.
- Read-only session context rehydration through `session.resume`.
- Non-writing policy profile catalog through `profile.list`.
- State-only session profile metadata updates through `profile.set`.
- State-only command proposal records through `command.propose` with policy classification but no approval creation or execution.
- Semantic prompt history writes through `prompt.send` without agent or command execution.
- Session-scoped semantic history through `message.list`.
- Read-only semantic history search through `message.search`.
- Planning-only swarm lane proposal records through `swarm.plan` without agent launch, PTY launch, Worktrunk mutation, or command execution.
- HUD session history panel backed by `message.list`.
- Runtime-managed PTY creation, input, resize, kill, and output streaming.
- Approval request, approval response, pending/approved approval listing, and approval-matched PTY launch.
- Same-origin WebSocket validation and per-runtime HUD token gating for approval decisions and approved action consumption.
- Runtime-served HUD shell for Codex, Antigravity, Codeburn, approvals, voice, sessions, and PWA status.
- HUD runtime readiness status and remaining-gap summary backed by the non-writing `runtime.readiness` RPC.
- Browser click-to-arm microphone flow with browser STT where available.
- Browser-managed spoken runtime status through `speechSynthesis` after a user click.
- Local audio chunk storage and approval-gated local STT adapter execution.
- Approval-gated local TTS adapter execution with server-configured command, runtime token, text-hash approval binding, and runtime-owned output paths.
- Voice intent proposals that do not execute commands.
- Plan-viewer route safety for display-only plan context.
- Session listing, session lookup, HUD session selection, and explicit HUD session creation.
- Fixed no-shell Codeburn telemetry adapter exposed through runtime RPC.
- Private-network PWA shell assets: manifest, SVG icon, service worker, and mobile viewport support.
- Non-writing `runtime.readiness` RPC that reports current foundation status and remaining release gaps.
- Operator CLI entrypoint `jarvis-codex runtime serve`, loopback by default with explicit `--allow-non-loopback` for approved private-network binding.

## Not Yet Production-Complete

The following remain future or incomplete production gates:

- Electron desktop app packaging.
- Full mobile device validation over Tailscale or WireGuard.
- Gemini realtime OAuth feasibility and cloud voice provider integration.
- Dynamic `/loop` and `/swarm` command surfaces.
- AG adversary panes inside the HUD.
- Persistent PTY transcript projection beyond streamed output.
- Release packaging, installer, and signed artifacts.
- External security review.

## Safety Invariants

- The browser HUD must not execute shell commands directly.
- Voice transcripts and voice intent proposals must not execute commands.
- Command proposals must not create approvals, launch PTYs, mutate Worktrunk, or execute commands.
- Browser-managed speech output must not run local TTS commands or grant approval authority.
- Displayed commands, queue entries, and plan-viewer routes are not execution authority.
- Swarm plans are planning records only; they must not be treated as permission to launch agents, mutate Worktrunk, start PTYs, or run commands.
- PTY launches that require approval must include an approved, command-matched approval id, and that approval is consumed on use.
- Approval responses and approved PTY launches require the per-runtime HUD token served from the same-origin HUD.
- Approval consumption must be atomic; concurrent consumers must not reuse the same approval.
- Hardline policy blocks must continue to override approvals.
- Codeburn telemetry uses a fixed adapter command with `shell=False`; it is not a generic command runner.
- Local STT transcription requires a matching approved audio-processing approval id, the per-runtime HUD token, a server-configured `JARVIS_LOCAL_STT_COMMAND`, a runtime-owned audio file, and a runtime-owned model path; clients cannot supply adapter commands through RPC.
- Local TTS synthesis requires a matching approved audio-processing approval id bound to the requested text SHA-256, the per-runtime HUD token, a server-configured `JARVIS_LOCAL_TTS_COMMAND`, and a runtime-owned output path; clients cannot supply adapter commands or output paths through RPC.
- The runtime WebSocket must reject cross-origin browser clients.
- Runtime PTYs do not execute through a shell. Shell pipelines and shell operators are not supported execution semantics in the current supervisor.
- The PWA service worker must not cache `/rpc`, `/ws`, or non-GET requests.
- Public internet exposure is not part of v1.
- Runtime serving must bind to loopback unless the operator explicitly chooses a private-network host with `--allow-non-loopback`.

## Required Local Validation

Run from the repo root:

```bash
python3 scripts/validate-jarvis-codex-phase1.py
uv run pytest tests/test_codeburn.py tests/test_event_stream.py tests/test_voice_intent.py tests/test_plan_viewer.py tests/test_voice_audio.py tests/test_hud.py tests/test_hud_browser.py tests/test_runtime_app.py tests/test_voice.py tests/test_whisper_cpp_adapter.py tests/test_approval.py tests/test_event_store.py tests/test_pty_supervisor.py tests/test_policy.py tests/test_protocol.py tests/test_governance.py tests/test_cli.py tests/test_state.py
```

Expected current baseline:

```text
Status: PASS
Checks passed: 156
Warnings: 0
Failures: 0
167 passed
```

The pytest run may report the existing Starlette `TestClient` deprecation warning.

## Browser Smoke Checks

Use a temporary state directory, not repo state:

```bash
uv run python - <<'PY'
from pathlib import Path
import uvicorn
from jarvis_codex.runtime_app import create_app
uvicorn.run(create_app(Path('/tmp/jarvis-hud-smoke-state')), host='127.0.0.1', port=8765, log_level='warning')
PY
```

Smoke-check these surfaces, then stop the server:

- `/` loads the HUD shell.
- `/assets/hud.js` loads from the runtime.
- `/manifest.webmanifest` returns `display: standalone`.
- `/service-worker.js` contains the HUD cache and excludes runtime RPC routes.
- The HUD shows socket, policy, voice, approval, Codeburn, PWA, and runtime readiness status metrics.
- The microphone button requires a click before browser permission.
- Approval cards expose operation, risk, and scope before approve/reject.
- Approval buttons approve/reject only; approved launches use a separate token-gated launch button.

## Mobile PWA Gate

Before marking mobile production-ready:

- Bind only to a private interface or private VPN address.
- Verify the route is inaccessible from public internet.
- Test on an actual iPhone Safari session.
- Confirm microphone permission flow on device.
- Confirm service worker registration does not cache runtime RPC responses.
- Confirm mobile approval details are complete before any approval response.

## Release Decision

The current build is a validated local runtime/HUD foundation. It is not yet a fully packaged production release.

Advance to production release only after:

- All required local validation passes.
- Browser and mobile smoke checks pass.
- Remaining production gaps are either implemented or explicitly waived.
- A human reviews the final diff, commit log, and safety invariants.

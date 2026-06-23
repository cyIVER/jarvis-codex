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
- Approval-gated swarm lifecycle records through `swarm.start` and `swarm.stop` without agent launch, PTY launch, Worktrunk mutation, runtime workflow execution, or command execution.
- Approval-gated role-labeled swarm launch through `swarm.launch`; it requires exact scoped approval for role command/profile/cwd plus the HUD runtime token, starts PTY panes through runtime policy, preserves hardline blocks, and does not mutate Worktrunk or Git.
- Approval-gated loop lifecycle records through `loop.start`, `loop.pause`, `loop.resume`, and `loop.stop` without agent launch, PTY launch, Worktrunk mutation, runtime workflow execution, or command execution.
- Bounded loop execution through `jarvis-codex loop run-once --allow-validation --json`; it runs fixed validators/readiness collectors plus fixed no-shell Codeburn telemetry and records a loop-run event under the selected `--state` directory.
- Read-only loop readiness verification through `jarvis-codex loop verify --json`; it checks loop state, CI wiring, budget policy markers, safety surfaces, and forbidden runtime-authority markers without writing files.
- Read-only unattended loop policy reporting through `jarvis-codex loop unattended-policy --json`; it summarizes budget, stop, escalation, foreground schedule, and approval requirements without writing files, starting a scheduler, or closing the unattended release gate.
- Read-only unattended loop scheduling evidence briefing through `jarvis-codex loop unattended-evidence-brief --json`; it packages accepted policy, run-log visibility, stop controls, escalation rules, and release-evidence recording instructions without writing state or closing the unattended release gate.
- Foreground bounded loop scheduling through `jarvis-codex loop schedule --allow-validation --json`; it runs only fixed `run-once` iterations, caps iterations and interval length, writes schedule evidence under the selected `--state`, and starts no daemon.
- HUD swarm launch controls for requesting exact scoped `swarm.launch` approval and launching approved role-labeled PTY panes through the runtime policy gate.
- HUD loop lifecycle controls for requesting approval and recording approved start, pause, resume, and stop state without launching execution.
- HUD session history panel backed by `message.list`.
- Runtime-managed PTY creation, input, resize, kill, and output streaming.
- Persistent PTY output projection into session-scoped `pty.output` runtime events for replay, search, and local transcript evidence.
- Approval request, approval response, pending/approved approval listing, and approval-matched PTY launch.
- Same-origin WebSocket validation and per-runtime HUD token gating for approval decisions and approved action consumption.
- Runtime-served screen-sized HUD shell with operator navigation pages for Codex, Antigravity, Codeburn, approvals, voice, sessions, loops, release gates, and PWA status.
- Shell-style HUD operator command bar for recording planning intent into session history; it does not execute Codex, Antigravity, PTYs, Worktrunk, shell commands, or runtime workflows.
- HUD Antigravity challenge approval requests that package a review brief for an approval-gated `agy` pane without launching AG, Codex, PTYs, Worktrunk, shell commands, services, or workflows.
- HUD runtime readiness status and remaining-gap summary backed by the non-writing `runtime.readiness` RPC.
- HUD mobile access readiness panel backed by non-writing mobile host discovery.
- Browser click-to-arm microphone flow with browser STT where available.
- Browser-managed spoken runtime status through `speechSynthesis` after a user click.
- Local audio chunk storage, approval request controls, approved local STT adapter execution controls, and server-resolved STT model ids.
- Read-only local STT asset discovery through `jarvis-codex voice discover --json` without microphone access, audio processing, model download, runtime start, cloud calls, or state writes.
- Approval-gated local TTS adapter execution with server-configured command, runtime token, text-hash approval binding, and runtime-owned output paths.
- Voice intent proposals that do not execute commands.
- Plan-viewer route safety for display-only plan context.
- Session listing, session lookup, HUD session selection, and explicit HUD session creation.
- Fixed no-shell Codeburn telemetry adapter exposed through runtime RPC.
- Non-writing Codex/Antigravity/Codeburn provider status matrix exposed through runtime RPC and HUD.
- Private-network PWA shell assets: manifest, SVG icon, service worker, and mobile viewport support.
- Non-writing `runtime.readiness` RPC that reports current foundation status and remaining release gaps.
- Non-writing `jarvis-codex runtime readiness --json` CLI summary that exposes the same operator readiness surface without starting the runtime server.
- Operator CLI entrypoint `jarvis-codex runtime serve`, loopback by default with explicit `--allow-non-loopback` for approved private-network binding.
- Read-only mobile host discovery through `jarvis-codex mobile discover --json`; it lists local private-interface candidates without probing, serving, opening browsers, or writing state.
- HUD runtime readiness displays the recommended mobile candidate, proposed serve/preflight/validation commands, and the mobile evidence brief as display-only planning text.
- Local-only Electron HUD scaffold with loopback runtime default, renderer sandboxing, context isolation, disabled Node integration, denied window-open/cross-origin navigation, and no shell authority.
- Electron HUD dependency lockfile generated separately with lifecycle scripts disabled.
- Electron HUD local dependencies installed under ignored `tools/electron-hud/node_modules/` for operator validation; `node_modules` is not a release artifact.
- Electron Builder dependency, `electron-builder.json`, and reviewed `npm run package` / `npm run make` scripts are present for an approval-gated packaging phase.
- Non-signing Electron package execution was locally validated with `npm run package`; generated artifacts live under ignored `tools/electron-hud/dist/` and are not release artifacts.
- Unsigned Electron AppImage generation was locally validated with `npm run make`; the generated AppImage is ignored local evidence only and is not signed, copied, reviewed, or publication-ready.
- A committed Electron HUD icon asset is configured for Electron Builder; local `npm run make` no longer emits the default Electron icon warning.
- Local dependency audit evidence is clean for the current JavaScript package surfaces: `tools/electron-hud` and `video/remotion` both report zero high-or-worse npm vulnerabilities.
- Read-only mobile private-network preflight through `jarvis-codex mobile preflight --json`; it classifies the intended runtime host without probing, serving, or writing state.
- Read-only mobile validation planning through `jarvis-codex mobile validation-plan --json`; it prepares iPhone/PWA evidence steps without probing, serving, opening browsers, or writing state.
- Read-only mobile evidence brief through `jarvis-codex mobile evidence-brief --json`; it packages the target URL, approval-gated serve command, evidence checklist, and release-evidence recording command without probing, serving, opening browsers, writing state, or closing the mobile release gate.
- Read-only Gemini Live feasibility check through `jarvis-codex gemini feasibility --json`; it reports credential signals without exposing secrets, starting OAuth, connecting to Gemini, probing the network, launching services, or writing state.
- Read-only Gemini Live validation planning through `jarvis-codex gemini validation-plan --json`; it prepares cloud voice evidence steps without starting OAuth, opening WebSockets, launching adapters, probing the network, writing state, exposing secrets, or granting execution authority.
- Read-only Gemini Live evidence brief through `jarvis-codex gemini evidence-brief --json`; it packages credential mode, redaction, approval-gated network-test expectations, evidence checklist, and release-evidence recording command without starting OAuth, opening WebSockets, probing the network, launching adapters, writing state, approving cloud spend, or closing the Gemini release gate.
- HUD release readiness displays the Gemini Live evidence brief as display-only planning text; it does not start OAuth, open Gemini WebSockets, probe the network, expose secrets, approve cloud spend, or close `networked_gemini_live_validation`.
- Read-only Nango/Gemini Live integration planning through `jarvis-codex gemini nango-plan --json`; it records Nango as a future credential/tool governance layer and keeps raw realtime audio, Nango API calls, OAuth, WebSockets, cloud spend, and token minting behind separate approvals.
- Read-only release packaging preflight through `jarvis-codex release packaging-preflight --json`; it reports Electron package, dependency, and signing readiness without installing, building, signing, copying artifacts, launching services, or writing files.
- Read-only release artifact evidence through `jarvis-codex release artifact-evidence --json`; it reports size/SHA-256 for the committed Electron icon and ignored local Electron artifacts without building, signing, copying, publishing, launching services, or writing files.
- Read-only packaging/signing evidence brief through `jarvis-codex release packaging-evidence-brief --json`; it packages packaging preflight, artifact evidence, signing/publication evidence requirements, and release-evidence recording commands without installing, building, signing, copying, publishing, writing files, or closing packaging gates.
- HUD release readiness displays the packaging/signing evidence brief as display-only planning text; it does not install dependencies, build packages, sign artifacts, copy/upload/publish artifacts, launch services, or close release gates.
- Read-only external security review packet through `jarvis-codex release security-review-plan --json`; it maps OWASP ASVS/WSTG review surfaces without running scanners, launching services, probing networks, building packages, signing artifacts, or writing files.
- Read-only external security evidence brief through `jarvis-codex release security-evidence-brief --json`; it packages reviewer scope, standards, findings, remediation, accepted-attestation requirements, and release-evidence recording command without scanners, service launches, network probes, builds, signing, copying, publishing, writing files, or closing the external review gate.
- HUD release readiness displays the external security evidence brief as display-only planning text; it does not run scanners, launch services, probe networks, build packages, sign artifacts, copy/upload/publish artifacts, complete external review, or close `external_security_review`.
- State-only release evidence ledger through `jarvis-codex --state <state-dir> release evidence add/list --json` plus `release gate-status --json`; it records operator or reviewer evidence metadata, optional state-local artifact hashes, and open-gate evidence counts without copying artifacts, launching validations, or closing gates.
- State-only release gate acceptance through `jarvis-codex --state <state-dir> release gate accept --gate <gate> --evidence-id <evidence-id> --json`; it closes only the named gate in local status/readiness summaries after human acceptance of an existing evidence record for the same gate, without running validators, launching services, signing, copying, publishing, or granting execution authority.
- Read-only release readiness checklist through `jarvis-codex --state <state-dir> release readiness-checklist --json`; it aggregates release manifest, artifact evidence, packaging preflight, mobile/Gemini validation plans, external security review, evidence counts, and explicit gate acceptances into blocked-gate next actions without running them.
- HUD release-gate status panel backed by the same read-only runtime RPC; it displays open gates and evidence counts without writing state, accepting evidence, or approving release.
- HUD release-readiness checklist panel backed by the same read-only runtime RPC; it displays blocked gates and next-action commands without running validations, launching services, signing artifacts, publishing releases, or closing gates.
- HUD release-evidence metadata form backed by a runtime-token-gated RPC; it records gate, summary, and reviewer metadata only, with no browser artifact path input and no gate closure.
- HUD release-gate acceptance form backed by a runtime-token-gated RPC; it requires an existing evidence id, writes a state-only human acceptance record, closes only the selected local gate in gate-status/readiness summaries, and grants no execution authority.

## Not Yet Production-Complete

The following release gates remain open until the required evidence is recorded and explicitly accepted:

- Electron desktop app signing, artifact security review, and distribution approval.
- Actual iPhone or approved mobile-device validation over an approved private-network address.
- Approved Gemini Live network validation with credential, billing/quota, redaction, and fallback evidence.
- Release packaging/signing review with explicit copy, upload, or publication approval if distribution is requested.
- External security reviewer attestation beyond local dependency audit evidence.
- Unattended/background scheduling policy acceptance before any daemon, background scheduler, or open-ended loop operation.

## Safety Invariants

- The browser HUD must not execute shell commands directly.
- Voice transcripts and voice intent proposals must not execute commands.
- Command proposals must not create approvals, launch PTYs, mutate Worktrunk, or execute commands.
- Browser-managed speech output must not run local TTS commands or grant approval authority.
- Displayed commands, queue entries, and plan-viewer routes are not execution authority.
- Swarm plans are planning records only; they must not be treated as permission to launch agents, mutate Worktrunk, start PTYs, or run commands.
- Swarm lifecycle records require matching approvals and the HUD runtime token, but they remain state records only and must not be treated as agent launch, Worktrunk mutation, PTY launch, runtime workflow execution, or command execution.
- Swarm role launch requires a matching `swarm.launch` approval that exactly names role IDs, commands, profiles, and cwd values, plus the HUD runtime token. Hardline blocks override approvals. The launch method starts only runtime-managed PTYs and must not mutate Worktrunk, mutate Git, or execute runtime workflows.
- Loop lifecycle records require matching approvals and the HUD runtime token, but they remain state records only and must not be treated as autonomous execution, agent launch, Worktrunk mutation, PTY launch, runtime workflow execution, or command execution.
- Bounded `loop run-once` does not accept arbitrary command strings, launch services, probe the network, mutate Git, mutate Worktrunk, start agents, start PTYs, or execute runtime workflows.
- Bounded `loop schedule` does not start a daemon, background itself, accept arbitrary command strings, launch services, probe the network, mutate Git, mutate Worktrunk, start agents, start PTYs, or execute runtime workflows.
- `loop unattended-policy` is read-only policy evidence. It does not start loops, write state, approve unattended operation, or close the `unattended_loop_scheduling` release gate.
- `loop unattended-evidence-brief` is read-only operator guidance. It does not start daemons, background schedulers, services, agents, PTYs, Worktrunk flows, Git mutation, runtime workflows, write state, approve unattended operation, or close the `unattended_loop_scheduling` release gate.
- PTY launches that require approval must include an approved, command-matched approval id, and that approval is consumed on use.
- Approval responses and approved PTY launches require the per-runtime HUD token served from the same-origin HUD.
- Approval consumption must be atomic; concurrent consumers must not reuse the same approval.
- Hardline policy blocks must continue to override approvals.
- Codeburn telemetry uses a fixed adapter command with `shell=False`; it is not a generic command runner.
- Agent provider status is a readiness matrix only; it must not launch Codex, Antigravity, Codeburn, PTYs, shell commands, Worktrunk, services, or runtime workflows.
- Local STT transcription requires a matching approved audio-processing approval id, the per-runtime HUD token, a server-configured `JARVIS_LOCAL_STT_COMMAND`, a runtime-owned audio file, and either a runtime-owned model path or a safe `model_id` resolved under server-configured `JARVIS_LOCAL_STT_MODELS_DIR`; clients cannot supply adapter commands or arbitrary model paths through RPC.
- Local STT discovery is read-only; it does not approve transcription or select hidden cloud/model fallbacks.
- Local TTS synthesis requires a matching approved audio-processing approval id bound to the requested text SHA-256, the per-runtime HUD token, a server-configured `JARVIS_LOCAL_TTS_COMMAND`, and a runtime-owned output path; clients cannot supply adapter commands or output paths through RPC.
- The runtime WebSocket must reject cross-origin browser clients.
- Runtime PTYs do not execute through a shell. Shell pipelines and shell operators are not supported execution semantics in the current supervisor.
- The PWA service worker must not cache `/rpc`, `/ws`, or non-GET requests.
- Public internet exposure is not part of v1.
- Runtime serving must bind to loopback unless the operator explicitly chooses a private-network host with `--allow-non-loopback`.
- Mobile host discovery is candidate selection only; it does not prove iPhone reachability or approve runtime serving.
- HUD-displayed mobile commands are not execution authority and must not be treated as approval to bind non-loopback, run Worktrunk, mutate git, start local ML, launch Docker, start services, or run daemons.
- Mobile validation plans are evidence checklists only; they must not launch the runtime, probe the network, open browsers, or grant execution authority.
- Mobile evidence briefs are operator collection aids only; they must not be treated as proof that an iPhone reached the HUD or as permission to close `actual_mobile_device_validation`.
- The Electron HUD must remain a client of the runtime. The renderer must not gain Node integration, shell authority, direct command execution, Worktrunk mutation, or runtime-policy bypasses.
- The Electron lockfile is not proof of an installed or packaged app; dependency installation, package builds, signing, and artifact copy remain separate gated actions.
- Local Electron `node_modules` is an ignored setup artifact only; package builds, signing, and artifact copy remain separate gated actions.
- Electron Builder configuration and scripts are reviewed package definitions only; they do not prove a package build ran or approve artifact distribution.
- Local Electron `dist/` artifacts prove only a non-signing package build ran on this machine; they do not approve installer generation, signing, malware review, artifact copy, or distribution.
- Local unsigned AppImage artifacts prove only local installer generation ran on this machine; they do not approve signing, malware review, artifact copy, or distribution.
- The committed Electron icon is package metadata only; it does not approve signing, artifact copy, publication, or distribution.
- Gemini feasibility checks must not expose secret values, start OAuth, open WebSockets, call Gemini, launch services, write state, or bypass the local STT/TTS fallback.
- Gemini validation plans must not expose secret values, start OAuth, open WebSockets, launch adapters, probe the network, write state, approve cloud spend, or bypass local approval boundaries.
- Gemini evidence briefs are operator collection aids only; they must not be treated as proof that Gemini Live connected, approval for cloud spend, permission to run future adapter commands, or permission to close `networked_gemini_live_validation`.
- Nango/Gemini plans are architecture guidance only; they must not create accounts, configure OAuth apps, call Nango APIs, mint Gemini Live tokens, open Gemini WebSockets, route raw audio through a proxy, approve cloud spend, store secrets, or close release gates.
- Packaging preflight must not run npm, install dependencies, build installers, sign artifacts, copy outputs, launch services, or write files.
- Release artifact evidence must not build, sign, copy, publish, launch services, mutate Git, or write files. Hash evidence is not publication approval.
- Packaging/signing evidence briefs are operator collection aids only; they must not run npm, build packages, sign artifacts, copy outputs, publish artifacts, access signing credentials, write files, or close `electron_packaging_and_signing` or `release_packaging_and_signing`.
- Security review planning must not run scanners, launch services, probe networks, build packages, sign artifacts, mutate Git, write files, or claim that review is complete.
- External security evidence briefs are operator collection aids only; they must not run scanners, launch services, probe networks, build packages, sign artifacts, copy outputs, publish artifacts, write files, replace human external reviewer sign-off, or close `external_security_review`.
- Release evidence records must not be treated as execution authority, proof of test execution, publication approval, or automatic gate closure. Human acceptance remains required for external/device/signing gates.
- Release gate acceptance records are human decisions tied to existing evidence. They affect local gate status only; they must not be treated as permission to run commands, publish artifacts, bypass signing/security review, or mutate Git/Worktrunk state.
- Release readiness checklist output must not be treated as permission to run the displayed commands, validate devices, open Gemini network connections, build packages, sign artifacts, copy artifacts, publish releases, or close gates.
- HUD release-gate status is display-only. Seeing evidence counts in the UI must not be treated as permission to close gates, publish artifacts, launch validators, or run release commands.
- HUD release-readiness checklist is display-only. Seeing a next action in the UI must not be treated as approval to run the listed command.
- HUD release-evidence recording must not be treated as artifact acceptance, test execution, publication approval, external reviewer sign-off, or gate closure. Browser clients cannot provide artifact paths for hashing.
- HUD release-gate acceptance must not be treated as permission to run validators, validate devices, open Gemini network connections, build packages, sign artifacts, copy artifacts, publish releases, mutate Git, mutate Worktrunk, or bypass external reviewer requirements.
- Local dependency audits are evidence only; they are not a replacement for external security review, signing review, or runtime threat modeling.

## Required Local Validation

Run from the repo root:

```bash
python3 scripts/validate-jarvis-codex-phase1.py
uv run pytest
```

Expected current baseline:

```text
Status: PASS
Checks passed: 156
Warnings: 0
Failures: 0
381 passed
```

The pytest run may report the existing Starlette `TestClient` deprecation warning, WebSocket deprecation warnings from HUD browser smoke coverage, and other deprecation warnings from dependency surfaces.

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

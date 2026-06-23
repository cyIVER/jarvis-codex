---
title: Jarvis Harness Dashboard
tags:
  - jarvis-harness
  - dashboard
status: active
updated: 2026-06-23 07:33 EDT
---

# Jarvis Harness Dashboard

## Current Objective

Build a Claude Code style JARVIS harness that coordinates Codex, Antigravity, Codeburn, voice, swarm loops, desktop HUD, and private mobile PWA through a governed local runtime.

## Current State

- Specs created under `docs/jarvis-harness/`.
- Spec slice committed and pushed as `5bcd036`.
- Runtime event store and protocol frames committed and pushed as `5442ab5`.
- Policy classifier committed and pushed as `faa97b3`.
- Runtime FastAPI app slice committed and pushed as `6a9d518`.
- Managed PTY supervision committed and pushed as `21ef4ab`.
- Approval lifecycle committed and pushed as `1332552`.
- Live WebSocket PTY stream multiplexing committed and pushed as `276b5ab`.
- Runtime-served HUD shell committed and pushed as `7cbc5c5`.
- Browser STT transcript submission committed and pushed as `11aa08b`.
- Server-side MediaRecorder audio chunk ingestion committed and pushed as `162b9b6`.
- Approval-gated local STT transcription job wiring committed and pushed as `b8be669`.
- Plan-viewer harness route and queue-safety package committed and pushed as `13f2b06`.
- Voice intent proposal layer committed and pushed as `dc9eb7f`.
- Live semantic runtime event push committed and pushed as `479aeda`.
- Voice proposal approval UI committed and pushed as `29c3c65`.
- Approval-matched PTY launch boundary committed and pushed as `6923200`.
- HUD approval response controls committed and pushed as `4ce3839`.
- Approved PTY launch controls committed and pushed as `b6f5fbf`.
- Session continuity controls committed and pushed as `2405333`.
- Live Codeburn telemetry committed and pushed as `fa1d8b1`.
- Mobile/PWA shell affordances committed and pushed as `b70ad56`.
- Production readiness runbook is committed with current implementation state, safety invariants, validation, and mobile gates.
- AG challenge review triggered safety hardening: one-shot approvals, server-configured STT adapter, narrowed dev-loop execution, and Codeburn telemetry-only HUD path.
- AG-triggered runtime safety hardening committed and pushed as `89b09fc`.
- Final integrated validation passed: governance PASS, 165 tests, and HUD/PWA browser smoke.
- Runtime readiness RPC committed and pushed as `c176976`.
- Runtime boundary hardening committed and pushed as `7d3e0b5`.
- HUD readiness panel committed and pushed as `495e7a9`.
- Browser-managed voice status output committed and pushed as `7d8685f`.
- Runtime policy profile catalog committed and pushed as `0b23f80`.
- Runtime semantic message history committed and pushed as `efe573e`.
- HUD semantic session history panel committed and pushed as `3e46529`.
- State-only session archive controls committed and pushed as `49f6fe9`.
- State-only session profile updates committed and pushed as `e08dbac`.
- Semantic prompt history composer committed and pushed as `8b893ed`.
- State-only session fork controls committed and pushed as `59b30f8`.
- Read-only session resume committed and pushed as `9d581a4`.
- Read-only semantic history search committed and pushed as `e8ca6e4`.
- Planning-only swarm plan recording committed and pushed as `f315583`.
- State-only command proposal recording committed and pushed as `ed9e22e`.
- Automated HUD browser smoke coverage committed and pushed as `79897e0`.
- Approval-gated local TTS adapter committed and pushed as `4c747cb`.
- Loopback runtime serve command committed and pushed as `c3db6ad`.
- Current harness release manifest committed and pushed as `b5fda5e`.
- Approval-gated swarm lifecycle records committed and pushed as `3e9d9d0`.
- HUD swarm lifecycle controls committed and pushed as `fa94e00`.
- Hardened Electron HUD scaffold committed and pushed as `95b8221`.
- Read-only mobile private-network preflight committed and pushed as `731340f`.
- Read-only Gemini Live feasibility check committed and pushed as `cdc112a`.
- Approval-gated loop lifecycle records committed and pushed as `5414bf4`.
- HUD loop lifecycle controls committed and pushed as `f9f240e`.
- Read-only release packaging preflight committed and pushed as `b9dcfb1`.
- Read-only mobile validation planner committed and pushed as `6acfb68`.
- Read-only Gemini Live validation planner committed and pushed as `e546350`.
- Electron HUD package-lock committed and pushed as `5577838`.
- Runtime readiness CLI committed and pushed as `2777f1f`.
- Electron HUD local dependency readiness committed and pushed as `8198500`.
- Electron Builder config and reviewed package/make scripts are ready for approval-gated packaging validation.
- Non-signing Electron package execution produced a local ignored `tools/electron-hud/dist/linux-unpacked` artifact; signing and distribution remain gated.
- Read-only local STT discovery is available through `jarvis-codex voice discover --json`.
- Read-only mobile host discovery recommends `172.28.39.152` as the current WSL private-interface candidate.
- Local dependency audits for `tools/electron-hud` and `video/remotion` report zero high-or-worse npm vulnerabilities.
- Unsigned Electron AppImage generation produced a local ignored `tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage` artifact.
- Electron Builder uses committed `tools/electron-hud/assets/icon.png`; local make validation no longer reports the default Electron icon warning.
- Read-only release artifact evidence reports size/SHA-256 for the committed icon and ignored Electron artifacts.
- The HUD renders a non-writing Codex, Antigravity, and Codeburn provider status matrix.
- Read-only mobile evidence brief committed and pushed as `467c4c6`; it packages iPhone validation evidence collection without launching, probing, browsing, writing state, or closing gates.
- Current Codeburn snapshot: today `$13.24` across 114 calls; month `$723.81`, 7507 calls.
- Runtime foundation selected: [[02 Architecture#Runtime]].
- Event store selected: [[02 Architecture#Event Store]].
- Mobile v1 selected: private-network PWA.
- Native iOS moved to future scope.
- Voice selected: Gemini realtime primary if server-mediated auth is approved and validated, local fallback otherwise.

## Active Work

- [[04 Phase Plan#Phase 1 Runtime Foundation And HUD Shell]]
- [[06 Morning Report]]

## Watchpoints

- Plan-viewer package must stay display-only and planning-only; commands and harness routes must not gain execution authority.
- Voice-origin command proposals must remain non-executing until an explicit runtime approval path is added.
- Runtime message history is a semantic event/history view; it is not an execution queue.
- HUD session history renders event history only; it does not authorize command execution.
- Session archive is state lifecycle only; it does not execute shell, PTY, Worktrunk, or runtime workflows.
- Session profile changes are metadata only; they do not grant execution or approval authority.
- Prompt composer records semantic intent only; it does not launch Codex, Antigravity, PTY, Worktrunk, shell, or workflows.
- Session forks create lineage state only; they do not launch agents or commands.
- Session resume is read-only context rehydration; it does not write state or grant approval authority.
- History search is read-only semantic lookup over the event store; blank or missing state returns no results without writes.
- Swarm plans are semantic planning records only; they do not launch agents, Worktrunk, PTYs, shell commands, or workflows.
- Swarm lifecycle records consume matching approvals but remain state only; they do not launch agents, Worktrunk, PTYs, shell commands, or workflows.
- Loop lifecycle records consume matching approvals but remain state only; they do not launch agents, Worktrunk, PTYs, shell commands, or runtime workflows.
- HUD loop lifecycle controls request approval and record approved state only; they do not auto-approve or execute.
- HUD swarm lifecycle controls request approvals and record approved lifecycle state only; they do not auto-approve or execute.
- Agent provider status is a readiness matrix only; it does not launch Codex, Antigravity, Codeburn, PTYs, shell commands, Worktrunk, services, or runtime workflows.
- Electron HUD scaffold loads the runtime as a client only; the renderer has no Node integration or shell authority.
- Electron package-lock pins dependency resolution only; it does not install dependencies, build packages, sign artifacts, copy outputs, or launch services.
- Electron Builder config and package/make scripts define the reviewed local packaging path only; they do not prove package execution, signing, distribution, or artifact security review.
- Local Electron dist artifacts are validation evidence only; they are not signed, copied, reviewed, or distribution-ready release artifacts.
- STT discovery is local asset inspection only; it does not access microphones, process audio, download models, call cloud services, start the runtime, or write state.
- Current local STT discovery result is `NEEDS_SETUP` because no local `whisper-cli` or ggml model candidate was found.
- Mobile host discovery is candidate selection only; it does not start the runtime, probe the iPhone, open a browser, approve non-loopback serving, or prove reachability.
- Local dependency audits are not a replacement for external security review, signing review, or runtime threat modeling.
- Local unsigned AppImage artifacts are not signed, reviewed, copied, or distribution-ready release artifacts.
- The committed Electron icon is package metadata only; it does not approve signing, artifact copy, publication, or distribution.
- Release artifact hash evidence is review data only; it does not approve signing, artifact copy, publication, or distribution.
- Mobile preflight is read-only host classification only; it does not prove actual iPhone reachability, probe the network, launch services, or write state.
- Mobile validation planner is an evidence checklist only; it does not prove actual iPhone reachability, probe the network, launch services, open browsers, write state, or grant execution authority.
- Mobile evidence brief is an operator collection aid only; it does not prove actual iPhone reachability, probe the network, launch services, open browsers, write state, or close the actual mobile validation gate.
- Command proposals classify and store proposed operations only; they do not create approvals, launch PTYs, mutate Worktrunk, or execute commands.
- Runtime serve binds to loopback by default; non-loopback binding requires the explicit `--allow-non-loopback` operator decision.
- Release manifest review is read-only; it does not package, copy artifacts, launch runtime, or approve generated assets.
- Packaging preflight is read-only; it does not install dependencies, build installers, sign artifacts, copy outputs, launch services, or write files.
- Release artifact evidence is read-only; it does not build, sign, copy, publish, launch services, mutate Git, or write files.
- Release readiness checklist is read-only; it aggregates release gates and proposed follow-up commands without running them, writing state, or closing gates.
- HUD release plan panel is read-only; it displays release readiness checklist commands without running validations or closing gates.
- Loop readiness now verifies the loop-budget policy markers, not just file presence.
- Product readiness artifacts now reflect the current validated release checklist, HUD release checklist, loop budget checks, approval-gated swarm launch, and open external release gates.
- Unattended loop policy reporting is available through `jarvis-codex loop unattended-policy --json`; it is read-only and keeps the release gate open.
- Runtime readiness CLI is non-writing and does not start the server.
- Networked Gemini Live validation is unproven and remains approval-gated; the local feasibility check is read-only credential-signal inspection only.
- Gemini validation planner is evidence planning only; it does not start OAuth, open WebSockets, probe the network, launch adapters, write state, expose secrets, approve cloud spend, or grant execution authority.
- Electron security model must keep shell execution in runtime, not renderer.
- Rezun gap coverage must remain explicit: voice, memory, tools, and mobile continuity.

## Next

1. Continue with remaining production gates: real iPhone private-network validation using the operator evidence brief, approved Gemini Live network test, Electron signing/distribution flow, signed release packaging, external reviewer attestation, unattended/background scheduling policy, and safe runtime operator polish.
2. Keep final dashboard current if additional overnight slices land.
3. Keep voice/STT feasibility, plan-viewer, and HUD design tied to the runtime API contract.

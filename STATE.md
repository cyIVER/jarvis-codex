# Loop State - Jarvis Codex

loop_status: active
last_run: 2026-06-23
level: L1
pattern: product-readiness-triage

## High Priority

- [x] PM-001 - Product readiness review
  Loop action: added product readiness review and prioritized backlog.
  Human decision: continue autonomous loop.
- [x] PM-002 - End-to-end workflow rehearsal
  Loop action: added pytest rehearsal covering capture, memory, approval, handoff, doctor governance, queue selection, and continuity.
  Human decision: continue autonomous loop.
- [x] PM-003 - Read-only safe handoff queue summary
  Loop action: added safe handoff module, CLI summary, JSON mode, tests, and docs.
  Human decision: no command runner without a separate PRD.
- [x] PM-004 - Plan viewer browser smoke
  Loop action: added headless Chromium smoke test and committed browser-smoke package.
  Human decision: keep browser launch out of production CLI automation.
- [x] PM-005 - Loop Engineering autonomous workflow
  Loop action: added `LOOP.md`, loop state, budget, run log, safety gates, and pattern registry.
  Human decision: L1 report-first loop only; no unattended mutation.
- [x] PM-006 - Worktrunk lane CLI design
  Loop action: added read-only-first PRD and guardrail test; lane mutation remains approval-gated.
  Human decision: implementation may only start with read-only `lane list` and `lane score`.
- [x] PM-007 - Read-only Worktrunk lane CLI implementation
  Loop action: added JSON-only `lane list` and `lane score`; no mutation verbs.
  Human decision: mutation commands remain out of scope.
- [x] PM-008 - Broader real-worktree lane review coverage
  Loop action: added an isolated real git-worktree pytest fixture for read-only lane inventory and scoring.
  Human decision: still no lane mutation commands.
- [x] PM-009 - Release artifact review manifest
  Loop action: added read-only release manifest CLI, docs, and tests for local review surfaces and generated Remotion asset approval labels.
  Human decision: no artifact copy, publish, upload, or release bundle without explicit approval.
- [x] PM-010 - GitHub CI and review templates
  Loop action: added validation-only GitHub CI, PR template, issue template, and guardrail tests.
  Human decision: no render, publish, release upload, or runtime execution in CI; workflow actions use current Node 24-compatible major versions.
- [x] PM-011 - Local loop readiness verifier
  Loop action: added read-only `jarvis-codex loop verify --json`, package tests, and docs.
  Human decision: no new project-local loop skills or agents until governance baseline expansion is approved.
- [x] PM-012 - File-based local STT voice ingress
  Loop action: added approval-gated `voice ingest --audio-file` with explicit local adapter command, model path, and included `whisper.cpp` wrapper.
  Human decision: microphone listeners, model downloads, cloud STT, GPU/NPU STT adapters, and Codex App Server bridge remain separate approval-gated phases.
- [x] PM-013 - STT readiness probe
  Loop action: added `voice probe --json` and `whisper-cpp-stt-adapter.py --check-only` so local STT wiring can be verified without processing audio or writing state.
  Human decision: real transcription requires operator-selected `whisper-cli`, a local ggml model, and explicit `--allow-audio-processing`.
- [x] PM-014 - Expanded release readiness manifest
  Loop action: expanded the read-only release manifest to cover core docs, loop state, voice ingress, local runtime, safe handoff, Worktrunk lane PRD, and explicit publication approval status.
  Human decision: publication, artifact copying, release uploads, and generated asset promotion still require separate approval.
- [x] PM-015 - whisper.cpp STT operator runbook
  Loop action: added a no-download runbook for operator-supplied `whisper-cli`, local ggml models, STT readiness probing, and guarded transcription.
  Human decision: Jarvis still does not install `whisper.cpp`, download models, convert audio, or approve microphone/background listeners.
- [x] PM-016 - Real local STT transcription exercise
  Loop action: cached whisper.cpp v1.9.1 and `ggml-tiny.en.bin` outside the repo, proved `voice discover --json` is `READY`, probed the JFK sample without writes, and captured one approved sample transcript into `/tmp` state.
  Human decision: this validates file-based local STT only; microphone listeners, runtime chunk transcription, cloud STT, and background capture remain gated.
- [x] PM-017 - Runtime STT model-id boundary
  Loop action: added server-resolved `model_id` support for `voice.transcribe_audio` so runtime audio can use a configured local model directory without accepting arbitrary client model paths.
  Human decision: clients still cannot supply adapter commands or arbitrary filesystem model paths; transcription remains approval-gated.
- [x] PM-018 - HUD approved local STT controls
  Loop action: added HUD controls to request approval for the last captured local audio chunk and run approved local STT transcription through `model_id`.
  Human decision: the HUD still separates microphone permission, audio storage, approval, and transcription; no command execution authority is granted.
- [x] PM-019 - HUD mobile access readiness
  Loop action: surfaced non-writing mobile host discovery in runtime readiness and the HUD, including recommended private URL and display-only serve/preflight/validation command proposals.
  Human decision: real iPhone private-network validation and non-loopback runtime serving still require explicit operator approval and evidence.
- [ ] PM-020 - Next product slice
  Loop action: pending prioritization between real browser microphone operator test, iPhone private-network validation, operator release review, Gemini Live network validation, actual swarm launch design, and actual loop execution design.
  Human decision: not selected yet.

## Watch List

- Validator portability and governance drift checks.
- Project-local `skills.config` only if repeated routing noise appears.
- Loop audit score is 86/100; generic loop-triage, loop-verifier skill, and loop-budget skill automation remain deferred to avoid changing the Phase 1 governance baseline.
- Voice microphone capture, cloud STT, Jarvis-managed model downloads, and Codex App Server bridge remain gated; file-based local STT plus a `whisper.cpp` adapter wrapper, non-runtime readiness probe, and one approved sample transcription are implemented.
- Generated Remotion PNG/MP4 artifacts remain local ignored outputs unless approved for release packaging; manifest output is review-only.

## Recent Noise

- Antigravity bridge broad repo request produced an empty file; direct `agy --print` returned a useful challenge pass.
- Loop audit recognizes only generic loop scaffolding names, so Jarvis-specific reviewer/governance controls need to be interpreted alongside the score.

---
Run log: 2026-06-23 | findings: voice ingress needed actual STT instead of transcript-only deferral | actions: added approval-gated local executable STT adapter path | escalations: 0
Run log: 2026-06-23 | findings: local STT cache was missing | actions: installed whisper.cpp v1.9.1 user-cache binary, downloaded `ggml-tiny.en.bin`, probed JFK sample, captured approved sample transcript into temp state | escalations: 0
Run log: 2026-06-23 | findings: runtime STT needed a model cache path that did not let clients pass arbitrary filesystem paths | actions: added server-resolved `model_id` support under `JARVIS_LOCAL_STT_MODELS_DIR` with traversal and direct-cache-path tests | escalations: 0
Run log: 2026-06-23 | findings: HUD lacked a button path from captured audio chunks to approved local STT | actions: added transcription approval request and approved transcription controls for the latest captured audio path | escalations: 0
Run log: 2026-06-23 | findings: mobile host discovery existed only in CLI/docs and was not visible in the harness | actions: added non-writing mobile access evidence to runtime readiness and HUD display-only command proposals | escalations: 0

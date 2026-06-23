# Jarvis Codex

Local-first voice and memory layer for Codex.

This project turns the "JARVIS for coding agents" idea into a practical system:

- **Voice loop**: capture spoken or typed intent and turn it into structured work.
- **Persistent memory**: preserve project facts, preferences, decisions, and task episodes outside chat history.
- **Tool boundary**: prepare Codex-ready handoffs while keeping execution, commits, deployments, and destructive actions behind explicit approval.

The current platform is a governed local harness foundation. It does not replace Codex or grant autonomous execution by default; it provides a runtime HUD, durable event/state surfaces, voice ingress, approval-gated PTY/swarm/loop controls, release evidence views, and explicit safety boundaries for operator-driven testing.

## Quick Start

```bash
uv run jarvis install
jarvis
```

`jarvis install` creates or updates `~/.local/bin/jarvis` for this WSL repo. Ensure `~/.local/bin` is on `PATH`, then `jarvis` starts the WSL runtime on `127.0.0.1:8765` and opens the Windows desktop UI when the portable Electron app is present.

By default, state is stored in `./state`.

From Windows, add the launcher directory to the user PATH:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\install-jarvis-path.ps1
jarvis
```

## Commands

```bash
jarvis                                 # start WSL runtime and open/connect Windows desktop UI
jarvis --help                          # detailed operator manual
jarvis chat --help                     # push-to-talk, mic/STT, interrupt, and approval notes
jarvis chat --loop                     # keep listening; Ctrl+C during an answer records a correction
jarvis chat --no-speak                 # run chat without spoken TTS output
jarvis chat --terminal-mode full       # print the full assistant text instead of compact terminal notes
jarvis ui --help                       # Windows portable UI launch and runtime connection notes
jarvis status                          # runtime health, PID file, and log path
jarvis stop                            # stop only the PID recorded by Jarvis
jarvis doctor                          # inspect local state
jarvis doctor --governance             # include project-local Codex governance validation
jarvis-codex capture "task text"          # create an inbox episode
jarvis-codex voice ingest --transcript-file transcript.txt --json
jarvis-codex voice plan grab this file in this location src/app.py --json
jarvis-codex voice ask "explore this codebase and summarize the routing" --sandbox read-only --approval-mode deny --json
jarvis-codex voice listen --record-command "$JARVIS_RECORD_COMMAND" --model models/ggml-base.en.bin --stt-command "python3 scripts/whisper-cpp-stt-adapter.py --whisper-command /path/to/whisper-cli" --allow-microphone --allow-audio-processing --sandbox read-only --json
jarvis-codex voice discover --json
jarvis-codex voice probe --audio-file recording.wav --model models/ggml-base.en.bin --stt-command "python3 scripts/whisper-cpp-stt-adapter.py --whisper-command /path/to/whisper-cli" --json
jarvis-codex voice ingest --audio-file recording.wav --model models/ggml-base.en.bin --stt-command "python3 scripts/whisper-cpp-stt-adapter.py --whisper-command /path/to/whisper-cli" --allow-audio-processing --json
jarvis-codex memory add KEY VALUE         # add durable memory
jarvis-codex memory list                  # print memory records
jarvis-codex approve request "summary"    # create an approval request
jarvis-codex handoff                      # generate a Codex handoff brief
jarvis-codex handoff --queue-summary      # print a read-only safe planning-queue handoff
jarvis-codex hardware --workload llm      # inspect CPU/GPU/NPU/Docker capabilities
jarvis-codex lane list --json             # inspect Worktrunk lane readiness without mutation
jarvis-codex lane score --repo . --branch main --json
jarvis-codex release manifest --json      # review release artifacts without packaging
jarvis-codex release packaging-preflight --json
jarvis-codex loop verify --json           # verify loop readiness without mutation
jarvis-codex runtime serve                # serve the runtime HUD on 127.0.0.1:8765
jarvis-codex runtime readiness --json     # print current runtime readiness without serving
jarvis-codex mobile discover --json       # discover private-network host candidates without probing
jarvis-codex mobile preflight --json      # classify private-network iPhone/PWA access without probing
jarvis-codex mobile validation-plan --json # prepare iPhone/PWA test evidence without serving
jarvis-codex gemini feasibility --json    # inspect Gemini Live auth readiness without connecting
jarvis-codex gemini validation-plan --json # prepare Gemini Live test evidence without connecting
jarvis-codex doctor                       # inspect local state
jarvis-codex doctor --governance          # include compact Codex governance validation
jarvis-plan-viewer                        # serve the local plan and next-step selector
```

`jarvis-codex runtime serve` binds to loopback by default. Non-loopback binding for private-network use requires `--allow-non-loopback` and should be treated as an explicit operator decision.

`jarvis` is the operator command. `jarvis-codex` remains the lower-level compatibility command for scripts, JSON-only review surfaces, and explicit runtime subcommands.

## Test The Local HUD

Use this path for a local operator smoke test:

```bash
cd /home/iveri/repos/jarvis-codex
uv run jarvis runtime readiness --json
uv run jarvis
```

Open:

```text
http://127.0.0.1:8765
```

Expected status:

- The HUD loads as a local runtime shell.
- Runtime readiness reports `foundation-ready`, not production-complete.
- Release panels show open gates, evidence briefs, and display-only next actions.
- Microphone access is requested only after an operator click.
- Approval and launch flows remain separate; displayed commands are not execution authority.

Do not treat a successful HUD smoke test as release approval. The remaining release gates still require separate human evidence and acceptance for actual iPhone validation, approved Gemini Live network validation, Electron/release signing, external security review, and unattended/background scheduling policy.

## Windows Desktop App

Jarvis is shaped as a split local desktop system:

- WSL owns runtime, Codex, voice routing, approvals, PTYs, state, and policy.
- Windows owns the portable Electron operator UI.
- The UI connects to `http://127.0.0.1:8765` and is not an executor.

Windows launchers live under `tools/windows/`:

```powershell
.\tools\windows\jarvis.cmd
.\tools\windows\jarvis.ps1
```

Both launchers call into WSL, start or connect the runtime through the `jarvis` command, and let the WSL-side operator command open the portable Electron app when available.

## Spoken Chat

`jarvis chat` records one foreground microphone turn, transcribes it locally, and speaks the assistant response in chunks as text arrives when local TTS is available.

Terminal output is compact by default. Jarvis reserves the terminal for material that voice alone does not handle well: commands, code blocks, paths, approvals, errors, and status. Use `--terminal-mode full` if you want the old full text stream.

By default it tries `JARVIS_LOCAL_TTS_COMMAND` first. If that is not set, it falls back to the local Windows Piper setup at `C:\Users\iveri\Apps\piper\say.ps1`.

Use `--no-speak` to disable audio, `--speech-mode full-final` to speak only after completion, or `--tts-command` for a custom local TTS adapter that reads text from stdin and accepts `--output-file`.

Use `--loop` for conversational correction. In loop mode, pressing Ctrl+C while Jarvis is answering cancels the current Codex turn and starts a new recording window, so you can correct a bad transcript such as "co-bitch" versus "code base" without restarting the command.

## Safety Boundary

This project prepares work for Codex. It does not execute tools, modify repositories, push branches, create PRs, deploy software, or spend money unless a future integration adds that behavior behind an approval gate.

## Codex Governance

Jarvis Codex includes project-local Codex governance files for read-only planning, review, docs research, and Worktrunk lane planning.

Validate the local governance state manually:

```bash
python3 scripts/validate-jarvis-codex-phase1.py
```

The validator is stdout-only and does not write reports. It checks the project-local `.codex/config.toml`, `.codex/agents/*.toml`, and `.agents/skills/*/SKILL.md` files.

`jarvis-codex doctor` does not run governance validation by default.

Use the opt-in governance check when needed:

```bash
jarvis-codex doctor --governance
```

This adds a compact `codex_governance` summary to doctor output. The standalone validator remains available:

```bash
python3 scripts/validate-jarvis-codex-phase1.py
```

The governance validator is stdout-only and does not write reports. It checks project-local Codex governance files; it is not a replacement for unit tests, browser checks, hardware checks, or runtime validation.

Governance validation does not approve installs, migrations, service launches, runtime workflows, Worktrunk mutation, or git mutation.

## Local Acceleration

Jarvis Codex can inspect local CPU, NVIDIA CUDA GPU, Windows NPU, WSL GPU bridge, and Docker Desktop availability:

```bash
uv run jarvis-codex hardware --workload voice
uv run jarvis-codex hardware --workload video
```

NPU use is routed conservatively. In WSL, NPUs are usually accessed through Windows runtimes such as ONNX Runtime DirectML or OpenVINO rather than as a normal Linux device. Jarvis reports that boundary instead of assuming NPU access.

## Local Review UI

`jarvis-plan-viewer` serves the Gate 2 plan and a local next-step selector from `127.0.0.1`.

```bash
uv run jarvis-plan-viewer --dir plans/jarvis-codex-swarm --state state
```

Selected next steps are written to `state/next-steps/selection.json`, which is ignored by Git. The tracked `state/next-steps/.gitkeep` file only preserves the local state directory.

## Gate Docs

- `LOOP.md`
- `STATE.md`
- `loop-budget.md`
- `loop-run-log.md`
- `docs/safety.md`
- `docs/VOICE_NOTIFICATIONS.md`
- `docs/VOICE_INGRESS.md`
- `docs/WHISPER_CPP_STT_RUNBOOK.md`
- `docs/RUNTIME_GATES.md`
- `docs/REMOTION_REVIEW.md`
- `docs/RELEASE_ARTIFACTS.md`
- `docs/PRODUCT_READINESS.md`
- `docs/SAFE_HANDOFF_GATEWAY_PRD.md`
- `docs/WORKTRUNK_LANE_CLI_PRD.md`
- `docs/WORKTRUNK_LANES.md`
- `docs/JARVIS_WHITE_PAPER.md`

## CI

GitHub CI runs Python tests, project-local Codex governance validation, and Remotion typecheck/audit checks. It does not render Remotion assets, publish artifacts, mutate Git/Worktrunk state, launch services, or execute local runtime workflows.

## Release Gates

The local governed harness foundation is implemented and validated. Do not treat it as production-complete until these gates have accepted evidence:

1. Actual iPhone or approved mobile-device validation over an approved private-network address.
2. Approved Gemini Live network validation with credential, billing/quota, redaction, and fallback evidence.
3. Electron packaging/signing review with signed artifact hashes and security review.
4. Release packaging/signing review with explicit copy, upload, or publication approval if distribution is requested.
5. External security reviewer attestation with reviewed scope, findings, remediation status, and sign-off.
6. Unattended/background scheduling policy acceptance before any daemon, background scheduler, or open-ended loop operation.

Useful read-only review commands:

```bash
uv run jarvis-codex runtime readiness --json
uv run jarvis-codex release readiness-checklist --json
uv run jarvis-codex mobile evidence-brief --json
uv run jarvis-codex gemini evidence-brief --json
uv run jarvis-codex release packaging-evidence-brief --json
uv run jarvis-codex release security-evidence-brief --json
uv run jarvis-codex loop unattended-evidence-brief --json
```

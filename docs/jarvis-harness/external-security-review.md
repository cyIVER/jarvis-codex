# External Security Review Packet

This packet prepares Jarvis Codex for an external security review. It is not proof that the review has been completed.

## Standards References

- OWASP Application Security Verification Standard 5.0.0: `https://owasp.org/www-project-application-security-verification-standard/`
- OWASP Web Security Testing Guide: `https://owasp.org/www-project-web-security-testing-guide/`
- OWASP Top 10 2025: `https://owasp.org/www-project-top-ten/`
- OWASP Top 10 for LLM Applications 2025: `https://genai.owasp.org/llm-top-10/`
- MITRE ATLAS: `https://atlas.mitre.org/`

Use ASVS as the application verification requirements baseline, WSTG as the web application and web service testing methodology, and OWASP Top 10 as a broad application-risk awareness checklist. Use OWASP Top 10 for LLM Applications and MITRE ATLAS for agentic, LLM, tool-use, excessive-agency, prompt-injection, and AI-adjacent review surfaces. ASVS alone is not sufficient for swarm, PTY, voice, or agentic-loop risk.

## Review Scope

External review should cover:

- Runtime JSON-RPC authorization, runtime-token gates, approval creation, and approval consumption.
- Browser HUD same-origin WebSocket use, CSP, displayed command boundaries, microphone/STT approval flow, and PTY launch controls.
- PTY supervision, command policy, hardline blocks, process cleanup, and output handling.
- Voice, local STT/TTS, local model path handling, transcript-to-action separation, and local adapter approval gates.
- Private-network mobile/PWA exposure, service worker cache boundaries, and non-loopback serving approval.
- Electron main/preload isolation, denied navigation/window-open behavior, packaging/signing boundaries, and generated artifact policy.
- Bounded loop and swarm surfaces, including `loop run-once`, foreground `loop schedule`, and approval-bound `swarm.launch`.

## Read-only Review Commands

These commands prepare evidence only:

```bash
python3 scripts/validate-jarvis-codex-phase1.py
uv run pytest tests/test_codeburn.py tests/test_event_stream.py tests/test_voice_intent.py tests/test_plan_viewer.py tests/test_voice_audio.py tests/test_hud.py tests/test_hud_browser.py tests/test_runtime_app.py tests/test_voice.py tests/test_whisper_cpp_adapter.py tests/test_approval.py tests/test_event_store.py tests/test_pty_supervisor.py tests/test_policy.py tests/test_protocol.py tests/test_governance.py tests/test_cli.py tests/test_state.py tests/test_release.py tests/test_electron_hud_scaffold.py tests/test_mobile.py tests/test_gemini.py tests/test_packaging.py tests/test_loop_readiness.py tests/test_autonomous_loop.py
uv run jarvis-codex release manifest --json
uv run jarvis-codex release artifact-evidence --json
uv run jarvis-codex release security-review-plan --json
uv run jarvis-codex runtime readiness --json
```

`runtime readiness` is a non-server-starting readiness summary. It must not be interpreted as permission to launch the runtime, bind a socket, open a browser, start a daemon, or probe the network.

## Not Authorized By This Packet

This packet does not authorize:

- Service or daemon launch.
- Runtime server launch.
- Browser opening.
- Network probing.
- Mobile device testing.
- Gemini Live connection testing.
- npm install, package builds, signing, artifact copying, or publishing.
- Git mutation or Worktrunk mutation.
- Destructive filesystem operations.
- Penetration testing against third-party systems.

## Reviewer Deliverables

The reviewer should return:

- Threat model notes for runtime, HUD, PTY, voice, mobile, Electron, release, swarm, and loop surfaces.
- ASVS/WSTG-aligned findings with severity, affected path, reproduction notes, and remediation recommendation.
- OWASP LLM Top 10 or MITRE ATLAS mapping for LLM, agentic, prompt, PTY, local model, and tool-use findings where applicable.
- Explicit sign-off or hold recommendation for release packaging and private-network/mobile exposure.
- List of tests, commands, manual evidence, and source files reviewed.

## Release Gate

`external_security_review` remains open until an external reviewer completes the review, any required fixes are implemented, the validation suite is rerun, and the operator accepts an explicit external reviewer attestation artifact.

Passing tests, implemented fixes, green readiness output, or this packet alone are not sufficient to set `external_review_completed=true` or close the gate.

# Voice Mode

Jarvis voice mode should feel conversational while preserving execution safety.

## Voice Strategy

Primary lane:

- Gemini realtime voice when existing OAuth-compatible auth can support it.
- No paid API-key fallback is assumed.
- If OAuth realtime is unavailable, cloud realtime voice is disabled and surfaced clearly.

Fallback lane:

- Local `faster-whisper` GPU STT.
- Local cinematic TTS adapter with an original Jarvis-inspired voice.
- No real-person or copyrighted character voice clone.

Current implemented browser lane:

- The HUD can speak the runtime readiness summary with browser-managed `speechSynthesis` after a user click.
- Browser speech output does not run a local TTS command, grant execution authority, or approve tool use.

Current implemented local TTS lane:

- `voice.synthesize_audio` can run a server-configured local TTS adapter only after a matching approval and HUD runtime token.
- Approval is bound to the requested text SHA-256.
- The runtime chooses the output path under its audio directory; clients cannot supply adapter commands or output paths.
- Local TTS output is audio processing only and does not grant command execution authority.

## UX Model

Use click-to-arm voice:

- User clicks the mic button.
- HUD shows listening state.
- Transcript preview appears in real time or near real time.
- Safe conversational turns can be routed quickly.
- Risky tool, file, git, runtime, money, public exposure, or credential actions require explicit confirmation.

Conversational mode should support:

- Turn-taking.
- Interruption or barge-in.
- Partial transcript display.
- Spoken response streaming when provider/backend supports it.
- Visible provider and privacy state.

## Local Voice Fallback

Local fallback pipeline:

1. Electron or PWA captures audio after user click.
2. Runtime receives audio chunks or utterance file.
3. `faster-whisper` GPU adapter transcribes.
4. Runtime classifies intent and risk.
5. Local TTS speaks a response when enabled.
6. Command execution still flows through policy gates.

The local fallback may be slower than cloud realtime but must be private and auditable.

The browser-managed speech output is a UX affordance. The local adapter is separately gated because it executes a runtime-side command.

## Gemini OAuth Constraint

The runtime must include an early feasibility gate:

- Check whether available Gemini or Antigravity OAuth auth can support realtime voice.
- If not, do not silently switch to API keys.
- Report the limitation in the HUD and CLI.

## Safety Rules

- Microphone access requires a user gesture.
- Cloud voice mode must show a visible cloud indicator.
- Transcripts are not commands until routed by the runtime.
- High-risk commands require approval even when spoken.
- Voice mode cannot grant durable permissions by itself.

## Acceptance Criteria

- Mic button cannot start recording without a click.
- User sees transcript before risky execution.
- Cloud realtime cannot activate without approved auth.
- Local fallback can route a spoken prompt to a session.
- Spoken commands that imply destructive action create approval requests.

# Voice Architecture

Voice is the primary bridge from off-desk creative flow into Jarvis execution.

## Voice Lanes

### Cloud Realtime Lane

Goal: conversational ChatGPT/Gemini-style voice.

Requirements:

- Gemini realtime primary.
- OAuth-compatible auth only.
- Visible cloud indicator.
- No silent API-key fallback.
- Realtime transcript and response events persisted.
- Tool execution still routed through policy.

Blocked if:

- Available OAuth cannot access realtime voice.
- Auth would require paid API-key setup not approved by the user.

### Local Privacy Lane

Goal: private/offline-capable voice command and conversation fallback.

Requirements:

- `faster-whisper` GPU STT adapter.
- Original cinematic local TTS adapter.
- Click-to-arm microphone.
- Transcript preview.
- Risk-gated command routing.

### Browser Output Lane

Goal: immediate spoken feedback without server-side TTS execution.

Implemented behavior:

- The HUD can speak runtime readiness status through browser `speechSynthesis` after a user click.
- The speech text is derived from the non-writing `runtime.readiness` response.
- Browser output is not command authority and does not run a local TTS adapter.

## Turn State Machine

States:

- `idle`
- `arming`
- `listening`
- `transcribing`
- `thinking`
- `speaking`
- `interrupted`
- `approval_required`
- `failed`

Events:

- `voice.start_requested`
- `voice.permission_granted`
- `voice.audio_chunk`
- `voice.transcript_partial`
- `voice.transcript_final`
- `voice.intent_classified`
- `voice.response_audio_chunk`
- `voice.interrupted`
- `voice.approval_required`
- `voice.stopped`
- browser-managed status speech click

## Command Safety

Voice transcripts are not commands by themselves.

The runtime must:

- classify intent,
- detect risk,
- map to a session action,
- request approval when needed,
- and log every transition.

## Mobile UX

The iPhone PWA should show:

- Mic state.
- Transcript preview.
- Cloud/local mode.
- Current session.
- Pending approval.
- Last routed action.

## Acceptance Criteria

- User can talk through an idea away from the desk.
- Jarvis can create structured plan/session notes.
- High-risk commands require confirmation.
- Local fallback works when cloud realtime is unavailable.

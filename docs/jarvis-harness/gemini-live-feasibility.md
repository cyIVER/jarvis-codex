# Gemini Live Feasibility

This note records the current Gemini Live voice feasibility decision for the Jarvis harness. It is planning and readiness documentation only; it does not authorize a live network connection.

## Current Finding

Gemini Live remains a viable cloud realtime voice lane, but Jarvis should integrate it through a server-mediated runtime adapter first.

The browser and iPhone PWA must not receive long-lived API keys. Direct browser-to-Gemini Live access requires a separately designed ephemeral-token backend.

## Source Grounding

Sources checked on 2026-06-23:

- Google AI for Developers: Gemini Live API overview, `https://ai.google.dev/gemini-api/docs/live-api`
- Google AI for Developers: Live API WebSocket guide, `https://ai.google.dev/gemini-api/docs/live-api/get-started-websocket`
- Google AI for Developers: OAuth quickstart, `https://ai.google.dev/gemini-api/docs/oauth`
- Google AI for Developers: API key guidance, `https://ai.google.dev/gemini-api/docs/api-key`

Relevant current constraints:

- Live API is documented as a low-latency voice and vision API over a stateful WebSocket.
- The WebSocket guide documents API-key authentication for direct WebSocket setup and a separate ephemeral-token path.
- The Live API overview recommends ephemeral tokens for production client-to-server browser access.
- OAuth is documented as stricter than basic API-key setup, but the quickstart is explicitly testing-oriented.
- Gemini API key handling is changing in 2026; unrestricted standard keys are not a production-safe Jarvis default.

## Implemented Local Check

Run:

```bash
jarvis-codex gemini feasibility --json
```

The check is read-only. It reports whether these credential signals are present:

- `GEMINI_API_KEY`
- `GOOGLE_API_KEY`
- `GOOGLE_APPLICATION_CREDENTIALS`
- local application-default credentials file presence

It does not:

- print secret values
- start OAuth
- open a WebSocket
- call Gemini
- probe the network
- launch services
- write state

## Recommended Integration Shape

Use this order:

1. Server-mediated runtime adapter using an operator-provided auth key or OAuth/ADC credential.
2. Explicit cloud indicator in the HUD and PWA.
3. Audio flow through the runtime event model.
4. Tool calls routed through existing policy, approvals, and PTY boundaries.
5. Browser-direct Live API only after ephemeral-token minting is designed, implemented, and reviewed.

## Remaining Gates

- Choose the approved credential mode.
- Confirm billing, quota, and key restriction policy.
- Design ephemeral-token minting before any browser-direct Live API path.
- Implement the Gemini Live adapter behind an explicit approval gate.
- Run a networked Gemini Live connection test only after separate operator approval.
- Preserve local STT/TTS fallback.

## Safety Boundary

The feasibility check is not a voice adapter. It is not proof that Gemini Live works in this environment. It is only a local readiness summary.

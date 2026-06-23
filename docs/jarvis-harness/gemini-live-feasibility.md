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

## Implemented Validation Plan

Run:

```bash
jarvis-codex gemini validation-plan --json
```

The validation plan is also read-only. It turns the current Live API constraints into an operator evidence checklist without:

- starting OAuth
- opening a Gemini WebSocket
- launching a runtime adapter
- probing the network
- writing state
- exposing secret values
- granting execution authority

The plan requires separate approval before any networked test. Browser-direct Live API remains blocked until ephemeral-token minting is designed and reviewed. Server-mediated validation remains the preferred first path.

## Nango Integration Planning

Run:

```bash
jarvis-codex gemini nango-plan --json
```

This plan records a future Nango-governed Gemini Live architecture without creating Nango accounts, configuring OAuth apps, calling Nango APIs, opening Gemini WebSockets, launching services, writing state, exposing secrets, or granting cloud-spend authority.

Current decision:

- Do not proxy raw realtime Gemini Live audio through Nango by default.
- Use Nango for governed Google credential, connection, tool/action, rate-limit, and audit surfaces.
- Use Jarvis runtime policy and HUD-token checks to guard a future token-mint endpoint.
- Use short-lived Gemini Live ephemeral tokens before any browser-direct HUD or PWA WebSocket path.
- Route any Gemini Live tool-call intent back through Jarvis approval gates before execution.

This decision is grounded in the official Gemini Live WebSocket and ephemeral-token guidance plus Nango's documented auth, proxy, and tool-calling role. An Antigravity read-only challenge agreed with this boundary: Nango should govern credentials and tool surfaces, while latency-sensitive Gemini Live audio should use a direct Live API connection with short-lived tokens when browser-direct streaming is required.

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
- Approve the Nango environment, provider integration id, credential storage model, token-mint endpoint design, and secret-redaction policy before live Nango work.
- Implement the Gemini Live adapter behind an explicit approval gate.
- Run a networked Gemini Live connection test only after separate operator approval.
- Preserve local STT/TTS fallback.

## Safety Boundary

The feasibility check and validation plan are not voice adapters. They are not proof that Gemini Live works in this environment. They are local readiness and evidence-planning summaries only.

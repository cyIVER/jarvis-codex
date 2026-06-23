# Jarvis Harness Product Spec

This directory defines the production harness target for Jarvis Codex.

Jarvis is a Claude Code style command harness with a JARVIS-inspired interface. It should coordinate Codex, Antigravity, Codeburn, local shell tools, voice input, mobile access, review gates, and autonomous loops through one governed runtime.

## Product Objective

Build a local-first agent command center that can:

- Run an interactive CLI/HUD harness with slash-command style control.
- Coordinate Codex execution, Antigravity planning/review, dynamic adversarial swarms, shell tasks, and Codeburn telemetry.
- Persist sessions, approvals, jobs, PTY events, voice turns, and review results in a searchable durable store.
- Provide a full animated Electron desktop HUD and a private-network iPhone PWA.
- Support conversational voice with Gemini realtime where OAuth allows it, and local voice fallback otherwise.
- Execute work autonomously after an approved plan while preserving hard safety gates.

## V1 Decisions

- Runtime core: Python FastAPI.
- Protocol: ACP-style JSON-RPC everywhere.
- State: SQLite/WAL append-only event store with FTS projections.
- Desktop: Electron, React, TypeScript, xterm.js, WebGL/Canvas HUD layer.
- Mobile: private-network PWA over Tailscale or WireGuard.
- Native iOS: planned future feature, not v1.
- Voice: cloud realtime primary through Gemini OAuth if available; local `faster-whisper` GPU plus cinematic local TTS fallback.
- PTYs: runtime-managed panes for Codex, Antigravity, shell, and Codeburn.
- Swarm: dynamic risk-scaled roles.
- Git flow: validate, commit coherent groups, push to main, monitor status, then continue after each phase.

## Spec Map

- [runtime-acp.md](runtime-acp.md): runtime service, JSON-RPC protocol, and process supervision.
- [event-store.md](event-store.md): SQLite event store, projections, exports, and retention.
- [hud-electron-pwa.md](hud-electron-pwa.md): desktop HUD, mobile PWA, modes, and visual system.
- [voice-mode.md](voice-mode.md): realtime voice, local fallback, turn-taking, and safety.
- [gemini-live-feasibility.md](gemini-live-feasibility.md): current Gemini Live auth, token, and validation gates.
- [permissions-policy.md](permissions-policy.md): policy profiles, command gates, and hard blocks.
- [swarm-and-loops.md](swarm-and-loops.md): `/loop`, `/swarm`, adversarial review, and Codeburn telemetry.
- [mobile-access.md](mobile-access.md): private iPhone access and future native app boundary.
- [phase-roadmap.md](phase-roadmap.md): shippable implementation phases and acceptance gates.
- [api-contract.md](api-contract.md): JSON-RPC method surface and frame model.
- [data-model.md](data-model.md): database tables, event categories, projections, and retention.
- [test-strategy.md](test-strategy.md): test layers and phase gates.
- [autonomous-loop-runbook.md](autonomous-loop-runbook.md): overnight/long-run operating loop.
- [acceptance-matrix.md](acceptance-matrix.md): release readiness matrix.
- [research-log.md](research-log.md): external and local research grounding.
- [rezun-gap-map.md](rezun-gap-map.md): direct mapping to the "Chasing Jarvis" missing pieces.
- [memory-architecture.md](memory-architecture.md): working, project, meta, and episodic memory layers.
- [voice-architecture.md](voice-architecture.md): cloud realtime and local fallback voice lanes.
- [continuity-model.md](continuity-model.md): cross-session, cross-client, and cross-agent continuity model.
- [production-readiness.md](production-readiness.md): current implementation state, validation commands, smoke checks, and release gates.

## Obsidian Vault

The implementation memory vault lives under [vault/](vault/). It uses Obsidian-flavored Markdown, wikilinks, frontmatter, and `.base` views to keep decisions, risks, phases, and research navigable.

## Non-Negotiable Boundaries

- Public internet exposure is not part of v1.
- Paid API-key realtime voice is not assumed or silently enabled.
- Native iOS is future scope.
- The harness may prepare, validate, commit, push, and monitor after phase approval, but destructive actions, secrets, money, public exposure, and high-risk runtime actions remain gated.
- Displayed commands and queue entries are not execution authority by themselves.

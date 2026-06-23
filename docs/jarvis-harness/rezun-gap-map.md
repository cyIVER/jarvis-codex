# Rezun Gap Map

This document maps the Jarvis harness plan to Dr. Tali Rezun's article, "Chasing Jarvis: The Three Missing Pieces in AI Coding Agents."

Source: <https://medium.com/@talirezun/chasing-jarvis-the-three-missing-pieces-in-ai-coding-agents-0343ee95356f>

## Article Thesis

Rezun argues that current coding agents are already strong at code generation, tool use, debugging, and multi-file implementation. The remaining gap is architectural rather than model intelligence.

The recurring blockers are:

- Real-time voice conversation attached to the actual coding agent.
- Persistent memory across sessions, projects, and development history.
- Tool and MCP integration that can be used through conversational, memory-aware workflows.
- Mobile availability that preserves creative flow away from the desk.

Jarvis harness is explicitly designed as the missing integration layer across these gaps.

## Gap 1: Real-Time Voice Conversation

Article need:

- Phone-call-quality conversation with the coding agent.
- Continuous or near-continuous dialogue.
- Interruption and course correction.
- Mobile availability.
- Real codebase context while speaking.

Jarvis response:

- Cloud realtime voice primary through Gemini OAuth if feasible.
- Local `faster-whisper` GPU fallback.
- Original cinematic local TTS fallback.
- Click-to-arm UX with live transcript preview.
- Risk-based confirmation before tool execution.
- Private-network iPhone PWA.
- ACP-style session context shared between voice, HUD, CLI, and agents.

Production acceptance:

- Voice can create a session turn from the iPhone PWA.
- Voice can inspect current project/session context before responding.
- Voice can be interrupted or corrected.
- Risky spoken actions produce approval prompts.
- Voice mode visibly indicates cloud or local mode.

## Gap 2: Memory Systems

Article need:

- Working memory for active tasks.
- Long-term project memory.
- Meta memory for recurring patterns and preferences.
- Episodic memory for session continuity.
- Reduced handoff lottery and fewer repeated explanations.

Jarvis response:

- SQLite/WAL append-only event store as canonical runtime memory.
- FTS projections for recall.
- JSONL exports for audit/replay.
- Markdown handoffs for human review.
- Obsidian vault for planning memory and durable spec navigation.
- Future memory promotion through governed knowledge-graph flow.

Production acceptance:

- A new session can resume from event-store facts, not only chat history.
- Search can find past decisions, bugs, approvals, and implementation reasons.
- Session handoffs cite event sequence ranges.
- Agents can retrieve relevant project memory without reloading every file.
- Rejected ideas and failed attempts remain discoverable.

## Gap 3: Tools And MCPs

Article need:

- Tool access is increasingly solved, but tools need memory and conversation to become useful.
- The remaining issue is governed integration, not raw tool inventory.
- Spending/money and high-risk automation need explicit limits.

Jarvis response:

- Runtime-owned tool execution.
- ACP-style tool and terminal events.
- Policy profiles for Observe, Dev Loop, Swarm, and High-Risk Runtime.
- Hardline blocks for destructive, secret, money, public exposure, and high-risk runtime actions.
- Codeburn usage telemetry.
- AG/Codex role split and dynamic adversarial swarms.
- Existing project-local governance stays intact.

Production acceptance:

- UI clients cannot execute tools directly.
- Tool calls are logged as events.
- High-risk tools require approval.
- Codeburn usage appears in the HUD and readiness notes.
- MCP/plugin lifecycle changes remain explicitly gated.

## Gap 4: Mobile Creative Flow

The article emphasizes the practical desk-bound limitation: inspiration happens while walking, driving, swimming, or away from the full workstation.

Jarvis response:

- Private-network iPhone PWA for v1.
- Native iOS remains future scope.
- Mobile voice, chat, approvals, session status, and lightweight HUD.
- Runtime remains local to the user's machine.

Production acceptance:

- iPhone can connect over private VPN.
- User can talk through an idea and have it become a structured session.
- Jarvis can create notes, tickets, or implementation plans without executing risky actions.
- The same session is visible on desktop later.

## Design Implication

The harness is not just a prettier terminal. It is the integration layer that binds:

- conversational voice,
- durable memory,
- governed tools,
- mobile access,
- autonomous loops,
- and reviewable execution.

Any implementation phase that does not strengthen at least one of those bridges should be deprioritized.


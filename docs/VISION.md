# Vision

The article prompt is useful because it frames three gaps in today's coding agents:

1. **Real-time collaboration**: agents need a natural conversational layer, not only typed prompts.
2. **Persistent memory**: agents need durable project continuity across runs, not only context windows.
3. **Tool execution**: agents need controlled access to real tools, with approval boundaries.

Jarvis Codex builds those as separate layers rather than one monolithic assistant.

## Product Shape

Jarvis Codex is a local companion for Codex:

- It listens for an idea or task.
- It records the task as an episode.
- It updates durable memory when the user says something worth preserving.
- It produces a concise handoff that Codex can execute.
- It tracks approvals for risky actions.

## Non-Goals

- Exact cloning of the fictional JARVIS voice.
- Replacing Codex.
- Autonomous destructive actions.
- Cloud-first memory storage.
- Hidden background execution.

## Initial Architecture

```text
voice/text input
  -> episode capture
  -> memory extraction
  -> approval ledger
  -> Codex handoff
  -> optional Codex App Server bridge
```

The filesystem is the first state machine. Each episode, memory record, approval request, and handoff is a readable file. This keeps the system debuggable and easy to hand to agents.


# Continuity Model

Jarvis continuity means a session can resume across time, clients, and agents without lottery-style handoffs.

## Continuity Surfaces

- Runtime event store.
- Session projections.
- Obsidian planning vault.
- Markdown handoffs.
- JSONL exports.
- AG challenge logs.
- Codeburn usage snapshots.
- Commit history.

## Handoff Elimination Strategy

Manual handoffs are not removed immediately. They become projections.

Instead of relying on one pasted Markdown file, a new session should receive:

- active objective,
- recent event sequence,
- relevant decisions,
- changed files,
- open risks,
- tests run,
- rejected paths,
- pending approvals,
- next phase.

The Markdown handoff is a readable summary generated from those facts.

## Cross-Client Resume

Desktop and mobile clients resume the same session by session ID.

The runtime should provide:

- current state,
- recent messages,
- active panes,
- current voice state,
- pending approvals,
- next recommended action.

## Cross-Agent Resume

Codex, Antigravity, and future agents should receive role-specific context slices.

Examples:

- Codex executor receives files, tests, plan, and constraints.
- AG reviewer receives architecture and risk context.
- Codeburn pane receives session/project context for usage reporting.

## Acceptance Criteria

- iPhone-created idea appears on desktop session.
- Desktop implementation phase references the original voice idea.
- A new Codex session can resume from event-store projection.
- AG adversary can review without requiring all chat history.


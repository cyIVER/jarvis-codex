# Event Store And Projections

Jarvis uses SQLite/WAL as the canonical production runtime database.

The runtime is event-sourced: durable facts are append-only events, and current views are projections.

## Canonical Store

Use SQLite with:

- WAL enabled.
- Append-only event table.
- Monotonic event sequence.
- Session, pane, job, approval, voice, tool, git, swarm, and telemetry event types.
- FTS5 projection tables for session search, transcript search, command search, and handoff search.

JSONL and Markdown are exports or projections, not the primary runtime database.

## Event Categories

Required categories:

- `session.*`
- `prompt.*`
- `message.*`
- `tool.*`
- `pty.*`
- `approval.*`
- `voice.*`
- `job.*`
- `swarm.*`
- `loop.*`
- `git.*`
- `policy.*`
- `codeburn.*`
- `system.*`

Each event should include:

- Event ID.
- Sequence number.
- Session ID.
- Actor ID.
- Source client.
- Event type.
- Payload JSON.
- Created timestamp.
- Correlation ID.
- Parent event ID when applicable.

## Projections

Build projections for:

- Current session state.
- HUD status cards.
- Active panes.
- Pending approvals.
- Recent events.
- Search index.
- Markdown handoffs.
- JSONL audit exports.
- Readiness and release reports.

Projections must be rebuildable from the canonical event table.

## Accuracy And Performance

SQLite gives fast local queries and FTS search. Append-only event discipline gives audit accuracy and replay.

Rules:

- Do not update historical events.
- Corrections are new events.
- Rebuild projections from events when schemas change.
- Export JSONL for audit and agent handoff compatibility.
- Export Markdown for human review.

## Migration Policy

- Migrations must be deterministic and tested.
- Runtime startup may create the database only in the configured state directory.
- No migration should touch repo-tracked files.
- Destructive migrations require explicit approval and backup.

## Acceptance Criteria

- A new runtime can bootstrap an empty database.
- Events append without rewriting historical rows.
- Session search works through FTS.
- Current HUD state can be rebuilt from events.
- JSONL and Markdown exports match event-store facts.


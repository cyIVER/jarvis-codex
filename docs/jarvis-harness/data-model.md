# Data Model

The data model is event-first. Tables that describe current state are projections from append-only events.

## Core Tables

### `events`

Canonical append-only table.

Required columns:

- `id`
- `sequence`
- `session_id`
- `actor_id`
- `source_client`
- `event_type`
- `payload_json`
- `correlation_id`
- `parent_event_id`
- `created_at`

### `sessions`

Projection of current session metadata.

Required fields:

- `id`
- `title`
- `profile_id`
- `source_client`
- `parent_session_id`
- `model_route`
- `status`
- `created_at`
- `updated_at`
- `archived_at`

### `panes`

Projection of active and historical PTY panes.

Required fields:

- `id`
- `session_id`
- `role`
- `command_label`
- `cwd`
- `policy_profile`
- `status`
- `created_at`
- `ended_at`

### `approvals`

Projection of pending and completed approval requests.

Required fields:

- `id`
- `session_id`
- `summary`
- `operation`
- `risk`
- `status`
- `scope_json`
- `created_at`
- `decided_at`

### `jobs`

Projection of background jobs and loop steps.

Required fields:

- `id`
- `session_id`
- `kind`
- `status`
- `owner_role`
- `started_at`
- `ended_at`
- `last_event_sequence`

## FTS Projections

Create FTS tables for:

- Session messages.
- Transcript text.
- PTY command and output snippets.
- Handoff Markdown.
- Approval summaries.
- Review findings.

FTS tables are projections and can be rebuilt.

## Export Projections

Keep compatibility exports:

- JSONL event export per session.
- Markdown handoff per session or phase.
- Compact readiness report.
- Codeburn usage snapshot.

Exports should include the event sequence range they were generated from.

## Retention

Default retention:

- Keep canonical events indefinitely unless explicitly archived.
- Allow projection rebuild.
- Allow old PTY output chunk compression after export.
- Never delete approval decisions without explicit maintenance command.

## Acceptance Criteria

- Current state can be rebuilt from `events`.
- Search returns relevant sessions and transcripts.
- JSONL export can replay event order.
- Markdown handoff cites event sequence range.


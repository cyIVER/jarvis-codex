# Memory Architecture

Jarvis memory is layered so agents can resume work without re-explaining context.

## Memory Layers

### Working Memory

Scope: active session.

Contains:

- Current objective.
- Active prompts and responses.
- Open panes.
- Pending approvals.
- Current files and tests.
- Current phase state.

Stored as:

- Canonical event-store events.
- Current-session projections.

### Project Memory

Scope: repository and product.

Contains:

- Architecture decisions.
- Runtime gates.
- Testing workflows.
- Deployment and validation patterns.
- Known constraints.
- Rejected approaches.

Stored as:

- Event-store projections.
- Obsidian vault notes.
- Markdown docs.
- JSONL exports.

### Meta Memory

Scope: cross-session and cross-project patterns.

Contains:

- User preferences.
- Agent routing patterns.
- Repeated failure modes.
- Tool usage patterns.
- Product principles.

Stored as:

- Governed memory promotion queue.
- Knowledge graph memory after review.
- Vault notes when project-local.

### Episodic Memory

Scope: historical development timeline.

Contains:

- Session starts and stops.
- What was changed.
- Why choices were made.
- Tests run.
- Commits and pushes.
- AG challenge findings.
- Codeburn snapshots.

Stored as:

- Append-only event store.
- Session JSONL export.
- Markdown handoff.
- Morning and phase reports.

## Retrieval Policy

Jarvis should retrieve memory by:

- Session recency.
- Project relevance.
- File/module overlap.
- Decision tags.
- Risk category.
- User preference.
- Failed/rejected idea similarity.

## Memory Safety

- Do not store secrets as memory.
- Store credential locations only when safe and user-approved.
- Durable global memory promotion remains reviewed.
- Project-local memory stays scoped to the repo.
- Memory writes must be traceable to event sequences.

## Acceptance Criteria

- A new session can answer what happened in the previous phase.
- A reviewer can find why a risky decision was accepted.
- Repeated failed approaches can be detected.
- Memory retrieval reduces context reload rather than increasing noise.


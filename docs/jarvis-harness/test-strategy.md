# Test Strategy

Jarvis harness testing must prove both capability and restraint.

## Test Layers

Unit tests:

- Event store append/replay.
- Projection rebuild.
- Protocol frame validation.
- Policy classification.
- Approval state transitions.
- Command blocklist.

Integration tests:

- Runtime WebSocket session lifecycle.
- PTY create/input/resize/kill with a harmless shell command.
- Electron client connection against test runtime.
- PWA client connection against test runtime.
- Voice adapter with mocked providers.
- Codeburn stats parsing.

Browser tests:

- Ten mode navigation.
- Terminal pane layout.
- Voice button permission flow.
- Approval prompt rendering.
- Mobile viewport HUD.

Safety tests:

- Destructive commands are blocked.
- Public tunnel commands require approval.
- Cloud realtime voice cannot activate without approved auth.
- UI displayed commands are not executed by the browser.
- Mobile client cannot bypass policy.

Regression tests:

- Existing `jarvis-codex` CLI tests.
- Phase 1 governance validator.
- Plan-viewer tests until the new HUD replaces it.

## Required Phase Gates

Every implementation phase must run:

- Targeted tests for changed modules.
- Governance validator if `.codex` or `.agents` governance files change.
- `git status --short`.
- Codeburn usage snapshot.

Before push:

- Required targeted tests pass.
- Diff is scoped.
- AG or adversary review passes for high-risk phases.
- Readiness note is produced.

## Fixtures

Use temporary directories for:

- Runtime state.
- SQLite databases.
- PTY working directories.
- Voice audio fixtures.
- Export outputs.

Do not write tests against default repo state.

## Acceptance Criteria

- Tests catch policy bypasses.
- Tests prove UI clients do not execute commands directly.
- Tests prove event projections can rebuild after deletion.
- Tests prove mobile/PWA routes do not expose public interfaces by default.


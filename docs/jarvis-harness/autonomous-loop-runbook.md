# Autonomous Loop Runbook

This runbook defines how Jarvis should operate during long autonomous build sessions.

## Loop Contract

The loop objective is to make production progress while preserving reviewability.

Each loop cycle:

1. Inspect current state.
2. Select the next smallest shippable phase.
3. Record assumptions and risk.
4. Use AG for read-only challenge when the phase is architectural, broad, or risky.
5. Implement the slice.
6. Run targeted tests.
7. Capture Codeburn usage.
8. Commit coherent files.
9. Push to main when phase policy allows.
10. Monitor status.
11. Write readiness notes.
12. Continue.

## Stop Conditions

Stop and ask for human direction when:

- Secret handling is required.
- Billing or paid API setup is required.
- Public exposure is required.
- Destructive git/filesystem action is required.
- A test failure repeats after reasonable repair attempts.
- AG and Codex disagree on a safety-critical interpretation.
- Native iOS signing or Apple Developer credentials are required.

## Codeburn Monitoring

At minimum capture:

- Before phase: `codeburn status` and `codeburn today`.
- After phase: `codeburn status`.
- In readiness note: cost, calls, project bucket, and any unusual usage pattern.

Codeburn telemetry informs budget and loop pacing. It does not approve actions.

## AG Challenge Reviews

Use Antigravity for:

- Architecture challenge.
- Broad spec review.
- Risk review before high-impact implementation.
- Adversarial review before commit/push for risky phases.

AG output is advisory. Codex remains responsible for edits, validation, and final integration.

## Phase Commit Rule

Commit only coherent phase groups.

Do not stage:

- Backup/reference patches unless explicitly requested.
- Unrelated held-out work.
- Generated caches.
- Secrets.
- Runtime state.

## Readiness Note Shape

Each phase readiness note should include:

- Phase name.
- Files changed.
- Validation run.
- Codeburn snapshot.
- AG review summary when used.
- Risks.
- Next phase.

## Acceptance Criteria

- A future agent can resume from the event store and readiness notes.
- Each phase can be reverted independently.
- Usage and validation are visible at every boundary.
- The loop never treats generated plans as execution authority without policy approval.


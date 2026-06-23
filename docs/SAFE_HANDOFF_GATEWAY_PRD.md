# Safe Handoff Gateway PRD

## Problem

The plan viewer can produce planning queues and displayed command proposals, but Jarvis Codex intentionally does not execute those commands. The next product risk is ambiguity: a queue file or displayed command could be mistaken for permission to act.

The safe handoff gateway should convert planning state into explicit, reviewable handoff briefs without running commands.

## Personas

- **Local operator:** wants fast movement from idea to checked handoff while preserving control over side effects.
- **Main Codex coordinator:** needs a deterministic artifact that separates proposed commands from execution authority.
- **Specialist agent:** needs clear preconditions, allowed reads, disallowed actions, and expected verification before doing any future work.

## Goals

- Read current planning queue state and selected next steps.
- Generate a structured handoff brief with preconditions, side effects, approval boundaries, verification, and rollback or inspection notes.
- Mark every command as proposed, not executed.
- Preserve `execution_authority: false` unless a future explicitly approved workflow changes it.
- Make the artifact usable by humans and agents without requiring hidden context.

## Non-Goals

- No command execution.
- No shell gateway.
- No Worktrunk mutation.
- No git mutation.
- No service launch, Docker launch, local ML execution, install, or migration.
- No automatic conversion from approval request to command execution.
- No background daemon.

## Functional Requirements

1. The gateway must accept a state directory and read `state/next-steps/queue.json` if present.
2. Missing, invalid, or empty queue state must produce a clear no-op result, not an exception.
3. The gateway must preserve and display `execution_authority: false`.
4. The generated handoff must include:
   - source state path
   - selected step ids
   - proposed commands or checks, if any
   - preconditions
   - expected writes and side effects
   - approval required before execution
   - verification after approval
   - rollback or inspection notes
5. The gateway must write nothing by default unless a future `--write` flag is explicitly approved and tested.
6. Any future write mode must write only to a documented state or handoff path.

## User Stories

### Story 1: Review Planning Queue

As the local operator, I want a command that summarizes the approved planning queue so I can decide whether the next action is ready for execution approval.

Acceptance:

- Given no queue file, output says no planning queue is available.
- Given invalid queue JSON, output says the queue is unreadable and suggests reselecting next steps.
- Given a valid queue, output lists selected step ids and states that the queue is not execution authority.

### Story 2: Generate Handoff Brief

As the main Codex coordinator, I want a structured handoff brief so a future worker can see exactly what is proposed and what is forbidden.

Acceptance:

- Output includes approval boundaries and verification.
- Output does not execute commands.
- Output can be copied into an approval request without additional context.

### Story 3: Prevent Accidental Runner Semantics

As a specialist agent, I want the handoff gateway to make it impossible to confuse a displayed command with a command that has already been approved.

Acceptance:

- Output uses labels such as `proposed command`, `approval required`, and `not executed`.
- Tests assert no `subprocess.run`, shell execution helper, Worktrunk command, or git mutation path exists in the gateway module.

## Data Contract

Input queue shape:

```json
{
  "id": "queue_...",
  "selected": ["hardware-runtime-gate"],
  "brief": "# Proceed",
  "approved_at": 1782170000,
  "source": "plan_viewer",
  "execution_authority": false,
  "purpose": "planning"
}
```

Output brief shape:

```markdown
# Safe CLI Handoff

Source:
Selected steps:
Execution authority: false
Proposed commands:
Preconditions:
Expected side effects:
Approval required:
Verification:
Rollback or inspection:
```

## Risks And Anti-Patterns

- **Anti-pattern:** adding a `--run` flag before the handoff format is proven.
- **Anti-pattern:** treating `approved_at` in a planning queue as execution approval.
- **Anti-pattern:** hiding multiple unrelated command proposals in one approval item.
- **Risk:** users may want speed and pressure the design toward a runner too early.
- **Risk:** future agents may parse markdown loosely unless the data contract stays explicit.

## Success Metrics

- A valid queue can be converted into a handoff without mutating repo or runtime state.
- Empty and invalid queues produce actionable no-op output.
- Tests prove the gateway has no command execution path.
- The operator can approve or reject each proposed command independently.

## Proposed First Implementation Slice

1. Add a pure Python module that reads queue state and returns a structured handoff object. Implemented as `jarvis_codex.safe_handoff`.
2. Add CLI read-only command. Implemented as `jarvis-codex handoff --queue-summary` with optional `--json`.
3. Add tests for missing queue, invalid queue, valid queue, no write default, and no execution helpers. Implemented in `tests/test_safe_handoff.py`.
4. Keep command execution out of scope until a separate runner PRD is approved.

## Open Decisions

- Should the first UI surface be CLI output, plan-viewer copy button, or both?
- Should handoff output be Markdown only, JSON only, or both?
- Should any write mode exist, or should callers pipe stdout into existing approval workflows?
- Which selected step ids map to known command templates, and which should remain free-form?

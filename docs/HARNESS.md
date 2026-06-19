# Harness

Jarvis Codex separates surfaces by risk.

## Locked

- Approval policy
- Memory schema
- Handoff schema
- Safety rules

Agents may propose changes to locked surfaces, but promotion requires review.

## Editable

- Episode text
- Draft handoffs
- UI/client code
- Speech adapters
- Codex App Server bridge code

## Append-Only

- Episode log
- Memory log
- Approval log
- Run log

## Human-Controlled

- Running Codex against a repository
- Creating worktrees
- Commits and pushes
- PR creation or merge
- Credential changes
- Purchases or deployments

## First Quality Gate

A handoff is acceptable when it contains:

- Objective
- Current context
- Recent episode summary
- Relevant memory records
- Approval requirements
- Explicit next action


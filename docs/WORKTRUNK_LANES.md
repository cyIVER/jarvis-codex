# Worktrunk Lane Reconciliation

This is a read-only lane inventory. `git worktree list` is the execution truth.

## Current Registered Worktrees

| Worktree | Branch | Status |
| --- | --- | --- |
| `/home/iveri/repos/jarvis-codex` | `main` | Current registered worktree |

## Stale Lane Notes

Previous planning docs referenced sibling lane worktrees for `lane/codex-bridge`, `lane/memory-state`, `lane/verification-eval`, `lane/visual-plan-ui`, and `lane/voice-ingress`.

Those entries are planning history only until a fresh read-only reconciliation proves they exist in current Git worktree metadata.

## Read-only Lane Planning Policy

Use `jarvis_worktrunk_planner` and `worktrunk-lane-governance` only for read-only lane planning and approval-gated command proposals.

Do not treat displayed lane commands, plan-viewer commands, or historical lane notes as execution authority.

## Approval-Gated Actions

Ask before any of these:

- `wt`
- `git checkout`
- `git reset`
- `git clean`
- `git merge`
- `git rebase`
- `git push`
- `git worktree add`
- `git worktree remove`
- branch deletion
- worktree removal
- Worktrunk shell integration
- hook edits
- agent launch from a worktree

## Worker Contract

```yaml
role:
lane:
branch:
worktree_path:
base_commit:
task_summary:
files_inspected:
files_changed:
commands_run:
verification_performed:
findings:
integration_notes:
risks_or_blockers:
merge_recommendation: merge | hold | abandon | needs-human-decision
next_action:
```

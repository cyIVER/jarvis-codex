# Worktrunk Lane Reconciliation

This is a read-only Gate 2 inventory. No lanes were refreshed, rebased, merged, pushed, removed, or deleted.

## Current Worktrees

| Worktree | Branch | Observed state | Recommendation |
| --- | --- | --- | --- |
| `/home/iveri/repos/jarvis-codex.lane-codex-bridge` | `lane/codex-bridge` | Untracked `video/` | Hold. Inspect `video/` before deciding whether to preserve or discard. |
| `/home/iveri/repos/jarvis-codex.lane-memory-state` | `lane/memory-state` | Untracked `docs/LOCAL_ML_RUNTIME.md` | Hold. Compare against `docs/RUNTIME_GATES.md` before merging or discarding. |
| `/home/iveri/repos/jarvis-codex.lane-verification-eval` | `lane/verification-eval` | Clean | Candidate for refresh from `main` after approval. |
| `/home/iveri/repos/jarvis-codex.lane-visual-plan-ui` | `lane/visual-plan-ui` | Modified `README.md`; untracked `docs/PLAN_VIEWER.md`, `scripts/`, `tools/` | Needs human decision. Likely stale because packaged `jarvis-plan-viewer` now owns the viewer path on `main`. |
| `/home/iveri/repos/jarvis-codex.lane-voice-ingress` | `lane/voice-ingress` | Clean | Candidate to abandon or refresh after confirming no unique voice-ingress work remains. |

## Approval-Gated Actions

Ask before any of these:

- `git push`
- lane merge or rebase
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

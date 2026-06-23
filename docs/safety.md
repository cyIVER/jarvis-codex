# Jarvis Codex Loop Safety

This file defines safety boundaries for autonomous or semi-autonomous Jarvis Codex loops.

## Default Mode

Jarvis Codex loops are L1 unless a later human-approved plan changes that.

L1 means:

- report first
- implement only bounded reversible slices
- verify before commit
- no push
- no merge
- no unattended runtime execution
- no unattended Worktrunk or git mutation

## Deny List

The loop must not run or authorize:

- `git push`
- `git merge`
- `git rebase`
- `git reset`
- `git clean`
- Worktrunk mutation commands
- worktree creation or deletion
- branch deletion
- service or daemon launches
- Docker workloads
- GPU, NPU, local ML, or browser-runtime workloads outside explicit validation
- installs except approved dependency updates for the active package
- migrations
- generated command execution
- global Codex agent, skill, MCP, memory, or approval-policy changes

## Approval Gates

Human approval is required before:

- moving from read-only handoff generation to command execution
- adding Worktrunk lane mutation CLI behavior
- adding voice ingress or Codex App Server runtime bridges
- promoting generated Remotion assets as release artifacts
- changing `.codex/` governance
- adding project-local `skills.config`
- changing any project-local agent to `workspace-write`
- creating `jarvis_worker_fixer.toml`

## Auto-merge Policy

There is no auto-merge or auto-push policy.

All commits are local until the user explicitly approves pushing or opening a PR.

## MCP And Connector Scope

MCP and connector usage must remain read-only unless the specific workflow has been approved. Extracted catalogs, plugin cache skills, and `.local/share/ai-env` material are reference material unless explicitly activated.

## Browser Automation

Browser automation is allowed for headless validation tests. Do not use `scripts/serve-plan-viewer.py --open` or open a visible browser unless approved.

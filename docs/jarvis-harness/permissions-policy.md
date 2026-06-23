# Permissions And Policy Profiles

Jarvis uses policy profiles to decide what the runtime may execute without interrupting the user.

## Profiles

V1 ships four profiles.

### Observe

Allowed:

- Read-only inspection.
- Status checks.
- Search.
- Documentation review.
- Session replay.

Blocked or approval-required:

- File edits.
- Git mutation.
- Runtime launches.
- Installs.
- Network exposure.
- External payments or API setup.

### Dev Loop

Allowed after plan approval:

- Scoped code edits.
- Targeted tests.
- Local non-service commands.
- Coherent commits.
- Push to main after validation if phase policy allows it.

Approval-required:

- Broad refactors.
- Destructive commands.
- Secret changes.
- Service launches.
- Public exposure.
- New paid API usage.

### Swarm

Allowed:

- Dynamic worker/adversary panes.
- Worktree proposals.
- Parallel read/review lanes.
- Worktree writes only when approved by risk policy.

Approval-required:

- Worktree creation/removal.
- Merges/rebases.
- Branch deletion.
- Hook changes.
- Agent launch from a worktree if not already covered by the phase plan.

### High-Risk Runtime

Allowed only with explicit confirmation:

- Docker.
- GPU workloads.
- Local ML model execution.
- Long-running services.
- Daemons.
- Public tunnels.
- Cloud realtime voice.
- Expensive or billable actions.

## Hardline Blocks

Always block until a human explicitly overrides in a specific context:

- `git reset --hard`
- `git clean`
- destructive filesystem deletion outside approved scratch paths
- credential exfiltration
- secret file creation
- public tunnel exposure
- production deploy
- payment or billing setup
- commands that hide destructive git or Worktrunk mutation

## Approval Events

Approval prompts must include:

- Action summary.
- Command or operation.
- Working directory.
- Files or resources affected.
- Expected writes.
- Rollback or cleanup notes.
- Policy profile.
- Expiration or one-shot scope.

## Acceptance Criteria

- Runtime classifies commands before execution.
- HUD shows current profile.
- High-risk actions create approval events.
- Approval of one action does not grant broad permanent authority.
- Policy decisions are persisted in the event store.


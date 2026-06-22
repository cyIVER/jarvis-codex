# Context Routing

Jarvis Codex work should stay within a small, explicit context budget even when the local Codex environment exposes many skills.

## Routing Rules

1. Read `~/.codex/packs/catalog.yaml` first.
2. Choose the narrowest matching pack by trigger and purpose.
3. Load only that pack manifest and any directly relevant companion manifests.
4. Load only skill bodies needed for the current step.
5. Load one-level references only when the skill entrypoint says they are required for the current action.
6. Keep long tool outputs out of the main thread unless they are needed for active debugging.
7. Use Worktrunk lane summaries as the coordinator context boundary.

## Project-local Jarvis Routing

Use the main thread for intake, approvals, final integration, and verification.

Use project-local agents only for read-only Jarvis governance work:

| Need | Project-local agent |
| --- | --- |
| Repo map, state inventory, governance surface discovery | `jarvis_explorer` |
| Correctness, security, gate, or missing-test review | `jarvis_reviewer` |
| Local docs and Codex/Jarvis reference synthesis | `jarvis_docs_researcher` |
| Worktrunk lane planning without mutation | `jarvis_worktrunk_planner` |

Use repo-local skills for Jarvis-specific governance tasks before falling back to broad global skills.

Global agents remain available for broader pack-scoped work, but they should not replace project-local Jarvis governance routing when the task is about this repo.

There is no `jarvis_worker_fixer` agent yet. Implementation remains main-thread and approval-gated.

Project-local `skills.config` scoping is deferred until trial runs show repeated routing noise and the exact entries are approved.

## Active Route For The Swarm

- Primary pack: `agent-engineering`
- Focused companion packs: `visual-planning`, `worktrunk-worktrees`, `context-engineering`
- Context-engineering concrete skills: `context-optimization`, `context-mode`, `context-compression`, `memory-systems`, `evaluation`

The `context-engineering` pack manifest is present at `~/.codex/packs/context-engineering.yaml`. In this environment there is no standalone `~/.codex/skills/context-engineering/SKILL.md`; future agents should use the concrete skill paths referenced by the pack manifest.

## Budget Policy

- Prefer retrieval scoping and selective file reads over broad directory loading.
- Mask or summarize resolved verbose outputs after their key facts have been captured.
- Preserve file paths, branch names, commands run, decisions, risks, and verification results verbatim in summaries.
- Use context partitioning only when the task has independent workstreams; this swarm qualifies because the five lanes own distinct branches and worktrees.
- Treat Context Mode as a governed optional runtime. Do not install hooks, register MCP servers, or create session databases without explicit approval.

## Worker Summary Contract

Each lane worker must return:

- lane name
- branch and worktree path
- task summary
- files inspected
- files changed
- verification performed
- findings
- risks or blockers
- merge recommendation

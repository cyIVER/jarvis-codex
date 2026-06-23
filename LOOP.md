# Jarvis Codex Autonomous Workflow

This repository uses a Loop Engineering L1 workflow: report first, implement only bounded reversible slices, verify before commit, and keep runtime or git mutation behind explicit human approval.

## Active Loop

### Product Readiness Triage (L1 report plus bounded implementation)

- Cadence: manual or operator-requested; do not run on an unattended timer yet.
- Pattern: `daily-triage`, narrowed to Jarvis Codex product readiness.
- State: `STATE.md`.
- Run log: `loop-run-log.md`.
- Budget: `loop-budget.md`.
- Primary backlog: `docs/PRODUCT_READINESS.md`.
- Local verifier: `jarvis-codex loop verify --json`.
- PM workflow: `pm-command-library` for discovery, PRD, prioritization, and roadmap decisions.
- Challenge lane: `gemini-integration` through Antigravity for read-only second-pass review when the next slice is ambiguous or high impact.
- Maker/checker split: main thread implements bounded slices; `jarvis_reviewer`, project tests, and validators act as checker gates.

## Loop Cycle

1. Inspect `STATE.md`, `docs/PRODUCT_READINESS.md`, and `git status --short --branch`.
2. Select the highest-value reversible slice from the current backlog.
3. Define acceptance criteria before editing.
4. Implement the smallest useful package.
5. Run targeted tests first, then full validation when the package changes shared behavior.
6. Commit with exact-path staging after validation passes.
7. Append a short run-log entry and update state when the loop outcome changes.
8. Stop or escalate if the next action requires a denied capability or unclear product decision.

## Safety Gates

The loop must not perform these actions without explicit approval for the exact action:

- `git push`, `git merge`, `git rebase`, `git reset`, `git clean`, or destructive git commands
- Worktrunk mutation, worktree creation, worktree deletion, or branch deletion
- installs outside approved dependency changes
- migrations
- service, daemon, Docker, GPU, local ML, or runtime workflow launch
- browser launch through `--open`
- global Codex agent, skill, MCP, or memory-policy changes
- changing any Jarvis project-local agent to `workspace-write`
- creating `jarvis_worker_fixer.toml`
- adding project-local `skills.config`

## Allowed Autonomous Actions

The loop may do these without a separate prompt when they are directly tied to the active slice:

- read repo files and local docs
- run static validators and tests
- add or update tests, docs, and package code for bounded slices
- run `uv run pytest`
- run `python3 scripts/validate-jarvis-codex-phase1.py`
- run `uv run jarvis-codex loop verify --json`
- run Remotion typecheck/audit in `video/remotion`
- run the global architecture validator after Codex governance, pack, agent, workflow, or architecture documentation changes
- create commits with exact-path staging for validated, scoped packages

## Kill Switch

Pause the loop immediately when any of these are true:

- `STATE.md` says `loop_status: paused`.
- Validation fails three times for the same cause.
- A package needs broad dependency, runtime, or workflow activation.
- The next step would weaken an approval boundary.
- The user asks to stop.

## Current Level

Target level: L1.

This loop is not L2 or L3. It does not auto-merge, auto-push, mutate Worktrunk state, run services, or execute generated commands.

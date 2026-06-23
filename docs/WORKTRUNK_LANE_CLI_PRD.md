# Worktrunk Lane CLI PRD

## Problem

Jarvis Codex has read-only lane scoring in `src/jarvis_codex/lanes.py`, but the user-facing CLI does not expose it yet. The current workaround is to inspect worktrees manually or through the plan viewer. That keeps mutation safe, but it makes lane review less repeatable and leaves future lane commands underspecified.

The product risk is not lack of mutation. The product risk is ambiguity: a future `jarvis-codex lane` command could be mistaken for permission to refresh, abandon, merge, rebase, or delete worktrees.

## Product Goal

Add a future lane CLI surface that makes Worktrunk lane state easier to review while preserving the current approval boundary.

The first implementation must be read-only by default. It must not run `wt`, create or remove worktrees, change branches, merge, rebase, push, delete branches, edit hooks, or launch agents.

## Current Evidence

- `git worktree list` currently reports only `/home/iveri/repos/jarvis-codex  3d1a1e6 [main]`.
- `src/jarvis_codex/lanes.py` provides read-only `score_lane()` and `list_lanes()` helpers.
- `log_lane_decision()` writes planning records to `state/logs/lane_decisions.jsonl`; those records set `mutation_performed: false` and `execution_authority: false`.
- `tests/test_lanes.py` covers read-only status scoring, worktree listing, and planning-record flags.
- `docs/WORKTRUNK_LANES.md` treats `git worktree list` as execution truth and lists mutation commands as approval-gated.

## Users

- Local operator: wants a fast lane inventory before deciding whether to split work, hold a lane, or ask for a mutation plan.
- Main Codex coordinator: needs a structured lane summary for handoffs and plan-viewer context.
- Future specialist agents: need unambiguous lane state and explicit non-authority labels before proposing work.

## Non-goals

- No `wt` execution.
- No `git worktree add` or `git worktree remove`.
- No branch creation, checkout, deletion, merge, rebase, reset, clean, or push.
- No hook edits.
- No Worktrunk shell integration.
- No agent launch from a worktree.
- No automatic conversion from planning records to execution approval.

## Proposed CLI Shape

Future read-only commands:

```bash
jarvis-codex lane list
jarvis-codex lane score --repo <path> --branch <branch>
jarvis-codex lane decision --action hold --branch <branch> --repo <path>
```

`lane list` and `lane score` should print read-only summaries only.

`lane decision` may append a planning record to the configured state directory. That write is local planning state, not Worktrunk or git mutation. The output must include `execution_authority: false`.

Future mutation commands such as `lane refresh`, `lane abandon`, or `lane merge` are intentionally out of scope. If they are ever proposed, they need a separate PRD, exact command semantics, rollback notes, and explicit approval.

## Requirements

1. `lane list` must call only read-only git inspection commands.
2. `lane list` must treat `git worktree list` as execution truth.
3. `lane score` must classify lanes as `ready`, `needs-review`, or `blocked` using read-only status evidence.
4. `lane decision` must write only to `state/logs/lane_decisions.jsonl`.
5. Every lane CLI output must include `mutation_performed: false` and `execution_authority: false` when returning planning records.
6. CLI help must say that lane commands are planning and review commands, not execution authority.
7. `--json` output should be supported for machine-readable handoff and plan-viewer use.
8. The default output should be compact enough for a human to inspect before deciding on next steps.

## User Stories

### Story 1: Review current lanes

As the local operator, I want `jarvis-codex lane list` to show current worktrees and readiness labels so I can decide whether Worktrunk work is needed.

Acceptance:

- Command prints every registered worktree from `git worktree list`.
- Command does not mutate git or Worktrunk state.
- Command handles a single-main-worktree repo without implying stale lanes exist.

### Story 2: Score one lane

As the main Codex coordinator, I want `jarvis-codex lane score --repo <path> --branch <branch>` to summarize readiness so I can include evidence in a handoff.

Acceptance:

- Clean tree returns `ready`.
- Untracked files return `needs-review`.
- Other uncommitted changes return `blocked`.
- Command output includes status evidence and merge recommendation.

### Story 3: Record planning decision

As the local operator, I want `jarvis-codex lane decision --action hold --branch <branch>` to append a planning record without touching Worktrunk or git.

Acceptance:

- Writes only to `state/logs/lane_decisions.jsonl`.
- Record includes `mutation_performed: false`.
- Record includes `execution_authority: false`.
- Record includes base commit, action, lane, decision, evidence, and merge recommendation.

## Anti-patterns

- Adding `lane refresh` before read-only lane review is proven.
- Hiding `git checkout`, `git rebase`, `git worktree remove`, or `wt` behind a friendly command name.
- Treating a planning record as approval to mutate branches or worktrees.
- Bundling multiple lane mutations into one approval item.
- Launching agents from lane commands.

## Validation Plan

Minimum tests before implementation:

- CLI test for `lane list` using monkeypatched `subprocess.run`.
- CLI test for `lane score` for clean, untracked, and dirty states.
- CLI test for `lane decision` writing only under a pytest `tmp_path` state directory.
- Test that no lane CLI path invokes `wt`, `git checkout`, `git merge`, `git rebase`, `git reset`, `git clean`, `git push`, `git worktree add`, or `git worktree remove`.
- Existing `uv run pytest` must pass.
- `python3 scripts/validate-jarvis-codex-phase1.py` must pass.

## Open Decisions

- Whether `lane decision` should be included in the first CLI implementation or remain an internal helper until more operator use exists.
- Whether `lane list` should be human-readable by default with optional `--json`, or JSON-only.
- Whether plan viewer should read `lane_decisions.jsonl` directly or consume CLI JSON later.
- Whether future mutation commands belong in this CLI at all, or should remain manual approval handoffs.

## First Implementation Slice Recommendation

Implement only:

```bash
jarvis-codex lane list --json
jarvis-codex lane score --repo <path> --branch <branch> --json
```

Defer `lane decision` and all mutation verbs until the operator has used read-only lane review enough to prove the output shape is correct.

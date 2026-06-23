# Plan Viewer

Jarvis Codex has two local plan-viewing surfaces:

- The package viewer in `jarvis_codex.plan_viewer`, normally run through the packaged CLI entry point.
- The static viewer tooling in `scripts/serve-plan-viewer.py` and `tools/plan-viewer/`.

Both are local review surfaces. Neither surface turns displayed commands into permission to execute them.

## Package Viewer

The package viewer renders the Jarvis plan files and a local next-step review surface. It can read current repo facts, selected next steps, recent episodes, pending approvals, and recent handoffs.

Package viewer APIs:

- `GET /api/files` lists local plan and reference documents.
- `GET /api/file/<name>` reads an approved local document source.
- `GET /api/current-state` returns local repo and state summaries.
- `GET /api/next-steps` reads selected next-step planning state.
- `POST /api/next-steps` writes selected next-step planning state to `state/next-steps/selection.json`.
- `POST /api/approve-queue` writes approved planning queue state to `state/next-steps/queue.json`.

`state/next-steps/selection.json` is browser selection state. `state/next-steps/queue.json` is planning state. It is not execution authority.

## Durable Queue Boundary

The "Approve Planning Queue" action records the selected planning items and generated brief in local state. It does not authorize command execution, git mutation, Worktrunk mutation, local ML, Docker, services, daemons, runtime workflows, hook edits, browser launches, or any other side-effecting command.

Agents and humans must treat queue entries as handoff context only. Before running any displayed command or mutating action, ask for explicit approval for that exact action.

## Displayed Commands

The viewer may show command strings such as:

```text
git push origin main
git worktree list
uv run jarvis-codex hardware --workload video
uv run jarvis-codex handoff --objective "Review Codex bridge contract"
```

These strings are display-only checks or proposals. The viewer does not execute them. They must not be treated as permission to run git, Worktrunk, local ML, Docker, services, daemons, runtime workflows, or other commands.

## Static Viewer

The static viewer is served by:

```bash
python3 scripts/serve-plan-viewer.py
```

It serves static assets from `tools/plan-viewer/` and reads only `.md` and `.mdx` files from the configured plans directory.

Optional flags:

```bash
python3 scripts/serve-plan-viewer.py --open
python3 scripts/serve-plan-viewer.py --port 8787
python3 scripts/serve-plan-viewer.py --plans plans/jarvis-codex-swarm
```

The `--open` flag belongs only to the static viewer script. It opens the local viewer URL in a browser. Do not use `--open` in automation unless browser launch is explicitly approved.

The static viewer does not publish, call hosted Agent-Native URLs, load external CDN assets, or execute plan content.

## Browser Smoke Validation

`tests/test_static_plan_viewer_browser.py` starts the static viewer handler on a random `127.0.0.1` port with a temporary plans directory and renders it in headless Chromium through Playwright.

The smoke test verifies the page title, active plan selection, rendered headings, rendered fenced code, outline entries, and absence of browser console or page errors. It does not use `--open`, does not execute displayed commands, and shuts down the local test server during teardown.

## Review Scope

The viewers render headings, paragraphs, lists, tables, blockquotes, fenced code, and inline links or code. Mermaid and MDX-specific blocks are treated as readable review content, not as a full MDX runtime.

Generated or runtime state should remain outside Git unless a specific file is intentionally approved for commit.

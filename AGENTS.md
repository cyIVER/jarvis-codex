# Jarvis Codex Agent Instructions

- If a required or clearly project-appropriate tool is missing, ask the user whether to install it instead of silently skipping that verification or workflow.

## Jarvis Project-local Codex Governance

- Phase 1 project-local governance is active under `.codex/` and `.agents/skills/`.
- Project-local agents are read-only: `jarvis_explorer`, `jarvis_reviewer`, `jarvis_docs_researcher`, and `jarvis_worktrunk_planner`.
- Repo-local Jarvis skills are instruction-only governance helpers: `jarvis-gate-stabilization`, `worktrunk-lane-governance`, `approval-handoff-briefing`, `local-state-continuity`, `ipc-orchestration-review`, `safe-cli-handoff`, and `agent-skill-governance`.
- Validate Phase 1 governance manually with `python3 scripts/validate-jarvis-codex-phase1.py`.
- Do not create `jarvis_worker_fixer.toml` without explicit approval.
- Do not change any Jarvis project-local agent to `workspace-write` without explicit approval.
- Do not activate `.local/share/ai-env` catalogs, extracted skills, temp skills, or plugin-cache skills.
- Do not add project-local `skills.config` scoping until trial evidence shows routing noise and the user approves the exact entries.

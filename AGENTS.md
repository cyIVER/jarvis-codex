# Jarvis Codex Agent Instructions

- If a required or clearly project-appropriate tool is missing, ask the user whether to install it instead of silently skipping that verification or workflow.

## Harness Guides (Feedforward)

- Phase 1 project-local governance is active under `.codex/` and `.agents/skills/`.
- Project-local agents are read-only: `jarvis_explorer`, `jarvis_reviewer`, `jarvis_docs_researcher`, and `jarvis_worktrunk_planner`.
- Repo-local Jarvis skills are instruction-only governance helpers: `jarvis-gate-stabilization`, `worktrunk-lane-governance`, `approval-handoff-briefing`, `local-state-continuity`, `ipc-orchestration-review`, `safe-cli-handoff`, `agent-skill-governance`, and `harness-evaluator`.
- Validations must be done automatically through local computational sensors where available. The tracked pre-commit sensor source is `scripts/harness/pre-commit-sensor.sh`; local clones must install it into `.git/hooks/pre-commit` because Git does not version hook files.
- **Progressive Disclosure:** Do not read or include `mic-harness` specific rules unless actively working on the live voice planning sub-project. Refer to `scripts/harness/mic-harness-policy.md`.

## The Ratchet (Explicit Negative Constraints)

*Every failure is a configuration problem. Record permanent constraints here based on past agent mistakes.*

- **[Ratchet 001]** Do not create `jarvis_worker_fixer.toml` without explicit approval.
- **[Ratchet 002]** Do not change any Jarvis project-local agent to `workspace-write` without explicit approval.
- **[Ratchet 003]** Do not activate `.local/share/ai-env` catalogs, extracted skills, temp skills, or plugin-cache skills.
- **[Ratchet 004]** Do not add project-local `skills.config` scoping until trial evidence shows routing noise and the user approves the exact entries.
- **[Ratchet 005]** Do not commit runtime-generated state, audio, database, release-output, or local transcript artifacts; preserve only intentional `.gitkeep` placeholders and source-controlled harness assets.

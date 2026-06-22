# Codex Custom Agent TOML Audit - 2026-06-22

## Source Baseline

Latest Codex manual fetched with the `openai-docs` helper on 2026-06-22:

- Manual: `/tmp/openai-docs-cache/codex-manual.md`
- Outline: `/tmp/openai-docs-cache/codex-manual.outline.md`
- Official sources represented in the manual:
  - `https://developers.openai.com/codex/subagents`
  - `https://developers.openai.com/codex/concepts/subagents`
  - `https://developers.openai.com/codex/config-basic`
  - `https://developers.openai.com/codex/config-reference`

Relevant documented rules:

- Custom agents are standalone TOML files under `~/.codex/agents/` or project `.codex/agents/`.
- Each custom agent file must define `name`, `description`, and `developer_instructions`.
- Optional settings such as `nickname_candidates`, `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and `skills.config` inherit from the parent session when omitted.
- Codex identifies an agent by its `name`; matching filename to name is the simplest convention.
- Subagents inherit current sandbox policy, and parent runtime overrides can supersede custom agent defaults.
- Best custom agents are narrow, opinionated, and have a tool/sandbox surface that matches their job.

## Audit Scope

Audited active custom agent files in:

- `/home/iveri/.codex/agents/*.toml`

Excluded:

- Backup copies under `/home/iveri/.codex/backups/`
- `/home/iveri/.codex/templates/custom-agent-template.toml`

## Summary

- Active agent files audited: 48
- Pack catalog agent references: 48
- Missing active agent files from catalog: 0
- Active agent files not referenced by catalog: 0
- TOML parse failures: 0
- Missing required custom-agent fields: 0
- Filename/name mismatches: 0
- Duplicate agent names: 0
- Invalid `nickname_candidates`: 0
- Agents pinned to `sandbox_mode = "read-only"`: 48

## Findings

### High Priority

1. `pm_engineering_team.toml` references a removed MCP server.

   The agent says: "Use the pm-engineering-team MCP server for catalog intelligence and structured artifacts."

   This conflicts with the current architecture kernel, which says `pm-engineering-team` MCP requirements were removed from active pack routing. It also conflicts with `/home/iveri/.codex/packs/pm-engineering-team.yaml`, which lists `knowledge-graph-memory` as the active MCP server and says to use static extracted PM skills and local artifact generation by default.

   Recommended correction: replace that line with guidance to use the PM delivery skills listed in the pack, local artifact generation, and `knowledge-graph-memory` for durable context.

### Medium Priority

1. Many agents use near-identical generic instructions.

   This is valid TOML and consistent with the pack-first architecture, but it leaves some specialists less "narrow and opinionated" than the current Codex subagent guidance recommends. The strongest files add domain-specific constraints, for example `dfir_cyber`, `flowsint_osint`, `nango_integrations`, `worktrunk_worktrees`, `ai_research_skills`, `context_mode_runtime`, `resume_career`, and `browser_testing`.

2. Implementation-lane agents are read-only by default.

   This is safe and matches the local human-decision gate that sandbox modes should not be changed from read-only to writable without approval. The practical tradeoff is that implementation-oriented agents such as `react_component_implementation`, `plugin_packaging`, `skill_creation`, and `remotion_generation` will need explicit parent assignment and runtime permissions before they can do direct edits.

## One-By-One Results

| Agent file | Status | Audit note |
| --- | --- | --- |
| `accessibility_audit.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic but acceptable for an audit specialist. |
| `agent_engineering.toml` | Pass | Valid schema, catalog-aligned, read-only. Strong local guardrail against legacy memory systems. |
| `ai_research_skills.toml` | Pass | Valid schema, catalog-aligned, read-only. Good explicit install/write boundaries. |
| `api_design.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could be made more API-contract-specific later. |
| `architecture_pattern_routing.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; acceptable because pack likely carries routing detail. |
| `auth_hardening.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add explicit identity/session/token review priorities. |
| `authorized_pentest.toml` | Pass | Valid schema, catalog-aligned, read-only. Scope wording is appropriate for gated pentest planning. |
| `autoresearch.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add source-backed evidence requirements. |
| `browser_harness.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could mention evidence capture expectations. |
| `browser_testing.toml` | Pass | Valid schema, catalog-aligned, read-only. Good domain-specific browser evidence requirements. |
| `career_pipelines.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; acceptable if pack carries career workflow detail. |
| `cloud_security.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add IAM/network/logging priority ordering. |
| `code_topology.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add dependency graph/topology output expectations. |
| `context_engineering.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add context-budget and memory-scope criteria. |
| `context_mode_runtime.toml` | Pass | Valid schema, catalog-aligned, read-only. Good explicit runtime/install/retention boundaries. |
| `data_modeling.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add schema/backward-compatibility priorities. |
| `database_migrations.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add rollback, data safety, and compatibility checklist. |
| `dependency_review.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add supply-chain and lockfile evidence expectations. |
| `design_extraction.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add asset/source provenance expectations. |
| `design_frontend.toml` | Pass | Valid schema, catalog-aligned, read-only. Good visual verification and existing-conventions guidance. |
| `design_systems.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add token/component consistency criteria. |
| `dfir_cyber.toml` | Pass | Valid schema, catalog-aligned, read-only. Strong evidence-handling and verified-capability boundaries. |
| `dfir_triage.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add timeline/IOC/evidence expectations. |
| `flowsint_osint.toml` | Pass | Valid schema, catalog-aligned, read-only. Good lawful-scope and durable-memory restrictions. |
| `knowledge_graph_memory.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add review-queue and promotion criteria. |
| `n8n_workflows.toml` | Pass | Valid schema, catalog-aligned, read-only. Should remain clear that n8n is disabled optional inventory unless approved. |
| `nango_integrations.toml` | Pass | Valid schema, catalog-aligned, read-only. Good account/OAuth/API/credential boundaries. |
| `native_tools.toml` | Pass | Valid schema, catalog-aligned, read-only. Good local-tool and huashu-design guardrails. |
| `notebooklm.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add source/corpus boundary expectations. |
| `obsidian_knowledge.toml` | Pass | Valid schema, catalog-aligned, read-only. Good Obsidian syntax and user-voice preservation guidance. |
| `obsidian_local_knowledge.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could align with `obsidian_knowledge` wording if intended overlap remains. |
| `open_design_runtime.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add daemon/runtime boundary constraints. |
| `playwright_e2e.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add screenshot/trace/viewport artifact expectations. |
| `plugin_packaging.toml` | Pass | Valid schema, catalog-aligned, read-only. Implementation-lane tradeoff: direct edits require explicit parent assignment and permissions. |
| `pm_engineering_team.toml` | Needs update | Valid schema and catalog-aligned, but stale `pm-engineering-team` MCP instruction conflicts with current kernel and pack manifest. |
| `react_component_implementation.toml` | Pass | Valid schema, catalog-aligned, read-only. Implementation-lane tradeoff: direct edits require explicit parent assignment and permissions. |
| `remotion_generation.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add render/build verification expectations. |
| `resume_career.toml` | Pass | Valid schema, catalog-aligned, read-only. Good sensitive-data and no-invention boundaries. |
| `secure_code_review.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add vulnerability/evidence/severity ordering. |
| `sequential_planning.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; acceptable for a reasoning/decomposition specialist. |
| `skill_creation.toml` | Pass | Valid schema, catalog-aligned, read-only. Implementation-lane tradeoff: direct edits require explicit parent assignment and permissions. |
| `skill_ingestion.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add URL/provenance and install-gate requirements. |
| `threat_modeling.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add assets/trust-boundary/abuse-case output structure. |
| `tool_audit.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add provenance, executable boundary, and MCP risk criteria. |
| `ui_polish_review.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add layout/contrast/responsive evidence expectations. |
| `visual_design.toml` | Pass | Valid schema, catalog-aligned, read-only. Generic instructions; could add asset and art-direction output expectations. |
| `visual_planning.toml` | Pass | Valid schema, catalog-aligned, read-only. Good local-first and hosted-sharing approval boundary. |
| `worktrunk_worktrees.toml` | Pass | Valid schema, catalog-aligned, read-only. Good explicit worktree/git side-effect boundaries. |

## Recommended Next Step

Make a focused patch to `pm_engineering_team.toml` first. After that, consider a second pass that improves the generic agents in small domain groups instead of broad mass-editing all 48 files.

## Post-audit Phase 1 Update

After this audit, Phase 1 Jarvis project-local governance was implemented.

Implemented state:

- Project-local config exists at `.codex/config.toml`.
- Four project-local agents exist and remain `sandbox_mode = "read-only"`:
  - `jarvis_explorer`
  - `jarvis_reviewer`
  - `jarvis_docs_researcher`
  - `jarvis_worktrunk_planner`
- Seven repo-local Jarvis governance skills exist under `.agents/skills/`.
- `pm_engineering_team.toml` stale MCP wording was patched to avoid relying on the removed `pm-engineering-team` MCP server.
- Existing global agents remain read-only and otherwise intact.
- `jarvis_worker_fixer.toml` remains deferred and absent.
- Project-local `skills.config` scoping remains deferred.
- The project-local validator passes:

```text
Status: PASS
Checks passed: 156
Warnings: 0
Failures: 0
```

This update records follow-up state without rewriting the original audit findings.

from __future__ import annotations

from pathlib import Path

from jarvis_codex import governance
from jarvis_codex.governance import DEFAULT_REPO, EXPECTED_AGENTS, EXPECTED_SKILLS, validate_phase1_governance


VALID_AGENT_INSTRUCTIONS = """Allowed skills:
- agent-skill-governance
Disallowed skills:
- writable worker skills
Allowed MCP servers:
- none by default
Disallowed MCP servers:
- unrelated MCPs
Allowed tools/actions:
- read-only inspection
Disallowed tools/actions:
- create, edit, delete, move, or rename files
- install packages
- run migrations
- launch services
Return structured output with findings and residual risk.
"""


VALID_SKILL_BODY = """# Purpose

Validate fixture behavior.

# When to use

Use in tests.

# When not to use

Do not use for runtime work.

# Tool expectations

Read-only inspection.

# Workflow

Inspect fixture files.

# Expected output

Structured validation result.

# Guardrails

No writes outside the test fixture.

# Validation

Run targeted tests.
"""


def write_valid_governance_fixture(repo: Path) -> None:
    codex = repo / ".codex"
    agents = codex / "agents"
    skills = repo / ".agents" / "skills"
    agents.mkdir(parents=True)
    skills.mkdir(parents=True)
    (codex / "config.toml").write_text(
        'sandbox_mode = "read-only"\n\n[agents]\nmax_threads = 5\nmax_depth = 1\n',
        encoding="utf-8",
    )

    for agent_file in EXPECTED_AGENTS:
        name = agent_file.removesuffix(".toml")
        (agents / agent_file).write_text(
            f"""name = "{name}"
description = "Test fixture agent."
sandbox_mode = "read-only"
developer_instructions = '''
{VALID_AGENT_INSTRUCTIONS}
'''
""",
            encoding="utf-8",
        )

    for skill in EXPECTED_SKILLS:
        skill_dir = skills / skill
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"""---
name: {skill}
description: Test fixture skill.
---
{VALID_SKILL_BODY}
""",
            encoding="utf-8",
        )


def test_current_governance_validation_returns_structured_pass_result():
    result = validate_phase1_governance()

    assert result.status == "PASS"
    assert result.checks_passed >= 168
    assert result.failure_count == 0

    summary = result.compact_summary()
    assert summary["label"] == "project-local Codex governance"
    assert summary["status"] == "PASS"
    assert summary["checks_passed"] == result.checks_passed
    assert summary["warnings"] == result.warning_count
    assert summary["failures"] == 0
    assert summary["writes_reports"] is False
    assert summary["not_test_replacement"] is True


def test_default_governance_repo_is_portable():
    source = Path(governance.__file__).read_text(encoding="utf-8")

    assert DEFAULT_REPO == Path(__file__).resolve().parents[1]
    assert "/home/iveri/repos/jarvis-codex" not in source


def test_governance_validation_failure_from_temp_fixture(tmp_path):
    repo = tmp_path / "repo"
    write_valid_governance_fixture(repo)
    agent_path = repo / ".codex" / "agents" / "jarvis_explorer.toml"
    agent_path.write_text(agent_path.read_text(encoding="utf-8").replace("read-only", "workspace-write", 1), encoding="utf-8")

    result = validate_phase1_governance(repo)

    assert result.status == "FAIL"
    assert result.failure_count > 0
    assert any("workspace-write" in failure for failure in result.failures)
    assert any("jarvis_worker_fixer.toml is absent" in item for item in result.sections["Agent Checks"].passed)
    assert "failure_details" in result.compact_summary()


def test_governance_validation_writes_no_report_files(tmp_path):
    repo = tmp_path / "repo"
    write_valid_governance_fixture(repo)

    result = validate_phase1_governance(repo)

    assert result.status == "PASS"
    assert not (repo / "reports").exists()
    assert not (repo / ".codex" / "reports").exists()
    assert not list(repo.rglob("*architecture-validation*"))

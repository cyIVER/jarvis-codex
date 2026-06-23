from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_runs_project_validation_without_release_rendering():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "uv run pytest" in workflow
    assert "python3 scripts/validate-jarvis-codex-phase1.py" in workflow
    assert "uv run jarvis-codex loop verify --json" in workflow
    assert "npm run typecheck" in workflow
    assert "npm audit --audit-level=high" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "actions/checkout@v7" in workflow
    assert "actions/setup-python@v6" in workflow
    assert "astral-sh/setup-uv@v8.2.0" in workflow
    assert "actions/setup-node@v6" in workflow
    assert "npm run render" not in workflow
    assert "npm run still" not in workflow
    assert "git push" not in workflow
    assert "git worktree add" not in workflow


def test_pr_template_keeps_runtime_and_artifact_boundaries_visible():
    template = (ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")

    assert "uv run pytest" in template
    assert "validate-jarvis-codex-phase1.py" in template
    assert "No Worktrunk mutation" in template
    assert "Generated Remotion outputs remain local ignored review assets" in template


def test_bug_template_requires_side_effect_disclosure():
    template = (ROOT / ".github/ISSUE_TEMPLATE/bug_report.md").read_text(encoding="utf-8")

    assert "Local validation" in template
    assert "Safety boundary impact" in template
    assert "the exact command and expected writes are listed for approval" in template

from __future__ import annotations

from pathlib import Path

from jarvis_codex.loop_readiness import (
    build_unattended_loop_evidence_brief,
    build_unattended_loop_policy,
    validate_loop_readiness,
)


def write(path: Path, text: str = "ok") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_minimal_loop_repo(root: Path) -> None:
    write(root / "STATE.md", "loop_status: active\nlevel: L1\n")
    write(root / "LOOP.md")
    write(
        root / "loop-budget.md",
        "Default cadence: manual/operator-requested\n"
        "Suggested token cap per loop cycle: 120k\n"
        "## Kill Switches\n"
        "## Escalation Rules\n",
    )
    write(root / "loop-run-log.md")
    write(root / "docs/safety.md")
    write(root / "docs/PRODUCT_READINESS.md")
    write(root / "docs/RELEASE_ARTIFACTS.md", "jarvis-codex release manifest --json\n")
    write(
        root / ".github/workflows/ci.yml",
        "permissions:\n  contents: read\nsteps:\n  - run: uv run pytest\n  - run: python3 scripts/validate-jarvis-codex-phase1.py\n",
    )


def test_loop_readiness_passes_for_minimal_governed_repo(tmp_path):
    write_minimal_loop_repo(tmp_path)

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "PASS"
    assert result["execution_authority"] is False
    assert result["writes_files"] is False
    assert result["failures"] == 0


def test_unattended_loop_policy_is_read_only_and_keeps_release_gate_open(tmp_path):
    write_minimal_loop_repo(tmp_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    policy = build_unattended_loop_policy(tmp_path)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert policy["status"] == "ready-for-human-policy-review"
    assert policy["writes_files"] is False
    assert policy["writes_state"] is False
    assert policy["execution_authority"] is False
    assert policy["arbitrary_command_execution"] is False
    assert policy["service_launch_performed"] is False
    assert policy["daemon_started"] is False
    assert policy["scheduler_backgrounded"] is False
    assert policy["network_probe_performed"] is False
    assert policy["git_mutation_performed"] is False
    assert policy["worktrunk_mutation_performed"] is False
    assert policy["release_gate_closed"] is False
    assert policy["approved_for_unattended_operation"] is False
    assert policy["background_scheduler_implemented"] is False
    assert policy["bounded_foreground_schedule_available"] is True
    assert "unattended_loop_scheduling" in policy["remaining_release_gates"]
    assert "--allow-validation" in policy["bounded_foreground_schedule_command"]
    assert "accepted kill switches" in policy["required_policy_evidence"]
    assert "launch daemons" in policy["unsafe_actions_not_authorized"]
    assert before == after


def test_unattended_loop_policy_reports_readiness_failures(tmp_path):
    policy = build_unattended_loop_policy(tmp_path)

    assert policy["status"] == "needs-readiness-fixes"
    assert policy["readiness_summary"]["status"] == "FAIL"
    assert policy["readiness_summary"]["failures"] > 0
    assert policy["release_gate_closed"] is False


def test_unattended_loop_evidence_brief_is_read_only_and_keeps_gate_open(tmp_path):
    write_minimal_loop_repo(tmp_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    brief = build_unattended_loop_evidence_brief(tmp_path)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert brief["label"] == "Jarvis unattended loop scheduling operator evidence brief"
    assert brief["status"] == "READY_FOR_OPERATOR_REVIEW"
    assert brief["policy_status"] == "ready-for-human-policy-review"
    assert brief["policy_command"] == "jarvis-codex loop unattended-policy --json"
    assert brief["validation_command"] == "jarvis-codex loop verify --json"
    assert "unattended_loop_scheduling" in brief["release_evidence_command"]
    assert "accepted kill switches and manual stop controls" in brief["required_operator_evidence"]
    assert any("do not start daemons" in action for action in brief["unsafe_actions"])
    assert any("do not run arbitrary commands" in action for action in brief["unsafe_actions"])
    assert brief["writes_files"] is False
    assert brief["writes_state"] is False
    assert brief["daemon_started"] is False
    assert brief["background_scheduler_started"] is False
    assert brief["service_launch_performed"] is False
    assert brief["arbitrary_command_authority"] is False
    assert brief["agent_fanout_authority"] is False
    assert brief["git_mutation_performed"] is False
    assert brief["worktrunk_mutation_performed"] is False
    assert brief["runtime_workflow_performed"] is False
    assert brief["release_gate_closed"] is False
    assert brief["execution_authority"] is False
    assert brief["requires_human_acceptance"] is True
    assert before == after


def test_loop_readiness_fails_when_required_surfaces_are_missing(tmp_path):
    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "FAIL"
    assert result["failures"] > 0
    assert any(item["path"] == "STATE.md" for item in result["failure_details"])


def test_loop_readiness_fails_when_budget_policy_is_incomplete(tmp_path):
    write_minimal_loop_repo(tmp_path)
    write(tmp_path / "loop-budget.md", "Default cadence: manual/operator-requested\n")

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "FAIL"
    assert any(item["name"] == "loop budget records token cap" for item in result["failure_details"])
    assert any(item["name"] == "loop budget records kill switches" for item in result["failure_details"])


def test_loop_readiness_flags_runtime_authority_markers(tmp_path):
    write_minimal_loop_repo(tmp_path)
    write(
        tmp_path / ".github/workflows/ci.yml",
        "steps:\n  - run: uv run pytest\n  - run: python3 scripts/validate-jarvis-codex-phase1.py\n  - run: git push origin main\n",
    )

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "FAIL"
    assert any("git push" in item["name"] for item in result["failure_details"])


def test_loop_readiness_scans_scripts_for_runtime_authority_markers(tmp_path):
    write_minimal_loop_repo(tmp_path)
    write(tmp_path / "scripts" / "deploy.sh", "#!/usr/bin/env bash\ngit push origin main\n")

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "FAIL"
    assert any(item["path"] == "scripts/deploy.sh" for item in result["failure_details"])


def test_loop_readiness_scans_standard_executable_directories(tmp_path):
    write_minimal_loop_repo(tmp_path)
    write(tmp_path / "bin" / "deploy.sh", "#!/usr/bin/env bash\ngit push origin main\n")

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "FAIL"
    assert any(item["path"] == "bin/deploy.sh" for item in result["failure_details"])


def test_loop_readiness_scans_package_json_for_runtime_markers(tmp_path):
    write_minimal_loop_repo(tmp_path)
    write(tmp_path / "package.json", '{"scripts": {"publish": "git push origin main"}}\n')

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "FAIL"
    assert any(item["path"] == "package.json" for item in result["failure_details"])


def test_loop_readiness_matches_spaced_runtime_markers(tmp_path):
    write_minimal_loop_repo(tmp_path)
    write(tmp_path / "scripts" / "deploy.sh", "#!/usr/bin/env bash\ngit    push origin main\n")

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "FAIL"
    assert any(item["path"] == "scripts/deploy.sh" for item in result["failure_details"])


def test_loop_readiness_matches_compact_workspace_write_marker(tmp_path):
    write_minimal_loop_repo(tmp_path)
    write(tmp_path / ".codex" / "agents" / "worker.toml", 'sandbox_mode="workspace-write"\n')

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "FAIL"
    assert any(item["path"] == ".codex/agents/worker.toml" for item in result["failure_details"])


def test_loop_readiness_does_not_hide_active_markers_near_generic_negative_words(tmp_path):
    write_minimal_loop_repo(tmp_path)
    write(tmp_path / "scripts" / "deploy.sh", "# if not ready, stop here\n# needs approval later\ngit push origin main\n")

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "FAIL"
    assert any(item["path"] == "scripts/deploy.sh" for item in result["failure_details"])


def test_loop_readiness_flags_active_test_time_runtime_markers(tmp_path):
    write_minimal_loop_repo(tmp_path)
    write(tmp_path / "tests" / "test_evil.py", "import os\n\ndef test_evil():\n    os.system('git push origin main')\n")

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "FAIL"
    assert any(item["path"] == "tests/test_evil.py" for item in result["failure_details"])


def test_loop_readiness_flags_split_test_time_runtime_markers(tmp_path):
    write_minimal_loop_repo(tmp_path)
    write(
        tmp_path / "tests" / "test_evil.py",
        "import os\n\ndef test_evil():\n    cmd = 'git push origin main'\n    os.system(cmd)\n",
    )

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "FAIL"
    assert any(item["path"] == "tests/test_evil.py" for item in result["failure_details"])


def test_loop_readiness_allows_negative_guardrail_marker_lists(tmp_path):
    write_minimal_loop_repo(tmp_path)
    write(tmp_path / "docs" / "safety.md", "Never run these without explicit approval:\n- git push\n- git reset\n")

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "PASS"

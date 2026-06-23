from __future__ import annotations

import json

import pytest

import jarvis_codex.autonomous_loop as autonomous_loop
from jarvis_codex.autonomous_loop import run_autonomous_loop_once


class FakeGovernance:
    status = "PASS"
    failure_count = 0

    def compact_summary(self):
        return {
            "label": "project-local Codex governance",
            "status": "PASS",
            "checks_passed": 156,
            "warnings": 0,
            "failures": 0,
            "writes_reports": False,
            "not_test_replacement": True,
        }


class FakeCodeburn:
    def to_dict(self):
        return {
            "available": True,
            "today_cost": 0.0,
            "today_calls": 0,
            "month_cost": 659.35,
            "month_calls": 6953,
            "raw": "fixture",
            "error": None,
            "writes_state": False,
            "shell": False,
        }


def test_loop_run_once_requires_explicit_validation_approval(tmp_path):
    with pytest.raises(ValueError, match="allow_validation"):
        run_autonomous_loop_once(tmp_path, tmp_path / "state")


def test_loop_run_once_records_bounded_validation_evidence(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    state = tmp_path / "state"
    monkeypatch.setattr(autonomous_loop, "validate_phase1_governance", lambda repo: FakeGovernance())
    monkeypatch.setattr(
        autonomous_loop,
        "validate_loop_readiness",
        lambda repo: {
            "status": "PASS",
            "checks_passed": 12,
            "failures": 0,
            "execution_authority": False,
            "writes_files": False,
        },
    )
    monkeypatch.setattr(
        autonomous_loop,
        "build_runtime_readiness",
        lambda repo: {
            "status": "foundation-ready",
            "production_complete": False,
            "writes_state": False,
            "remaining_gaps": ["signed_release_artifacts"],
        },
    )
    monkeypatch.setattr(autonomous_loop, "read_codeburn_status", lambda: FakeCodeburn())

    result = run_autonomous_loop_once(root, state, allow_validation=True)

    assert list(root.rglob("*")) == []
    assert result.status == "PASS"
    assert result.writes_state is True
    assert result.execution_authority is False
    assert result.arbitrary_command_execution is False
    assert result.service_launch_performed is False
    assert result.network_probe_performed is False
    assert result.git_mutation_performed is False
    assert result.worktrunk_mutation_performed is False
    assert result.checks_run == ["governance", "loop_readiness", "runtime_readiness", "codeburn_status"]
    record = json.loads((state / "loop-runs" / f"{result.run_id}.json").read_text(encoding="utf-8"))
    log_lines = (state / "logs" / "loop-runs.jsonl").read_text(encoding="utf-8").splitlines()
    assert record["run_id"] == result.run_id
    assert len(log_lines) == 1
    assert json.loads(log_lines[0])["run_id"] == result.run_id
    assert record["evidence"]["governance"]["status"] == "PASS"

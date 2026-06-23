from __future__ import annotations

import json

import pytest

import jarvis_codex.autonomous_loop as autonomous_loop
from jarvis_codex.autonomous_loop import run_autonomous_loop_once, run_autonomous_loop_schedule


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


def test_loop_schedule_requires_explicit_validation_approval(tmp_path):
    with pytest.raises(ValueError, match="allow_validation"):
        run_autonomous_loop_schedule(tmp_path, tmp_path / "state")

    with pytest.raises(ValueError, match="max_iterations"):
        run_autonomous_loop_schedule(tmp_path, tmp_path / "state", allow_validation=True, max_iterations=13)

    with pytest.raises(ValueError, match="interval_seconds"):
        run_autonomous_loop_schedule(tmp_path, tmp_path / "state", allow_validation=True, interval_seconds=3601)


def test_loop_schedule_records_bounded_foreground_iterations(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    state = tmp_path / "state"
    sleep_calls = []
    run_count = 0

    class FakeRun:
        def __init__(self, index: int):
            self.run_id = f"run_{index}"
            self.status = "PASS"
            self.warnings = []

        def to_dict(self):
            return {
                "run_id": self.run_id,
                "status": self.status,
                "writes_state": True,
                "execution_authority": False,
                "arbitrary_command_execution": False,
                "service_launch_performed": False,
                "network_probe_performed": False,
                "git_mutation_performed": False,
                "worktrunk_mutation_performed": False,
            }

    def fake_run_once(repo, state_root, *, allow_validation, pattern, level):
        nonlocal run_count
        run_count += 1
        assert repo == root.resolve()
        assert state_root == state.resolve()
        assert allow_validation is True
        assert pattern == "product-readiness-triage"
        assert level == "L1"
        return FakeRun(run_count)

    monkeypatch.setattr(autonomous_loop, "run_autonomous_loop_once", fake_run_once)

    result = run_autonomous_loop_schedule(
        root,
        state,
        allow_validation=True,
        max_iterations=3,
        interval_seconds=7,
        sleep_fn=sleep_calls.append,
    )

    assert list(root.rglob("*")) == []
    assert result.status == "PASS"
    assert result.iterations_requested == 3
    assert result.iterations_completed == 3
    assert result.run_ids == ["run_1", "run_2", "run_3"]
    assert sleep_calls == [7, 7]
    assert result.execution_authority is False
    assert result.arbitrary_command_execution is False
    assert result.service_launch_performed is False
    assert result.daemon_started is False
    assert result.scheduler_backgrounded is False
    assert result.network_probe_performed is False
    assert result.git_mutation_performed is False
    assert result.worktrunk_mutation_performed is False
    record = json.loads((state / "loop-schedules" / f"{result.schedule_id}.json").read_text(encoding="utf-8"))
    log_lines = (state / "logs" / "loop-schedules.jsonl").read_text(encoding="utf-8").splitlines()
    assert record["schedule_id"] == result.schedule_id
    assert len(log_lines) == 1
    assert json.loads(log_lines[0])["schedule_id"] == result.schedule_id
    assert record["runs"][0]["schedule_iteration"] == 1


def test_loop_schedule_reports_iteration_failures(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    state = tmp_path / "state"

    class FakeRun:
        def __init__(self, index: int):
            self.run_id = f"run_{index}"
            self.status = "FAIL" if index == 2 else "PASS"
            self.warnings = ["fixture warning"] if index == 2 else []

        def to_dict(self):
            return {"run_id": self.run_id, "status": self.status, "warnings": self.warnings}

    counter = {"value": 0}

    def fake_run_once(*args, **kwargs):
        counter["value"] += 1
        return FakeRun(counter["value"])

    monkeypatch.setattr(autonomous_loop, "run_autonomous_loop_once", fake_run_once)

    result = run_autonomous_loop_schedule(
        root,
        state,
        allow_validation=True,
        max_iterations=2,
        interval_seconds=0,
    )

    assert result.status == "FAIL"
    assert result.failures == [{"iteration": 2, "run_id": "run_2", "status": "FAIL"}]
    assert result.warnings == ["iteration 2: fixture warning"]

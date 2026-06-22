from __future__ import annotations

import json
import sys
from dataclasses import dataclass

from jarvis_codex import cli


@dataclass
class FakeGovernanceResult:
    failure_count: int
    status: str = "PASS"
    checks_passed: int = 156
    warnings: int = 0
    failures: int = 0

    def compact_summary(self):
        summary = {
            "label": "project-local Codex governance",
            "status": self.status,
            "checks_passed": self.checks_passed,
            "warnings": self.warnings,
            "failures": self.failures,
            "writes_reports": False,
            "not_test_replacement": True,
        }
        if self.failure_count:
            summary["failure_details"] = ["fixture governance failure"]
        return summary


def run_cli(monkeypatch, args):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", *args])
    return cli.main()


def test_doctor_default_compact_output_has_no_governance(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"

    code = run_cli(monkeypatch, ["--state", str(state), "doctor"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data == {
        "approvals": 0,
        "episodes": 0,
        "handoffs": 0,
        "memories": 0,
        "state_root": str(state),
    }
    assert "codex_governance" not in data
    assert (state / "inbox" / ".gitkeep").exists()


def test_doctor_governance_adds_compact_summary(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"
    monkeypatch.setattr(cli, "validate_phase1_governance", lambda: FakeGovernanceResult(failure_count=0))

    code = run_cli(monkeypatch, ["--state", str(state), "doctor", "--governance"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["codex_governance"] == {
        "label": "project-local Codex governance",
        "status": "PASS",
        "checks_passed": 156,
        "warnings": 0,
        "failures": 0,
        "writes_reports": False,
        "not_test_replacement": True,
    }


def test_doctor_governance_failure_returns_nonzero_and_visible_failure(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"
    monkeypatch.setattr(
        cli,
        "validate_phase1_governance",
        lambda: FakeGovernanceResult(failure_count=1, status="FAIL", checks_passed=12, failures=1),
    )

    code = run_cli(monkeypatch, ["--state", str(state), "doctor", "--governance"])

    assert code == 1
    data = json.loads(capsys.readouterr().out)
    governance = data["codex_governance"]
    assert governance["status"] == "FAIL"
    assert governance["failures"] == 1
    assert governance["failure_details"] == ["fixture governance failure"]

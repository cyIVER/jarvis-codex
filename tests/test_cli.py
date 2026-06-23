from __future__ import annotations

import json
import sys
import wave
from dataclasses import dataclass

import pytest

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


def write_wav(path):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 160)


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
        "release_evidence": 0,
        "state_root": str(state),
    }
    assert "codex_governance" not in data
    assert not state.exists()


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
    assert not state.exists()


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
    assert not state.exists()


def test_lane_list_json_is_read_only_summary(monkeypatch, capsys):
    seen = {}

    def fake_list_lanes(repo):
        seen["repo"] = repo
        return [
            {
                "path": "/repo",
                "branch": "main",
                "decision": "ready",
                "evidence": "clean working tree",
                "merge_recommendation": "ready to merge or refresh",
            }
        ]

    monkeypatch.setattr(cli, "list_lanes", fake_list_lanes)

    code = run_cli(monkeypatch, ["lane", "list", "--repo", "/repo", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert str(seen["repo"]) == "/repo"
    assert data["execution_authority"] is False
    assert data["lanes"][0]["branch"] == "main"


def test_lane_score_json_is_read_only_summary(monkeypatch, capsys):
    seen = {}

    def fake_score_lane(repo, branch):
        seen["repo"] = repo
        seen["branch"] = branch
        return {
            "decision": "needs-review",
            "evidence": "untracked files present",
            "merge_recommendation": "review untracked files before merge",
        }

    monkeypatch.setattr(cli, "score_lane", fake_score_lane)

    code = run_cli(monkeypatch, ["lane", "score", "--repo", "/repo.lane", "--branch", "lane/test", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert str(seen["repo"]) == "/repo.lane"
    assert seen["branch"] == "lane/test"
    assert data["mutation_performed"] is False
    assert data["execution_authority"] is False
    assert data["decision"] == "needs-review"


def test_lane_commands_require_json(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "lane", "list"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_release_manifest_json_is_read_only_summary(monkeypatch, capsys):
    seen = {}

    def fake_manifest(root):
        seen["root"] = root
        return {
            "label": "Jarvis Codex release artifact manifest",
            "status": "ready-for-review",
            "execution_authority": False,
            "writes_files": False,
            "artifact_copy_performed": False,
            "generated_assets_require_approval": True,
            "artifacts": [],
            "warnings": [],
        }

    monkeypatch.setattr(cli, "build_release_manifest", fake_manifest)

    code = run_cli(monkeypatch, ["release", "manifest", "--root", "/repo", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert str(seen["root"]) == "/repo"
    assert data["execution_authority"] is False
    assert data["writes_files"] is False
    assert data["artifact_copy_performed"] is False


def test_release_packaging_preflight_json_is_read_only_summary(monkeypatch, capsys):
    class FakePackagingPreflight:
        def to_dict(self):
            return {
                "label": "Jarvis release packaging preflight",
                "status": "READY_FOR_APPROVAL",
                "install_performed": False,
                "package_build_performed": False,
                "signing_performed": False,
                "artifact_copy_performed": False,
                "writes_files": False,
                "approval_required": True,
            }

    monkeypatch.setattr(cli, "build_packaging_preflight", lambda root: FakePackagingPreflight())

    code = run_cli(monkeypatch, ["release", "packaging-preflight", "--root", "/repo", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["package_build_performed"] is False
    assert data["signing_performed"] is False
    assert data["artifact_copy_performed"] is False
    assert data["writes_files"] is False
    assert data["approval_required"] is True


def test_release_packaging_evidence_brief_json_is_read_only_summary(monkeypatch, capsys):
    seen = {}

    def fake_brief(root):
        seen["root"] = root
        return {
            "label": "Jarvis packaging and signing operator evidence brief",
            "status": "READY_FOR_OPERATOR_REVIEW",
            "install_performed": False,
            "package_build_performed": False,
            "signing_performed": False,
            "artifact_copy_performed": False,
            "publication_performed": False,
            "writes_files": False,
            "execution_authority": False,
            "publication_ready": False,
            "release_gate_closed": False,
            "release_evidence_commands": [
                "jarvis-codex --state <state-dir> release evidence add --gate electron_packaging_and_signing --json"
            ],
        }

    monkeypatch.setattr(cli, "build_packaging_signing_evidence_brief", fake_brief)

    code = run_cli(monkeypatch, ["release", "packaging-evidence-brief", "--root", "/repo", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert str(seen["root"]) == "/repo"
    assert data["label"] == "Jarvis packaging and signing operator evidence brief"
    assert data["package_build_performed"] is False
    assert data["signing_performed"] is False
    assert data["artifact_copy_performed"] is False
    assert data["publication_performed"] is False
    assert data["writes_files"] is False
    assert data["execution_authority"] is False
    assert data["publication_ready"] is False
    assert data["release_gate_closed"] is False
    assert "electron_packaging_and_signing" in data["release_evidence_commands"][0]


def test_release_artifact_evidence_json_is_read_only_summary(monkeypatch, capsys):
    seen = {}

    def fake_evidence(root):
        seen["root"] = root
        return {
            "label": "Jarvis Codex release artifact evidence",
            "status": "ready-for-review",
            "writes_files": False,
            "package_build_performed": False,
            "signing_performed": False,
            "artifact_copy_performed": False,
            "publication_ready": False,
            "artifacts": [],
        }

    monkeypatch.setattr(cli, "build_release_artifact_evidence", fake_evidence)

    code = run_cli(monkeypatch, ["release", "artifact-evidence", "--root", "/repo", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert str(seen["root"]) == "/repo"
    assert data["writes_files"] is False
    assert data["signing_performed"] is False
    assert data["artifact_copy_performed"] is False
    assert data["publication_ready"] is False


def test_release_security_review_plan_json_is_read_only_summary(monkeypatch, capsys):
    seen = {}

    def fake_plan(root):
        seen["root"] = root
        return {
            "label": "Jarvis Codex external security review plan",
            "status": "ready-for-external-review",
            "writes_files": False,
            "services_started": False,
            "network_probe_performed": False,
            "scanner_run_performed": False,
            "external_review_completed": False,
            "external_security_review_required": True,
        }

    monkeypatch.setattr(cli, "build_external_security_review_plan", fake_plan)

    code = run_cli(monkeypatch, ["release", "security-review-plan", "--root", "/repo", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert str(seen["root"]) == "/repo"
    assert data["writes_files"] is False
    assert data["services_started"] is False
    assert data["network_probe_performed"] is False
    assert data["scanner_run_performed"] is False
    assert data["external_review_completed"] is False
    assert data["external_security_review_required"] is True


def test_release_security_evidence_brief_json_is_read_only_summary(monkeypatch, capsys):
    seen = {}

    def fake_brief(root):
        seen["root"] = root
        return {
            "label": "Jarvis external security review evidence brief",
            "status": "READY_FOR_EXTERNAL_REVIEW",
            "writes_files": False,
            "services_started": False,
            "network_probe_performed": False,
            "scanner_run_performed": False,
            "package_build_performed": False,
            "signing_performed": False,
            "artifact_copy_performed": False,
            "publication_performed": False,
            "execution_authority": False,
            "external_review_completed": False,
            "release_gate_closed": False,
            "release_evidence_command": "jarvis-codex --state <state-dir> release evidence add --gate external_security_review --json",
        }

    monkeypatch.setattr(cli, "build_external_security_evidence_brief", fake_brief)

    code = run_cli(monkeypatch, ["release", "security-evidence-brief", "--root", "/repo", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert str(seen["root"]) == "/repo"
    assert data["label"] == "Jarvis external security review evidence brief"
    assert data["writes_files"] is False
    assert data["services_started"] is False
    assert data["network_probe_performed"] is False
    assert data["scanner_run_performed"] is False
    assert data["package_build_performed"] is False
    assert data["signing_performed"] is False
    assert data["artifact_copy_performed"] is False
    assert data["publication_performed"] is False
    assert data["execution_authority"] is False
    assert data["external_review_completed"] is False
    assert data["release_gate_closed"] is False
    assert "external_security_review" in data["release_evidence_command"]


def test_release_evidence_add_records_metadata_without_closing_gate(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"
    artifact_dir = state / "release"
    artifact_dir.mkdir(parents=True)
    artifact = artifact_dir / "security-review-attestation.txt"
    artifact.write_text("external reviewer holds release", encoding="utf-8")

    code = run_cli(
        monkeypatch,
        [
            "--state",
            str(state),
            "release",
            "evidence",
            "add",
            "--gate",
            "external_security_review",
            "--summary",
            "Reviewer returned hold pending fixes.",
            "--reviewer",
            "external-reviewer",
            "--artifact",
            str(artifact),
            "--json",
        ],
    )

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    evidence = data["evidence"]
    assert data["state_write_performed"] is True
    assert evidence["gate"] == "external_security_review"
    assert evidence["reviewer"] == "external-reviewer"
    assert evidence["artifact_path"] == str(artifact.resolve())
    assert evidence["artifact_size_bytes"] == artifact.stat().st_size
    assert evidence["artifact_sha256"]
    assert evidence["execution_authority"] is False
    assert evidence["release_gate_closed"] is False
    assert (state / "release" / "evidence.jsonl").exists()


def test_release_evidence_list_is_state_only_summary(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"
    add_code = run_cli(
        monkeypatch,
        [
            "--state",
            str(state),
            "release",
            "evidence",
            "add",
            "--gate",
            "actual_mobile_device_validation",
            "--summary",
            "Operator captured iPhone evidence.",
            "--json",
        ],
    )
    assert add_code == 0
    capsys.readouterr()

    list_code = run_cli(monkeypatch, ["--state", str(state), "release", "evidence", "list", "--json"])

    assert list_code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["execution_authority"] is False
    assert len(data["release_evidence"]) == 1
    assert data["release_evidence"][0]["gate"] == "actual_mobile_device_validation"
    assert data["release_evidence"][0]["release_gate_closed"] is False
    assert "writes_state" not in data["release_evidence"][0]


def test_release_gate_accept_requires_existing_evidence_and_closes_gate(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"
    add_code = run_cli(
        monkeypatch,
        [
            "--state",
            str(state),
            "release",
            "evidence",
            "add",
            "--gate",
            "external_security_review",
            "--summary",
            "External reviewer attestation accepted by operator.",
            "--reviewer",
            "external-reviewer",
            "--json",
        ],
    )
    assert add_code == 0
    evidence = json.loads(capsys.readouterr().out)["evidence"]

    accept_code = run_cli(
        monkeypatch,
        [
            "--state",
            str(state),
            "release",
            "gate",
            "accept",
            "--gate",
            "external_security_review",
            "--evidence-id",
            evidence["id"],
            "--summary",
            "Operator accepts the external reviewer attestation.",
            "--reviewer",
            "operator",
            "--json",
        ],
    )

    assert accept_code == 0
    accepted = json.loads(capsys.readouterr().out)
    acceptance = accepted["acceptance"]
    assert accepted["state_write_performed"] is True
    assert accepted["execution_authority"] is False
    assert accepted["evidence_closes_gates"] is False
    assert acceptance["gate"] == "external_security_review"
    assert acceptance["evidence_id"] == evidence["id"]
    assert acceptance["reviewer"] == "operator"
    assert acceptance["release_gate_closed"] is True
    assert acceptance["publication_ready"] is False
    assert (state / "release" / "gate-acceptance.jsonl").exists()

    status_code = run_cli(monkeypatch, ["--state", str(state), "release", "gate-status", "--json"])
    assert status_code == 0
    status = json.loads(capsys.readouterr().out)
    external = next(item for item in status["gates"] if item["gate"] == "external_security_review")
    assert external["status"] == "accepted"
    assert external["release_gate_closed"] is True
    assert external["accepted_evidence_id"] == evidence["id"]
    assert status["accepted_gate_count"] == 1
    assert status["open_gate_count"] == 5


def test_release_gate_accept_rejects_unknown_or_mismatched_evidence(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"
    add_code = run_cli(
        monkeypatch,
        [
            "--state",
            str(state),
            "release",
            "evidence",
            "add",
            "--gate",
            "actual_mobile_device_validation",
            "--summary",
            "Operator captured mobile evidence.",
            "--json",
        ],
    )
    assert add_code == 0
    evidence = json.loads(capsys.readouterr().out)["evidence"]

    with pytest.raises(ValueError) as exc_info:
        run_cli(
            monkeypatch,
            [
                "--state",
                str(state),
                "release",
                "gate",
                "accept",
                "--gate",
                "external_security_review",
                "--evidence-id",
                evidence["id"],
                "--summary",
                "Wrong gate should be rejected.",
                "--json",
            ],
        )

    assert "existing evidence record for the same gate" in str(exc_info.value)


def test_release_gate_list_is_state_only_summary(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"
    add_code = run_cli(
        monkeypatch,
        [
            "--state",
            str(state),
            "release",
            "evidence",
            "add",
            "--gate",
            "unattended_loop_scheduling",
            "--summary",
            "Operator accepted bounded loop evidence.",
            "--json",
        ],
    )
    assert add_code == 0
    evidence = json.loads(capsys.readouterr().out)["evidence"]
    accept_code = run_cli(
        monkeypatch,
        [
            "--state",
            str(state),
            "release",
            "gate",
            "accept",
            "--gate",
            "unattended_loop_scheduling",
            "--evidence-id",
            evidence["id"],
            "--summary",
            "Operator accepts bounded loop policy evidence.",
            "--json",
        ],
    )
    assert accept_code == 0
    capsys.readouterr()

    list_code = run_cli(monkeypatch, ["--state", str(state), "release", "gate", "list", "--json"])

    assert list_code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["execution_authority"] is False
    assert len(data["release_gate_acceptances"]) == 1
    assert data["release_gate_acceptances"][0]["gate"] == "unattended_loop_scheduling"
    assert data["release_gate_acceptances"][0]["release_gate_closed"] is True


def test_release_evidence_add_rejects_external_artifact_path(tmp_path, monkeypatch):
    state = tmp_path / "state"
    artifact = tmp_path / "outside-state-release.txt"
    artifact.write_text("sensitive-ish external evidence", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        run_cli(
            monkeypatch,
            [
                "--state",
                str(state),
                "release",
                "evidence",
                "add",
                "--gate",
                "external_security_review",
                "--summary",
                "External file should be rejected.",
                "--artifact",
                str(artifact),
                "--json",
            ],
        )

    assert "selected state release directory" in str(exc_info.value)


def test_release_gate_status_reports_open_gates_from_state_evidence(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"
    add_code = run_cli(
        monkeypatch,
        [
            "--state",
            str(state),
            "release",
            "evidence",
            "add",
            "--gate",
            "networked_gemini_live_validation",
            "--summary",
            "Operator has not run the network test yet.",
            "--json",
        ],
    )
    assert add_code == 0
    capsys.readouterr()

    code = run_cli(monkeypatch, ["--state", str(state), "release", "gate-status", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    gemini = next(item for item in data["gates"] if item["gate"] == "networked_gemini_live_validation")
    assert data["writes_state"] is False
    assert data["execution_authority"] is False
    assert data["publication_ready"] is False
    assert data["evidence_closes_gates"] is False
    assert data["human_acceptance_required"] is True
    assert gemini["status"] == "open"
    assert gemini["evidence_count"] == 1
    assert gemini["release_gate_closed"] is False


def test_release_readiness_checklist_json_is_read_only_summary(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"
    seen = {}

    def fake_checklist(root, evidence_records, acceptance_records):
        seen["root"] = root
        seen["evidence_records"] = evidence_records
        seen["acceptance_records"] = acceptance_records
        return {
            "label": "Jarvis Codex release readiness checklist",
            "status": "blocked",
            "writes_files": False,
            "writes_state": False,
            "network_probe_performed": False,
            "service_launch_performed": False,
            "package_build_performed": False,
            "signing_performed": False,
            "artifact_copy_performed": False,
            "execution_authority": False,
            "publication_ready": False,
            "release_gate_closed": False,
            "blocked_by": ["external_security_review"],
            "checklist": [],
        }

    monkeypatch.setattr(cli, "build_release_readiness_checklist", fake_checklist)

    code = run_cli(monkeypatch, ["--state", str(state), "release", "readiness-checklist", "--root", "/repo", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert str(seen["root"]) == "/repo"
    assert seen["evidence_records"] == []
    assert seen["acceptance_records"] == []
    assert data["writes_files"] is False
    assert data["writes_state"] is False
    assert data["network_probe_performed"] is False
    assert data["service_launch_performed"] is False
    assert data["package_build_performed"] is False
    assert data["signing_performed"] is False
    assert data["artifact_copy_performed"] is False
    assert data["execution_authority"] is False
    assert data["publication_ready"] is False
    assert data["release_gate_closed"] is False
    assert not state.exists()


def test_release_commands_require_json(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "release", "manifest"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_runtime_serve_defaults_to_loopback_and_temp_state(tmp_path, monkeypatch):
    calls = {}

    def fake_create_app(state):
        calls["state"] = state
        return "runtime-app"

    def fake_uvicorn_run(app, host, port, log_level):
        calls["app"] = app
        calls["host"] = host
        calls["port"] = port
        calls["log_level"] = log_level

    monkeypatch.setattr(cli, "create_app", fake_create_app)
    monkeypatch.setattr(cli.uvicorn, "run", fake_uvicorn_run)

    code = run_cli(monkeypatch, ["--state", str(tmp_path / "state"), "runtime", "serve", "--port", "9999"])

    assert code == 0
    assert calls == {
        "state": tmp_path / "state",
        "app": "runtime-app",
        "host": "127.0.0.1",
        "port": 9999,
        "log_level": "info",
    }
    assert not (tmp_path / "state").exists()


def test_runtime_serve_rejects_non_loopback_without_explicit_flag(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "runtime", "serve", "--host", "0.0.0.0"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_runtime_serve_allows_non_loopback_when_explicitly_requested(tmp_path, monkeypatch):
    calls = {}

    def fake_create_app(state):
        calls["state"] = state
        return "runtime-app"

    def fake_uvicorn_run(app, host, port, log_level):
        calls.update({"app": app, "host": host, "port": port, "log_level": log_level})

    monkeypatch.setattr(cli, "create_app", fake_create_app)
    monkeypatch.setattr(cli.uvicorn, "run", fake_uvicorn_run)

    code = run_cli(
        monkeypatch,
        [
            "--state",
            str(tmp_path / "state"),
            "runtime",
            "serve",
            "--host",
            "0.0.0.0",
            "--allow-non-loopback",
        ],
    )

    assert code == 0
    assert calls["host"] == "0.0.0.0"
    assert calls["port"] == 8765
    assert calls["state"] == tmp_path / "state"
    assert calls["app"] == "runtime-app"


def test_runtime_readiness_json_is_non_writing_summary(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "build_runtime_readiness",
        lambda: {
            "status": "foundation-ready",
            "production_complete": False,
            "writes_state": False,
            "checks": {"electron_lockfile": True},
            "remaining_gaps": ["actual_loop_execution"],
        },
    )

    code = run_cli(monkeypatch, ["runtime", "readiness", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "foundation-ready"
    assert data["writes_state"] is False
    assert data["checks"]["electron_lockfile"] is True
    assert "actual_loop_execution" in data["remaining_gaps"]


def test_runtime_readiness_requires_json(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "runtime", "readiness"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_mobile_preflight_json_is_read_only_summary(monkeypatch, capsys):
    code = run_cli(monkeypatch, ["mobile", "preflight", "--host", "100.99.88.77", "--port", "8765", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["host_class"] == "tailscale-cgnat"
    assert data["iphone_reachable_candidate"] is True
    assert data["requires_allow_non_loopback"] is True
    assert data["service_launch_performed"] is False
    assert data["network_probe_performed"] is False
    assert data["writes_state"] is False
    assert data["runtime_command"].endswith("--allow-non-loopback")


def test_mobile_discover_json_reports_candidates_without_launching(monkeypatch, capsys):
    fake_candidate = {
        "interface": "eth0",
        "host": "192.168.1.20",
        "host_class": "private-lan",
        "url": "http://192.168.1.20:8765",
        "iphone_reachable_candidate": True,
        "public_exposure_risk": False,
        "requires_allow_non_loopback": True,
        "runtime_command": "jarvis-codex runtime serve --host 192.168.1.20 --port 8765 --allow-non-loopback",
        "preflight_command": "jarvis-codex mobile preflight --host 192.168.1.20 --port 8765 --scheme http --json",
        "validation_plan_command": "jarvis-codex mobile validation-plan --host 192.168.1.20 --port 8765 --scheme http --json",
        "warnings": [],
    }

    class FakeDiscovery:
        def to_dict(self):
            return {
                "label": "Jarvis mobile host discovery",
                "status": "READY_FOR_OPERATOR_TEST",
                "candidates": [fake_candidate],
                "recommended_candidate": fake_candidate,
                "writes_state": False,
                "network_probe_performed": False,
                "service_launch_performed": False,
                "browser_opened": False,
                "execution_authority": False,
                "warnings": [],
            }

    monkeypatch.setattr(cli, "discover_mobile_hosts", lambda port, scheme: FakeDiscovery())

    code = run_cli(monkeypatch, ["mobile", "discover", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "READY_FOR_OPERATOR_TEST"
    assert data["recommended_candidate"]["host"] == "192.168.1.20"
    assert data["network_probe_performed"] is False
    assert data["service_launch_performed"] is False
    assert data["browser_opened"] is False


def test_mobile_preflight_requires_json(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "mobile", "preflight"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_mobile_validation_plan_json_is_read_only_summary(monkeypatch, capsys):
    code = run_cli(monkeypatch, ["mobile", "validation-plan", "--host", "192.168.1.20", "--port", "8765", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["label"] == "Jarvis mobile PWA validation plan"
    assert data["status"] == "READY_FOR_OPERATOR_TEST"
    assert data["host_class"] == "private-lan"
    assert data["network_probe_performed"] is False
    assert data["service_launch_performed"] is False
    assert data["writes_state"] is False
    assert data["execution_authority"] is False


def test_mobile_evidence_brief_json_is_read_only_summary(monkeypatch, capsys):
    code = run_cli(monkeypatch, ["mobile", "evidence-brief", "--host", "192.168.1.20", "--port", "8765", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["label"] == "Jarvis mobile operator evidence brief"
    assert data["status"] == "READY_FOR_OPERATOR_TEST"
    assert data["target_url"] == "http://192.168.1.20:8765"
    assert data["network_probe_performed"] is False
    assert data["service_launch_performed"] is False
    assert data["writes_state"] is False
    assert data["browser_opened"] is False
    assert data["execution_authority"] is False
    assert data["release_gate_closed"] is False
    assert "actual_mobile_device_validation" in data["release_evidence_command"]
    assert any("microphone permission" in item for item in data["required_operator_evidence"])
    assert any("<state-dir>/release/" in step for step in data["operator_steps"])


def test_mobile_validation_plan_requires_json(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "mobile", "validation-plan"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_gemini_feasibility_json_is_read_only_summary(monkeypatch, capsys):
    class FakeGeminiFeasibility:
        def to_dict(self):
            return {
                "label": "Gemini Live feasibility",
                "status": "NEEDS_CREDENTIALS",
                "network_probe_performed": False,
                "service_launch_performed": False,
                "writes_state": False,
                "secret_values_exposed": False,
                "remaining_gates": ["run an explicit networked Gemini Live connection test only after operator approval"],
            }

    monkeypatch.setattr(cli, "build_gemini_feasibility", lambda: FakeGeminiFeasibility())

    code = run_cli(monkeypatch, ["gemini", "feasibility", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "NEEDS_CREDENTIALS"
    assert data["network_probe_performed"] is False
    assert data["service_launch_performed"] is False
    assert data["writes_state"] is False
    assert data["secret_values_exposed"] is False


def test_gemini_feasibility_requires_json(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "gemini", "feasibility"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_gemini_validation_plan_json_is_read_only_summary(monkeypatch, capsys):
    class FakeGeminiValidationPlan:
        def to_dict(self):
            return {
                "label": "Gemini Live validation plan",
                "status": "READY_FOR_OPERATOR_TEST",
                "credential_mode_ready": True,
                "network_probe_performed": False,
                "oauth_flow_started": False,
                "websocket_opened": False,
                "service_launch_performed": False,
                "writes_state": False,
                "execution_authority": False,
                "secret_values_exposed": False,
            }

    monkeypatch.setattr(cli, "build_gemini_live_validation_plan", lambda: FakeGeminiValidationPlan())

    code = run_cli(monkeypatch, ["gemini", "validation-plan", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["label"] == "Gemini Live validation plan"
    assert data["status"] == "READY_FOR_OPERATOR_TEST"
    assert data["network_probe_performed"] is False
    assert data["websocket_opened"] is False
    assert data["service_launch_performed"] is False
    assert data["writes_state"] is False
    assert data["execution_authority"] is False


def test_gemini_evidence_brief_json_is_read_only_summary(monkeypatch, capsys):
    class FakeGeminiEvidenceBrief:
        def to_dict(self):
            return {
                "label": "Gemini Live operator evidence brief",
                "status": "READY_FOR_OPERATOR_TEST",
                "credential_mode_ready": True,
                "network_probe_performed": False,
                "oauth_flow_started": False,
                "websocket_opened": False,
                "service_launch_performed": False,
                "writes_state": False,
                "execution_authority": False,
                "secret_values_exposed": False,
                "cloud_spend_authority": False,
                "release_gate_closed": False,
                "release_evidence_command": "jarvis-codex --state <state-dir> release evidence add --gate networked_gemini_live_validation --json",
            }

    monkeypatch.setattr(cli, "build_gemini_live_evidence_brief", lambda: FakeGeminiEvidenceBrief())

    code = run_cli(monkeypatch, ["gemini", "evidence-brief", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["label"] == "Gemini Live operator evidence brief"
    assert data["status"] == "READY_FOR_OPERATOR_TEST"
    assert data["network_probe_performed"] is False
    assert data["oauth_flow_started"] is False
    assert data["websocket_opened"] is False
    assert data["service_launch_performed"] is False
    assert data["writes_state"] is False
    assert data["execution_authority"] is False
    assert data["secret_values_exposed"] is False
    assert data["cloud_spend_authority"] is False
    assert data["release_gate_closed"] is False
    assert "networked_gemini_live_validation" in data["release_evidence_command"]


def test_gemini_nango_plan_json_is_read_only_summary(monkeypatch, capsys):
    class FakeNangoGeminiPlan:
        def to_dict(self):
            return {
                "label": "Nango-governed Gemini Live integration plan",
                "status": "PLANNING_ONLY",
                "direct_nango_audio_proxy_recommended": False,
                "browser_direct_requires_ephemeral_tokens": True,
                "network_probe_performed": False,
                "oauth_flow_started": False,
                "websocket_opened": False,
                "nango_api_called": False,
                "service_launch_performed": False,
                "writes_state": False,
                "execution_authority": False,
                "secret_values_exposed": False,
                "cloud_spend_authority": False,
            }

    monkeypatch.setattr(cli, "build_nango_gemini_live_integration_plan", lambda: FakeNangoGeminiPlan())

    code = run_cli(monkeypatch, ["gemini", "nango-plan", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["label"] == "Nango-governed Gemini Live integration plan"
    assert data["status"] == "PLANNING_ONLY"
    assert data["direct_nango_audio_proxy_recommended"] is False
    assert data["browser_direct_requires_ephemeral_tokens"] is True
    assert data["network_probe_performed"] is False
    assert data["oauth_flow_started"] is False
    assert data["websocket_opened"] is False
    assert data["nango_api_called"] is False
    assert data["service_launch_performed"] is False
    assert data["writes_state"] is False
    assert data["execution_authority"] is False
    assert data["secret_values_exposed"] is False
    assert data["cloud_spend_authority"] is False


def test_gemini_validation_plan_requires_json(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "gemini", "validation-plan"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_gemini_evidence_brief_requires_json(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "gemini", "evidence-brief"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_gemini_nango_plan_requires_json(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "gemini", "nango-plan"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_loop_verify_json_returns_read_only_status(monkeypatch, capsys):
    seen = {}

    def fake_loop_readiness(root):
        seen["root"] = root
        return {
            "label": "Jarvis Codex loop readiness",
            "status": "PASS",
            "execution_authority": False,
            "writes_files": False,
            "checks_passed": 3,
            "failures": 0,
            "failure_details": [],
            "checks": [],
        }

    monkeypatch.setattr(cli, "validate_loop_readiness", fake_loop_readiness)

    code = run_cli(monkeypatch, ["loop", "verify", "--root", "/repo", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert str(seen["root"]) == "/repo"
    assert data["status"] == "PASS"
    assert data["execution_authority"] is False
    assert data["writes_files"] is False


def test_loop_verify_failure_returns_nonzero(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "validate_loop_readiness",
        lambda root: {
            "label": "Jarvis Codex loop readiness",
            "status": "FAIL",
            "execution_authority": False,
            "writes_files": False,
            "checks_passed": 1,
            "failures": 1,
            "failure_details": [{"name": "state", "path": "STATE.md", "status": "fail", "note": "missing"}],
            "checks": [],
        },
    )

    code = run_cli(monkeypatch, ["loop", "verify", "--root", "/repo", "--json"])

    assert code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "FAIL"
    assert data["failures"] == 1


def test_loop_run_once_requires_allow_validation(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "loop", "run-once", "--json"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_loop_run_once_json_records_bounded_execution(tmp_path, monkeypatch, capsys):
    seen = {}

    class FakeLoopRun:
        status = "PASS"

        def to_dict(self):
            return {
                "run_id": "loop_fixture",
                "status": "PASS",
                "writes_state": True,
                "execution_authority": False,
                "arbitrary_command_execution": False,
                "service_launch_performed": False,
                "network_probe_performed": False,
                "git_mutation_performed": False,
                "worktrunk_mutation_performed": False,
            }

    def fake_run_once(root, state_root, *, allow_validation):
        seen["root"] = root
        seen["state_root"] = state_root
        seen["allow_validation"] = allow_validation
        return FakeLoopRun()

    monkeypatch.setattr(cli, "run_autonomous_loop_once", fake_run_once)

    code = run_cli(
        monkeypatch,
        ["--state", str(tmp_path / "state"), "loop", "run-once", "--root", "/repo", "--allow-validation", "--json"],
    )

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert str(seen["root"]) == "/repo"
    assert str(seen["state_root"]) == str(tmp_path / "state")
    assert seen["allow_validation"] is True
    assert data["status"] == "PASS"
    assert data["writes_state"] is True
    assert data["execution_authority"] is False
    assert data["arbitrary_command_execution"] is False
    assert data["service_launch_performed"] is False


def test_loop_schedule_requires_allow_validation(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "loop", "schedule", "--json"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_loop_schedule_json_records_bounded_foreground_execution(tmp_path, monkeypatch, capsys):
    seen = {}

    class FakeLoopSchedule:
        status = "PASS"

        def to_dict(self):
            return {
                "schedule_id": "schedule_fixture",
                "status": "PASS",
                "iterations_requested": 3,
                "iterations_completed": 3,
                "interval_seconds": 0,
                "writes_state": True,
                "execution_authority": False,
                "arbitrary_command_execution": False,
                "service_launch_performed": False,
                "daemon_started": False,
                "scheduler_backgrounded": False,
            }

    def fake_schedule(root, state_root, *, allow_validation, max_iterations, interval_seconds):
        seen["root"] = root
        seen["state_root"] = state_root
        seen["allow_validation"] = allow_validation
        seen["max_iterations"] = max_iterations
        seen["interval_seconds"] = interval_seconds
        return FakeLoopSchedule()

    monkeypatch.setattr(cli, "run_autonomous_loop_schedule", fake_schedule)

    code = run_cli(
        monkeypatch,
        [
            "--state",
            str(tmp_path / "state"),
            "loop",
            "schedule",
            "--root",
            "/repo",
            "--allow-validation",
            "--max-iterations",
            "3",
            "--interval-seconds",
            "0",
            "--json",
        ],
    )

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert str(seen["root"]) == "/repo"
    assert str(seen["state_root"]) == str(tmp_path / "state")
    assert seen["allow_validation"] is True
    assert seen["max_iterations"] == 3
    assert seen["interval_seconds"] == 0
    assert data["status"] == "PASS"
    assert data["execution_authority"] is False
    assert data["daemon_started"] is False
    assert data["scheduler_backgrounded"] is False


def test_loop_unattended_policy_json_is_read_only(monkeypatch, capsys):
    def fake_policy(root):
        return {
            "label": "Jarvis Codex unattended loop policy",
            "status": "ready-for-human-policy-review",
            "root": str(root),
            "writes_files": False,
            "writes_state": False,
            "execution_authority": False,
            "daemon_started": False,
            "scheduler_backgrounded": False,
            "release_gate_closed": False,
        }

    monkeypatch.setattr(cli, "build_unattended_loop_policy", fake_policy)

    code = run_cli(monkeypatch, ["loop", "unattended-policy", "--root", "/repo", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "ready-for-human-policy-review"
    assert data["writes_files"] is False
    assert data["writes_state"] is False
    assert data["execution_authority"] is False
    assert data["daemon_started"] is False
    assert data["scheduler_backgrounded"] is False
    assert data["release_gate_closed"] is False


def test_loop_unattended_evidence_brief_json_is_read_only(monkeypatch, capsys):
    def fake_brief(root):
        return {
            "label": "Jarvis unattended loop scheduling operator evidence brief",
            "status": "READY_FOR_OPERATOR_REVIEW",
            "root": str(root),
            "writes_files": False,
            "writes_state": False,
            "daemon_started": False,
            "background_scheduler_started": False,
            "service_launch_performed": False,
            "arbitrary_command_authority": False,
            "agent_fanout_authority": False,
            "git_mutation_performed": False,
            "worktrunk_mutation_performed": False,
            "runtime_workflow_performed": False,
            "execution_authority": False,
            "release_gate_closed": False,
            "release_evidence_command": "jarvis-codex --state <state-dir> release evidence add --gate unattended_loop_scheduling --json",
        }

    monkeypatch.setattr(cli, "build_unattended_loop_evidence_brief", fake_brief)

    code = run_cli(monkeypatch, ["loop", "unattended-evidence-brief", "--root", "/repo", "--json"])

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["label"] == "Jarvis unattended loop scheduling operator evidence brief"
    assert data["writes_files"] is False
    assert data["writes_state"] is False
    assert data["daemon_started"] is False
    assert data["background_scheduler_started"] is False
    assert data["service_launch_performed"] is False
    assert data["arbitrary_command_authority"] is False
    assert data["agent_fanout_authority"] is False
    assert data["git_mutation_performed"] is False
    assert data["worktrunk_mutation_performed"] is False
    assert data["runtime_workflow_performed"] is False
    assert data["execution_authority"] is False
    assert data["release_gate_closed"] is False
    assert "unattended_loop_scheduling" in data["release_evidence_command"]


def test_loop_commands_require_json(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "loop", "verify"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_voice_ingest_transcript_file_json(tmp_path, monkeypatch, capsys):
    transcript = tmp_path / "transcript.txt"
    transcript.write_text("Voice idea for Jarvis.\n", encoding="utf-8")
    state = tmp_path / "state"

    code = run_cli(
        monkeypatch,
        ["--state", str(state), "voice", "ingest", "--transcript-file", str(transcript), "--json"],
    )

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["captured"].startswith("ep_")
    assert data["source"] == "voice-transcript-file"
    assert data["execution_authority"] is False
    assert data["runtime_started"] is False
    assert data["audio_processed"] is False
    assert data["external_services"] is False


def test_voice_commands_require_json(tmp_path, monkeypatch):
    transcript = tmp_path / "transcript.txt"
    transcript.write_text("Voice idea for Jarvis.\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "voice", "ingest", "--transcript-file", str(transcript)])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_voice_probe_checks_stt_readiness_without_runtime_or_state(tmp_path, monkeypatch, capsys):
    audio = tmp_path / "sample.wav"
    model = tmp_path / "ggml-base.en.bin"
    write_wav(audio)
    model.write_bytes(b"model")
    state = tmp_path / "state"

    code = run_cli(
        monkeypatch,
        [
            "--state",
            str(state),
            "voice",
            "probe",
            "--audio-file",
            str(audio),
            "--model",
            str(model),
            "--stt-command",
            sys.executable,
            "--json",
        ],
    )

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "PASS"
    assert data["source"] == "voice-audio-probe"
    assert data["runtime_started"] is False
    assert data["audio_processed"] is False
    assert data["writes_state"] is False
    assert data["audio"]["whisper_cpp_compatible"] is True
    assert not state.exists()


def test_voice_discover_reports_local_stt_assets_without_state(tmp_path, monkeypatch, capsys):
    bin_dir = tmp_path / "bin"
    model_dir = tmp_path / "models"
    whisper = bin_dir / "whisper-cli"
    model = model_dir / "ggml-small.en.bin"
    bin_dir.mkdir()
    model_dir.mkdir()
    whisper.write_text("#!/bin/sh\n", encoding="utf-8")
    whisper.chmod(0o755)
    model.write_bytes(b"model")
    state = tmp_path / "state"
    monkeypatch.setenv("PATH", str(bin_dir))

    code = run_cli(
        monkeypatch,
        [
            "--state",
            str(state),
            "voice",
            "discover",
            "--search-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "READY"
    assert str(whisper.resolve()) in data["command_candidates"]
    assert str(model.resolve()) in data["model_candidates"]
    assert data["runtime_started"] is False
    assert data["microphone_accessed"] is False
    assert data["audio_processed"] is False
    assert data["writes_state"] is False
    assert not state.exists()


def test_voice_ingest_audio_requires_approval_without_runtime(tmp_path, monkeypatch, capsys):
    audio = tmp_path / "sample.wav"
    model = tmp_path / "model.bin"
    audio.write_bytes(b"fake audio")
    model.write_bytes(b"fake model")
    state = tmp_path / "state"

    code = run_cli(
        monkeypatch,
        [
            "--state",
            str(state),
            "voice",
            "ingest",
            "--audio-file",
            str(audio),
            "--model",
            str(model),
            "--stt-command",
            "fake-stt",
            "--json",
        ],
    )

    assert code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "approval-required"
    assert data["runtime_started"] is False
    assert data["audio_processed"] is False
    assert not state.exists()


def test_voice_ingest_audio_runs_explicit_adapter_when_approved(tmp_path, monkeypatch, capsys):
    audio = tmp_path / "sample.wav"
    model = tmp_path / "model.bin"
    adapter = tmp_path / "fake_stt.py"
    audio.write_bytes(b"fake audio")
    model.write_bytes(b"fake model")
    adapter.write_text(
        "import argparse\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--audio-file', required=True)\n"
        "parser.add_argument('--model', required=True)\n"
        "parser.parse_args()\n"
        "print('Captured approved audio transcript.')\n",
        encoding="utf-8",
    )
    state = tmp_path / "state"

    code = run_cli(
        monkeypatch,
        [
            "--state",
            str(state),
            "voice",
            "ingest",
            "--audio-file",
            str(audio),
            "--model",
            str(model),
            "--stt-command",
            f"{sys.executable} {adapter}",
            "--allow-audio-processing",
            "--json",
        ],
    )

    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "captured"
    assert data["source"] == "voice-audio-file"
    assert data["runtime_started"] is True
    assert data["audio_processed"] is True
    assert data["external_services"] is False

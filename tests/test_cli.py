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


def test_release_commands_require_json(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "release", "manifest"])

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

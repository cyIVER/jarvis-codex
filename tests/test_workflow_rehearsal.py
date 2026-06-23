import json
import sys
from dataclasses import dataclass
from pathlib import Path

from jarvis_codex import cli
from jarvis_codex.plan_viewer import (
    approve_next_steps_queue,
    build_current_state,
    save_next_steps_selection,
)


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class PassingGovernance:
    failure_count: int = 0

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


def run_cli(monkeypatch, capsys, args):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", *args])
    code = cli.main()
    output = capsys.readouterr().out
    return code, json.loads(output)


def test_local_workflow_rehearsal_uses_temp_state_only(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"

    code, capture = run_cli(monkeypatch, capsys, ["--state", str(state), "capture", "Review", "platform", "readiness"])
    assert code == 0
    assert capture["captured"].startswith("ep_")

    transcript = tmp_path / "voice-transcript.txt"
    transcript.write_text("Capture voice-origin platform note.\n", encoding="utf-8")
    code, voice = run_cli(
        monkeypatch,
        capsys,
        ["--state", str(state), "voice", "ingest", "--transcript-file", str(transcript), "--json"],
    )
    assert code == 0
    assert voice["captured"].startswith("ep_")
    assert voice["runtime_started"] is False

    code, memory = run_cli(monkeypatch, capsys, ["--state", str(state), "memory", "add", "platform_status", "ready"])
    assert code == 0
    assert memory["memory"].startswith("mem_")

    code, approval = run_cli(monkeypatch, capsys, ["--state", str(state), "approve", "request", "Review generated Remotion asset"])
    assert code == 0
    assert approval["approval"].startswith("approval_")

    code, handoff = run_cli(monkeypatch, capsys, ["--state", str(state), "handoff", "--objective", "Run product readiness review"])
    assert code == 0
    assert Path(handoff["handoff"]).exists()

    monkeypatch.setattr(cli, "validate_phase1_governance", lambda: PassingGovernance())
    code, doctor = run_cli(monkeypatch, capsys, ["--state", str(state), "doctor", "--governance"])
    assert code == 0
    assert doctor["episodes"] == 2
    assert doctor["memories"] == 1
    assert doctor["approvals"] == 1
    assert doctor["handoffs"] == 1
    assert doctor["codex_governance"]["status"] == "PASS"

    save_next_steps_selection(state, ["hardware-runtime-gate", "voice-notification-hardening"], "# Proceed")
    queue = approve_next_steps_queue(state)
    assert queue["execution_authority"] is False
    assert queue["purpose"] == "planning"

    def fake_run_git(args, cwd):
        assert cwd == ROOT
        if args == ["status", "--short", "--branch"]:
            return "## main...origin/main [ahead 18]"
        if args == ["worktree", "list"]:
            return f"{ROOT} 1234567 [main]"
        if args == ["ls-files", "state"]:
            return "state/approvals/.gitkeep\nstate/memory/.gitkeep\nstate/next-steps/.gitkeep"
        return ""

    monkeypatch.setattr("jarvis_codex.plan_viewer.run_git", fake_run_git)
    current = build_current_state(ROOT, state)

    assert current["selected_count"] == 2
    assert {episode["text"] for episode in current["continuity"]["episodes"]} == {
        "Review platform readiness",
        "Capture voice-origin platform note.",
    }
    assert current["continuity"]["unresolved_approvals"][0]["summary"] == "Review generated Remotion asset"
    assert current["continuity"]["last_handoff"]["text"].startswith("# Codex Handoff")
    assert current["continuity"]["queued_state"]["execution_authority"] is False

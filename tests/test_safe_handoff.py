import json
import sys

import pytest

from jarvis_codex import cli
from jarvis_codex.plan_viewer import next_steps_queue_path, save_next_steps_selection, approve_next_steps_queue
from jarvis_codex.safe_handoff import build_safe_handoff, render_safe_handoff_markdown


def test_safe_handoff_empty_queue_is_noop(tmp_path):
    handoff = build_safe_handoff(tmp_path / "state")

    assert handoff.status == "empty"
    assert handoff.selected_steps == []
    assert handoff.execution_authority is False


def test_safe_handoff_invalid_queue_is_noop(tmp_path):
    state = tmp_path / "state"
    path = next_steps_queue_path(state)
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")

    handoff = build_safe_handoff(state)

    assert handoff.status == "empty"
    assert handoff.execution_authority is False


def test_safe_handoff_valid_queue_renders_non_execution_markdown(tmp_path):
    state = tmp_path / "state"
    save_next_steps_selection(state, ["hardware-runtime-gate"], "# Proceed")
    approve_next_steps_queue(state)

    handoff = build_safe_handoff(state)
    markdown = render_safe_handoff_markdown(handoff)

    assert handoff.status == "ready"
    assert handoff.selected_steps == ["hardware-runtime-gate"]
    assert handoff.execution_authority is False
    assert "Execution authority: `false`" in markdown
    assert "None executed." in markdown
    assert "requires explicit approval" in markdown


def test_safe_handoff_cli_summary_writes_no_files(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"
    save_next_steps_selection(state, ["voice-notification-hardening"], "# Brief")
    approve_next_steps_queue(state)
    before = sorted(path.relative_to(state) for path in state.rglob("*"))

    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "--state", str(state), "handoff", "--queue-summary"])
    code = cli.main()
    output = capsys.readouterr().out
    after = sorted(path.relative_to(state) for path in state.rglob("*"))

    assert code == 0
    assert before == after
    assert "# Safe CLI Handoff" in output
    assert "voice-notification-hardening" in output


def test_safe_handoff_cli_json_summary(tmp_path, monkeypatch, capsys):
    state = tmp_path / "state"
    save_next_steps_selection(state, ["hardware-runtime-gate"], "# Brief")
    approve_next_steps_queue(state)

    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "--state", str(state), "handoff", "--queue-summary", "--json"])
    code = cli.main()
    data = json.loads(capsys.readouterr().out)

    assert code == 0
    assert data["selected_steps"] == ["hardware-runtime-gate"]
    assert data["execution_authority"] is False


def test_safe_handoff_cli_json_requires_queue_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["jarvis-codex", "--state", str(tmp_path / "state"), "handoff", "--json"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


def test_safe_handoff_module_has_no_execution_helpers():
    import jarvis_codex.safe_handoff as safe_handoff

    source = safe_handoff.__file__
    text = open(source, encoding="utf-8").read()
    assert "subprocess" not in text
    assert "os.system" not in text
    assert '["git"' not in text
    assert "shell=True" not in text

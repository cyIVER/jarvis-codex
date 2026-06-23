from __future__ import annotations

import os
from pathlib import Path

from jarvis_codex import runtime_control


def test_runtime_status_reports_stopped_without_state_write(tmp_path):
    state = tmp_path / "state"

    status = runtime_control.runtime_status(state, port=9, timeout=0.01)

    assert status.status == "stopped"
    assert status.healthy is False
    assert status.pid is None
    assert status.url == "http://127.0.0.1:9"
    assert not state.exists()


def test_start_runtime_skips_duplicate_when_health_is_running(tmp_path, monkeypatch):
    state = tmp_path / "state"

    monkeypatch.setattr(
        runtime_control,
        "runtime_status",
        lambda state_dir, host=runtime_control.DEFAULT_RUNTIME_HOST, port=runtime_control.DEFAULT_RUNTIME_PORT, timeout=0.5: runtime_control.RuntimeStatus(
            status="running",
            url=f"http://{host}:{port}",
            healthy=True,
            pid=123,
            pid_file=str(state_dir / "runtime" / "jarvis-runtime.pid"),
            log_file=str(state_dir / "runtime" / "jarvis-runtime.log"),
        ),
    )

    status = runtime_control.start_runtime(state)

    assert status.status == "running"
    assert status.pid == 123
    assert status.duplicate_runtime_started is False
    assert not state.exists()


def test_install_wsl_shim_points_at_repo_and_uv_run_jarvis(tmp_path):
    repo = tmp_path / "repo"
    target = tmp_path / "bin" / "jarvis"

    installed = runtime_control.install_wsl_shim(repo, target)

    assert installed == target
    assert os.access(installed, os.X_OK)
    text = installed.read_text(encoding="utf-8")
    assert f'JARVIS_REPO:-{repo}' in text
    assert "exec uv run jarvis" in text
    assert "python3 -m jarvis_codex.cli" in text


def test_launch_windows_ui_reports_missing_powershell(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime_control, "_which", lambda name: None)

    result = runtime_control.launch_windows_ui(tmp_path)

    assert result["status"] == "unavailable"
    assert result["launched"] is False


def test_launch_windows_ui_reports_missing_portable_app(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime_control, "_which", lambda name: "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")

    result = runtime_control.launch_windows_ui(tmp_path)

    assert result["status"] == "missing-electron-app"
    assert result["launched"] is False
    assert "tools/electron-hud/dist/win-unpacked/Jarvis Codex.exe" in result["expected_paths"][0]

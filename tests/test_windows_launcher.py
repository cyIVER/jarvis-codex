from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WINDOWS = ROOT / "tools" / "windows"


def test_windows_cmd_launcher_calls_wsl_jarvis() -> None:
    text = (WINDOWS / "jarvis.cmd").read_text(encoding="utf-8")

    assert "wsl.exe" in text
    assert "JARVIS_WSL_REPO" in text
    assert "/home/iveri/repos/jarvis-codex" in text
    assert "command -v jarvis" in text
    assert "uv run jarvis" in text


def test_windows_powershell_launcher_calls_wsl_jarvis() -> None:
    text = (WINDOWS / "jarvis.ps1").read_text(encoding="utf-8")

    assert "wsl.exe" in text
    assert "JARVIS_WSL_DISTRO" in text
    assert "JARVIS_WSL_REPO" in text
    assert "exec jarvis" in text
    assert "exec uv run jarvis" in text


def test_windows_path_installer_updates_user_path_only() -> None:
    text = (WINDOWS / "install-jarvis-path.ps1").read_text(encoding="utf-8")

    assert 'GetEnvironmentVariable("Path", "User")' in text
    assert 'SetEnvironmentVariable("Path", $newPath, "User")' in text
    assert "LauncherDirectory" in text
    assert "Open a new PowerShell window" in text

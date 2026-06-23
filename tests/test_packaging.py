from __future__ import annotations

import json
from pathlib import Path

from jarvis_codex.packaging import build_packaging_preflight


def write(path: Path, text: str = "ok") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_packaging_preflight_is_read_only_and_detects_electron_package(tmp_path: Path) -> None:
    package = {"devDependencies": {"electron": "42.4.1"}}
    write(tmp_path / "tools/electron-hud/package.json", json.dumps(package))
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    preflight = build_packaging_preflight(tmp_path, {})

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert preflight.electron_hud_present is True
    assert preflight.electron_version == "42.4.1"
    assert preflight.install_performed is False
    assert preflight.package_build_performed is False
    assert preflight.signing_performed is False
    assert preflight.artifact_copy_performed is False
    assert preflight.service_launch_performed is False
    assert preflight.writes_files is False
    assert preflight.approval_required is True
    assert before == after


def test_packaging_preflight_reports_missing_lock_and_install(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps({"devDependencies": {"electron": "42.4.1"}}))

    preflight = build_packaging_preflight(tmp_path, {})

    assert preflight.package_lock_present is False
    assert preflight.node_modules_present is False
    assert any("package-lock.json is missing" in warning for warning in preflight.warnings)
    assert any("dependencies are not installed" in warning for warning in preflight.warnings)


def test_packaging_preflight_detects_lock_install_and_signing_signal(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps({"devDependencies": {"electron": "42.4.1"}}))
    write(tmp_path / "tools/electron-hud/package-lock.json", "{}")
    (tmp_path / "tools/electron-hud/node_modules").mkdir(parents=True)

    preflight = build_packaging_preflight(tmp_path, {"CSC_LINK": "secret-signing-material"})

    assert preflight.package_lock_present is True
    assert preflight.node_modules_present is True
    assert preflight.signing_signal_present is True
    assert "secret-signing-material" not in str(preflight.to_dict())


def test_packaging_preflight_missing_package_needs_setup(tmp_path: Path) -> None:
    preflight = build_packaging_preflight(tmp_path, {})

    assert preflight.status == "NEEDS_SETUP"
    assert preflight.electron_hud_present is False
    assert preflight.electron_version is None
    assert "Electron HUD package.json is missing." in preflight.warnings


def test_packaging_preflight_keeps_packaging_commands_as_recommendations(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps({"devDependencies": {"electron": "42.4.1"}}))

    preflight = build_packaging_preflight(tmp_path, {})

    assert "npm install" in preflight.recommended_commands
    assert "npm run package" in preflight.recommended_commands
    assert "npm install --package-lock-only" in preflight.recommended_commands
    assert "approve dependency lockfile generation before npm writes package-lock.json" in preflight.remaining_gates
    assert "approve dependency installation before creating node_modules" in preflight.remaining_gates


def test_packaging_preflight_drops_lock_generation_gate_when_lock_exists(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps({"devDependencies": {"electron": "42.4.1"}}))
    write(tmp_path / "tools/electron-hud/package-lock.json", "{}")

    preflight = build_packaging_preflight(tmp_path, {})

    assert preflight.package_lock_present is True
    assert "npm install --package-lock-only" not in preflight.recommended_commands
    assert "approve dependency lockfile generation before npm writes package-lock.json" not in preflight.remaining_gates
    assert "approve dependency installation before creating node_modules" in preflight.remaining_gates

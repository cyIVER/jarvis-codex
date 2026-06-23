from __future__ import annotations

import json
from pathlib import Path

from jarvis_codex.packaging import build_packaging_preflight


def write(path: Path, text: str = "ok") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def electron_package(with_builder: bool = False) -> dict:
    package = {
        "scripts": {"start": "electron ."},
        "devDependencies": {"electron": "42.4.1"},
    }
    if with_builder:
        package["scripts"].update(
            {
                "package": "electron-builder --dir --config electron-builder.json",
                "make": "electron-builder --config electron-builder.json --publish never",
            }
        )
        package["devDependencies"]["electron-builder"] = "26.15.3"
    return package


def test_packaging_preflight_is_read_only_and_detects_electron_package(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps(electron_package()))
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    preflight = build_packaging_preflight(tmp_path, {})

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert preflight.electron_hud_present is True
    assert preflight.electron_version == "42.4.1"
    assert preflight.electron_builder_version is None
    assert preflight.electron_builder_config_present is False
    assert preflight.packaging_scripts_present is False
    assert preflight.install_performed is False
    assert preflight.package_build_performed is False
    assert preflight.signing_performed is False
    assert preflight.artifact_copy_performed is False
    assert preflight.service_launch_performed is False
    assert preflight.writes_files is False
    assert preflight.approval_required is True
    assert before == after


def test_packaging_preflight_reports_missing_lock_and_install(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps(electron_package()))

    preflight = build_packaging_preflight(tmp_path, {})

    assert preflight.package_lock_present is False
    assert preflight.node_modules_present is False
    assert any("package-lock.json is missing" in warning for warning in preflight.warnings)
    assert any("dependencies are not installed" in warning for warning in preflight.warnings)
    assert any("Electron Builder is not declared" in warning for warning in preflight.warnings)
    assert any("package/make scripts are missing" in warning for warning in preflight.warnings)


def test_packaging_preflight_detects_lock_install_and_signing_signal(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps(electron_package(with_builder=True)))
    write(tmp_path / "tools/electron-hud/electron-builder.json", json.dumps({"directories": {"buildResources": "assets"}, "icon": "icon.png"}))
    write(tmp_path / "tools/electron-hud/package-lock.json", "{}")
    write(tmp_path / "tools/electron-hud/assets/icon.png", "png")
    (tmp_path / "tools/electron-hud/node_modules").mkdir(parents=True)

    preflight = build_packaging_preflight(tmp_path, {"CSC_LINK": "secret-signing-material"})

    assert preflight.package_lock_present is True
    assert preflight.node_modules_present is True
    assert preflight.electron_builder_version == "26.15.3"
    assert preflight.electron_builder_config_present is True
    assert preflight.electron_icon_present is True
    assert preflight.electron_icon_path == "tools/electron-hud/assets/icon.png"
    assert preflight.packaging_scripts_present is True
    assert preflight.signing_signal_present is True
    assert "secret-signing-material" not in str(preflight.to_dict())


def test_packaging_preflight_missing_package_needs_setup(tmp_path: Path) -> None:
    preflight = build_packaging_preflight(tmp_path, {})

    assert preflight.status == "NEEDS_SETUP"
    assert preflight.electron_hud_present is False
    assert preflight.electron_version is None
    assert "Electron HUD package.json is missing." in preflight.warnings


def test_packaging_preflight_keeps_packaging_commands_as_recommendations(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps(electron_package(with_builder=True)))
    write(tmp_path / "tools/electron-hud/electron-builder.json", "{}")

    preflight = build_packaging_preflight(tmp_path, {})

    assert "npm install" in preflight.recommended_commands
    assert "npm run package" in preflight.recommended_commands
    assert "npm install --package-lock-only" in preflight.recommended_commands
    assert "approve dependency lockfile generation before npm writes package-lock.json" in preflight.remaining_gates
    assert "approve dependency installation before creating node_modules" in preflight.remaining_gates


def test_packaging_preflight_does_not_recommend_package_commands_without_reviewed_scripts(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps(electron_package()))

    preflight = build_packaging_preflight(tmp_path, {})

    assert "npm run package" not in preflight.recommended_commands
    assert "npm run make" not in preflight.recommended_commands
    assert "add reviewed Electron Builder dependency, config, and package/make scripts" in preflight.remaining_gates


def test_packaging_preflight_drops_lock_generation_gate_when_lock_exists(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps(electron_package(with_builder=True)))
    write(tmp_path / "tools/electron-hud/electron-builder.json", "{}")
    write(tmp_path / "tools/electron-hud/package-lock.json", "{}")

    preflight = build_packaging_preflight(tmp_path, {})

    assert preflight.package_lock_present is True
    assert "npm install --package-lock-only" not in preflight.recommended_commands
    assert "approve dependency lockfile generation before npm writes package-lock.json" not in preflight.remaining_gates
    assert "approve dependency installation before creating node_modules" in preflight.remaining_gates


def test_packaging_preflight_drops_install_gate_when_node_modules_exists(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps(electron_package(with_builder=True)))
    write(tmp_path / "tools/electron-hud/electron-builder.json", "{}")
    write(tmp_path / "tools/electron-hud/package-lock.json", "{}")
    (tmp_path / "tools/electron-hud/node_modules").mkdir(parents=True)

    preflight = build_packaging_preflight(tmp_path, {})

    assert preflight.node_modules_present is True
    assert "npm install" not in preflight.recommended_commands
    assert "approve dependency installation before creating node_modules" not in preflight.remaining_gates
    assert "npm run package" in preflight.recommended_commands
    assert "add reviewed Electron Builder dependency, config, and package/make scripts" not in preflight.remaining_gates


def test_packaging_preflight_detects_local_unpacked_artifact(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps(electron_package(with_builder=True)))
    write(tmp_path / "tools/electron-hud/electron-builder.json", "{}")
    write(tmp_path / "tools/electron-hud/package-lock.json", "{}")
    write(tmp_path / "tools/electron-hud/dist/linux-unpacked/jarvis-codex-electron-hud")

    preflight = build_packaging_preflight(tmp_path, {})

    assert preflight.package_artifact_present is True
    assert preflight.package_artifact_paths == [
        "tools/electron-hud/dist/linux-unpacked",
        "tools/electron-hud/dist/linux-unpacked/jarvis-codex-electron-hud",
    ]
    assert "npm run package" not in preflight.recommended_commands
    assert "npm run make" in preflight.recommended_commands
    assert "review local package artifact before make/sign/distribution" in preflight.remaining_gates


def test_packaging_preflight_detects_unsigned_appimage_artifact(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps(electron_package(with_builder=True)))
    write(tmp_path / "tools/electron-hud/electron-builder.json", "{}")
    write(tmp_path / "tools/electron-hud/package-lock.json", "{}")
    write(tmp_path / "tools/electron-hud/dist/linux-unpacked/jarvis-codex-electron-hud")
    write(tmp_path / "tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage")

    preflight = build_packaging_preflight(tmp_path, {})

    assert preflight.installer_artifact_present is True
    assert preflight.installer_artifact_paths == ["tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage"]
    assert "npm run make" not in preflight.recommended_commands
    assert "review unsigned local installer artifact before signing/distribution" in preflight.remaining_gates


def test_packaging_preflight_reports_missing_electron_icon(tmp_path: Path) -> None:
    write(tmp_path / "tools/electron-hud/package.json", json.dumps(electron_package(with_builder=True)))
    write(tmp_path / "tools/electron-hud/electron-builder.json", json.dumps({"directories": {"buildResources": "assets"}, "icon": "icon.png"}))
    write(tmp_path / "tools/electron-hud/package-lock.json", "{}")

    preflight = build_packaging_preflight(tmp_path, {})

    assert preflight.electron_icon_present is False
    assert preflight.electron_icon_path is None
    assert "Electron HUD package icon is missing; default Electron icon warning remains." in preflight.warnings
    assert "add reviewed Electron icon before installer generation" in preflight.remaining_gates

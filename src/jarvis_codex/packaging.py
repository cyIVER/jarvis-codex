from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class PackagingPreflight:
    label: str
    status: str
    root: str
    electron_hud_present: bool
    electron_version: str | None
    npm_available: bool
    node_modules_present: bool
    package_lock_present: bool
    electron_builder_version: str | None
    electron_builder_config_present: bool
    packaging_scripts_present: bool
    package_artifact_present: bool
    package_artifact_paths: list[str]
    installer_artifact_present: bool
    installer_artifact_paths: list[str]
    signing_signal_present: bool
    install_performed: bool
    package_build_performed: bool
    signing_performed: bool
    artifact_copy_performed: bool
    service_launch_performed: bool
    writes_files: bool
    approval_required: bool
    recommended_commands: list[str]
    warnings: list[str]
    remaining_gates: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_packaging_preflight(root: Path, env: Mapping[str, str] | None = None) -> PackagingPreflight:
    """Inspect release packaging readiness without installing, building, signing, or copying artifacts."""
    repo_root = root.resolve()
    source_env = os.environ if env is None else env
    electron_dir = repo_root / "tools/electron-hud"
    package_json = electron_dir / "package.json"
    package_lock = electron_dir / "package-lock.json"
    node_modules = electron_dir / "node_modules"
    builder_config = electron_dir / "electron-builder.json"
    package_artifact_paths = _package_artifacts(electron_dir)
    installer_artifact_paths = _installer_artifacts(electron_dir)

    package_data = _package_data(package_json)
    electron_version = _dev_dependency_version(package_data, "electron")
    electron_builder_version = _dev_dependency_version(package_data, "electron-builder")
    packaging_scripts_present = _has_packaging_scripts(package_data)
    npm_available = shutil.which("npm") is not None
    signing_signal_present = any(
        bool(source_env.get(name))
        for name in (
            "CSC_LINK",
            "CSC_KEY_PASSWORD",
            "WINDOWS_CODESIGN_CERT",
            "APPLE_ID",
            "APPLE_APP_SPECIFIC_PASSWORD",
        )
    )

    warnings: list[str] = []
    if not package_json.exists():
        warnings.append("Electron HUD package.json is missing.")
    if not npm_available:
        warnings.append("npm was not found on PATH; Electron dependency installation and packaging cannot run yet.")
    if not package_lock.exists():
        warnings.append("Electron HUD package-lock.json is missing; dependency resolution is not pinned yet.")
    if not node_modules.exists():
        warnings.append("Electron HUD dependencies are not installed; do not run npm install without explicit approval.")
    if electron_builder_version is None:
        warnings.append("Electron Builder is not declared; packaging scripts cannot build local artifacts yet.")
    if not builder_config.exists():
        warnings.append("Electron Builder config is missing; package and make commands are not reviewed yet.")
    if not packaging_scripts_present:
        warnings.append("Electron HUD package/make scripts are missing or unreviewed.")
    if not signing_signal_present:
        warnings.append("No signing credential signal detected; signed installers remain blocked.")

    package_build_ready = package_json.exists() and npm_available and bool(electron_builder_version) and builder_config.exists() and packaging_scripts_present
    status = "READY_FOR_APPROVAL" if package_build_ready else "NEEDS_SETUP"

    recommended_commands: list[str] = []
    remaining_gates: list[str] = []
    if not package_lock.exists():
        recommended_commands.append("npm install --package-lock-only")
        remaining_gates.append("approve dependency lockfile generation before npm writes package-lock.json")
    if not node_modules.exists():
        recommended_commands.append("npm install")
        remaining_gates.append("approve dependency installation before creating node_modules")
    if package_build_ready and not package_artifact_paths:
        recommended_commands.append("npm run package")
    if package_build_ready:
        if not installer_artifact_paths:
            recommended_commands.append("npm run make")
    else:
        remaining_gates.append("add reviewed Electron Builder dependency, config, and package/make scripts")
    if package_artifact_paths:
        remaining_gates.append("review local package artifact before make/sign/distribution")
    if installer_artifact_paths:
        remaining_gates.append("review unsigned local installer artifact before signing/distribution")
    remaining_gates.extend(
        [
            "choose Windows/macOS/Linux artifact targets",
            "configure and verify signing credentials without committing secrets",
            "run packaging in an isolated release worktree or clean checkout",
            "perform malware/security review before distributing installers",
        ]
    )

    return PackagingPreflight(
        label="Jarvis release packaging preflight",
        status=status,
        root=str(repo_root),
        electron_hud_present=package_json.exists(),
        electron_version=electron_version,
        npm_available=npm_available,
        node_modules_present=node_modules.exists(),
        package_lock_present=package_lock.exists(),
        electron_builder_version=electron_builder_version,
        electron_builder_config_present=builder_config.exists(),
        packaging_scripts_present=packaging_scripts_present,
        package_artifact_present=bool(package_artifact_paths),
        package_artifact_paths=package_artifact_paths,
        installer_artifact_present=bool(installer_artifact_paths),
        installer_artifact_paths=installer_artifact_paths,
        signing_signal_present=signing_signal_present,
        install_performed=False,
        package_build_performed=False,
        signing_performed=False,
        artifact_copy_performed=False,
        service_launch_performed=False,
        writes_files=False,
        approval_required=True,
        recommended_commands=recommended_commands,
        warnings=warnings,
        remaining_gates=remaining_gates,
    )


def _package_data(package_json: Path) -> dict[str, Any]:
    if not package_json.exists():
        return {}
    try:
        value = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _dev_dependency_version(package_data: Mapping[str, Any], dependency: str) -> str | None:
    dev_dependencies = package_data.get("devDependencies")
    if not isinstance(dev_dependencies, dict):
        return None
    value = dev_dependencies.get(dependency)
    return str(value) if value is not None else None


def _has_packaging_scripts(package_data: Mapping[str, Any]) -> bool:
    scripts = package_data.get("scripts")
    if not isinstance(scripts, dict):
        return False
    return scripts.get("package") == "electron-builder --dir --config electron-builder.json" and scripts.get("make") == "electron-builder --config electron-builder.json --publish never"


def _package_artifacts(electron_dir: Path) -> list[str]:
    dist = electron_dir / "dist"
    linux_unpacked = dist / "linux-unpacked"
    executable = linux_unpacked / "jarvis-codex-electron-hud"
    paths: list[str] = []
    if linux_unpacked.is_dir():
        paths.append("tools/electron-hud/dist/linux-unpacked")
    if executable.is_file():
        paths.append("tools/electron-hud/dist/linux-unpacked/jarvis-codex-electron-hud")
    return paths


def _installer_artifacts(electron_dir: Path) -> list[str]:
    dist = electron_dir / "dist"
    if not dist.exists():
        return []
    return [str(path.relative_to(electron_dir.parent.parent)) for path in sorted(dist.glob("*.AppImage")) if path.is_file()]

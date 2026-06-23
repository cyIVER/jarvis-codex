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

    electron_version = _electron_version(package_json)
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
    if not signing_signal_present:
        warnings.append("No signing credential signal detected; signed installers remain blocked.")

    status = "READY_FOR_APPROVAL" if package_json.exists() and npm_available else "NEEDS_SETUP"

    return PackagingPreflight(
        label="Jarvis release packaging preflight",
        status=status,
        root=str(repo_root),
        electron_hud_present=package_json.exists(),
        electron_version=electron_version,
        npm_available=npm_available,
        node_modules_present=node_modules.exists(),
        package_lock_present=package_lock.exists(),
        signing_signal_present=signing_signal_present,
        install_performed=False,
        package_build_performed=False,
        signing_performed=False,
        artifact_copy_performed=False,
        service_launch_performed=False,
        writes_files=False,
        approval_required=True,
        recommended_commands=[
            "npm install --package-lock-only",
            "npm install",
            "npm run package",
            "npm run make",
        ],
        warnings=warnings,
        remaining_gates=[
            "approve dependency lockfile generation before npm writes package-lock.json",
            "approve dependency installation before creating node_modules",
            "add reviewed Electron packaging scripts before running package or make commands",
            "choose Windows/macOS/Linux artifact targets",
            "configure and verify signing credentials without committing secrets",
            "run packaging in an isolated release worktree or clean checkout",
            "perform malware/security review before distributing installers",
        ],
    )


def _electron_version(package_json: Path) -> str | None:
    if not package_json.exists():
        return None
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    dev_dependencies = data.get("devDependencies")
    if not isinstance(dev_dependencies, dict):
        return None
    value = dev_dependencies.get("electron")
    return str(value) if value is not None else None

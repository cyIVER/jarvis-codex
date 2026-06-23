from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ELECTRON_HUD = ROOT / "tools" / "electron-hud"


def test_electron_hud_package_is_private_and_pinned() -> None:
    package = json.loads((ELECTRON_HUD / "package.json").read_text(encoding="utf-8"))

    assert package["private"] is True
    assert package["main"] == "main.js"
    assert package["scripts"]["start"] == "electron ."
    assert package["devDependencies"]["electron"] == "42.4.1"


def test_electron_hud_builder_uses_committed_icon_asset() -> None:
    config = json.loads((ELECTRON_HUD / "electron-builder.json").read_text(encoding="utf-8"))
    icon = ELECTRON_HUD / "assets" / "icon.png"

    assert config["directories"]["buildResources"] == "assets"
    assert config["icon"] == "icon.png"
    assert icon.is_file()
    assert icon.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_electron_main_uses_loopback_default_and_private_network_gate() -> None:
    main = (ELECTRON_HUD / "main.js").read_text(encoding="utf-8")

    assert 'const DEFAULT_RUNTIME_URL = "http://127.0.0.1:8765";' in main
    assert "JARVIS_ELECTRON_ALLOW_NON_LOOPBACK" in main
    assert "isLoopbackHost(parsed.hostname)" in main
    assert "Electron HUD loads loopback runtime by default" in main


def test_electron_main_hardens_renderer_and_navigation() -> None:
    main = (ELECTRON_HUD / "main.js").read_text(encoding="utf-8")

    assert "contextIsolation: true" in main
    assert "nodeIntegration: false" in main
    assert "sandbox: true" in main
    assert "webSecurity: true" in main
    assert "setWindowOpenHandler(() => ({ action: \"deny\" }))" in main
    assert "will-navigate" in main
    assert "event.preventDefault()" in main
    assert "setPermissionRequestHandler" in main
    assert 'permission === "media"' in main


def test_electron_preload_exposes_no_shell_authority() -> None:
    preload = (ELECTRON_HUD / "preload.js").read_text(encoding="utf-8")

    assert "contextBridge.exposeInMainWorld" in preload
    assert "shellAuthority: false" in preload
    assert "child_process" not in preload
    assert "exec(" not in preload
    assert "spawn(" not in preload

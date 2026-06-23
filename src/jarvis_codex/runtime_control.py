from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

DEFAULT_RUNTIME_HOST = "127.0.0.1"
DEFAULT_RUNTIME_PORT = 8765
DEFAULT_RUNTIME_URL = f"http://{DEFAULT_RUNTIME_HOST}:{DEFAULT_RUNTIME_PORT}"
RUNTIME_PID_FILE = "jarvis-runtime.pid"
RUNTIME_LOG_FILE = "jarvis-runtime.log"


@dataclass(frozen=True)
class RuntimeStatus:
    status: str
    url: str
    healthy: bool
    pid: int | None
    pid_file: str
    log_file: str
    duplicate_runtime_started: bool = False
    message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def runtime_status(state_dir: Path, host: str = DEFAULT_RUNTIME_HOST, port: int = DEFAULT_RUNTIME_PORT, timeout: float = 0.5) -> RuntimeStatus:
    url = f"http://{host}:{port}"
    pid_file = _pid_file(state_dir)
    log_file = _log_file(state_dir)
    pid = _read_pid(pid_file)
    healthy = _healthcheck(url, timeout=timeout)
    if healthy:
        status = "running"
        message = "Jarvis runtime is reachable on loopback."
    elif pid and _pid_is_running(pid):
        status = "starting"
        message = "Jarvis runtime process exists but health is not ready yet."
    else:
        status = "stopped"
        message = "Jarvis runtime is not reachable."
        if pid_file.exists():
            _remove_stale_pid(pid_file)
            pid = None
    return RuntimeStatus(status=status, url=url, healthy=healthy, pid=pid, pid_file=str(pid_file), log_file=str(log_file), message=message)


def start_runtime(
    state_dir: Path,
    host: str = DEFAULT_RUNTIME_HOST,
    port: int = DEFAULT_RUNTIME_PORT,
    *,
    repo_root: Path | None = None,
    timeout: float = 5.0,
) -> RuntimeStatus:
    before = runtime_status(state_dir, host=host, port=port)
    if before.status in {"running", "starting"}:
        return RuntimeStatus(**{**before.to_dict(), "duplicate_runtime_started": False})

    state_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir = state_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    log_file = _log_file(state_dir)
    pid_file = _pid_file(state_dir)
    command = [
        sys.executable,
        "-m",
        "jarvis_codex.cli",
        "--state",
        str(state_dir),
        "runtime",
        "serve",
        "--host",
        host,
        "--port",
        str(port),
    ]
    env = os.environ.copy()
    if repo_root:
        env["PYTHONPATH"] = _with_src_on_pythonpath(repo_root, env.get("PYTHONPATH"))
    with log_file.open("ab") as log:
        process = subprocess.Popen(
            command,
            cwd=str(repo_root) if repo_root else None,
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )
    pid_file.write_text(str(process.pid), encoding="utf-8")

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        current = runtime_status(state_dir, host=host, port=port, timeout=0.5)
        if current.healthy:
            return RuntimeStatus(**{**current.to_dict(), "duplicate_runtime_started": False})
        if process.poll() is not None:
            break
        time.sleep(0.2)

    current = runtime_status(state_dir, host=host, port=port, timeout=0.5)
    return RuntimeStatus(**{**current.to_dict(), "duplicate_runtime_started": False})


def stop_runtime(state_dir: Path, host: str = DEFAULT_RUNTIME_HOST, port: int = DEFAULT_RUNTIME_PORT) -> RuntimeStatus:
    status = runtime_status(state_dir, host=host, port=port)
    pid = status.pid
    if not pid:
        return status
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        _remove_stale_pid(Path(status.pid_file))
        return runtime_status(state_dir, host=host, port=port)
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline and _pid_is_running(pid):
        time.sleep(0.1)
    if not _pid_is_running(pid):
        _remove_stale_pid(Path(status.pid_file))
    return runtime_status(state_dir, host=host, port=port)


def install_wsl_shim(repo_root: Path, target: Path | None = None) -> Path:
    target_path = target or Path.home() / ".local" / "bin" / "jarvis"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    script = f"""#!/usr/bin/env bash
set -euo pipefail
REPO="${{JARVIS_REPO:-{repo_root}}}"
cd "$REPO"
if command -v uv >/dev/null 2>&1; then
  exec uv run jarvis "$@"
fi
PYTHONPATH="$REPO/src${{PYTHONPATH:+:$PYTHONPATH}}" exec python3 -m jarvis_codex.cli "$@"
"""
    target_path.write_text(script, encoding="utf-8")
    target_path.chmod(0o755)
    return target_path


def launch_windows_ui(repo_root: Path, runtime_url: str = DEFAULT_RUNTIME_URL) -> dict[str, object]:
    powershell = _which("powershell.exe")
    if not powershell:
        return {"status": "unavailable", "reason": "powershell.exe not found from WSL PATH", "launched": False}
    candidates = [
        repo_root / "tools" / "electron-hud" / "dist" / "win-unpacked" / "Jarvis Codex.exe",
        repo_root / "tools" / "electron-hud" / "dist" / "Jarvis Codex.exe",
    ]
    candidates.extend(sorted((repo_root / "tools" / "electron-hud" / "dist").glob("Jarvis Codex*.exe")))
    executable = next((path for path in candidates if path.is_file()), None)
    if not executable:
        return {
            "status": "missing-electron-app",
            "reason": "Windows portable Electron app has not been built yet.",
            "expected_paths": [str(path) for path in candidates[:2]],
            "launched": False,
        }
    windows_exe = _wslpath_windows(executable)
    script = f"$env:JARVIS_RUNTIME_URL = '{runtime_url}'; Start-Process -FilePath '{windows_exe}'"
    subprocess.Popen([powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], stdin=subprocess.DEVNULL)
    return {"status": "launched", "path": str(executable), "runtime_url": runtime_url, "launched": True}


def write_json(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def _healthcheck(url: str, timeout: float) -> bool:
    try:
        with urlopen(f"{url}/health", timeout=timeout) as response:
            return response.status == 200
    except (OSError, URLError, ValueError):
        return False


def _pid_file(state_dir: Path) -> Path:
    return state_dir / "runtime" / RUNTIME_PID_FILE


def _log_file(state_dir: Path) -> Path:
    return state_dir / "runtime" / RUNTIME_LOG_FILE


def _read_pid(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _remove_stale_pid(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _with_src_on_pythonpath(repo_root: Path, current: str | None) -> str:
    src = str(repo_root / "src")
    if not current:
        return src
    return f"{src}:{current}"


def _which(name: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / name
        if candidate.exists():
            return str(candidate)
    return None


def _wslpath_windows(path: Path) -> str:
    try:
        return subprocess.check_output(["wslpath", "-w", str(path)], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return str(path)

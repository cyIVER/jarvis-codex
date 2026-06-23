from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path


DEFAULT_RECORD_SECONDS = 8


class VoiceMicError(ValueError):
    pass


@dataclass(frozen=True)
class RecorderDiscovery:
    status: str
    command: str | None
    source: str | None
    message: str

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "command": self.command,
            "source": self.source,
            "message": self.message,
            "microphone_accessed": False,
            "audio_processed": False,
            "execution_authority": False,
        }


@dataclass(frozen=True)
class MicrophoneRecording:
    audio_file: Path
    recorder_command: str
    seconds: int
    returncode: int

    def to_dict(self) -> dict[str, object]:
        return {
            "audio_file": str(self.audio_file),
            "recorder_command": self.recorder_command,
            "seconds": self.seconds,
            "returncode": self.returncode,
            "microphone_accessed": True,
            "audio_processed": False,
            "execution_authority": False,
        }


def discover_recorder_command(record_command: str | None = None, env: dict[str, str] | None = None) -> RecorderDiscovery:
    """Find the configured foreground mic recorder adapter without recording."""
    environment = env if env is not None else os.environ
    configured = (record_command or environment.get("JARVIS_RECORD_COMMAND") or "").strip()
    if configured:
        command, error = _split_command(configured)
        if error:
            return RecorderDiscovery("NEEDS_SETUP", configured, "argument", f"invalid recorder command: {error}")
        resolved = _resolve_command(command)
        if resolved:
            return RecorderDiscovery("READY", configured, "argument", "configured recorder command is available")
        return RecorderDiscovery("NEEDS_SETUP", configured, "argument", "configured recorder command executable was not found")

    for candidate in ["jarvis-mic-recorder.exe", "jarvis-mic-recorder", "ffmpeg.exe", "ffmpeg"]:
        resolved = shutil.which(candidate)
        if resolved:
            message = (
                "recorder binary was found, but Jarvis still needs an adapter command that accepts "
                "--output-file and --seconds"
            )
            return RecorderDiscovery("ADAPTER_REQUIRED", resolved, "path", message)
    return RecorderDiscovery(
        "NEEDS_SETUP",
        None,
        None,
        "set JARVIS_RECORD_COMMAND or pass --record-command; the adapter must accept --output-file and --seconds",
    )


def record_microphone_once(
    *,
    state_dir: Path,
    record_command: str,
    seconds: int = DEFAULT_RECORD_SECONDS,
    timeout_seconds: int | None = None,
) -> MicrophoneRecording:
    if seconds < 1 or seconds > 300:
        raise VoiceMicError("recording seconds must be between 1 and 300")
    command, error = _split_command(record_command)
    if error:
        raise VoiceMicError(f"invalid recorder command: {error}")
    if not command:
        raise VoiceMicError("recorder command is required")
    if _resolve_command(command) is None:
        raise VoiceMicError(f"recorder command not found: {command[0]}")

    output = state_dir / "runtime" / "audio" / "cli-mic" / f"mic_{uuid.uuid4().hex[:16]}.wav"
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            [*command, "--output-file", str(output), "--seconds", str(seconds)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds or seconds + 30,
            check=False,
        )
    except FileNotFoundError as exc:
        raise VoiceMicError(f"recorder command not found: {exc.filename}") from exc
    except subprocess.TimeoutExpired as exc:
        raise VoiceMicError(f"recorder command timed out after {timeout_seconds or seconds + 30} seconds") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise VoiceMicError(f"recorder command failed with {result.returncode}: {stderr}") from None
    if not output.is_file() or output.stat().st_size == 0:
        raise VoiceMicError("recorder command did not write audio output")
    return MicrophoneRecording(audio_file=output.resolve(), recorder_command=record_command, seconds=seconds, returncode=0)


def _split_command(command_text: str) -> tuple[list[str], str | None]:
    try:
        return shlex.split(command_text), None
    except ValueError as exc:
        return [], str(exc)


def _resolve_command(command: list[str]) -> str | None:
    if not command:
        return None
    executable = command[0]
    if "/" in executable or "\\" in executable:
        path = Path(executable).expanduser()
        return str(path.resolve()) if path.exists() else None
    return shutil.which(executable)

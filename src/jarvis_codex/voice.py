from __future__ import annotations

import shlex
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Any

from .state import JarvisState


def _resolve_command(command: list[str]) -> str | None:
    if not command:
        return None
    executable = command[0]
    if "/" in executable:
        path = Path(executable).expanduser().resolve()
        return str(path) if path.exists() else None
    return shutil.which(executable)


def _split_command(command_text: str) -> tuple[list[str], str | None]:
    try:
        return shlex.split(command_text), None
    except ValueError as exc:
        return [], str(exc)


def _wav_metadata(audio: Path) -> dict[str, Any]:
    try:
        with wave.open(str(audio), "rb") as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            sample_width = wav.getsampwidth()
            return {
                "format": "wav",
                "channels": wav.getnchannels(),
                "sample_rate_hz": rate,
                "sample_width_bytes": sample_width,
                "duration_seconds": round(frames / rate, 3) if rate else 0,
                "whisper_cpp_compatible": sample_width == 2,
            }
    except (wave.Error, EOFError):
        return {
            "format": "unknown",
            "whisper_cpp_compatible": False,
            "error": "audio file is not a readable WAV file",
        }


def probe_audio_file(audio_path: Path, model_path: Path, stt_command: str) -> dict[str, Any]:
    """Inspect local STT inputs without running audio processing or writing state."""
    audio = audio_path.resolve()
    model = model_path.resolve()
    command, split_error = _split_command(stt_command)
    command_path = _resolve_command(command)
    audio_info = _wav_metadata(audio) if audio.is_file() else {}
    checks = [
        {"name": "audio_file_exists", "status": "pass" if audio.is_file() else "fail", "path": str(audio)},
        {"name": "model_file_exists", "status": "pass" if model.is_file() else "fail", "path": str(model)},
        {
            "name": "stt_command_resolves",
            "status": "pass" if command_path and not split_error else "fail",
            "command": command[0] if command else "",
            "resolved": command_path or "",
            "error": split_error or "",
        },
        {
            "name": "audio_is_readable_16bit_wav",
            "status": "pass" if audio_info.get("whisper_cpp_compatible") else "fail",
            "note": audio_info.get("error", "16-bit WAV input is compatible with whisper.cpp"),
        },
    ]
    failures = [check for check in checks if check["status"] != "pass"]
    return {
        "status": "PASS" if not failures else "FAIL",
        "source": "voice-audio-probe",
        "audio_file": str(audio),
        "model": str(model),
        "stt_command": stt_command,
        "stt_command_resolved": command_path,
        "audio": audio_info,
        "checks": checks,
        "failures": len(failures),
        "execution_authority": False,
        "runtime_started": False,
        "audio_processed": False,
        "external_services": False,
        "model_downloaded": False,
        "writes_state": False,
    }


def ingest_transcript_file(state: JarvisState, transcript_path: Path) -> dict[str, Any]:
    """Capture a text transcript as a voice-origin episode without audio/runtime work."""
    path = transcript_path.resolve()
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("transcript file cannot be empty")

    episode = state.capture_episode(text, source="voice-transcript-file")
    return {
        "captured": episode.id,
        "source": episode.source,
        "transcript_path": str(path),
        "characters": len(text),
        "execution_authority": False,
        "runtime_started": False,
        "audio_processed": False,
        "external_services": False,
    }


def ingest_audio_file(
    state: JarvisState,
    audio_path: Path,
    model_path: Path,
    stt_command: str,
    allow_audio_processing: bool,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """Transcribe a local audio file through an explicit local STT adapter."""
    audio = audio_path.resolve()
    model = model_path.resolve()

    base = {
        "source": "voice-audio-file",
        "audio_file": str(audio),
        "model": str(model),
        "execution_authority": False,
        "runtime_started": False,
        "audio_processed": False,
        "external_services": False,
        "model_downloaded": False,
    }

    if not allow_audio_processing:
        return {
            **base,
            "status": "approval-required",
            "approval_required": "audio-processing",
            "message": "Audio transcription requires explicit --allow-audio-processing approval for this command.",
        }
    command, split_error = _split_command(stt_command)
    if split_error:
        return {**base, "status": "failed", "error": f"invalid stt command: {split_error}"}
    if not command:
        return {**base, "status": "failed", "error": "stt command is required"}
    if not audio.is_file():
        return {**base, "status": "failed", "error": f"audio file not found: {audio}"}
    if not model.is_file():
        return {**base, "status": "failed", "error": f"model file not found: {model}"}

    try:
        result = subprocess.run(
            [*command, "--audio-file", str(audio), "--model", str(model)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        return {**base, "status": "failed", "error": f"stt adapter not found: {exc.filename}"}
    except subprocess.TimeoutExpired:
        return {
            **base,
            "status": "failed",
            "runtime_started": True,
            "audio_processed": True,
            "error": f"stt adapter timed out after {timeout_seconds} seconds",
        }
    if result.returncode != 0:
        return {
            **base,
            "status": "failed",
            "runtime_started": True,
            "audio_processed": True,
            "returncode": result.returncode,
            "stderr": result.stderr.strip(),
        }

    transcript = result.stdout.strip()
    if not transcript:
        return {
            **base,
            "status": "failed",
            "runtime_started": True,
            "audio_processed": True,
            "returncode": 0,
            "error": "stt adapter returned an empty transcript",
        }

    episode = state.capture_episode(transcript, source="voice-audio-file")
    return {
        **base,
        "status": "captured",
        "captured": episode.id,
        "runtime_started": True,
        "audio_processed": True,
        "characters": len(transcript),
        "returncode": 0,
    }

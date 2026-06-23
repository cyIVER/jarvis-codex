from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Any

from .state import JarvisState


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
    command = shlex.split(stt_command)

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

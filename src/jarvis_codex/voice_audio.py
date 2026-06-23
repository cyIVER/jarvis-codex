from __future__ import annotations

import base64
import binascii
import re
import shlex
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path


MAX_AUDIO_CHUNK_BYTES = 2 * 1024 * 1024
SAFE_MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,80}$")


@dataclass(frozen=True)
class VoiceAudioChunkResult:
    session_id: str
    utterance_id: str
    sequence: int
    mime_type: str
    path: Path
    bytes_written: int
    final: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "utterance_id": self.utterance_id,
            "sequence": self.sequence,
            "mime_type": self.mime_type,
            "path": str(self.path),
            "bytes_written": self.bytes_written,
            "final": self.final,
            "execution_authority": False,
            "audio_processed": False,
        }


class VoiceAudioError(ValueError):
    pass


@dataclass(frozen=True)
class LocalSttResult:
    transcript: str
    audio_file: Path
    model_path: Path
    command: str
    returncode: int

    def to_dict(self) -> dict[str, object]:
        return {
            "transcript": self.transcript,
            "audio_file": str(self.audio_file),
            "model_path": str(self.model_path),
            "command": self.command,
            "returncode": self.returncode,
            "audio_processed": True,
            "external_services": False,
            "execution_authority": False,
        }


@dataclass(frozen=True)
class LocalTtsResult:
    text: str
    audio_file: Path
    command: str
    returncode: int

    def to_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "audio_file": str(self.audio_file),
            "command": self.command,
            "returncode": self.returncode,
            "audio_processed": True,
            "external_services": False,
            "execution_authority": False,
        }


class VoiceAudioBuffer:
    def __init__(self, state_dir: Path) -> None:
        self.root = state_dir / "runtime" / "audio"
        self.model_root = state_dir / "runtime" / "models"

    def append_chunk(
        self,
        *,
        session_id: str,
        chunk_b64: str,
        utterance_id: str | None = None,
        sequence: int = 0,
        mime_type: str = "audio/webm",
        final: bool = False,
    ) -> VoiceAudioChunkResult:
        if sequence < 0:
            raise VoiceAudioError("audio chunk sequence must be non-negative")
        if not chunk_b64.strip():
            raise VoiceAudioError("audio chunk payload is required")
        try:
            chunk = base64.b64decode(chunk_b64, validate=True)
        except binascii.Error as exc:
            raise VoiceAudioError("audio chunk payload must be base64") from exc
        if len(chunk) > MAX_AUDIO_CHUNK_BYTES:
            raise VoiceAudioError("audio chunk is too large")

        safe_session = _safe_name(session_id or "hud")
        safe_utterance = _safe_name(utterance_id or f"utt_{uuid.uuid4().hex[:16]}")
        path = self.root / safe_session / f"{safe_utterance}{_extension_for_mime(mime_type)}"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as handle:
            handle.write(chunk)
        return VoiceAudioChunkResult(
            session_id=session_id or "hud",
            utterance_id=safe_utterance,
            sequence=sequence,
            mime_type=mime_type,
            path=path,
            bytes_written=len(chunk),
            final=final,
        )

    def tts_output_path(self, *, session_id: str, suffix: str = ".wav") -> Path:
        safe_session = _safe_name(session_id or "hud")
        safe_suffix = suffix if suffix.startswith(".") and re.fullmatch(r"\.[A-Za-z0-9]+", suffix) else ".wav"
        return self.root / safe_session / f"tts_{uuid.uuid4().hex[:16]}{safe_suffix}"


def resolve_local_stt_model(model_root: Path, model_id: str) -> Path:
    """Resolve an identifier-only ggml model name under a server-owned root."""
    candidate = model_id.strip()
    if not candidate or not SAFE_MODEL_ID.fullmatch(candidate) or ".." in candidate:
        raise VoiceAudioError("model_id must be a safe ggml model identifier")
    filename = candidate if candidate.startswith("ggml-") and candidate.endswith(".bin") else f"ggml-{candidate}.bin"
    resolved_root = model_root.expanduser().resolve()
    resolved = (resolved_root / filename).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise VoiceAudioError("model_id resolved outside the local STT model directory") from exc
    if not resolved.is_file():
        raise VoiceAudioError(f"local STT model not found for model_id: {candidate}")
    return resolved


def _safe_name(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return safe[:96] or "unnamed"


def _extension_for_mime(mime_type: str) -> str:
    lowered = mime_type.lower()
    if "wav" in lowered:
        return ".wav"
    if "ogg" in lowered:
        return ".ogg"
    if "mp4" in lowered:
        return ".mp4"
    return ".webm"


def transcribe_with_local_adapter(
    *,
    audio_file: Path,
    model_path: Path,
    stt_command: str,
    timeout_seconds: int = 120,
) -> LocalSttResult:
    audio = audio_file.resolve()
    model = model_path.resolve()
    if not audio.is_file():
        raise VoiceAudioError(f"audio file not found: {audio}")
    if not model.is_file():
        raise VoiceAudioError(f"model file not found: {model}")
    try:
        command = shlex.split(stt_command)
    except ValueError as exc:
        raise VoiceAudioError(f"invalid stt command: {exc}") from exc
    if not command:
        raise VoiceAudioError("stt command is required")

    try:
        result = subprocess.run(
            [*command, "--audio-file", str(audio), "--model", str(model)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise VoiceAudioError(f"stt adapter not found: {exc.filename}") from exc
    except subprocess.TimeoutExpired as exc:
        raise VoiceAudioError(f"stt adapter timed out after {timeout_seconds} seconds") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise VoiceAudioError(f"stt adapter failed with {result.returncode}: {stderr}")
    transcript = result.stdout.strip()
    if not transcript:
        raise VoiceAudioError("stt adapter returned an empty transcript")
    return LocalSttResult(
        transcript=transcript,
        audio_file=audio,
        model_path=model,
        command=stt_command,
        returncode=result.returncode,
    )


def synthesize_with_local_adapter(
    *,
    text: str,
    output_file: Path,
    tts_command: str,
    timeout_seconds: int = 120,
) -> LocalTtsResult:
    speech_text = text.strip()
    if not speech_text:
        raise VoiceAudioError("tts text is required")
    output = output_file.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        command = shlex.split(tts_command)
    except ValueError as exc:
        raise VoiceAudioError(f"invalid tts command: {exc}") from exc
    if not command:
        raise VoiceAudioError("tts command is required")

    try:
        result = subprocess.run(
            [*command, "--output-file", str(output)],
            input=speech_text,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise VoiceAudioError(f"tts adapter not found: {exc.filename}") from exc
    except subprocess.TimeoutExpired as exc:
        raise VoiceAudioError(f"tts adapter timed out after {timeout_seconds} seconds") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise VoiceAudioError(f"tts adapter failed with {result.returncode}: {stderr}")
    if not output.is_file() or output.stat().st_size == 0:
        raise VoiceAudioError("tts adapter did not write audio output")
    return LocalTtsResult(
        text=speech_text,
        audio_file=output,
        command=tts_command,
        returncode=result.returncode,
    )

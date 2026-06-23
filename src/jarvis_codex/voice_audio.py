from __future__ import annotations

import base64
import binascii
import re
import uuid
from dataclasses import dataclass
from pathlib import Path


MAX_AUDIO_CHUNK_BYTES = 2 * 1024 * 1024


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


class VoiceAudioBuffer:
    def __init__(self, state_dir: Path) -> None:
        self.root = state_dir / "runtime" / "audio"

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

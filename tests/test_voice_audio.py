import base64

import pytest

from jarvis_codex.voice_audio import VoiceAudioBuffer, VoiceAudioError


def test_voice_audio_buffer_appends_base64_chunks(tmp_path):
    buffer = VoiceAudioBuffer(tmp_path / "state")
    first = base64.b64encode(b"audio-").decode("ascii")
    second = base64.b64encode(b"chunk").decode("ascii")

    result1 = buffer.append_chunk(session_id="session/voice", utterance_id="utt-1", sequence=0, chunk_b64=first)
    result2 = buffer.append_chunk(
        session_id="session/voice",
        utterance_id="utt-1",
        sequence=1,
        chunk_b64=second,
        final=True,
    )

    assert result1.path == result2.path
    assert result2.final is True
    assert result2.path.read_bytes() == b"audio-chunk"
    assert "session_voice" in str(result2.path)
    assert result2.to_dict()["audio_processed"] is False


def test_voice_audio_buffer_rejects_invalid_chunks(tmp_path):
    buffer = VoiceAudioBuffer(tmp_path / "state")

    with pytest.raises(VoiceAudioError):
        buffer.append_chunk(session_id="s", sequence=-1, chunk_b64="abc")
    with pytest.raises(VoiceAudioError):
        buffer.append_chunk(session_id="s", chunk_b64="")
    with pytest.raises(VoiceAudioError):
        buffer.append_chunk(session_id="s", chunk_b64="not base64!")

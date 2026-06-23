import base64
import sys

import pytest

from jarvis_codex.voice_audio import (
    VoiceAudioBuffer,
    VoiceAudioError,
    synthesize_with_local_adapter,
    transcribe_with_local_adapter,
)


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


def test_transcribe_with_local_adapter_invokes_command_without_shell(tmp_path):
    audio = tmp_path / "sample.webm"
    model = tmp_path / "model.bin"
    adapter = tmp_path / "fake_stt.py"
    audio.write_bytes(b"audio")
    model.write_bytes(b"model")
    adapter.write_text(
        "import argparse\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--audio-file')\n"
        "parser.add_argument('--model')\n"
        "args = parser.parse_args()\n"
        "print('turn on the jarvis microphone')\n",
        encoding="utf-8",
    )

    result = transcribe_with_local_adapter(
        audio_file=audio,
        model_path=model,
        stt_command=f"{sys.executable} {adapter}",
        timeout_seconds=5,
    )

    assert result.transcript == "turn on the jarvis microphone"
    assert result.audio_file == audio.resolve()
    assert result.model_path == model.resolve()
    assert result.to_dict()["audio_processed"] is True
    assert result.to_dict()["external_services"] is False
    assert result.to_dict()["execution_authority"] is False


def test_transcribe_with_local_adapter_rejects_missing_inputs(tmp_path):
    audio = tmp_path / "missing.webm"
    model = tmp_path / "model.bin"
    model.write_bytes(b"model")

    with pytest.raises(VoiceAudioError, match="audio file not found"):
        transcribe_with_local_adapter(
            audio_file=audio,
            model_path=model,
            stt_command=f"{sys.executable} -c 'print(1)'",
        )

    audio.write_bytes(b"audio")
    with pytest.raises(VoiceAudioError, match="model file not found"):
        transcribe_with_local_adapter(
            audio_file=audio,
            model_path=tmp_path / "missing-model.bin",
            stt_command=f"{sys.executable} -c 'print(1)'",
        )


def test_transcribe_with_local_adapter_surfaces_adapter_failures(tmp_path):
    audio = tmp_path / "sample.webm"
    model = tmp_path / "model.bin"
    adapter = tmp_path / "failing_stt.py"
    audio.write_bytes(b"audio")
    model.write_bytes(b"model")
    adapter.write_text("import sys\nprint('failed', file=sys.stderr)\nsys.exit(17)\n", encoding="utf-8")

    with pytest.raises(VoiceAudioError, match="stt adapter failed with 17"):
        transcribe_with_local_adapter(
            audio_file=audio,
            model_path=model,
            stt_command=f"{sys.executable} {adapter}",
            timeout_seconds=5,
        )


def test_synthesize_with_local_adapter_invokes_command_without_shell(tmp_path):
    output = tmp_path / "speech.wav"
    adapter = tmp_path / "fake_tts.py"
    adapter.write_text(
        "import argparse, pathlib, sys\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--output-file')\n"
        "args = parser.parse_args()\n"
        "text = sys.stdin.read()\n"
        "pathlib.Path(args.output_file).write_bytes(('audio:' + text).encode())\n",
        encoding="utf-8",
    )

    result = synthesize_with_local_adapter(
        text="Systems are online.",
        output_file=output,
        tts_command=f"{sys.executable} {adapter}",
        timeout_seconds=5,
    )

    assert output.read_bytes() == b"audio:Systems are online."
    assert result.text == "Systems are online."
    assert result.audio_file == output.resolve()
    assert result.to_dict()["audio_processed"] is True
    assert result.to_dict()["external_services"] is False
    assert result.to_dict()["execution_authority"] is False


def test_synthesize_with_local_adapter_rejects_missing_output(tmp_path):
    output = tmp_path / "missing.wav"
    adapter = tmp_path / "empty_tts.py"
    adapter.write_text("pass\n", encoding="utf-8")

    with pytest.raises(VoiceAudioError, match="did not write audio output"):
        synthesize_with_local_adapter(
            text="say this",
            output_file=output,
            tts_command=f"{sys.executable} {adapter}",
            timeout_seconds=5,
        )


def test_synthesize_with_local_adapter_surfaces_adapter_failures(tmp_path):
    output = tmp_path / "speech.wav"
    adapter = tmp_path / "failing_tts.py"
    adapter.write_text("import sys\nprint('failed', file=sys.stderr)\nsys.exit(23)\n", encoding="utf-8")

    with pytest.raises(VoiceAudioError, match="tts adapter failed with 23"):
        synthesize_with_local_adapter(
            text="say this",
            output_file=output,
            tts_command=f"{sys.executable} {adapter}",
            timeout_seconds=5,
        )

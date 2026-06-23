from __future__ import annotations

import json
import sys
import wave

import pytest

from jarvis_codex.state import JarvisState
from jarvis_codex.voice import ingest_audio_file, ingest_transcript_file, probe_audio_file


def write_wav(path, sample_width=2):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(sample_width)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 160)


def test_ingest_transcript_file_captures_voice_origin_episode(tmp_path):
    state = JarvisState(tmp_path / "state")
    transcript = tmp_path / "transcript.txt"
    transcript.write_text("Capture this spoken idea for Codex.\n", encoding="utf-8")

    result = ingest_transcript_file(state, transcript)

    assert result["captured"].startswith("ep_")
    assert result["source"] == "voice-transcript-file"
    assert result["execution_authority"] is False
    assert result["runtime_started"] is False
    assert result["audio_processed"] is False
    assert result["external_services"] is False
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in (tmp_path / "state/inbox").glob("*.json")]
    assert rows[0]["text"] == "Capture this spoken idea for Codex."
    assert rows[0]["source"] == "voice-transcript-file"


def test_ingest_transcript_file_rejects_empty_transcript(tmp_path):
    state = JarvisState(tmp_path / "state")
    transcript = tmp_path / "empty.txt"
    transcript.write_text("  \n", encoding="utf-8")

    with pytest.raises(ValueError, match="transcript file cannot be empty"):
        ingest_transcript_file(state, transcript)

    assert not (tmp_path / "state").exists()


def test_ingest_audio_file_requires_explicit_audio_processing_approval(tmp_path):
    state = JarvisState(tmp_path / "state")
    audio = tmp_path / "sample.wav"
    model = tmp_path / "model.bin"
    audio.write_bytes(b"fake audio")
    model.write_bytes(b"fake model")

    result = ingest_audio_file(state, audio, model, "fake-stt", allow_audio_processing=False)

    assert result["status"] == "approval-required"
    assert result["approval_required"] == "audio-processing"
    assert result["runtime_started"] is False
    assert result["audio_processed"] is False
    assert result["external_services"] is False
    assert not (tmp_path / "state").exists()


def test_ingest_audio_file_runs_explicit_local_adapter_and_captures_transcript(tmp_path):
    state = JarvisState(tmp_path / "state")
    audio = tmp_path / "sample.wav"
    model = tmp_path / "model.bin"
    adapter = tmp_path / "fake_stt.py"
    audio.write_bytes(b"fake audio")
    model.write_bytes(b"fake model")
    adapter.write_text(
        "\n".join(
            [
                "import argparse",
                "parser = argparse.ArgumentParser()",
                "parser.add_argument('--audio-file', required=True)",
                "parser.add_argument('--model', required=True)",
                "args = parser.parse_args()",
                "print('Transcribed local audio for Jarvis.')",
            ]
        ),
        encoding="utf-8",
    )

    result = ingest_audio_file(
        state,
        audio,
        model,
        f"{sys.executable} {adapter}",
        allow_audio_processing=True,
    )

    assert result["status"] == "captured"
    assert result["captured"].startswith("ep_")
    assert result["source"] == "voice-audio-file"
    assert result["runtime_started"] is True
    assert result["audio_processed"] is True
    assert result["external_services"] is False
    assert result["model_downloaded"] is False
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in (tmp_path / "state/inbox").glob("*.json")]
    assert rows[0]["text"] == "Transcribed local audio for Jarvis."
    assert rows[0]["source"] == "voice-audio-file"


def test_ingest_audio_file_reports_adapter_failure_without_capture(tmp_path):
    state = JarvisState(tmp_path / "state")
    audio = tmp_path / "sample.wav"
    model = tmp_path / "model.bin"
    adapter = tmp_path / "fake_stt_fail.py"
    audio.write_bytes(b"fake audio")
    model.write_bytes(b"fake model")
    adapter.write_text("import sys\nprint('nope', file=sys.stderr)\nsys.exit(7)\n", encoding="utf-8")

    result = ingest_audio_file(
        state,
        audio,
        model,
        f"{sys.executable} {adapter}",
        allow_audio_processing=True,
    )

    assert result["status"] == "failed"
    assert result["returncode"] == 7
    assert result["runtime_started"] is True
    assert result["audio_processed"] is True
    assert result["external_services"] is False
    assert not (tmp_path / "state").exists()


def test_probe_audio_file_reports_ready_without_runtime_or_state(tmp_path):
    state_dir = tmp_path / "state"
    audio = tmp_path / "sample.wav"
    model = tmp_path / "ggml-base.en.bin"
    write_wav(audio)
    model.write_bytes(b"model")

    result = probe_audio_file(audio, model, sys.executable)

    assert result["status"] == "PASS"
    assert result["source"] == "voice-audio-probe"
    assert result["runtime_started"] is False
    assert result["audio_processed"] is False
    assert result["external_services"] is False
    assert result["model_downloaded"] is False
    assert result["writes_state"] is False
    assert result["audio"]["whisper_cpp_compatible"] is True
    assert not state_dir.exists()


def test_probe_audio_file_fails_missing_model_and_bad_wav_without_runtime(tmp_path):
    audio = tmp_path / "sample.wav"
    audio.write_bytes(b"not a wav")

    result = probe_audio_file(audio, tmp_path / "missing.bin", "missing-stt-command")

    assert result["status"] == "FAIL"
    assert result["failures"] == 3
    assert result["runtime_started"] is False
    assert result["audio_processed"] is False
    assert result["audio"]["whisper_cpp_compatible"] is False


def test_ingest_audio_file_reports_invalid_stt_command_without_runtime(tmp_path):
    state = JarvisState(tmp_path / "state")
    audio = tmp_path / "sample.wav"
    model = tmp_path / "ggml-base.en.bin"
    write_wav(audio)
    model.write_bytes(b"model")

    result = ingest_audio_file(state, audio, model, '"unterminated', allow_audio_processing=True)

    assert result["status"] == "failed"
    assert "invalid stt command" in result["error"]
    assert result["runtime_started"] is False
    assert result["audio_processed"] is False
    assert not (tmp_path / "state").exists()

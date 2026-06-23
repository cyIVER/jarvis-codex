from __future__ import annotations

import json
import sys

import pytest

from jarvis_codex.state import JarvisState
from jarvis_codex.voice import ingest_audio_file, ingest_transcript_file


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

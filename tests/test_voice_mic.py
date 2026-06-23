from __future__ import annotations

import sys

import pytest

from jarvis_codex.voice_mic import VoiceMicError, discover_recorder_command, record_microphone_once


def test_discover_recorder_command_reports_configured_adapter(tmp_path):
    recorder = tmp_path / "fake_recorder.py"
    recorder.write_text("pass\n", encoding="utf-8")

    result = discover_recorder_command(f"{sys.executable} {recorder}")

    assert result.status == "READY"
    assert result.command == f"{sys.executable} {recorder}"
    assert result.to_dict()["microphone_accessed"] is False
    assert result.to_dict()["audio_processed"] is False


def test_record_microphone_once_invokes_adapter_without_shell(tmp_path):
    recorder = tmp_path / "fake_recorder.py"
    recorder.write_text(
        "import argparse, pathlib\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--output-file', required=True)\n"
        "parser.add_argument('--seconds', required=True)\n"
        "args = parser.parse_args()\n"
        "pathlib.Path(args.output_file).write_bytes(b'wav')\n",
        encoding="utf-8",
    )

    result = record_microphone_once(
        state_dir=tmp_path / "state",
        record_command=f"{sys.executable} {recorder}",
        seconds=1,
        timeout_seconds=5,
    )

    assert result.audio_file.is_file()
    assert result.audio_file.read_bytes() == b"wav"
    assert result.to_dict()["microphone_accessed"] is True
    assert result.to_dict()["audio_processed"] is False


def test_record_microphone_once_rejects_missing_adapter(tmp_path):
    with pytest.raises(VoiceMicError, match="recorder command not found"):
        record_microphone_once(state_dir=tmp_path / "state", record_command="missing-jarvis-recorder", seconds=1)


def test_record_microphone_once_rejects_bad_duration(tmp_path):
    with pytest.raises(VoiceMicError, match="between 1 and 300"):
        record_microphone_once(state_dir=tmp_path / "state", record_command=sys.executable, seconds=0)

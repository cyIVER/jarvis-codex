from __future__ import annotations

import subprocess
import sys
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts" / "whisper-cpp-stt-adapter.py"


def write_wav(path):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 160)


def test_whisper_cpp_adapter_runs_explicit_command_and_cleans_timestamps(tmp_path):
    audio = tmp_path / "sample.wav"
    model = tmp_path / "ggml-base.en.bin"
    fake = tmp_path / "fake_whisper.py"
    audio.write_bytes(b"audio")
    model.write_bytes(b"model")
    fake.write_text(
        "import argparse\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('-m', required=True)\n"
        "parser.add_argument('-f', required=True)\n"
        "parser.add_argument('-np', action='store_true')\n"
        "args = parser.parse_args()\n"
        "assert args.m.endswith('ggml-base.en.bin')\n"
        "assert args.f.endswith('sample.wav')\n"
        "assert args.np is True\n"
        "print('[00:00:00.000 --> 00:00:01.000] Hello Jarvis')\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ADAPTER),
            "--audio-file",
            str(audio),
            "--model",
            str(model),
            "--whisper-command",
            f"{sys.executable} {fake}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "Hello Jarvis"


def test_whisper_cpp_adapter_reports_missing_inputs(tmp_path):
    model = tmp_path / "ggml-base.en.bin"
    model.write_bytes(b"model")

    result = subprocess.run(
        [
            sys.executable,
            str(ADAPTER),
            "--audio-file",
            str(tmp_path / "missing.wav"),
            "--model",
            str(model),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "audio file not found" in result.stderr


def test_whisper_cpp_adapter_propagates_command_failure(tmp_path):
    audio = tmp_path / "sample.wav"
    model = tmp_path / "ggml-base.en.bin"
    fake = tmp_path / "fake_fail.py"
    audio.write_bytes(b"audio")
    model.write_bytes(b"model")
    fake.write_text("import sys\nprint('adapter failed', file=sys.stderr)\nsys.exit(9)\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ADAPTER),
            "--audio-file",
            str(audio),
            "--model",
            str(model),
            "--whisper-command",
            f"{sys.executable} {fake}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 9
    assert "adapter failed" in result.stderr


def test_whisper_cpp_adapter_check_only_reports_ready_without_transcription(tmp_path):
    audio = tmp_path / "sample.wav"
    model = tmp_path / "ggml-base.en.bin"
    fake = tmp_path / "fake_whisper.py"
    write_wav(audio)
    model.write_bytes(b"model")
    fake.write_text("raise SystemExit('should not run')\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ADAPTER),
            "--audio-file",
            str(audio),
            "--model",
            str(model),
            "--whisper-command",
            f"{sys.executable} {fake}",
            "--check-only",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert '"status": "PASS"' in result.stdout
    assert '"runtime_started": false' in result.stdout
    assert "should not run" not in result.stderr


def test_whisper_cpp_adapter_check_only_fails_missing_command_and_bad_audio(tmp_path):
    audio = tmp_path / "sample.wav"
    model = tmp_path / "ggml-base.en.bin"
    audio.write_bytes(b"not a wav")
    model.write_bytes(b"model")

    result = subprocess.run(
        [
            sys.executable,
            str(ADAPTER),
            "--audio-file",
            str(audio),
            "--model",
            str(model),
            "--whisper-command",
            "missing-whisper-command",
            "--check-only",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert '"status": "FAIL"' in result.stdout
    assert "audio file is not a readable WAV file" in result.stdout


def test_whisper_cpp_adapter_reports_invalid_whisper_command(tmp_path):
    audio = tmp_path / "sample.wav"
    model = tmp_path / "ggml-base.en.bin"
    write_wav(audio)
    model.write_bytes(b"model")

    result = subprocess.run(
        [
            sys.executable,
            str(ADAPTER),
            "--audio-file",
            str(audio),
            "--model",
            str(model),
            "--whisper-command",
            '"unterminated',
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "invalid whisper command" in result.stderr

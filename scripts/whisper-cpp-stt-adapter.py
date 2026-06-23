from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
import wave
from pathlib import Path


TIMESTAMP_LINE = re.compile(r"^\s*\[[0-9:.]+\s+-->\s+[0-9:.]+\]\s*")


def clean_whisper_stdout(text: str) -> str:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = TIMESTAMP_LINE.sub("", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines).strip()


def resolve_command(command: list[str]) -> str | None:
    if not command:
        return None
    executable = command[0]
    if "/" in executable:
        path = Path(executable).expanduser().resolve()
        return str(path) if path.exists() else None
    return shutil.which(executable)


def split_command(command_text: str) -> tuple[list[str], str | None]:
    try:
        return shlex.split(command_text), None
    except ValueError as exc:
        return [], str(exc)


def wav_metadata(audio: Path) -> dict[str, object]:
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


def check_readiness(audio: Path, model: Path, whisper_command: str) -> dict[str, object]:
    command, split_error = split_command(whisper_command)
    command_path = resolve_command(command)
    audio_info = wav_metadata(audio) if audio.is_file() else {}
    checks = [
        {"name": "audio_file_exists", "status": "pass" if audio.is_file() else "fail", "path": str(audio)},
        {"name": "model_file_exists", "status": "pass" if model.is_file() else "fail", "path": str(model)},
        {
            "name": "whisper_command_resolves",
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
        "checks": checks,
        "failures": len(failures),
        "audio": audio_info,
        "audio_file": str(audio),
        "model": str(model),
        "whisper_command": whisper_command,
        "whisper_command_resolved": command_path,
        "runtime_started": False,
        "audio_processed": False,
        "external_services": False,
        "model_downloaded": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Jarvis Codex whisper.cpp STT adapter")
    parser.add_argument("--audio-file", required=True, help="Path to 16-bit WAV audio input")
    parser.add_argument("--model", required=True, help="Path to a local ggml Whisper model")
    parser.add_argument("--whisper-command", default="whisper-cli", help="whisper.cpp command or path")
    parser.add_argument("--timeout-seconds", type=int, default=120, help="Adapter timeout")
    parser.add_argument("--check-only", action="store_true", help="Validate local inputs without running transcription")
    args = parser.parse_args()

    audio = Path(args.audio_file).resolve()
    model = Path(args.model).resolve()
    if args.check_only:
        readiness = check_readiness(audio, model, args.whisper_command)
        print(json.dumps(readiness, indent=2, sort_keys=True))
        return 0 if readiness["status"] == "PASS" else 1
    if not audio.is_file():
        print(f"audio file not found: {audio}", file=sys.stderr)
        return 2
    if not model.is_file():
        print(f"model file not found: {model}", file=sys.stderr)
        return 2

    whisper_command, split_error = split_command(args.whisper_command)
    if split_error:
        print(f"invalid whisper command: {split_error}", file=sys.stderr)
        return 2
    command = [*whisper_command, "-m", str(model), "-f", str(audio), "-np"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout_seconds, check=False)
    except FileNotFoundError as exc:
        print(f"whisper.cpp command not found: {exc.filename}", file=sys.stderr)
        return 127
    except subprocess.TimeoutExpired:
        print(f"whisper.cpp command timed out after {args.timeout_seconds} seconds", file=sys.stderr)
        return 124

    if result.returncode != 0:
        if result.stdout.strip():
            print(result.stdout.strip(), file=sys.stderr)
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        return result.returncode

    transcript = clean_whisper_stdout(result.stdout)
    if not transcript:
        print("whisper.cpp returned an empty transcript", file=sys.stderr)
        return 1
    print(transcript)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

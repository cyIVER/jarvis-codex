from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Jarvis Codex whisper.cpp STT adapter")
    parser.add_argument("--audio-file", required=True, help="Path to 16-bit WAV audio input")
    parser.add_argument("--model", required=True, help="Path to a local ggml Whisper model")
    parser.add_argument("--whisper-command", default="whisper-cli", help="whisper.cpp command or path")
    parser.add_argument("--timeout-seconds", type=int, default=120, help="Adapter timeout")
    args = parser.parse_args()

    audio = Path(args.audio_file).resolve()
    model = Path(args.model).resolve()
    if not audio.is_file():
        print(f"audio file not found: {audio}", file=sys.stderr)
        return 2
    if not model.is_file():
        print(f"model file not found: {model}", file=sys.stderr)
        return 2

    command = [*shlex.split(args.whisper_command), "-m", str(model), "-f", str(audio), "-np"]
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

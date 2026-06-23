# Jarvis Windows Mic Recorder

This is a Windows-side foreground microphone recorder for the Jarvis CLI voice path.

It implements the recorder adapter contract expected by:

```bash
jarvis-codex voice listen
```

The adapter contract is:

```powershell
JarvisMicRecorder.exe --output-file C:\path\mic.wav --seconds 8
```

The recorder writes one WAV file and exits. It does not transcribe audio, call cloud services, start a daemon, listen for a wake word, or grant execution authority.

## Build

Install the .NET SDK on Windows, then from PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\windows-mic\build.ps1
```

The build script publishes:

```text
tools\windows-mic\JarvisMicRecorder\bin\Release\net10.0-windows\win-x64\publish\JarvisMicRecorder.exe
```

The published `bin/` and `obj/` outputs are local setup artifacts and must stay uncommitted.

## WSL Bridge

From WSL, configure Jarvis to call the PowerShell wrapper:

```bash
export JARVIS_RECORD_COMMAND="powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/windows-mic/jarvis-record.ps1"
```

Then run:

```bash
uv run jarvis chat \
  --model /home/iveri/.cache/whisper.cpp/models/ggml-tiny.en.bin \
  --stt-command "python3 scripts/whisper-cpp-stt-adapter.py --whisper-command /home/iveri/.cache/whisper.cpp/bin/v1.9.1/whisper-cli" \
  --allow-microphone \
  --allow-audio-processing \
  --sandbox read-only \
  --approval-mode inline \
  --no-daemon-start
```

`jarvis chat` speaks the assistant response in chunks through `JARVIS_LOCAL_TTS_COMMAND` when configured, or through the local Windows Piper setup at `C:\Users\iveri\Apps\piper\say.ps1` when available. Terminal output is compact by default and focuses on commands, code, paths, approvals, errors, and status. Pass `--terminal-mode full` to print the full assistant text, or `--no-speak` to disable audio.

For conversational correction, add `--loop`. Press Ctrl+C while Jarvis is answering to cancel that answer and start the next recording window.

The wrapper converts WSL output paths to Windows paths before invoking the recorder executable.

## Safety Boundaries

- Foreground command only.
- No background listener.
- No wake word.
- No automatic transcript submission outside `voice listen`.
- No network calls.
- No cloud speech-to-text fallback.
- No command execution authority.
- The microphone is touched only after `voice listen --allow-microphone`.

# Voice Ingress

Jarvis Codex supports transcript ingestion and explicit local speech-to-text (STT) ingestion.

Run:

```bash
jarvis-codex voice ingest --transcript-file transcript.txt --json
```

This reads a UTF-8 text transcript and captures it as a normal Jarvis episode with source `voice-transcript-file`.

Before processing audio, check local STT readiness without writing state or running transcription:

```bash
jarvis-codex voice probe \
  --audio-file recording.wav \
  --model models/ggml-base.en.bin \
  --stt-command "python3 scripts/whisper-cpp-stt-adapter.py --whisper-command /path/to/whisper-cli" \
  --json
```

The probe verifies the audio path, model path, adapter command resolution, and 16-bit WAV compatibility. It returns `runtime_started: false`, `audio_processed: false`, and `writes_state: false`.

For audio files, use an explicit local STT adapter command:

```bash
jarvis-codex voice ingest \
  --audio-file recording.wav \
  --model models/ggml-base.en.bin \
  --stt-command "python3 scripts/whisper-cpp-stt-adapter.py --whisper-command /path/to/whisper-cli" \
  --allow-audio-processing \
  --json
```

The STT adapter command receives `--audio-file <path>` and `--model <path>`, prints the transcript to stdout, and exits. Jarvis captures stdout as a normal episode with source `voice-audio-file`.

The included `scripts/whisper-cpp-stt-adapter.py` wraps a local `whisper.cpp` `whisper-cli` executable. It expects a local ggml model file and audio in a format accepted by `whisper-cli`; upstream `whisper.cpp` documents 16-bit WAV as the baseline CLI input format.

The wrapper also supports readiness checks without transcription:

```bash
python3 scripts/whisper-cpp-stt-adapter.py \
  --audio-file recording.wav \
  --model models/ggml-base.en.bin \
  --whisper-command /path/to/whisper-cli \
  --check-only
```

## What It Does

- Reads one local text transcript file, or one explicit local audio file through an approved local STT adapter.
- Writes a captured episode under the configured Jarvis state directory.
- Returns JSON with `execution_authority: false` and `external_services: false`.
- For transcript files, returns `runtime_started: false` and `audio_processed: false`.
- For approved audio files, returns `runtime_started: true`, `audio_processed: true`, and `model_downloaded: false`.
- For readiness probes, returns no episode and writes no state.

## What It Does Not Do

- Does not access a microphone.
- Does not process audio unless `--audio-file`, `--model`, `--stt-command`, and `--allow-audio-processing` are all present.
- Does not call external APIs.
- Does not start Codex App Server.
- Does not launch a service, daemon, Docker container, GPU workload, or long-running runtime workflow.
- Does not download or discover models.
- Does not approve tool execution.

## Approval Boundary

The implemented STT path is file-based and adapter-based only. The operator must approve each audio-processing command with `--allow-audio-processing`.

Microphone capture, Codex App Server bridges, background listeners, wake-word flows, GPU/NPU transcription adapters, model downloads, Dockerized STT, and always-on voice workflows require separate approval-gated designs and implementations.

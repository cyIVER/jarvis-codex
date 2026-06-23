# whisper.cpp STT Runbook

This runbook covers local file-based speech-to-text for Jarvis Codex through an operator-supplied `whisper.cpp` binary and local ggml model.

Jarvis does not install `whisper.cpp`, download models, convert audio, access microphones, start listeners, or choose a cloud fallback.

## Current Local Evidence

The current WSL environment has a user-cache `whisper.cpp` setup that was prepared outside the Jarvis command path:

- `whisper-cli`: `/home/iveri/.cache/whisper.cpp/bin/v1.9.1/whisper-cli`
- ggml model: `/home/iveri/.cache/whisper.cpp/models/ggml-tiny.en.bin`
- sample audio: `/home/iveri/.cache/whisper.cpp/samples/jfk.wav`

`jarvis-codex voice discover --json` now reports `READY` for this local cache. A readiness probe against the JFK sample passed without writing state or processing audio, and one explicitly approved local transcription wrote only to a temporary state directory under `/tmp`.

The proof transcript captured:

```text
And so my fellow Americans ask not what your country can do for you
ask what you can do for your country.
```

This evidence proves the file-based local STT path. It does not approve background microphone listeners, model downloads from Jarvis commands, cloud STT, Dockerized STT, GPU/NPU adapters, or runtime workflow execution. Foreground microphone use is a separate `voice listen` path that requires an explicit recorder adapter plus `--allow-microphone` and `--allow-audio-processing`.

## Required Local Inputs

- A local `whisper-cli` executable built or installed by the operator.
- A local ggml Whisper model file, for example `ggml-base.en.bin`.
- A local 16-bit WAV audio file.

The upstream `whisper.cpp` CLI documents `whisper-cli` with `-m <model>` and `-f <audio>` arguments, and its examples use 16-bit WAV input.

Reference: https://github.com/ggml-org/whisper.cpp

## Readiness Probe

First discover local candidates:

```bash
jarvis-codex voice discover --json
```

Add explicit search roots when models or `whisper.cpp` live outside common locations:

```bash
jarvis-codex voice discover --search-root ~/whisper.cpp --search-root ~/models --json
```

Discovery is read-only. It does not access microphones, process audio, download models, call cloud services, start the runtime, or write state.

Run this before transcription:

```bash
jarvis-codex voice probe \
  --audio-file recording.wav \
  --model models/ggml-base.en.bin \
  --stt-command "python3 scripts/whisper-cpp-stt-adapter.py --whisper-command /path/to/whisper-cli" \
  --json
```

The probe verifies only local readiness. It should report:

- `runtime_started: false`
- `audio_processed: false`
- `writes_state: false`
- `external_services: false`
- `model_downloaded: false`

The standalone adapter can also check its own inputs:

```bash
python3 scripts/whisper-cpp-stt-adapter.py \
  --audio-file recording.wav \
  --model models/ggml-base.en.bin \
  --whisper-command /path/to/whisper-cli \
  --check-only
```

## Approved Transcription

Only run transcription after the readiness probe passes and the operator approves one local audio-processing action:

```bash
jarvis-codex voice ingest \
  --audio-file recording.wav \
  --model models/ggml-base.en.bin \
  --stt-command "python3 scripts/whisper-cpp-stt-adapter.py --whisper-command /path/to/whisper-cli" \
  --allow-audio-processing \
  --json
```

On success, Jarvis captures the transcript as a normal episode with source `voice-audio-file`.

## Guardrails

- Do not use file-based STT approval as approval to record from a microphone; use the separately gated `voice listen` foreground command.
- Do not download or convert models from this command path.
- Do not run Dockerized STT from this command path.
- Do not use a cloud STT fallback.
- Do not start background listeners, wake-word flows, daemons, or Codex App Server bridges.
- Do not treat the captured transcript as execution authority.

## Troubleshooting

- `stt_command_resolves` fails: provide the full path to `whisper-cli`, or ensure the executable is on `PATH`.
- `model_file_exists` fails: provide a local model path. Jarvis will not download it.
- `audio_is_readable_16bit_wav` fails: provide a readable 16-bit WAV file. Audio conversion is an operator-managed step outside Jarvis.
- Transcription returns an empty transcript: inspect the audio/model pairing and run the adapter directly with the same paths.

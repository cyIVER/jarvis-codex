# Mic-Harness Live Voice Policy (Progressive Disclosure)

This file contains instructions specific to the `mic-harness` and `whisper-cpp-stt-adapter.py` components.
It is separated from `AGENTS.md` to prevent context rot and ensure the live voice planning agent only loads what it needs.

## Context
- The `mic-harness` directory (`.codex/blackboard/mic-harness`) is used for live voice planning.
- The `whisper-cpp-stt-adapter.py` script is the adapter connecting the audio stream to the agent.

## Harness Guides
- Do not modify the structure of `.codex/blackboard/mic-harness/gemini` without confirming the adapter is stopped.
- If the adapter crashes, verbose logging should be collected in the `mic-harness` directory.
- The live voice agent must rely on its specific tools and should not attempt to govern other lanes (like `worktrunk-lane`).

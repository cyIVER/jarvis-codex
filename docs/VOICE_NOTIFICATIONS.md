# Voice Notifications

Jarvis Codex uses local Codex hooks for concise voice feedback. Prompt-start speech is enabled by default with `CODEX_NOTIFY_SPEAK_START=true`.

Completion speech defaults to `CODEX_NOTIFY_SPEAK_COMPLETIONS=action-needed`, so routine successful completions do not speak unless explicitly configured.

## Categories

| Event | Spoken phrase |
| --- | --- |
| Planning | Planning pass started. |
| UI/browser | Reviewing the interface. |
| Agent swarm | Swarm coordination started. |
| Worktrunk | Worktree operation queued. |
| Hardware/ML | Checking local acceleration. |
| GitHub | Checking the GitHub workflow. |
| Coding | Code change pass started. |
| General | I'm on it. |
| Error | The task needs attention. |
| Approval wait | Approval is needed. |
| Blocked | I'm blocked and need input. |
| User action needed | Input is needed. |

## Local Smoke

```bash
python3 ~/.codex/bin/codex_notify_jarvis.py --test
```

The hook logs include the selected message category, spoken phrase, whether speech was attempted, and whether delivery was reported.

`jarvis_codex.notifications` contains the reusable classification policy covered by the package test suite. The local Codex hook scripts can import that module after the repo package is installed into the hook runtime.

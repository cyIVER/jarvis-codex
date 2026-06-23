# Harness Integration Assessment

Date: 2026-06-23
Branch assessed: `harness-integration`

## Scope

This assessment covers the Agent Harness Engineering layer added to Jarvis Codex:

- Feedforward guide and ratchet updates in `AGENTS.md`.
- Progressive-disclosure live voice policy in `scripts/harness/mic-harness-policy.md`.
- Computational pre-commit sensor in `scripts/harness/pre-commit-sensor.sh`.
- Inferential sensor skill in `.agents/skills/harness-evaluator/SKILL.md`.

The same branch also contains the Jarvis WSL runtime, Windows launcher, Electron portable target, and voice chat improvements that were already under active integration.

## Assessment

The harness layer matches the Jarvis governance direction:

- `AGENTS.md` now separates feedforward guidance from explicit negative constraints.
- The ratchet makes prior failure modes durable and includes a runtime-state artifact rule.
- Mic-harness rules are progressively disclosed instead of loaded into every agent turn.
- The pre-commit sensor is deterministic and blocks on governance failures.
- The harness evaluator skill is read-only and uses the ratchet as its judging surface.

## Corrections Applied

- Added `harness-evaluator` to the expected repo-local governance skill baseline.
- Relaxed the current-state governance test away from brittle exact pass/warning counts while still requiring `PASS`, zero failures, no report writes, and a valid compact summary.
- Added `.gitignore` coverage for `state/runtime/**` and `state/release/**` so runtime audio, SQLite databases, and release-local artifacts do not enter commits.
- Clarified in `AGENTS.md` that `.git/hooks/pre-commit` is local clone state and must be installed from the tracked sensor script.

## Sensor Installation Note

Git does not version `.git/hooks/pre-commit`. The tracked source is:

```bash
scripts/harness/pre-commit-sensor.sh
```

Install or refresh the local hook with:

```bash
ln -sf ../../scripts/harness/pre-commit-sensor.sh .git/hooks/pre-commit
```

The current local hook was verified as byte-identical to the tracked sensor before this assessment.

## Residual Risk

- `.agents/skills/phd-research-analyst/` is present as an unexpected repo-local skill. It now satisfies the structural validator, so it is a warning rather than a blocking failure, but it was not part of the stated harness integration scope.
- Runtime/generated local files under `state/runtime/`, `state/release/`, `diff.txt`, and `markdown_output/` were treated as non-release local artifacts and were not staged for merge.

## Verification

Commands run:

```bash
python3 scripts/validate-jarvis-codex-phase1.py
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_governance.py
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_cli.py tests/test_runtime_control.py tests/test_windows_launcher.py tests/test_electron_hud_scaffold.py tests/test_packaging.py tests/test_voice_audio.py tests/test_windows_mic_scaffold.py tests/test_notifications.py
```

Expected merge gate:

- Governance validation must report `Status: PASS`.
- Test suites must pass before committing and merging to `main`.

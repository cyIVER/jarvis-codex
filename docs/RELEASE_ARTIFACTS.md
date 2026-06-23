# Release Artifact Review

Jarvis Codex has a read-only release artifact manifest for local release review.

Run:

```bash
jarvis-codex release manifest --json
```

The command inspects expected local review surfaces and generated review assets. It does not copy files, write reports, package artifacts, run Remotion, start a server, open a browser, mutate Git, or approve publication.

## Included Review Surfaces

- `README.md`
- `STATE.md`
- `LOOP.md`
- `loop-budget.md`
- `loop-run-log.md`
- `docs/PRODUCT_READINESS.md`
- `docs/PLAN_VIEWER.md`
- `docs/REMOTION_REVIEW.md`
- `docs/RELEASE_ARTIFACTS.md`
- `docs/RUNTIME_GATES.md`
- `docs/VOICE_INGRESS.md`
- `docs/WHISPER_CPP_STT_RUNBOOK.md`
- `docs/LOCAL_ML_RUNTIME.md`
- `docs/SAFE_HANDOFF_GATEWAY_PRD.md`
- `docs/WORKTRUNK_LANE_CLI_PRD.md`
- `tools/plan-viewer/index.html`

These files are release candidates for documenting and reviewing the local governed workflow.

The manifest reports `publication_ready: false` until an operator approves a specific packaging or publication action. A ready-for-review manifest is review evidence, not release authority.

## Generated Assets

Generated Remotion outputs under `video/remotion/out/` are local review assets only.

The manifest reports whether these files are present:

- `video/remotion/out/jarvis-codex-plan.png`
- `video/remotion/out/jarvis-codex-plan.mp4`

Presence does not make them release artifacts. They require explicit operator approval before copying, publishing, attaching to releases, or moving into any tracked artifact bundle.

## Required Validation

Before release review, run:

```bash
uv run pytest
python3 scripts/validate-jarvis-codex-phase1.py
```

If Remotion assets are being considered for release packaging, separately run the Remotion checks from `docs/REMOTION_REVIEW.md` with explicit approval.

## Non-authority

The manifest is not execution authority. It does not approve installs, Docker, GPU workloads, Remotion rendering, browser launch, service launch, Worktrunk mutation, Git mutation, packaging, publication, or release upload.

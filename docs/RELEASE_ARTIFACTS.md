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

## Local Artifact Evidence

After an approved local package or make validation has created ignored Electron artifacts, inspect hashes and sizes with:

```bash
jarvis-codex release artifact-evidence --json
```

This command reads the committed Electron icon source asset and ignored local Electron `dist/` artifacts, then reports size and SHA-256 evidence. It does not build packages, sign artifacts, copy artifacts, write reports, publish files, launch services, mutate Git, or approve release publication.

Ignored local Electron artifacts remain non-release candidates until a separate signing, security review, artifact-copy, and distribution plan is approved.

## Operator Evidence Ledger

After a human operator or external reviewer completes a separately approved validation step, record metadata in local state with:

```bash
jarvis-codex --state <state-dir> release evidence add --gate <gate> --summary "<summary>" --json
```

Optionally pass `--reviewer <name>` and `--artifact <path>` to hash a local evidence artifact. For safety, hashed artifacts must already live under `<state-dir>/release/`; the command reads the file for size and SHA-256 only and does not copy it into state.

List recorded evidence with:

```bash
jarvis-codex --state <state-dir> release evidence list --json
```

Summarize open gates and evidence counts with:

```bash
jarvis-codex --state <state-dir> release gate-status --json
```

Evidence records are state-only review metadata. They do not close release gates, approve publication, launch tests, run mobile or Gemini validation, sign artifacts, copy artifacts, mutate Git, or grant execution authority.

Before accepting any gate, inspect which gates have evidence ready for human acceptance with:

```bash
jarvis-codex --state <state-dir> release gate acceptance-brief --json
```

The acceptance brief is read-only. It shows gates that still need evidence, gates that already have accepted evidence, and proposed future `release gate accept` commands for evidence-ready gates. It does not accept gates, write state, run validations, approve publication, or grant execution authority.

After a human has reviewed and accepted a specific evidence record, record that gate decision separately:

```bash
jarvis-codex --state <state-dir> release gate accept --gate <gate> --evidence-id <evidence-id> --summary "<acceptance summary>" --json
```

List gate acceptance records with:

```bash
jarvis-codex --state <state-dir> release gate list --json
```

Gate acceptance is state-only. It closes only the named release gate in local gate-status/readiness summaries, and only by referencing an existing evidence record for the same gate. It does not run validations, approve publication, sign artifacts, copy artifacts, open networks, launch services, mutate Git, or grant execution authority.

## Release Readiness Checklist

Aggregate the current open release gates and operator next actions with:

```bash
jarvis-codex --state <state-dir> release readiness-checklist --json
```

This command combines the release manifest, artifact evidence, packaging preflight, external security review packet, mobile validation plan, Gemini validation plan, recorded evidence counts, and explicit gate acceptances into one checklist.

The checklist is read-only. It does not write files, write state, probe networks, launch services, build packages, sign artifacts, copy artifacts, run mobile or Gemini validation, automatically close release gates, or approve publication.

Commands displayed in the checklist are proposed read-only or approval-gated follow-up commands. They are not execution authority.

## Generated Assets

Generated Remotion outputs under `video/remotion/out/` are local review assets only.

The manifest reports whether these files are present:

- `video/remotion/out/jarvis-codex-plan.png`
- `video/remotion/out/jarvis-codex-plan.mp4`
- `video/remotion/out/jarvis-codex-overnight-brief.png`
- `video/remotion/out/jarvis-codex-overnight-brief.mp4`

Presence does not make them release artifacts. They require explicit operator approval before copying, publishing, attaching to releases, or moving into any tracked artifact bundle.

## Required Validation

Before release review, run:

```bash
uv run pytest
python3 scripts/validate-jarvis-codex-phase1.py
```

If Remotion assets are being considered for release packaging, separately run the Remotion checks from `docs/REMOTION_REVIEW.md` with explicit approval.

## Non-authority

The manifest, artifact evidence, gate status, and readiness checklist commands are not execution authority. They do not approve installs, Docker, GPU workloads, Remotion rendering, browser launch, service launch, Worktrunk mutation, Git mutation, mobile validation, Gemini network calls, packaging, signing, artifact copying, publication, release upload, or automatic gate closure.

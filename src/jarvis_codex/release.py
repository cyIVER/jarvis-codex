from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReleaseArtifact:
    path: str
    kind: str
    status: str
    release_candidate: bool
    requires_approval: bool
    note: str


@dataclass(frozen=True)
class ReleaseArtifactEvidence:
    path: str
    kind: str
    status: str
    size_bytes: int | None
    sha256: str | None
    release_candidate: bool
    ignored_local_artifact: bool
    requires_approval: bool
    signing_required: bool
    note: str


def _artifact(root: Path, relative_path: str, kind: str, release_candidate: bool, requires_approval: bool, note: str) -> ReleaseArtifact:
    path = root / relative_path
    return ReleaseArtifact(
        path=relative_path,
        kind=kind,
        status="present" if path.exists() else "missing",
        release_candidate=release_candidate,
        requires_approval=requires_approval,
        note=note,
    )


def _artifact_evidence(
    root: Path,
    relative_path: str,
    kind: str,
    release_candidate: bool,
    ignored_local_artifact: bool,
    requires_approval: bool,
    signing_required: bool,
    note: str,
) -> ReleaseArtifactEvidence:
    path = root / relative_path
    if not path.is_file():
        return ReleaseArtifactEvidence(
            path=relative_path,
            kind=kind,
            status="missing",
            size_bytes=None,
            sha256=None,
            release_candidate=release_candidate,
            ignored_local_artifact=ignored_local_artifact,
            requires_approval=requires_approval,
            signing_required=signing_required,
            note=note,
        )
    return ReleaseArtifactEvidence(
        path=relative_path,
        kind=kind,
        status="present",
        size_bytes=path.stat().st_size,
        sha256=_sha256(path),
        release_candidate=release_candidate,
        ignored_local_artifact=ignored_local_artifact,
        requires_approval=requires_approval,
        signing_required=signing_required,
        note=note,
    )


def build_release_artifact_evidence(root: Path) -> dict[str, Any]:
    """Build a read-only hash/size evidence manifest for local release artifacts."""
    root = root.resolve()
    artifacts = [
        _artifact_evidence(
            root,
            "tools/electron-hud/assets/icon.png",
            "electron-icon-source-asset",
            True,
            False,
            False,
            False,
            "Committed Electron package icon source asset.",
        ),
        _artifact_evidence(
            root,
            "tools/electron-hud/dist/linux-unpacked/jarvis-codex-electron-hud",
            "electron-unpacked-linux-executable",
            False,
            True,
            True,
            True,
            "Ignored local package-build evidence only; not signed, copied, reviewed, or publication-ready.",
        ),
        _artifact_evidence(
            root,
            "tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage",
            "electron-linux-appimage",
            False,
            True,
            True,
            True,
            "Ignored unsigned local installer evidence only; not signed, copied, reviewed, or publication-ready.",
        ),
    ]
    missing_required_source = [
        artifact.path for artifact in artifacts if artifact.release_candidate and artifact.status == "missing"
    ]
    present_local_artifacts = [
        artifact.path for artifact in artifacts if artifact.ignored_local_artifact and artifact.status == "present"
    ]
    status = "ready-for-review" if not missing_required_source else "needs-review"
    return {
        "label": "Jarvis Codex release artifact evidence",
        "status": status,
        "root": str(root),
        "writes_files": False,
        "package_build_performed": False,
        "signing_performed": False,
        "artifact_copy_performed": False,
        "publication_ready": False,
        "publication_requires_approval": True,
        "local_artifacts_are_release_candidates": False,
        "present_local_artifacts": present_local_artifacts,
        "missing_required_source_artifacts": missing_required_source,
        "remaining_release_gates": [
            "sign Electron artifacts before distribution",
            "perform artifact security and malware review",
            "copy artifacts only through an approved release plan",
            "publish artifacts only after explicit operator approval",
        ],
        "artifacts": [asdict(artifact) for artifact in artifacts],
    }


def build_release_manifest(root: Path) -> dict[str, Any]:
    """Build a read-only release artifact review manifest."""
    root = root.resolve()
    artifacts = [
        _artifact(
            root,
            "README.md",
            "operator-readme",
            True,
            False,
            "Primary operator entrypoint for local governed workflows.",
        ),
        _artifact(
            root,
            "STATE.md",
            "loop-state",
            True,
            False,
            "Current loop status, completed slices, and open product decisions.",
        ),
        _artifact(
            root,
            "LOOP.md",
            "loop-contract",
            True,
            False,
            "Autonomous loop operating contract and safety gates.",
        ),
        _artifact(
            root,
            "loop-budget.md",
            "loop-budget",
            True,
            False,
            "Loop budget and scope constraints.",
        ),
        _artifact(
            root,
            "loop-run-log.md",
            "loop-run-log",
            True,
            False,
            "Append-only local loop validation history.",
        ),
        _artifact(
            root,
            "docs/PRODUCT_READINESS.md",
            "release-readiness-doc",
            True,
            False,
            "Product readiness summary for the local governed review release.",
        ),
        _artifact(
            root,
            "docs/PLAN_VIEWER.md",
            "review-surface-doc",
            True,
            False,
            "Documents package and static plan-viewer behavior.",
        ),
        _artifact(
            root,
            "docs/REMOTION_REVIEW.md",
            "review-asset-policy-doc",
            True,
            False,
            "Documents Remotion as local-only review asset generation.",
        ),
        _artifact(
            root,
            "docs/RELEASE_ARTIFACTS.md",
            "release-policy-doc",
            True,
            False,
            "Documents release manifest behavior and non-authority boundaries.",
        ),
        _artifact(
            root,
            "docs/RUNTIME_GATES.md",
            "runtime-gate-doc",
            True,
            False,
            "Documents runtime, Worktrunk, git, and governance approval boundaries.",
        ),
        _artifact(
            root,
            "docs/VOICE_INGRESS.md",
            "voice-ingress-doc",
            True,
            False,
            "Documents transcript capture, STT readiness probes, and approved local STT.",
        ),
        _artifact(
            root,
            "docs/WHISPER_CPP_STT_RUNBOOK.md",
            "stt-runbook",
            True,
            False,
            "Documents operator-supplied whisper.cpp setup, readiness probing, and guarded transcription.",
        ),
        _artifact(
            root,
            "docs/LOCAL_ML_RUNTIME.md",
            "local-runtime-doc",
            True,
            False,
            "Documents local ML adapter boundaries and approval gates.",
        ),
        _artifact(
            root,
            "docs/SAFE_HANDOFF_GATEWAY_PRD.md",
            "safe-handoff-prd",
            True,
            False,
            "Defines safe handoff gateway requirements before any future runner.",
        ),
        _artifact(
            root,
            "docs/WORKTRUNK_LANE_CLI_PRD.md",
            "worktrunk-lane-prd",
            True,
            False,
            "Defines read-only lane CLI behavior and mutation guardrails.",
        ),
        _artifact(
            root,
            "docs/jarvis-harness/README.md",
            "harness-spec-index",
            True,
            False,
            "Index for the Jarvis harness architecture, runtime, voice, mobile, and release specs.",
        ),
        _artifact(
            root,
            "docs/jarvis-harness/production-readiness.md",
            "harness-production-runbook",
            True,
            False,
            "Current production readiness surface, validation baseline, safety invariants, and release gates.",
        ),
        _artifact(
            root,
            "docs/jarvis-harness/runtime-acp.md",
            "runtime-protocol-spec",
            True,
            False,
            "Runtime protocol and operator serving boundary for CLI, HUD, PWA, and future adapters.",
        ),
        _artifact(
            root,
            "docs/jarvis-harness/api-contract.md",
            "runtime-api-contract",
            True,
            False,
            "ACP-style JSON-RPC contract for sessions, approvals, voice, PTYs, and runtime readiness.",
        ),
        _artifact(
            root,
            "docs/jarvis-harness/acceptance-matrix.md",
            "acceptance-matrix",
            True,
            False,
            "Release acceptance matrix for HUD, mobile, voice, memory, tools, approvals, and loops.",
        ),
        _artifact(
            root,
            "docs/jarvis-harness/mobile-access.md",
            "mobile-access-spec",
            True,
            False,
            "Private-network PWA access model and mobile validation gate.",
        ),
        _artifact(
            root,
            "docs/jarvis-harness/voice-mode.md",
            "voice-mode-spec",
            True,
            False,
            "Browser voice, local STT/TTS, and Gemini OAuth feasibility boundaries.",
        ),
        _artifact(
            root,
            "docs/jarvis-harness/gemini-live-feasibility.md",
            "gemini-live-feasibility-doc",
            True,
            False,
            "Documents current Gemini Live auth, browser token, and network validation gates.",
        ),
        _artifact(
            root,
            "docs/jarvis-harness/morning-dashboard.html",
            "operator-dashboard",
            True,
            False,
            "Operator-facing morning dashboard for current harness state.",
        ),
        _artifact(
            root,
            "src/jarvis_codex/runtime_app.py",
            "runtime-source",
            True,
            False,
            "FastAPI runtime application that owns ACP-style RPC, HUD serving, PTYs, approvals, and voice adapters.",
        ),
        _artifact(
            root,
            "src/jarvis_codex/hud.py",
            "hud-source",
            True,
            False,
            "Runtime-served HUD source for desktop browser and private-network PWA clients.",
        ),
        _artifact(
            root,
            "src/jarvis_codex/cli.py",
            "operator-cli-source",
            True,
            False,
            "Operator CLI entrypoint including read-only release review and loopback runtime serving.",
        ),
        _artifact(
            root,
            "src/jarvis_codex/mobile.py",
            "mobile-preflight-source",
            True,
            False,
            "Read-only mobile private-network preflight classifier for iPhone/PWA access planning.",
        ),
        _artifact(
            root,
            "src/jarvis_codex/gemini.py",
            "gemini-feasibility-source",
            True,
            False,
            "Read-only Gemini Live feasibility classifier that exposes no secrets and starts no auth flow.",
        ),
        _artifact(
            root,
            "src/jarvis_codex/packaging.py",
            "packaging-preflight-source",
            True,
            False,
            "Read-only release packaging preflight classifier that performs no install, build, signing, or artifact copy.",
        ),
        _artifact(
            root,
            "tests/test_hud_browser.py",
            "browser-smoke-test",
            True,
            False,
            "Automated HUD browser smoke coverage using temporary runtime state.",
        ),
        _artifact(
            root,
            "tools/electron-hud/package.json",
            "electron-hud-package",
            True,
            False,
            "Local-only Electron HUD scaffold package. Installing or packaging remains a separate approval-gated step.",
        ),
        _artifact(
            root,
            "tools/electron-hud/package-lock.json",
            "electron-hud-lockfile",
            True,
            False,
            "Pinned Electron HUD dependency lockfile generated without installing node_modules or running package scripts.",
        ),
        _artifact(
            root,
            "tools/electron-hud/electron-builder.json",
            "electron-hud-builder-config",
            True,
            False,
            "Reviewed Electron Builder package configuration; it is not evidence that package or signing commands ran.",
        ),
        _artifact(
            root,
            "tools/electron-hud/main.js",
            "electron-hud-main",
            True,
            False,
            "Hardened Electron main process that loads the local runtime HUD and denies cross-origin navigation.",
        ),
        _artifact(
            root,
            "tools/electron-hud/preload.js",
            "electron-hud-preload",
            True,
            False,
            "Minimal preload bridge that exposes no shell authority to the renderer.",
        ),
        _artifact(
            root,
            "tools/plan-viewer/index.html",
            "static-review-surface",
            True,
            False,
            "Static plan viewer entrypoint; serving it remains an explicit local action.",
        ),
        _artifact(
            root,
            "video/remotion/out/jarvis-codex-plan.png",
            "generated-review-asset",
            False,
            True,
            "Generated local asset; keep ignored unless operator approves release packaging.",
        ),
        _artifact(
            root,
            "video/remotion/out/jarvis-codex-plan.mp4",
            "generated-review-asset",
            False,
            True,
            "Generated local asset; keep ignored unless operator approves release packaging.",
        ),
    ]

    warnings = []
    remotion_ignore = root / "video/remotion/.gitignore"
    if remotion_ignore.exists():
        ignore_text = remotion_ignore.read_text(encoding="utf-8")
        if "out/*" not in ignore_text or "!out/.gitkeep" not in ignore_text:
            warnings.append("Remotion output ignore policy is missing expected out/* and !out/.gitkeep rules.")
    else:
        warnings.append("video/remotion/.gitignore is missing.")

    missing = [artifact.path for artifact in artifacts if artifact.status == "missing" and artifact.release_candidate]
    generated_assets_present = [
        artifact.path for artifact in artifacts if artifact.kind == "generated-review-asset" and artifact.status == "present"
    ]

    status = "ready-for-review" if not missing else "needs-review"
    if warnings:
        status = "needs-review"
    release_candidates_present = [artifact.path for artifact in artifacts if artifact.release_candidate and artifact.status == "present"]

    return {
        "label": "Jarvis Codex release artifact manifest",
        "status": status,
        "root": str(root),
        "execution_authority": False,
        "writes_files": False,
        "artifact_copy_performed": False,
        "package_build_performed": False,
        "runtime_launch_performed": False,
        "publication_ready": False,
        "publication_requires_approval": True,
        "mobile_device_validation_required": True,
        "external_security_review_required": True,
        "generated_assets_require_approval": True,
        "generated_assets_present": generated_assets_present,
        "release_candidates_present": release_candidates_present,
        "missing_release_candidates": missing,
        "warnings": warnings,
        "required_validation": [
            "python3 scripts/validate-jarvis-codex-phase1.py",
            (
                "uv run pytest tests/test_codeburn.py tests/test_event_stream.py tests/test_voice_intent.py "
                "tests/test_plan_viewer.py tests/test_voice_audio.py tests/test_hud.py tests/test_hud_browser.py "
                "tests/test_runtime_app.py tests/test_voice.py tests/test_whisper_cpp_adapter.py tests/test_approval.py "
                "tests/test_event_store.py tests/test_pty_supervisor.py tests/test_policy.py tests/test_protocol.py "
                "tests/test_governance.py tests/test_cli.py tests/test_state.py tests/test_release.py "
                "tests/test_electron_hud_scaffold.py tests/test_mobile.py tests/test_gemini.py tests/test_packaging.py "
                "tests/test_loop_readiness.py tests/test_autonomous_loop.py"
            ),
        ],
        "remaining_release_gates": [
            "electron_packaging_and_signing",
            "actual_mobile_device_validation",
            "networked_gemini_live_validation",
            "hud_swarm_launch_controls",
            "unattended_loop_scheduling",
            "release_packaging_and_signing",
            "external_security_review",
        ],
        "artifacts": [asdict(artifact) for artifact in artifacts],
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

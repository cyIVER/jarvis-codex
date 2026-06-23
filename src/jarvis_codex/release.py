from __future__ import annotations

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
        "publication_ready": False,
        "publication_requires_approval": True,
        "generated_assets_require_approval": True,
        "generated_assets_present": generated_assets_present,
        "release_candidates_present": release_candidates_present,
        "missing_release_candidates": missing,
        "warnings": warnings,
        "required_validation": [
            "uv run pytest",
            "python3 scripts/validate-jarvis-codex-phase1.py",
            "npm run typecheck",
            "npm audit --audit-level=high",
        ],
        "artifacts": [asdict(artifact) for artifact in artifacts],
    }

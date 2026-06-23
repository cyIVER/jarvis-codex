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

    return {
        "label": "Jarvis Codex release artifact manifest",
        "status": status,
        "root": str(root),
        "execution_authority": False,
        "writes_files": False,
        "artifact_copy_performed": False,
        "generated_assets_require_approval": True,
        "generated_assets_present": generated_assets_present,
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

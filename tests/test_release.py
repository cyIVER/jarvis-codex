from __future__ import annotations

from pathlib import Path

from jarvis_codex.release import build_release_manifest


def write(path: Path, text: str = "ok") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_release_manifest_is_read_only_and_marks_generated_assets_unapproved(tmp_path):
    write(tmp_path / "docs/PRODUCT_READINESS.md")
    write(tmp_path / "docs/PLAN_VIEWER.md")
    write(tmp_path / "docs/REMOTION_REVIEW.md")
    write(tmp_path / "tools/plan-viewer/index.html")
    write(tmp_path / "video/remotion/.gitignore", "out/*\n!out/.gitkeep\n")
    write(tmp_path / "video/remotion/out/jarvis-codex-plan.png")
    write(tmp_path / "video/remotion/out/jarvis-codex-plan.mp4")

    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    manifest = build_release_manifest(tmp_path)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    generated = [item for item in manifest["artifacts"] if item["kind"] == "generated-review-asset"]

    assert manifest["status"] == "ready-for-review"
    assert manifest["execution_authority"] is False
    assert manifest["writes_files"] is False
    assert manifest["artifact_copy_performed"] is False
    assert manifest["generated_assets_require_approval"] is True
    assert all(item["release_candidate"] is False for item in generated)
    assert all(item["requires_approval"] is True for item in generated)
    assert before == after


def test_release_manifest_reports_missing_required_review_surfaces(tmp_path):
    write(tmp_path / "video/remotion/.gitignore", "out/*\n!out/.gitkeep\n")

    manifest = build_release_manifest(tmp_path)

    assert manifest["status"] == "needs-review"
    assert "docs/PRODUCT_READINESS.md" in manifest["missing_release_candidates"]
    assert "tools/plan-viewer/index.html" in manifest["missing_release_candidates"]


def test_release_manifest_warns_when_remotion_outputs_are_not_ignored(tmp_path):
    write(tmp_path / "docs/PRODUCT_READINESS.md")
    write(tmp_path / "docs/PLAN_VIEWER.md")
    write(tmp_path / "docs/REMOTION_REVIEW.md")
    write(tmp_path / "tools/plan-viewer/index.html")
    write(tmp_path / "video/remotion/.gitignore", "")

    manifest = build_release_manifest(tmp_path)

    assert manifest["status"] == "needs-review"
    assert manifest["warnings"] == ["Remotion output ignore policy is missing expected out/* and !out/.gitkeep rules."]

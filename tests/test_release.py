from __future__ import annotations

from pathlib import Path

from jarvis_codex.release import build_release_manifest


def write(path: Path, text: str = "ok") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_release_manifest_is_read_only_and_marks_generated_assets_unapproved(tmp_path):
    write(tmp_path / "README.md")
    write(tmp_path / "STATE.md")
    write(tmp_path / "LOOP.md")
    write(tmp_path / "loop-budget.md")
    write(tmp_path / "loop-run-log.md")
    write(tmp_path / "docs/PRODUCT_READINESS.md")
    write(tmp_path / "docs/PLAN_VIEWER.md")
    write(tmp_path / "docs/REMOTION_REVIEW.md")
    write(tmp_path / "docs/RELEASE_ARTIFACTS.md")
    write(tmp_path / "docs/RUNTIME_GATES.md")
    write(tmp_path / "docs/VOICE_INGRESS.md")
    write(tmp_path / "docs/WHISPER_CPP_STT_RUNBOOK.md")
    write(tmp_path / "docs/LOCAL_ML_RUNTIME.md")
    write(tmp_path / "docs/SAFE_HANDOFF_GATEWAY_PRD.md")
    write(tmp_path / "docs/WORKTRUNK_LANE_CLI_PRD.md")
    write(tmp_path / "docs/jarvis-harness/README.md")
    write(tmp_path / "docs/jarvis-harness/production-readiness.md")
    write(tmp_path / "docs/jarvis-harness/runtime-acp.md")
    write(tmp_path / "docs/jarvis-harness/api-contract.md")
    write(tmp_path / "docs/jarvis-harness/acceptance-matrix.md")
    write(tmp_path / "docs/jarvis-harness/mobile-access.md")
    write(tmp_path / "docs/jarvis-harness/voice-mode.md")
    write(tmp_path / "docs/jarvis-harness/gemini-live-feasibility.md")
    write(tmp_path / "docs/jarvis-harness/morning-dashboard.html")
    write(tmp_path / "src/jarvis_codex/runtime_app.py")
    write(tmp_path / "src/jarvis_codex/hud.py")
    write(tmp_path / "src/jarvis_codex/cli.py")
    write(tmp_path / "src/jarvis_codex/mobile.py")
    write(tmp_path / "src/jarvis_codex/gemini.py")
    write(tmp_path / "tests/test_hud_browser.py")
    write(tmp_path / "tools/electron-hud/package.json")
    write(tmp_path / "tools/electron-hud/main.js")
    write(tmp_path / "tools/electron-hud/preload.js")
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
    assert manifest["package_build_performed"] is False
    assert manifest["runtime_launch_performed"] is False
    assert manifest["publication_ready"] is False
    assert manifest["publication_requires_approval"] is True
    assert manifest["mobile_device_validation_required"] is True
    assert manifest["external_security_review_required"] is True
    assert manifest["generated_assets_require_approval"] is True
    assert "docs/VOICE_INGRESS.md" in manifest["release_candidates_present"]
    assert "docs/WHISPER_CPP_STT_RUNBOOK.md" in manifest["release_candidates_present"]
    assert "docs/SAFE_HANDOFF_GATEWAY_PRD.md" in manifest["release_candidates_present"]
    assert "docs/jarvis-harness/production-readiness.md" in manifest["release_candidates_present"]
    assert "docs/jarvis-harness/gemini-live-feasibility.md" in manifest["release_candidates_present"]
    assert "src/jarvis_codex/runtime_app.py" in manifest["release_candidates_present"]
    assert "src/jarvis_codex/mobile.py" in manifest["release_candidates_present"]
    assert "src/jarvis_codex/gemini.py" in manifest["release_candidates_present"]
    assert "tests/test_hud_browser.py" in manifest["release_candidates_present"]
    assert "tools/electron-hud/main.js" in manifest["release_candidates_present"]
    assert "electron_packaging_and_signing" in manifest["remaining_release_gates"]
    assert "actual_swarm_agent_launch" in manifest["remaining_release_gates"]
    assert "npm run typecheck" not in manifest["required_validation"]
    assert "tests/test_electron_hud_scaffold.py" in manifest["required_validation"][1]
    assert "tests/test_mobile.py" in manifest["required_validation"][1]
    assert "tests/test_gemini.py" in manifest["required_validation"][1]
    assert all(item["release_candidate"] is False for item in generated)
    assert all(item["requires_approval"] is True for item in generated)
    assert before == after


def test_release_manifest_reports_missing_required_review_surfaces(tmp_path):
    write(tmp_path / "video/remotion/.gitignore", "out/*\n!out/.gitkeep\n")

    manifest = build_release_manifest(tmp_path)

    assert manifest["status"] == "needs-review"
    assert "docs/PRODUCT_READINESS.md" in manifest["missing_release_candidates"]
    assert "docs/jarvis-harness/production-readiness.md" in manifest["missing_release_candidates"]
    assert "tools/plan-viewer/index.html" in manifest["missing_release_candidates"]


def test_release_manifest_warns_when_remotion_outputs_are_not_ignored(tmp_path):
    write(tmp_path / "README.md")
    write(tmp_path / "STATE.md")
    write(tmp_path / "LOOP.md")
    write(tmp_path / "loop-budget.md")
    write(tmp_path / "loop-run-log.md")
    write(tmp_path / "docs/PRODUCT_READINESS.md")
    write(tmp_path / "docs/PLAN_VIEWER.md")
    write(tmp_path / "docs/REMOTION_REVIEW.md")
    write(tmp_path / "docs/RELEASE_ARTIFACTS.md")
    write(tmp_path / "docs/RUNTIME_GATES.md")
    write(tmp_path / "docs/VOICE_INGRESS.md")
    write(tmp_path / "docs/WHISPER_CPP_STT_RUNBOOK.md")
    write(tmp_path / "docs/LOCAL_ML_RUNTIME.md")
    write(tmp_path / "docs/SAFE_HANDOFF_GATEWAY_PRD.md")
    write(tmp_path / "docs/WORKTRUNK_LANE_CLI_PRD.md")
    write(tmp_path / "docs/jarvis-harness/README.md")
    write(tmp_path / "docs/jarvis-harness/production-readiness.md")
    write(tmp_path / "docs/jarvis-harness/runtime-acp.md")
    write(tmp_path / "docs/jarvis-harness/api-contract.md")
    write(tmp_path / "docs/jarvis-harness/acceptance-matrix.md")
    write(tmp_path / "docs/jarvis-harness/mobile-access.md")
    write(tmp_path / "docs/jarvis-harness/voice-mode.md")
    write(tmp_path / "docs/jarvis-harness/gemini-live-feasibility.md")
    write(tmp_path / "docs/jarvis-harness/morning-dashboard.html")
    write(tmp_path / "src/jarvis_codex/runtime_app.py")
    write(tmp_path / "src/jarvis_codex/hud.py")
    write(tmp_path / "src/jarvis_codex/cli.py")
    write(tmp_path / "src/jarvis_codex/mobile.py")
    write(tmp_path / "src/jarvis_codex/gemini.py")
    write(tmp_path / "tests/test_hud_browser.py")
    write(tmp_path / "tools/electron-hud/package.json")
    write(tmp_path / "tools/electron-hud/main.js")
    write(tmp_path / "tools/electron-hud/preload.js")
    write(tmp_path / "tools/plan-viewer/index.html")
    write(tmp_path / "video/remotion/.gitignore", "")

    manifest = build_release_manifest(tmp_path)

    assert manifest["status"] == "needs-review"
    assert manifest["warnings"] == ["Remotion output ignore policy is missing expected out/* and !out/.gitkeep rules."]

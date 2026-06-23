from __future__ import annotations

from pathlib import Path

from jarvis_codex.release import (
    build_external_security_review_plan,
    build_release_artifact_evidence,
    build_release_gate_status,
    build_release_manifest,
)


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
    write(tmp_path / "docs/jarvis-harness/external-security-review.md")
    write(tmp_path / "docs/jarvis-harness/morning-dashboard.html")
    write(tmp_path / "src/jarvis_codex/runtime_app.py")
    write(tmp_path / "src/jarvis_codex/hud.py")
    write(tmp_path / "src/jarvis_codex/cli.py")
    write(tmp_path / "src/jarvis_codex/mobile.py")
    write(tmp_path / "src/jarvis_codex/gemini.py")
    write(tmp_path / "src/jarvis_codex/packaging.py")
    write(tmp_path / "tests/test_hud_browser.py")
    write(tmp_path / "tools/electron-hud/package.json")
    write(tmp_path / "tools/electron-hud/package-lock.json")
    write(tmp_path / "tools/electron-hud/electron-builder.json")
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
    assert "docs/jarvis-harness/external-security-review.md" in manifest["release_candidates_present"]
    assert "src/jarvis_codex/runtime_app.py" in manifest["release_candidates_present"]
    assert "src/jarvis_codex/mobile.py" in manifest["release_candidates_present"]
    assert "src/jarvis_codex/gemini.py" in manifest["release_candidates_present"]
    assert "src/jarvis_codex/packaging.py" in manifest["release_candidates_present"]
    assert "tests/test_hud_browser.py" in manifest["release_candidates_present"]
    assert "tools/electron-hud/main.js" in manifest["release_candidates_present"]
    assert "tools/electron-hud/package-lock.json" in manifest["release_candidates_present"]
    assert "tools/electron-hud/electron-builder.json" in manifest["release_candidates_present"]
    assert "electron_packaging_and_signing" in manifest["remaining_release_gates"]
    assert "hud_swarm_launch_controls" not in manifest["remaining_release_gates"]
    assert "unattended_loop_scheduling" in manifest["remaining_release_gates"]
    assert "npm run typecheck" not in manifest["required_validation"]
    assert "tests/test_electron_hud_scaffold.py" in manifest["required_validation"][1]
    assert "tests/test_mobile.py" in manifest["required_validation"][1]
    assert "tests/test_gemini.py" in manifest["required_validation"][1]
    assert "tests/test_packaging.py" in manifest["required_validation"][1]
    assert "tests/test_loop_readiness.py" in manifest["required_validation"][1]
    assert "tests/test_autonomous_loop.py" in manifest["required_validation"][1]
    assert all(item["release_candidate"] is False for item in generated)
    assert all(item["requires_approval"] is True for item in generated)
    assert before == after


def test_release_manifest_reports_missing_required_review_surfaces(tmp_path):
    write(tmp_path / "video/remotion/.gitignore", "out/*\n!out/.gitkeep\n")

    manifest = build_release_manifest(tmp_path)

    assert manifest["status"] == "needs-review"
    assert "docs/PRODUCT_READINESS.md" in manifest["missing_release_candidates"]
    assert "docs/jarvis-harness/production-readiness.md" in manifest["missing_release_candidates"]
    assert "docs/jarvis-harness/external-security-review.md" in manifest["missing_release_candidates"]
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
    write(tmp_path / "docs/jarvis-harness/external-security-review.md")
    write(tmp_path / "docs/jarvis-harness/morning-dashboard.html")
    write(tmp_path / "src/jarvis_codex/runtime_app.py")
    write(tmp_path / "src/jarvis_codex/hud.py")
    write(tmp_path / "src/jarvis_codex/cli.py")
    write(tmp_path / "src/jarvis_codex/mobile.py")
    write(tmp_path / "src/jarvis_codex/gemini.py")
    write(tmp_path / "src/jarvis_codex/packaging.py")
    write(tmp_path / "tests/test_hud_browser.py")
    write(tmp_path / "tools/electron-hud/package.json")
    write(tmp_path / "tools/electron-hud/package-lock.json")
    write(tmp_path / "tools/electron-hud/electron-builder.json")
    write(tmp_path / "tools/electron-hud/main.js")
    write(tmp_path / "tools/electron-hud/preload.js")
    write(tmp_path / "tools/plan-viewer/index.html")
    write(tmp_path / "video/remotion/.gitignore", "")

    manifest = build_release_manifest(tmp_path)

    assert manifest["status"] == "needs-review"
    assert manifest["warnings"] == ["Remotion output ignore policy is missing expected out/* and !out/.gitkeep rules."]


def test_release_artifact_evidence_hashes_local_artifacts_without_writing(tmp_path):
    write(tmp_path / "tools/electron-hud/assets/icon.png", "icon-source")
    write(tmp_path / "tools/electron-hud/dist/linux-unpacked/jarvis-codex-electron-hud", "binary")
    write(tmp_path / "tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage", "appimage")
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    evidence = build_release_artifact_evidence(tmp_path)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    artifacts = {item["path"]: item for item in evidence["artifacts"]}
    assert evidence["status"] == "ready-for-review"
    assert evidence["writes_files"] is False
    assert evidence["package_build_performed"] is False
    assert evidence["signing_performed"] is False
    assert evidence["artifact_copy_performed"] is False
    assert evidence["publication_ready"] is False
    assert evidence["local_artifacts_are_release_candidates"] is False
    assert "tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage" in evidence["present_local_artifacts"]
    assert artifacts["tools/electron-hud/assets/icon.png"]["release_candidate"] is True
    assert artifacts["tools/electron-hud/assets/icon.png"]["ignored_local_artifact"] is False
    assert artifacts["tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage"]["release_candidate"] is False
    assert artifacts["tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage"]["ignored_local_artifact"] is True
    assert artifacts["tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage"]["requires_approval"] is True
    assert artifacts["tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage"]["size_bytes"] == len("appimage")
    assert len(artifacts["tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage"]["sha256"]) == 64
    assert before == after


def test_release_artifact_evidence_reports_missing_icon_source(tmp_path):
    evidence = build_release_artifact_evidence(tmp_path)

    assert evidence["status"] == "needs-review"
    assert evidence["missing_required_source_artifacts"] == ["tools/electron-hud/assets/icon.png"]
    assert evidence["present_local_artifacts"] == []


def test_external_security_review_plan_is_read_only_and_keeps_gate_open(tmp_path):
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    plan = build_external_security_review_plan(tmp_path)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert plan["status"] == "ready-for-external-review"
    assert plan["writes_files"] is False
    assert plan["services_started"] is False
    assert plan["network_probe_performed"] is False
    assert plan["scanner_run_performed"] is False
    assert plan["package_build_performed"] is False
    assert plan["signing_performed"] is False
    assert plan["external_review_completed"] is False
    assert plan["external_security_review_required"] is True
    assert plan["external_reviewer_attestation_required"] is True
    assert plan["tests_and_fixes_are_not_review_signoff"] is True
    assert plan["not_a_penetration_test"] is True
    assert any(item["name"] == "OWASP ASVS" and item["version"] == "5.0.0" for item in plan["standards"])
    assert any(item["name"] == "OWASP Top 10 for LLM Applications" and item["version"] == "2025" for item in plan["standards"])
    assert any(item["name"] == "MITRE ATLAS" for item in plan["standards"])
    assert any(item["surface"] == "runtime_api" for item in plan["review_surfaces"])
    assert "external reviewer must perform and sign off the review with a human attestation artifact" in plan["remaining_release_gates"]
    assert "tests passing and fixes being implemented do not close the external_security_review gate" in plan["remaining_release_gates"]
    assert any("non-server-starting" in item for item in plan["validation_boundaries"])
    assert before == after


def test_release_gate_status_summarizes_evidence_without_closing_gates():
    status = build_release_gate_status(
        [
            {
                "id": "evidence_old",
                "created_at": 1,
                "gate": "external_security_review",
                "reviewer": "reviewer-a",
                "summary": "older evidence",
                "release_gate_closed": False,
            },
            {
                "id": "evidence_new",
                "created_at": 2,
                "gate": "external_security_review",
                "reviewer": "reviewer-b",
                "summary": "newer evidence",
                "release_gate_closed": False,
            },
        ]
    )

    external = next(item for item in status["gates"] if item["gate"] == "external_security_review")
    assert status["status"] == "open-gates"
    assert status["writes_state"] is False
    assert status["execution_authority"] is False
    assert status["publication_ready"] is False
    assert status["evidence_closes_gates"] is False
    assert status["human_acceptance_required"] is True
    assert external["status"] == "open"
    assert external["evidence_count"] == 2
    assert external["latest_evidence_id"] == "evidence_new"
    assert external["latest_reviewer"] == "reviewer-b"
    assert external["release_gate_closed"] is False
    assert all(item["release_gate_closed"] is False for item in status["gates"])

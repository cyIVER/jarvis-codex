from __future__ import annotations

from pathlib import Path

from jarvis_codex.release import (
    build_external_security_evidence_brief,
    build_external_security_review_plan,
    build_packaging_signing_evidence_brief,
    build_release_artifact_evidence,
    build_release_gate_acceptance_brief,
    build_release_gate_status,
    build_release_manifest,
    build_release_readiness_checklist,
)


def write(path: Path, text: str = "ok") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_release_manifest_is_read_only_and_marks_generated_assets_unapproved(tmp_path):
    write(tmp_path / "README.md")
    write(tmp_path / "STATE.md", "loop_status: active\nlevel: L1\n")
    write(tmp_path / "LOOP.md")
    write(
        tmp_path / "loop-budget.md",
        "Default cadence: manual/operator-requested\n"
        "Suggested token cap per loop cycle: 120k\n"
        "## Kill Switches\n"
        "## Escalation Rules\n",
    )
    write(tmp_path / "loop-run-log.md")
    write(tmp_path / "docs/PRODUCT_READINESS.md")
    write(tmp_path / "docs/safety.md")
    write(tmp_path / "docs/PLAN_VIEWER.md")
    write(tmp_path / "docs/REMOTION_REVIEW.md")
    write(tmp_path / "docs/RELEASE_ARTIFACTS.md", "jarvis-codex release manifest --json\n")
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
    write(tmp_path / "video/remotion/out/jarvis-codex-overnight-brief.png")
    write(tmp_path / "video/remotion/out/jarvis-codex-overnight-brief.mp4")

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
    assert "video/remotion/out/jarvis-codex-plan.png" in manifest["generated_assets_present"]
    assert "video/remotion/out/jarvis-codex-plan.mp4" in manifest["generated_assets_present"]
    assert "video/remotion/out/jarvis-codex-overnight-brief.png" in manifest["generated_assets_present"]
    assert "video/remotion/out/jarvis-codex-overnight-brief.mp4" in manifest["generated_assets_present"]
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
    write(
        tmp_path / "loop-budget.md",
        "Default cadence: manual/operator-requested\n"
        "Suggested token cap per loop cycle: 120k\n"
        "## Kill Switches\n"
        "## Escalation Rules\n",
    )
    write(tmp_path / "loop-run-log.md")
    write(tmp_path / "docs/PRODUCT_READINESS.md")
    write(tmp_path / "docs/PLAN_VIEWER.md")
    write(tmp_path / "docs/REMOTION_REVIEW.md")
    write(tmp_path / "docs/RELEASE_ARTIFACTS.md", "jarvis-codex release manifest --json\n")
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


def test_packaging_signing_evidence_brief_is_read_only_and_keeps_gates_open(tmp_path):
    write(tmp_path / "tools/electron-hud/package.json", '{"devDependencies":{"electron":"42.4.1","electron-builder":"26.15.3"},"scripts":{"package":"electron-builder --dir --config electron-builder.json","make":"electron-builder --config electron-builder.json --publish never"}}')
    write(tmp_path / "tools/electron-hud/package-lock.json", "{}")
    write(tmp_path / "tools/electron-hud/node_modules/.keep")
    write(tmp_path / "tools/electron-hud/electron-builder.json", '{"directories":{"buildResources":"assets"},"icon":"icon.png"}')
    write(tmp_path / "tools/electron-hud/assets/icon.png", "icon-source")
    write(tmp_path / "tools/electron-hud/dist/linux-unpacked/jarvis-codex-electron-hud", "binary")
    write(tmp_path / "tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage", "appimage")
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    brief = build_packaging_signing_evidence_brief(tmp_path)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert brief["label"] == "Jarvis packaging and signing operator evidence brief"
    assert brief["status"] == "READY_FOR_OPERATOR_REVIEW"
    assert brief["packaging_preflight_status"] == "READY_FOR_APPROVAL"
    assert brief["artifact_evidence_status"] == "ready-for-review"
    assert "tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage" in brief["present_local_artifacts"]
    assert brief["local_artifacts_are_release_candidates"] is False
    assert brief["install_performed"] is False
    assert brief["package_build_performed"] is False
    assert brief["signing_performed"] is False
    assert brief["artifact_copy_performed"] is False
    assert brief["publication_performed"] is False
    assert brief["service_launch_performed"] is False
    assert brief["writes_files"] is False
    assert brief["execution_authority"] is False
    assert brief["publication_ready"] is False
    assert brief["release_gate_closed"] is False
    assert brief["requires_human_acceptance"] is True
    assert any("electron_packaging_and_signing" in command for command in brief["release_evidence_commands"])
    assert any("release_packaging_and_signing" in command for command in brief["release_evidence_commands"])
    assert any("do not run npm install" in action for action in brief["unsafe_actions"])
    assert before == after


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


def test_external_security_evidence_brief_is_read_only_and_keeps_gate_open(tmp_path):
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    brief = build_external_security_evidence_brief(tmp_path)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert brief["label"] == "Jarvis external security review evidence brief"
    assert brief["status"] == "READY_FOR_EXTERNAL_REVIEW"
    assert brief["security_review_plan_status"] == "ready-for-external-review"
    assert brief["writes_files"] is False
    assert brief["services_started"] is False
    assert brief["network_probe_performed"] is False
    assert brief["scanner_run_performed"] is False
    assert brief["package_build_performed"] is False
    assert brief["signing_performed"] is False
    assert brief["artifact_copy_performed"] is False
    assert brief["publication_performed"] is False
    assert brief["execution_authority"] is False
    assert brief["external_review_completed"] is False
    assert brief["release_gate_closed"] is False
    assert brief["requires_human_acceptance"] is True
    assert "external_security_review" in brief["release_evidence_command"]
    assert any("human external reviewer" in criterion for criterion in brief["pass_criteria"])
    assert any("do not run scanners" in action for action in brief["unsafe_actions"])
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
    assert external["acceptance_count"] == 0
    assert external["release_gate_closed"] is False


def test_release_gate_status_closes_only_with_explicit_acceptance():
    status = build_release_gate_status(
        [
            {
                "id": "evidence_external",
                "created_at": 1,
                "gate": "external_security_review",
                "reviewer": "external-reviewer",
                "summary": "reviewer attestation",
                "release_gate_closed": False,
            },
        ],
        [
            {
                "id": "gate_acceptance_external",
                "created_at": 2,
                "gate": "external_security_review",
                "evidence_id": "evidence_external",
                "reviewer": "operator",
                "summary": "operator accepted reviewer attestation",
                "release_gate_closed": True,
            },
        ],
    )

    external = next(item for item in status["gates"] if item["gate"] == "external_security_review")
    assert status["status"] == "open-gates"
    assert status["publication_ready"] is False
    assert status["open_gate_count"] == 5
    assert status["accepted_gate_count"] == 1
    assert status["evidence_closes_gates"] is False
    assert external["status"] == "accepted"
    assert external["release_gate_closed"] is True
    assert external["accepted_evidence_id"] == "evidence_external"
    assert external["latest_acceptance_id"] == "gate_acceptance_external"


def test_release_gate_acceptance_brief_is_read_only_and_separates_ready_gates():
    brief = build_release_gate_acceptance_brief(
        [
            {
                "id": "evidence_mobile",
                "created_at": 1,
                "gate": "actual_mobile_device_validation",
                "reviewer": "operator",
                "summary": "iPhone validation evidence",
                "release_gate_closed": False,
            },
            {
                "id": "evidence_external",
                "created_at": 2,
                "gate": "external_security_review",
                "reviewer": "external-reviewer",
                "summary": "external review attestation",
                "release_gate_closed": False,
            },
        ],
        [
            {
                "id": "gate_acceptance_external",
                "created_at": 3,
                "gate": "external_security_review",
                "evidence_id": "evidence_external",
                "reviewer": "operator",
                "summary": "accepted external review attestation",
                "release_gate_closed": True,
            },
        ],
    )

    mobile = next(item for item in brief["acceptance_items"] if item["gate"] == "actual_mobile_device_validation")
    external = next(item for item in brief["acceptance_items"] if item["gate"] == "external_security_review")
    gemini = next(item for item in brief["acceptance_items"] if item["gate"] == "networked_gemini_live_validation")
    assert brief["label"] == "Jarvis release gate acceptance brief"
    assert brief["status"] == "needs-human-review"
    assert brief["writes_files"] is False
    assert brief["writes_state"] is False
    assert brief["execution_authority"] is False
    assert brief["evidence_closes_gates"] is False
    assert brief["acceptance_command_writes_state"] is True
    assert brief["acceptance_command_grants_execution_authority"] is False
    assert brief["publication_ready"] is False
    assert brief["ready_for_acceptance"] == ["actual_mobile_device_validation"]
    assert "networked_gemini_live_validation" in brief["needs_evidence"]
    assert mobile["status"] == "ready-for-human-acceptance"
    assert mobile["acceptance_command"]
    assert "--gate actual_mobile_device_validation" in mobile["acceptance_command"]
    assert "--evidence-id evidence_mobile" in mobile["acceptance_command"]
    assert external["status"] == "accepted"
    assert external["acceptance_command"] is None
    assert external["release_gate_closed"] is True
    assert gemini["status"] == "needs-evidence"
    assert gemini["acceptance_command"] is None
    assert any("run validations" in action for action in brief["unsafe_actions_not_authorized"])


def test_release_readiness_checklist_aggregates_open_gates_without_authority(tmp_path):
    write(tmp_path / "README.md")
    write(tmp_path / "STATE.md", "loop_status: active\nlevel: L1\n")
    write(tmp_path / "LOOP.md")
    write(
        tmp_path / "loop-budget.md",
        "Default cadence: manual/operator-requested\n"
        "Suggested token cap per loop cycle: 120k\n"
        "## Kill Switches\n"
        "## Escalation Rules\n",
    )
    write(tmp_path / "loop-run-log.md")
    write(tmp_path / "docs/PRODUCT_READINESS.md")
    write(tmp_path / "docs/safety.md")
    write(tmp_path / "docs/PLAN_VIEWER.md")
    write(tmp_path / "docs/REMOTION_REVIEW.md")
    write(tmp_path / "docs/RELEASE_ARTIFACTS.md", "jarvis-codex release manifest --json\n")
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
    write(tmp_path / "tools/electron-hud/assets/icon.png", "icon")
    write(tmp_path / "video/remotion/.gitignore", "out/*\n!out/.gitkeep\n")
    write(
        tmp_path / ".github/workflows/ci.yml",
        "permissions:\n  contents: read\nsteps:\n  - run: uv run pytest\n  - run: python3 scripts/validate-jarvis-codex-phase1.py\n",
    )
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    checklist = build_release_readiness_checklist(
        tmp_path,
        [
            {
                "id": "evidence_1",
                "created_at": 1,
                "gate": "external_security_review",
                "reviewer": "external-reviewer",
                "summary": "review pending fixes",
                "release_gate_closed": False,
            }
        ],
    )

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    mobile = next(item for item in checklist["checklist"] if item["gate"] == "actual_mobile_device_validation")
    gemini = next(item for item in checklist["checklist"] if item["gate"] == "networked_gemini_live_validation")
    electron = next(item for item in checklist["checklist"] if item["gate"] == "electron_packaging_and_signing")
    release_packaging = next(item for item in checklist["checklist"] if item["gate"] == "release_packaging_and_signing")
    external = next(item for item in checklist["checklist"] if item["gate"] == "external_security_review")
    unattended = next(item for item in checklist["checklist"] if item["gate"] == "unattended_loop_scheduling")
    assert checklist["status"] == "blocked"
    assert checklist["writes_files"] is False
    assert checklist["writes_state"] is False
    assert checklist["network_probe_performed"] is False
    assert checklist["service_launch_performed"] is False
    assert checklist["package_build_performed"] is False
    assert checklist["signing_performed"] is False
    assert checklist["artifact_copy_performed"] is False
    assert checklist["execution_authority"] is False
    assert checklist["publication_ready"] is False
    assert checklist["release_gate_closed"] is False
    assert checklist["evidence_closes_gates"] is False
    assert checklist["human_acceptance_required"] is True
    assert "actual_mobile_device_validation" in checklist["blocked_by"]
    assert "networked_gemini_live_validation" in checklist["blocked_by"]
    assert "jarvis-codex mobile evidence-brief --host <private-host> --json" in checklist["recommended_read_only_commands"]
    assert "jarvis-codex gemini evidence-brief --json" in checklist["recommended_read_only_commands"]
    assert "jarvis-codex release packaging-evidence-brief --json" in checklist["recommended_read_only_commands"]
    assert "jarvis-codex release security-review-plan --json" in checklist["recommended_read_only_commands"]
    assert "jarvis-codex release security-evidence-brief --json" in checklist["recommended_read_only_commands"]
    assert "jarvis-codex loop unattended-policy --json" in checklist["recommended_read_only_commands"]
    assert "jarvis-codex loop unattended-evidence-brief --json" in checklist["recommended_read_only_commands"]
    assert checklist["summary"]["unattended_loop_policy_status"] == "ready-for-human-policy-review"
    assert "launch runtime services" in checklist["unsafe_actions_not_authorized"]
    assert "mobile evidence-brief" in mobile["read_only_command"]
    assert mobile["release_gate_closed"] is False
    assert "gemini evidence-brief" in gemini["read_only_command"]
    assert gemini["release_gate_closed"] is False
    assert electron["read_only_command"] == "jarvis-codex release packaging-evidence-brief --json"
    assert electron["release_gate_closed"] is False
    assert release_packaging["read_only_command"] == "jarvis-codex release packaging-evidence-brief --json"
    assert release_packaging["release_gate_closed"] is False
    assert external["read_only_command"] == "jarvis-codex release security-evidence-brief --json"
    assert external["evidence_count"] == 1
    assert external["latest_evidence_id"] == "evidence_1"
    assert external["release_gate_closed"] is False
    assert any("accepted attestation artifact" in item for item in external["required_evidence"])
    assert unattended["read_only_command"] == "jarvis-codex loop unattended-evidence-brief --json"
    assert unattended["release_gate_closed"] is False
    assert "accepted kill switches and manual stop controls" in unattended["required_evidence"]
    assert any("do not start daemons" in action for action in unattended["unsafe_actions_not_authorized"])
    assert any("READY_FOR_OPERATOR_REVIEW" in note for note in unattended["notes"])
    assert before == after


def test_release_readiness_checklist_reports_ready_when_all_gates_accepted(tmp_path):
    write(tmp_path / "README.md")
    write(tmp_path / "STATE.md", "loop_status: active\nlevel: L1\n")
    write(tmp_path / "LOOP.md")
    write(
        tmp_path / "loop-budget.md",
        "Default cadence: manual/operator-requested\n"
        "Suggested token cap per loop cycle: 120k\n"
        "## Kill Switches\n"
        "## Escalation Rules\n",
    )
    write(tmp_path / "loop-run-log.md")
    write(tmp_path / "docs/PRODUCT_READINESS.md")
    write(tmp_path / "docs/safety.md")
    write(tmp_path / "docs/PLAN_VIEWER.md")
    write(tmp_path / "docs/REMOTION_REVIEW.md")
    write(tmp_path / "docs/RELEASE_ARTIFACTS.md", "jarvis-codex release manifest --json\n")
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
    write(tmp_path / "tools/electron-hud/assets/icon.svg")
    write(tmp_path / "tools/electron-hud/assets/icon.png")
    write(tmp_path / "tools/electron-hud/dist/linux-unpacked/jarvis")
    write(tmp_path / "tools/electron-hud/dist/Jarvis Codex-0.1.0.AppImage")
    write(tmp_path / "video/remotion/README.md")
    write(tmp_path / "video/remotion/src/MorningBriefing.tsx")
    write(tmp_path / "video/remotion/out/morning-briefing.png")
    write(tmp_path / "video/remotion/out/morning-briefing.mp4")

    gates = [
        "actual_mobile_device_validation",
        "electron_packaging_and_signing",
        "external_security_review",
        "networked_gemini_live_validation",
        "release_packaging_and_signing",
        "unattended_loop_scheduling",
    ]
    evidence_records = [
        {
            "id": f"evidence_{gate}",
            "created_at": index,
            "gate": gate,
            "reviewer": "operator",
            "summary": f"accepted evidence for {gate}",
            "release_gate_closed": False,
        }
        for index, gate in enumerate(gates, start=1)
    ]
    acceptance_records = [
        {
            "id": f"gate_acceptance_{gate}",
            "created_at": index + 10,
            "gate": gate,
            "evidence_id": f"evidence_{gate}",
            "reviewer": "operator",
            "summary": f"operator accepted {gate}",
            "release_gate_closed": True,
        }
        for index, gate in enumerate(gates, start=1)
    ]

    checklist = build_release_readiness_checklist(tmp_path, evidence_records, acceptance_records)

    assert checklist["status"] == "ready-for-human-release-review"
    assert checklist["publication_ready"] is True
    assert checklist["release_gate_closed"] is True
    assert checklist["human_acceptance_required"] is False
    assert checklist["blocked_by"] == []
    assert checklist["summary"]["open_gate_count"] == 0
    assert checklist["summary"]["accepted_gate_count"] == 6
    assert all(item["release_gate_closed"] is True for item in checklist["checklist"])
    assert all(item["requires_human_acceptance"] is False for item in checklist["checklist"])

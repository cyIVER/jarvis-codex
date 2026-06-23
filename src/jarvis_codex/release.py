from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .gemini import build_gemini_live_evidence_brief, build_gemini_live_validation_plan
from .loop_readiness import build_unattended_loop_evidence_brief, build_unattended_loop_policy
from .mobile import build_mobile_validation_plan
from .packaging import build_packaging_preflight
from .state import RELEASE_EVIDENCE_GATES


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


def build_packaging_signing_evidence_brief(root: Path) -> dict[str, Any]:
    """Build a read-only operator brief for packaging, signing, artifact review, and release evidence."""
    root = root.resolve()
    preflight = build_packaging_preflight(root).to_dict()
    artifact_evidence = build_release_artifact_evidence(root)
    present_local_artifacts = artifact_evidence["present_local_artifacts"]
    release_evidence_commands = [
        (
            "jarvis-codex --state <state-dir> release evidence add "
            "--gate electron_packaging_and_signing "
            "--summary \"Electron package/signing review completed with signed artifact hashes and redacted signing notes\" "
            "--reviewer operator --json"
        ),
        (
            "jarvis-codex --state <state-dir> release evidence add "
            "--gate release_packaging_and_signing "
            "--summary \"Release artifact packaging/signing review completed with publication approval notes\" "
            "--reviewer operator --json"
        ),
    ]
    required_operator_evidence = [
        "approved packaging target list and platform scope",
        "isolated release worktree or clean checkout note",
        "dependency install/build/make command approvals with exact commands and outputs",
        "signing credential readiness note with no secret values",
        "signed artifact hashes, sizes, and platform target list",
        "artifact security or malware review result",
        "explicit copy, upload, or publication approval if distribution is requested",
    ]
    return {
        "label": "Jarvis packaging and signing operator evidence brief",
        "status": "READY_FOR_OPERATOR_REVIEW" if preflight["status"] == "READY_FOR_APPROVAL" else "NEEDS_SETUP",
        "root": str(root),
        "packaging_preflight_status": preflight["status"],
        "artifact_evidence_status": artifact_evidence["status"],
        "present_local_artifacts": present_local_artifacts,
        "local_artifacts_are_release_candidates": artifact_evidence["local_artifacts_are_release_candidates"],
        "preflight_command": "jarvis-codex release packaging-preflight --json",
        "artifact_evidence_command": "jarvis-codex release artifact-evidence --json",
        "release_evidence_commands": release_evidence_commands,
        "recommended_commands": preflight["recommended_commands"],
        "required_operator_evidence": required_operator_evidence,
        "operator_steps": [
            "Run packaging-preflight and artifact-evidence first.",
            "Review local ignored artifacts as evidence only; do not treat them as release candidates.",
            "Approve each install, package, make, signing, copy, upload, or publish command separately before execution.",
            "Run package/build/signing work only in an approved isolated release worktree or clean checkout.",
            "Capture signed artifact hashes and security review notes with secret values redacted.",
            "Store any accepted evidence artifact under <state-dir>/release/ before hashing it with release evidence add.",
            "Record release evidence metadata only after a human accepts the signed artifact and publication evidence.",
        ],
        "pass_criteria": [
            "all packaging, signing, copy, upload, and publish commands were separately approved before execution",
            "signed artifacts have recorded hashes, sizes, and target platforms",
            "signing secrets are not committed, logged, printed, or copied into release evidence",
            "local ignored artifacts are either regenerated in an approved release context or explicitly rejected for publication",
            "operator explicitly accepts publication scope before any distribution",
        ],
        "fail_criteria": [
            "npm install, package, make, signing, copy, upload, or publish ran without explicit approval",
            "signing secrets appear in stdout, logs, docs, state, or artifacts",
            "ignored local artifacts are treated as release candidates without human approval",
            "artifact security review or malware review is skipped",
            "release evidence records are treated as automatic gate closure",
        ],
        "unsafe_actions": [
            "do not run npm install, npm run package, npm run make, signing, copy, upload, or publish from this brief",
            "do not access signing credentials from this brief",
            "do not copy ignored local artifacts into release output from this brief",
            "do not publish, upload, or distribute artifacts from this brief",
            "do not treat this brief as packaging proof, signing proof, publication approval, or gate closure",
        ],
        "warnings": [
            *preflight["warnings"],
            *artifact_evidence["remaining_release_gates"],
        ],
        "install_performed": False,
        "package_build_performed": False,
        "signing_performed": False,
        "artifact_copy_performed": False,
        "publication_performed": False,
        "service_launch_performed": False,
        "writes_files": False,
        "execution_authority": False,
        "publication_ready": False,
        "release_gate_closed": False,
        "requires_human_acceptance": True,
    }


def build_external_security_review_plan(root: Path) -> dict[str, Any]:
    """Build a read-only external security review packet plan."""
    root = root.resolve()
    review_surfaces = [
        {
            "surface": "runtime_api",
            "paths": ["src/jarvis_codex/runtime_app.py", "docs/jarvis-harness/api-contract.md"],
            "focus": "JSON-RPC method authorization, runtime-token gates, approval consumption, and error handling.",
        },
        {
            "surface": "hud_browser_client",
            "paths": ["src/jarvis_codex/hud.py", "tests/test_hud.py", "tests/test_hud_browser.py"],
            "focus": "Same-origin WebSocket use, CSP, displayed command boundaries, microphone/STT approval flows, and PTY launch controls.",
        },
        {
            "surface": "pty_and_command_policy",
            "paths": ["src/jarvis_codex/pty_supervisor.py", "src/jarvis_codex/policy.py", "tests/test_policy.py", "tests/test_pty_supervisor.py"],
            "focus": "Command classification, hardline blocks, approval-matched execution, process cleanup, and PTY output handling.",
        },
        {
            "surface": "voice_and_local_ml",
            "paths": ["src/jarvis_codex/voice.py", "src/jarvis_codex/whisper_cpp.py", "docs/VOICE_INGRESS.md", "docs/LOCAL_ML_RUNTIME.md"],
            "focus": "Audio-file boundaries, model path restrictions, local adapter execution gates, and transcript-to-action separation.",
        },
        {
            "surface": "mobile_and_pwa",
            "paths": ["src/jarvis_codex/mobile.py", "docs/jarvis-harness/mobile-access.md", "src/jarvis_codex/hud.py"],
            "focus": "Private-network exposure, service worker cache boundaries, non-loopback operator approval, and iPhone validation evidence.",
        },
        {
            "surface": "electron_and_release",
            "paths": ["tools/electron-hud/main.js", "tools/electron-hud/preload.js", "src/jarvis_codex/packaging.py", "src/jarvis_codex/release.py"],
            "focus": "Renderer isolation, denied navigation/window-open behavior, signing boundaries, ignored generated artifacts, and release evidence.",
        },
        {
            "surface": "loop_and_swarm",
            "paths": ["src/jarvis_codex/autonomous_loop.py", "docs/jarvis-harness/swarm-and-loops.md", "LOOP.md", "docs/safety.md"],
            "focus": "No arbitrary command runners, no daemon/background scheduler at L1, bounded loop evidence, and swarm launch approval binding.",
        },
    ]
    required_validation = [
        "python3 scripts/validate-jarvis-codex-phase1.py",
        "uv run pytest tests/test_codeburn.py tests/test_event_stream.py tests/test_voice_intent.py tests/test_plan_viewer.py tests/test_voice_audio.py tests/test_hud.py tests/test_hud_browser.py tests/test_runtime_app.py tests/test_voice.py tests/test_whisper_cpp_adapter.py tests/test_approval.py tests/test_event_store.py tests/test_pty_supervisor.py tests/test_policy.py tests/test_protocol.py tests/test_governance.py tests/test_cli.py tests/test_state.py tests/test_release.py tests/test_electron_hud_scaffold.py tests/test_mobile.py tests/test_gemini.py tests/test_packaging.py tests/test_loop_readiness.py tests/test_autonomous_loop.py",
        "uv run jarvis-codex release manifest --json",
        "uv run jarvis-codex release artifact-evidence --json",
        "uv run jarvis-codex runtime readiness --json",
    ]
    return {
        "label": "Jarvis Codex external security review plan",
        "status": "ready-for-external-review",
        "root": str(root),
        "writes_files": False,
        "services_started": False,
        "network_probe_performed": False,
        "scanner_run_performed": False,
        "package_build_performed": False,
        "signing_performed": False,
        "external_review_completed": False,
        "external_security_review_required": True,
        "external_reviewer_attestation_required": True,
        "tests_and_fixes_are_not_review_signoff": True,
        "not_a_penetration_test": True,
        "standards": [
            {
                "name": "OWASP ASVS",
                "version": "5.0.0",
                "url": "https://owasp.org/www-project-application-security-verification-standard/",
                "use": "Application security verification requirements baseline.",
            },
            {
                "name": "OWASP Web Security Testing Guide",
                "url": "https://owasp.org/www-project-web-security-testing-guide/",
                "use": "Web application and web service testing methodology reference.",
            },
            {
                "name": "OWASP Top 10",
                "version": "2025",
                "url": "https://owasp.org/www-project-top-ten/",
                "use": "Broad application-risk awareness checklist.",
            },
            {
                "name": "OWASP Top 10 for LLM Applications",
                "version": "2025",
                "url": "https://genai.owasp.org/llm-top-10/",
                "use": "Agentic prompt, tool-use, excessive-agency, output-handling, and LLM application risk checklist.",
            },
            {
                "name": "MITRE ATLAS",
                "url": "https://atlas.mitre.org/",
                "use": "AI-system adversary tactics and techniques reference for agentic and ML-adjacent review surfaces.",
            },
        ],
        "review_surfaces": review_surfaces,
        "required_validation": required_validation,
        "validation_boundaries": [
            "runtime readiness command is a non-server-starting static/readiness summary only",
            "validation output must not be treated as external reviewer sign-off",
            "fixes plus passing tests are not sufficient to set external_review_completed=true",
            "closing the gate requires a human external reviewer artifact or explicit attestation accepted by the operator",
        ],
        "reviewer_deliverables": [
            "threat model notes for runtime, HUD, PTY, voice, mobile, Electron, and loop surfaces",
            "ASVS/WSTG-aligned findings with severity, affected path, reproduction notes, and remediation recommendation",
            "LLM/agentic-risk findings mapped to OWASP LLM Top 10 or MITRE ATLAS where applicable",
            "explicit sign-off or hold recommendation for release packaging and private-network/mobile exposure",
            "list of tests or manual evidence reviewed",
        ],
        "remaining_release_gates": [
            "external reviewer must perform and sign off the review with a human attestation artifact",
            "approved fixes must be implemented and revalidated",
            "tests passing and fixes being implemented do not close the external_security_review gate",
            "security review is not a substitute for signing, mobile validation, or Gemini Live validation",
        ],
    }


def build_external_security_evidence_brief(root: Path) -> dict[str, Any]:
    """Build a read-only operator brief for external reviewer attestation evidence."""
    root = root.resolve()
    plan = build_external_security_review_plan(root)
    release_evidence_command = (
        "jarvis-codex --state <state-dir> release evidence add "
        "--gate external_security_review "
        "--summary \"External security reviewer attestation accepted with findings and remediation status\" "
        "--reviewer <external-reviewer> --json"
    )
    return {
        "label": "Jarvis external security review evidence brief",
        "status": "READY_FOR_EXTERNAL_REVIEW",
        "root": str(root),
        "security_review_plan_status": plan["status"],
        "review_plan_command": "jarvis-codex release security-review-plan --json",
        "release_evidence_command": release_evidence_command,
        "standards": plan["standards"],
        "review_surfaces": plan["review_surfaces"],
        "required_operator_evidence": [
            "external reviewer identity, role, and independence note",
            "reviewed artifact or commit range",
            "standards or methodology used",
            "findings list with severity and affected paths",
            "remediation status or explicit accepted-risk notes",
            "reviewer sign-off, hold recommendation, or release-blocking finding",
            "accepted attestation artifact stored under <state-dir>/release/ if an artifact is recorded",
        ],
        "operator_steps": [
            "Generate the security-review-plan packet first.",
            "Send the packet, commit range, and validation evidence to a human external reviewer.",
            "Receive findings and a sign-off or hold recommendation from the reviewer.",
            "Implement and revalidate any accepted fixes before recording release evidence.",
            "Store any attestation artifact under <state-dir>/release/ before hashing it with release evidence add.",
            "Record release evidence metadata only after the operator accepts the reviewer attestation.",
        ],
        "pass_criteria": [
            "human external reviewer performed the review",
            "review scope includes runtime, HUD, PTY/policy, voice/local ML, mobile/PWA, Electron/release, loop/swarm surfaces",
            "findings are recorded with severity, affected paths, and remediation or accepted-risk status",
            "release evidence references the accepted reviewer attestation",
            "passing tests and internal fixes are not treated as external review sign-off",
        ],
        "fail_criteria": [
            "review was performed only by the implementation agent",
            "scanner output or passing tests are treated as human external reviewer sign-off",
            "review scope omits runtime authority, browser HUD, PTY, local audio, mobile, Electron, release, or loop surfaces",
            "critical findings are unresolved without accepted-risk approval",
            "release evidence records are treated as automatic gate closure",
        ],
        "unsafe_actions": [
            "do not run scanners from this brief",
            "do not launch services from this brief",
            "do not probe networks from this brief",
            "do not build, sign, copy, publish, or upload artifacts from this brief",
            "do not treat tests passing or internal fixes as external reviewer sign-off",
            "do not close the external_security_review gate from this brief",
        ],
        "warnings": plan["remaining_release_gates"],
        "writes_files": False,
        "services_started": False,
        "network_probe_performed": False,
        "scanner_run_performed": False,
        "package_build_performed": False,
        "signing_performed": False,
        "artifact_copy_performed": False,
        "publication_performed": False,
        "execution_authority": False,
        "external_review_completed": False,
        "release_gate_closed": False,
        "requires_human_acceptance": True,
    }


def build_release_gate_status(
    evidence_records: list[dict[str, Any]],
    acceptance_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Summarize release-gate evidence and explicit human acceptances."""
    records_by_gate: dict[str, list[dict[str, Any]]] = {gate: [] for gate in sorted(RELEASE_EVIDENCE_GATES)}
    for record in evidence_records:
        gate = record.get("gate")
        if isinstance(gate, str) and gate in records_by_gate:
            records_by_gate[gate].append(record)

    accepted_by_gate: dict[str, list[dict[str, Any]]] = {gate: [] for gate in sorted(RELEASE_EVIDENCE_GATES)}
    for record in acceptance_records or []:
        gate = record.get("gate")
        if isinstance(gate, str) and gate in accepted_by_gate and record.get("release_gate_closed") is True:
            accepted_by_gate[gate].append(record)

    gates: list[dict[str, Any]] = []
    for gate in sorted(RELEASE_EVIDENCE_GATES):
        records = sorted(records_by_gate[gate], key=lambda item: item.get("created_at", 0), reverse=True)
        acceptances = sorted(accepted_by_gate[gate], key=lambda item: item.get("created_at", 0), reverse=True)
        latest = records[0] if records else None
        latest_acceptance = acceptances[0] if acceptances else None
        accepted = latest_acceptance is not None
        gates.append(
            {
                "gate": gate,
                "status": "accepted" if accepted else "open",
                "evidence_count": len(records),
                "acceptance_count": len(acceptances),
                "latest_evidence_id": latest.get("id") if latest else None,
                "latest_reviewer": latest.get("reviewer") if latest else None,
                "latest_summary": latest.get("summary") if latest else None,
                "latest_acceptance_id": latest_acceptance.get("id") if latest_acceptance else None,
                "latest_acceptance_reviewer": latest_acceptance.get("reviewer") if latest_acceptance else None,
                "latest_acceptance_summary": latest_acceptance.get("summary") if latest_acceptance else None,
                "accepted_evidence_id": latest_acceptance.get("evidence_id") if latest_acceptance else None,
                "release_gate_closed": accepted,
                "requires_human_acceptance": not accepted,
            }
        )

    open_gate_count = sum(1 for gate in gates if not gate["release_gate_closed"])
    return {
        "label": "Jarvis Codex release gate status",
        "status": "open-gates" if open_gate_count else "accepted",
        "writes_state": False,
        "execution_authority": False,
        "publication_ready": open_gate_count == 0,
        "evidence_closes_gates": False,
        "human_acceptance_required": open_gate_count > 0,
        "open_gate_count": open_gate_count,
        "accepted_gate_count": len(gates) - open_gate_count,
        "gates": gates,
    }


def build_release_gate_acceptance_brief(
    evidence_records: list[dict[str, Any]],
    acceptance_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a read-only operator brief for explicit release-gate acceptance."""
    gate_status = build_release_gate_status(evidence_records, acceptance_records)
    items: list[dict[str, Any]] = []
    for gate in gate_status["gates"]:
        latest_evidence_id = gate["latest_evidence_id"]
        accepted = gate["release_gate_closed"]
        evidence_ready = latest_evidence_id is not None and not accepted
        if accepted:
            status = "accepted"
        elif evidence_ready:
            status = "ready-for-human-acceptance"
        else:
            status = "needs-evidence"
        acceptance_command = None
        if evidence_ready:
            acceptance_command = (
                "jarvis-codex --state <state-dir> release gate accept "
                f"--gate {gate['gate']} "
                f"--evidence-id {latest_evidence_id} "
                "--summary \"<human acceptance summary>\" --json"
            )
        items.append(
            {
                "gate": gate["gate"],
                "status": status,
                "evidence_count": gate["evidence_count"],
                "acceptance_count": gate["acceptance_count"],
                "latest_evidence_id": latest_evidence_id,
                "latest_reviewer": gate["latest_reviewer"],
                "latest_summary": gate["latest_summary"],
                "latest_acceptance_id": gate["latest_acceptance_id"],
                "accepted_evidence_id": gate["accepted_evidence_id"],
                "release_gate_closed": accepted,
                "requires_human_acceptance": not accepted,
                "acceptance_command": acceptance_command,
                "required_human_review": [
                    "review the referenced evidence record",
                    "confirm the evidence belongs to the same release gate",
                    "write a non-empty human acceptance summary",
                    "confirm acceptance is state-only and grants no execution authority",
                ],
            }
        )
    ready_gates = [item["gate"] for item in items if item["status"] == "ready-for-human-acceptance"]
    needs_evidence = [item["gate"] for item in items if item["status"] == "needs-evidence"]
    return {
        "label": "Jarvis release gate acceptance brief",
        "status": "accepted" if not ready_gates and not needs_evidence else "needs-human-review",
        "writes_files": False,
        "writes_state": False,
        "execution_authority": False,
        "evidence_closes_gates": False,
        "acceptance_command_writes_state": True,
        "acceptance_command_grants_execution_authority": False,
        "publication_ready": gate_status["publication_ready"],
        "ready_for_acceptance": ready_gates,
        "needs_evidence": needs_evidence,
        "accepted_gate_count": gate_status["accepted_gate_count"],
        "open_gate_count": gate_status["open_gate_count"],
        "acceptance_items": items,
        "unsafe_actions_not_authorized": [
            "run validations",
            "launch runtime services",
            "open network probes or Gemini WebSockets",
            "run mobile browser validation",
            "build, sign, copy, upload, or publish artifacts",
            "start background schedulers or daemons",
            "mutate Git or Worktrunk state",
            "close gates without explicit human acceptance",
        ],
    }


def build_release_readiness_checklist(
    root: Path,
    evidence_records: list[dict[str, Any]],
    acceptance_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Aggregate release gate next actions without launching validators or closing gates."""
    root = root.resolve()
    manifest = build_release_manifest(root)
    artifact_evidence = build_release_artifact_evidence(root)
    packaging_preflight = build_packaging_preflight(root).to_dict()
    packaging_brief = build_packaging_signing_evidence_brief(root)
    security_review = build_external_security_review_plan(root)
    security_brief = build_external_security_evidence_brief(root)
    gate_status = build_release_gate_status(evidence_records, acceptance_records)
    mobile_validation = build_mobile_validation_plan().to_dict()
    gemini_validation = build_gemini_live_validation_plan().to_dict()
    gemini_evidence_brief = build_gemini_live_evidence_brief().to_dict()
    unattended_policy = build_unattended_loop_policy(root)
    unattended_evidence_brief = build_unattended_loop_evidence_brief(root)

    gate_lookup = {gate["gate"]: gate for gate in gate_status["gates"]}
    checklist_items = [
        _release_checklist_item(
            gate_lookup,
            "actual_mobile_device_validation",
            "Validate the HUD on an actual iPhone or approved mobile device over a private network.",
            "jarvis-codex mobile discover --json && jarvis-codex mobile evidence-brief --host <private-host> --json",
            mobile_validation["required_operator_evidence"],
            mobile_validation["unsafe_actions"],
            [f"current default validation status: {mobile_validation['status']}"],
        ),
        _release_checklist_item(
            gate_lookup,
            "networked_gemini_live_validation",
            "Run an approved Gemini Live network validation using the selected credential mode.",
            "jarvis-codex gemini feasibility --json && jarvis-codex gemini evidence-brief --json",
            gemini_evidence_brief["required_operator_evidence"],
            gemini_evidence_brief["unsafe_actions"],
            [f"current evidence-brief status: {gemini_evidence_brief['status']}"],
        ),
        _release_checklist_item(
            gate_lookup,
            "electron_packaging_and_signing",
            "Review Electron packaging readiness, then separately approve any install, build, make, or signing command.",
            "jarvis-codex release packaging-evidence-brief --json",
            packaging_brief["required_operator_evidence"],
            packaging_brief["unsafe_actions"],
            [f"current packaging evidence brief status: {packaging_brief['status']}"],
        ),
        _release_checklist_item(
            gate_lookup,
            "release_packaging_and_signing",
            "Review release artifact evidence and approve any artifact copy, signing, publication, or upload separately.",
            "jarvis-codex release packaging-evidence-brief --json",
            packaging_brief["required_operator_evidence"],
            packaging_brief["unsafe_actions"],
            [f"current packaging evidence brief status: {packaging_brief['status']}"],
        ),
        _release_checklist_item(
            gate_lookup,
            "external_security_review",
            "Send the external security review packet to a human reviewer and record the accepted attestation as evidence.",
            "jarvis-codex release security-evidence-brief --json",
            security_brief["required_operator_evidence"],
            security_brief["unsafe_actions"],
            [f"current security evidence brief status: {security_brief['status']}"],
        ),
        _release_checklist_item(
            gate_lookup,
            "unattended_loop_scheduling",
            "Keep unattended scheduling blocked until an explicit scheduler, budget, stop, and human-observable run policy is approved.",
            "jarvis-codex loop unattended-evidence-brief --json",
            unattended_evidence_brief["required_operator_evidence"],
            unattended_evidence_brief["unsafe_actions"],
            [f"current unattended evidence brief status: {unattended_evidence_brief['status']}"],
        ),
    ]

    open_gates = [item["gate"] for item in checklist_items if item["status"] == "open"]
    blocked_by = sorted(open_gates)

    return {
        "label": "Jarvis Codex release readiness checklist",
        "status": "blocked" if blocked_by else "ready-for-human-release-review",
        "root": str(root),
        "writes_files": False,
        "writes_state": False,
        "network_probe_performed": False,
        "service_launch_performed": False,
        "package_build_performed": False,
        "signing_performed": False,
        "artifact_copy_performed": False,
        "runtime_launch_performed": False,
        "execution_authority": False,
        "publication_ready": not blocked_by,
        "release_gate_closed": not blocked_by,
        "human_acceptance_required": bool(blocked_by),
        "not_test_replacement": True,
        "evidence_closes_gates": False,
        "blocked_by": blocked_by,
        "summary": {
            "manifest_status": manifest["status"],
            "artifact_evidence_status": artifact_evidence["status"],
            "packaging_preflight_status": packaging_preflight["status"],
            "security_review_plan_status": security_review["status"],
            "mobile_validation_plan_status": mobile_validation["status"],
            "gemini_validation_plan_status": gemini_validation["status"],
            "unattended_loop_policy_status": unattended_policy["status"],
            "open_gate_count": gate_status["open_gate_count"],
            "accepted_gate_count": gate_status["accepted_gate_count"],
        },
        "recommended_read_only_commands": [
            "jarvis-codex release manifest --json",
            "jarvis-codex release artifact-evidence --json",
            "jarvis-codex release packaging-preflight --json",
            "jarvis-codex release packaging-evidence-brief --json",
            "jarvis-codex release security-review-plan --json",
            "jarvis-codex release security-evidence-brief --json",
            "jarvis-codex --state <state-dir> release gate-status --json",
            "jarvis-codex mobile discover --json",
            "jarvis-codex mobile evidence-brief --host <private-host> --json",
            "jarvis-codex gemini feasibility --json",
            "jarvis-codex gemini evidence-brief --json",
            "jarvis-codex loop verify --json",
            "jarvis-codex loop unattended-policy --json",
            "jarvis-codex loop unattended-evidence-brief --json",
        ],
        "unsafe_actions_not_authorized": [
            "install packages",
            "build packages",
            "sign artifacts",
            "copy or publish release artifacts",
            "launch runtime services",
            "open network probes or Gemini WebSockets",
            "run mobile browser validation",
            "start background schedulers or daemons",
            "mutate Git or Worktrunk state",
            "automatically close release gates from evidence records",
        ],
        "checklist": checklist_items,
    }


def _release_checklist_item(
    gate_lookup: dict[str, dict[str, Any]],
    gate: str,
    next_action: str,
    read_only_command: str,
    required_evidence: list[str],
    unsafe_actions: list[str],
    notes: list[str],
) -> dict[str, Any]:
    status = gate_lookup.get(gate, {})
    return {
        "gate": gate,
        "status": status.get("status", "open"),
        "evidence_count": status.get("evidence_count", 0),
        "latest_evidence_id": status.get("latest_evidence_id"),
        "accepted_evidence_id": status.get("accepted_evidence_id"),
        "latest_acceptance_id": status.get("latest_acceptance_id"),
        "release_gate_closed": status.get("release_gate_closed", False),
        "requires_human_acceptance": status.get("requires_human_acceptance", True),
        "next_action": next_action,
        "read_only_command": read_only_command,
        "required_evidence": required_evidence,
        "unsafe_actions_not_authorized": unsafe_actions,
        "notes": notes,
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
            "docs/jarvis-harness/external-security-review.md",
            "external-security-review-plan",
            True,
            False,
            "External reviewer packet and standards-aligned security review scope.",
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
        _artifact(
            root,
            "video/remotion/out/jarvis-codex-overnight-brief.png",
            "generated-review-asset",
            False,
            True,
            "Generated 0800 briefing poster; keep ignored unless operator approves release packaging.",
        ),
        _artifact(
            root,
            "video/remotion/out/jarvis-codex-overnight-brief.mp4",
            "generated-review-asset",
            False,
            True,
            "Generated 0800 briefing video; keep ignored unless operator approves release packaging.",
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

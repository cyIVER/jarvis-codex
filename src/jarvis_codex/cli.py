from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

import uvicorn

from .autonomous_loop import run_autonomous_loop_once, run_autonomous_loop_schedule
from .codex_app_server import CodexAppServerConfig, CodexAppServerError, inline_approval_prompt, run_codex_turn
from .gemini import (
    build_gemini_feasibility,
    build_gemini_live_evidence_brief,
    build_gemini_live_validation_plan,
    build_nango_gemini_live_integration_plan,
)
from .governance import validate_phase1_governance
from .hardware import inspect_hardware, recommend_backend
from .lanes import list_lanes, score_lane
from .loop_readiness import build_unattended_loop_evidence_brief, build_unattended_loop_policy, validate_loop_readiness
from .mobile import build_mobile_evidence_brief, build_mobile_preflight, build_mobile_validation_plan, discover_mobile_hosts
from .packaging import build_packaging_preflight
from .release import (
    build_external_security_evidence_brief,
    build_external_security_review_plan,
    build_packaging_signing_evidence_brief,
    build_release_artifact_evidence,
    build_release_gate_acceptance_brief,
    build_release_gate_status,
    build_release_manifest,
    build_release_readiness_checklist,
)
from .runtime_app import build_runtime_readiness, create_app
from .safe_handoff import build_safe_handoff, render_safe_handoff_json, render_safe_handoff_markdown
from .state import RELEASE_EVIDENCE_GATES, JarvisState
from .voice import discover_local_stt_assets, ingest_audio_file, ingest_transcript_file, probe_audio_file
from .voice_audio import VoiceAudioError, transcribe_with_local_adapter
from .voice_intent import propose_voice_intent
from .voice_mic import DEFAULT_RECORD_SECONDS, VoiceMicError, discover_recorder_command, record_microphone_once


def main() -> int:
    parser = argparse.ArgumentParser(prog="jarvis-codex")
    parser.add_argument("--state", default="state", help="State directory")
    sub = parser.add_subparsers(dest="command", required=True)

    capture = sub.add_parser("capture", help="Capture a task episode")
    capture.add_argument("text", nargs="+")
    capture.add_argument("--source", default="text")

    memory = sub.add_parser("memory", help="Manage durable memory")
    memory_sub = memory.add_subparsers(dest="memory_command", required=True)
    memory_add = memory_sub.add_parser("add")
    memory_add.add_argument("key")
    memory_add.add_argument("value", nargs="+")
    memory_sub.add_parser("list")

    approve = sub.add_parser("approve", help="Create approval requests")
    approve_sub = approve.add_subparsers(dest="approval_command", required=True)
    approve_request = approve_sub.add_parser("request")
    approve_request.add_argument("summary", nargs="+")

    handoff = sub.add_parser("handoff", help="Generate a Codex handoff")
    handoff.add_argument("--objective", default="Continue Jarvis Codex work")
    handoff.add_argument("--queue-summary", action="store_true", help="Print a safe handoff summary from the planning queue")
    handoff.add_argument("--json", action="store_true", help="Print queue summary as JSON; only valid with --queue-summary")

    hardware = sub.add_parser("hardware", help="Inspect local acceleration capabilities")
    hardware.add_argument(
        "--workload",
        choices=["general", "llm", "vision", "voice", "video", "background"],
        default="general",
        help="Workload to recommend a backend for",
    )
    voice = sub.add_parser("voice", help="Capture voice-origin input through transcript or approved local STT")
    voice_sub = voice.add_subparsers(dest="voice_command", required=True)
    voice_discover = voice_sub.add_parser("discover", help="Discover local STT binaries and models without processing audio")
    voice_discover.add_argument("--search-root", action="append", default=[], help="Additional local directory to search")
    voice_discover.add_argument("--json", action="store_true", help="Print local STT discovery as JSON")
    voice_probe = voice_sub.add_parser("probe", help="Check local STT inputs without processing audio")
    voice_probe.add_argument("--audio-file", required=True, help="Path to a local audio file for STT")
    voice_probe.add_argument("--model", required=True, help="Path to an explicit local STT model file")
    voice_probe.add_argument("--stt-command", required=True, help="Local STT adapter command to inspect")
    voice_probe.add_argument("--json", action="store_true", help="Print STT readiness as JSON")
    voice_ingest = voice_sub.add_parser("ingest", help="Capture a transcript file or approved local STT audio file")
    voice_source = voice_ingest.add_mutually_exclusive_group(required=True)
    voice_source.add_argument("--transcript-file", help="Path to a UTF-8 text transcript")
    voice_source.add_argument("--audio-file", help="Path to a local audio file for STT")
    voice_ingest.add_argument("--model", help="Path to an explicit local STT model file; required with --audio-file")
    voice_ingest.add_argument("--stt-command", help="Local STT adapter command; receives --audio-file and --model")
    voice_ingest.add_argument("--allow-audio-processing", action="store_true", help="Approve local audio processing for this command")
    voice_ingest.add_argument("--timeout-seconds", type=int, default=120, help="STT adapter timeout")
    voice_ingest.add_argument("--json", action="store_true", help="Print voice ingest result as JSON")
    voice_plan = voice_sub.add_parser("plan", help="Classify a voice transcript into a planning turn without launching")
    voice_plan.add_argument("transcript", nargs="+", help="Transcript text to classify")
    voice_plan.add_argument("--profile", default="observe", help="Policy profile to use for command classification")
    voice_plan.add_argument("--json", action="store_true", help="Print voice planning turn as JSON")
    voice_ask = voice_sub.add_parser("ask", help="Send typed transcript text to Codex app-server")
    voice_ask.add_argument("transcript", nargs="+", help="Transcript text to send")
    _add_codex_voice_turn_args(voice_ask)
    voice_listen = voice_sub.add_parser("listen", help="Record one foreground mic utterance, transcribe it, then send it to Codex")
    voice_listen.add_argument("--seconds", type=int, default=DEFAULT_RECORD_SECONDS, help="Foreground recording duration")
    voice_listen.add_argument("--record-command", help="Recorder adapter command; accepts --output-file and --seconds")
    voice_listen.add_argument("--model", required=True, help="Path to an explicit local STT model file")
    voice_listen.add_argument("--stt-command", required=True, help="Local STT adapter command; receives --audio-file and --model")
    voice_listen.add_argument("--allow-microphone", action="store_true", help="Approve microphone access for this foreground command")
    voice_listen.add_argument("--allow-audio-processing", action="store_true", help="Approve local STT processing for this foreground command")
    voice_listen.add_argument("--timeout-seconds", type=int, default=120, help="Recorder and STT timeout")
    _add_codex_voice_turn_args(voice_listen)
    lane = sub.add_parser("lane", help="Review Worktrunk lane state without mutation")
    lane_sub = lane.add_subparsers(dest="lane_command", required=True)
    lane_list = lane_sub.add_parser("list", help="List lane readiness from git worktree metadata")
    lane_list.add_argument("--repo", default=".", help="Repository path to inspect")
    lane_list.add_argument("--json", action="store_true", help="Print lane list as JSON")
    lane_score = lane_sub.add_parser("score", help="Score one lane using read-only git status")
    lane_score.add_argument("--repo", required=True, help="Lane repository path to inspect")
    lane_score.add_argument("--branch", required=True, help="Lane branch name")
    lane_score.add_argument("--json", action="store_true", help="Print lane score as JSON")
    release = sub.add_parser("release", help="Review release artifacts without packaging or copying")
    release_sub = release.add_subparsers(dest="release_command", required=True)
    release_manifest = release_sub.add_parser("manifest", help="Print a read-only release artifact manifest")
    release_manifest.add_argument("--root", default=".", help="Repository root to inspect")
    release_manifest.add_argument("--json", action="store_true", help="Print release manifest as JSON")
    release_packaging = release_sub.add_parser("packaging-preflight", help="Print a read-only release packaging preflight")
    release_packaging.add_argument("--root", default=".", help="Repository root to inspect")
    release_packaging.add_argument("--json", action="store_true", help="Print packaging preflight as JSON")
    release_packaging_brief = release_sub.add_parser("packaging-evidence-brief", help="Print a read-only packaging and signing evidence brief")
    release_packaging_brief.add_argument("--root", default=".", help="Repository root to inspect")
    release_packaging_brief.add_argument("--json", action="store_true", help="Print packaging evidence brief as JSON")
    release_evidence = release_sub.add_parser("artifact-evidence", help="Print read-only release artifact hashes and sizes")
    release_evidence.add_argument("--root", default=".", help="Repository root to inspect")
    release_evidence.add_argument("--json", action="store_true", help="Print artifact evidence as JSON")
    release_security = release_sub.add_parser("security-review-plan", help="Print a read-only external security review packet")
    release_security.add_argument("--root", default=".", help="Repository root to inspect")
    release_security.add_argument("--json", action="store_true", help="Print security review plan as JSON")
    release_security_brief = release_sub.add_parser("security-evidence-brief", help="Print a read-only external security review evidence brief")
    release_security_brief.add_argument("--root", default=".", help="Repository root to inspect")
    release_security_brief.add_argument("--json", action="store_true", help="Print security evidence brief as JSON")
    release_evidence_state = release_sub.add_parser("evidence", help="Record or list operator-supplied release-gate evidence")
    release_evidence_sub = release_evidence_state.add_subparsers(dest="release_evidence_command", required=True)
    release_evidence_add = release_evidence_sub.add_parser("add", help="Record release-gate evidence metadata without closing the gate")
    release_evidence_add.add_argument("--gate", required=True, choices=sorted(RELEASE_EVIDENCE_GATES), help="Release gate this evidence supports")
    release_evidence_add.add_argument("--summary", required=True, help="Human-readable evidence summary")
    release_evidence_add.add_argument("--reviewer", default="operator", help="Reviewer or operator name/handle")
    release_evidence_add.add_argument("--artifact", help="Optional local artifact path to hash; the file is not copied")
    release_evidence_add.add_argument("--json", action="store_true", help="Print evidence record as JSON")
    release_evidence_list = release_evidence_sub.add_parser("list", help="List release-gate evidence records")
    release_evidence_list.add_argument("--json", action="store_true", help="Print evidence records as JSON")
    release_gate = release_sub.add_parser("gate", help="Accept or list explicit human release-gate decisions")
    release_gate_sub = release_gate.add_subparsers(dest="release_gate_command", required=True)
    release_gate_accept = release_gate_sub.add_parser("accept", help="Accept a release gate using an existing evidence record")
    release_gate_accept.add_argument("--gate", required=True, choices=sorted(RELEASE_EVIDENCE_GATES), help="Release gate to accept")
    release_gate_accept.add_argument("--evidence-id", required=True, help="Existing evidence id for the same release gate")
    release_gate_accept.add_argument("--summary", required=True, help="Human-readable acceptance summary")
    release_gate_accept.add_argument("--reviewer", default="operator", help="Reviewer or operator name/handle")
    release_gate_accept.add_argument("--json", action="store_true", help="Print gate acceptance as JSON")
    release_gate_list = release_gate_sub.add_parser("list", help="List release-gate acceptance records")
    release_gate_list.add_argument("--json", action="store_true", help="Print gate acceptance records as JSON")
    release_gate_acceptance_brief = release_gate_sub.add_parser(
        "acceptance-brief",
        help="Print a read-only gate acceptance brief without accepting gates",
    )
    release_gate_acceptance_brief.add_argument("--json", action="store_true", help="Print gate acceptance brief as JSON")
    release_gate_status = release_sub.add_parser("gate-status", help="Summarize release gates and recorded evidence without closing gates")
    release_gate_status.add_argument("--json", action="store_true", help="Print gate status as JSON")
    release_checklist = release_sub.add_parser("readiness-checklist", help="Print a read-only release readiness checklist")
    release_checklist.add_argument("--root", default=".", help="Repository root to inspect")
    release_checklist.add_argument("--json", action="store_true", help="Print readiness checklist as JSON")
    runtime = sub.add_parser("runtime", help="Run the local Jarvis runtime")
    runtime_sub = runtime.add_subparsers(dest="runtime_command", required=True)
    runtime_serve = runtime_sub.add_parser("serve", help="Serve the runtime HUD on loopback by default")
    runtime_serve.add_argument("--host", default="127.0.0.1", help="Bind host; non-loopback requires --allow-non-loopback")
    runtime_serve.add_argument("--port", type=int, default=8765, help="Bind port")
    runtime_serve.add_argument(
        "--allow-non-loopback",
        action="store_true",
        help="Allow binding outside loopback for explicitly approved private-network use",
    )
    runtime_readiness = runtime_sub.add_parser("readiness", help="Print the non-writing runtime readiness summary")
    runtime_readiness.add_argument("--json", action="store_true", help="Print runtime readiness as JSON")
    mobile = sub.add_parser("mobile", help="Review private-network mobile access without probing or serving")
    mobile_sub = mobile.add_subparsers(dest="mobile_command", required=True)
    mobile_discover = mobile_sub.add_parser("discover", help="Discover local private-network host candidates without probing")
    mobile_discover.add_argument("--port", type=int, default=8765, help="Runtime port")
    mobile_discover.add_argument("--scheme", default="http", choices=["http", "https"], help="Runtime URL scheme")
    mobile_discover.add_argument("--json", action="store_true", help="Print mobile host discovery as JSON")
    mobile_preflight = mobile_sub.add_parser("preflight", help="Print a read-only mobile PWA access preflight")
    mobile_preflight.add_argument("--host", default="127.0.0.1", help="Runtime host or private-network address to classify")
    mobile_preflight.add_argument("--port", type=int, default=8765, help="Runtime port")
    mobile_preflight.add_argument("--scheme", default="http", choices=["http", "https"], help="Runtime URL scheme")
    mobile_preflight.add_argument("--json", action="store_true", help="Print mobile preflight as JSON")
    mobile_validation = mobile_sub.add_parser("validation-plan", help="Print a read-only iPhone/PWA validation plan")
    mobile_validation.add_argument("--host", default="127.0.0.1", help="Runtime host or private-network address to validate")
    mobile_validation.add_argument("--port", type=int, default=8765, help="Runtime port")
    mobile_validation.add_argument("--scheme", default="http", choices=["http", "https"], help="Runtime URL scheme")
    mobile_validation.add_argument("--json", action="store_true", help="Print mobile validation plan as JSON")
    mobile_evidence = mobile_sub.add_parser("evidence-brief", help="Print a read-only mobile operator evidence brief")
    mobile_evidence.add_argument("--host", default="127.0.0.1", help="Runtime host or private-network address to validate")
    mobile_evidence.add_argument("--port", type=int, default=8765, help="Runtime port")
    mobile_evidence.add_argument("--scheme", default="http", choices=["http", "https"], help="Runtime URL scheme")
    mobile_evidence.add_argument("--json", action="store_true", help="Print mobile evidence brief as JSON")
    gemini = sub.add_parser("gemini", help="Review Gemini Live feasibility without connecting to Gemini")
    gemini_sub = gemini.add_subparsers(dest="gemini_command", required=True)
    gemini_feasibility = gemini_sub.add_parser("feasibility", help="Print a read-only Gemini Live auth feasibility report")
    gemini_feasibility.add_argument("--json", action="store_true", help="Print Gemini feasibility as JSON")
    gemini_validation = gemini_sub.add_parser("validation-plan", help="Print a read-only Gemini Live connection validation plan")
    gemini_validation.add_argument("--json", action="store_true", help="Print Gemini validation plan as JSON")
    gemini_evidence = gemini_sub.add_parser("evidence-brief", help="Print a read-only Gemini Live operator evidence brief")
    gemini_evidence.add_argument("--json", action="store_true", help="Print Gemini evidence brief as JSON")
    gemini_nango = gemini_sub.add_parser("nango-plan", help="Print a read-only Nango/Gemini Live integration plan")
    gemini_nango.add_argument("--json", action="store_true", help="Print Nango/Gemini plan as JSON")
    loop = sub.add_parser("loop", help="Review autonomous loop readiness without mutation")
    loop_sub = loop.add_subparsers(dest="loop_command", required=True)
    loop_verify = loop_sub.add_parser("verify", help="Print a read-only loop readiness report")
    loop_verify.add_argument("--root", default=".", help="Repository root to inspect")
    loop_verify.add_argument("--json", action="store_true", help="Print loop readiness as JSON")
    loop_policy = loop_sub.add_parser("unattended-policy", help="Print a read-only unattended-loop policy report")
    loop_policy.add_argument("--root", default=".", help="Repository root to inspect")
    loop_policy.add_argument("--json", action="store_true", help="Print unattended-loop policy as JSON")
    loop_evidence = loop_sub.add_parser("unattended-evidence-brief", help="Print a read-only unattended-loop evidence brief")
    loop_evidence.add_argument("--root", default=".", help="Repository root to inspect")
    loop_evidence.add_argument("--json", action="store_true", help="Print unattended-loop evidence brief as JSON")
    loop_run_once = loop_sub.add_parser("run-once", help="Run one bounded autonomous loop iteration")
    loop_run_once.add_argument("--root", default=".", help="Repository root to inspect")
    loop_run_once.add_argument("--json", action="store_true", help="Print loop run result as JSON")
    loop_run_once.add_argument(
        "--allow-validation",
        action="store_true",
        help="Required confirmation to run fixed validators and write a loop-run record under --state",
    )
    loop_schedule = loop_sub.add_parser("schedule", help="Run a bounded foreground schedule of fixed loop iterations")
    loop_schedule.add_argument("--root", default=".", help="Repository root to inspect")
    loop_schedule.add_argument("--json", action="store_true", help="Print loop schedule result as JSON")
    loop_schedule.add_argument(
        "--allow-validation",
        action="store_true",
        help="Required confirmation to run fixed validators and write schedule records under --state",
    )
    loop_schedule.add_argument("--max-iterations", type=int, default=2, help="Bounded iteration count, 1 through 12")
    loop_schedule.add_argument("--interval-seconds", type=int, default=300, help="Sleep interval between iterations, 0 through 3600")
    doctor = sub.add_parser("doctor", help="Inspect state")
    doctor.add_argument("--governance", action="store_true", help="Include project-local Codex governance validation")

    args = parser.parse_args()
    state = JarvisState(Path(args.state))

    if args.command == "capture":
        episode = state.capture_episode(" ".join(args.text), source=args.source)
        print(json.dumps({"captured": episode.id}, sort_keys=True))
        return 0
    if args.command == "memory":
        if args.memory_command == "add":
            memory_item = state.add_memory(args.key, " ".join(args.value))
            print(json.dumps({"memory": memory_item.id}, sort_keys=True))
            return 0
        print(json.dumps(state.memories(), indent=2, sort_keys=True))
        return 0
    if args.command == "approve":
        request = state.request_approval(" ".join(args.summary))
        print(json.dumps({"approval": request.id}, sort_keys=True))
        return 0
    if args.command == "handoff":
        if args.json and not args.queue_summary:
            parser.error("handoff --json is only valid with --queue-summary")
        if args.queue_summary:
            safe_handoff = build_safe_handoff(Path(args.state))
            if args.json:
                print(render_safe_handoff_json(safe_handoff), end="")
            else:
                print(render_safe_handoff_markdown(safe_handoff), end="")
            return 0
        path = state.write_handoff(args.objective)
        print(json.dumps({"handoff": str(path)}, sort_keys=True))
        return 0
    if args.command == "hardware":
        profile = inspect_hardware()
        data = profile.to_dict()
        data["selected_workload"] = args.workload
        data["selected_backend"] = recommend_backend(profile, args.workload)
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    if args.command == "voice":
        if args.voice_command in {"discover", "probe", "ingest", "plan"} and not args.json:
            parser.error("voice commands are JSON-only; pass --json")
        if args.voice_command == "discover":
            roots = [Path(value) for value in args.search_root] if args.search_root else None
            result = discover_local_stt_assets(roots)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["status"] == "READY" else 1
        if args.voice_command == "probe":
            result = probe_audio_file(Path(args.audio_file), Path(args.model), args.stt_command)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["status"] == "PASS" else 1
        if args.voice_command == "ingest":
            if args.transcript_file:
                print(json.dumps(ingest_transcript_file(state, Path(args.transcript_file)), indent=2, sort_keys=True))
                return 0
            if not args.model:
                parser.error("voice ingest --audio-file requires --model")
            if not args.stt_command:
                parser.error("voice ingest --audio-file requires --stt-command")
            result = ingest_audio_file(
                state,
                Path(args.audio_file),
                Path(args.model),
                args.stt_command,
                args.allow_audio_processing,
                args.timeout_seconds,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["status"] == "captured" else 1
        if args.voice_command == "plan":
            proposal = propose_voice_intent(" ".join(args.transcript), profile=args.profile)
            print(json.dumps(proposal.to_dict(), indent=2, sort_keys=True))
            return 0
        if args.voice_command == "ask":
            transcript = " ".join(args.transcript)
            return _run_codex_voice_turn(args, transcript)
        if args.voice_command == "listen":
            record_command = args.record_command or os.environ.get("JARVIS_RECORD_COMMAND")
            if not record_command:
                discovery = discover_recorder_command()
                print(json.dumps(discovery.to_dict(), indent=2, sort_keys=True))
                return 1
            if not args.allow_microphone:
                result = {
                    "status": "approval-required",
                    "approval_required": "microphone",
                    "message": "Microphone recording requires --allow-microphone for this foreground command.",
                    "microphone_accessed": False,
                    "audio_processed": False,
                    "execution_authority": False,
                }
                print(json.dumps(result, indent=2, sort_keys=True))
                return 1
            if not args.allow_audio_processing:
                result = {
                    "status": "approval-required",
                    "approval_required": "audio-processing",
                    "message": "Local transcription requires --allow-audio-processing for this foreground command.",
                    "microphone_accessed": False,
                    "audio_processed": False,
                    "execution_authority": False,
                }
                print(json.dumps(result, indent=2, sort_keys=True))
                return 1
            try:
                recording = record_microphone_once(
                    state_dir=Path(args.state),
                    record_command=record_command,
                    seconds=args.seconds,
                    timeout_seconds=args.timeout_seconds,
                )
                stt = transcribe_with_local_adapter(
                    audio_file=recording.audio_file,
                    model_path=Path(args.model),
                    stt_command=args.stt_command,
                    timeout_seconds=args.timeout_seconds,
                )
            except (VoiceMicError, VoiceAudioError) as exc:
                print(json.dumps({"status": "failed", "error": str(exc), "execution_authority": False}, indent=2, sort_keys=True))
                return 1
            if args.json:
                print(json.dumps({"event_type": "microphone_recorded", **recording.to_dict()}, sort_keys=True))
                print(json.dumps({"event_type": "transcript_ready", **stt.to_dict()}, sort_keys=True))
            else:
                print(f"Transcript: {stt.transcript}")
            return _run_codex_voice_turn(args, stt.transcript)
    if args.command == "lane":
        if not args.json:
            parser.error("lane commands are JSON-only in this read-only first implementation; pass --json")
        repo = Path(args.repo)
        if args.lane_command == "list":
            print(json.dumps({"lanes": list_lanes(repo), "execution_authority": False}, indent=2, sort_keys=True))
            return 0
        if args.lane_command == "score":
            score = score_lane(repo, args.branch)
            payload = {
                "branch": args.branch,
                "repo": str(repo),
                "decision": score["decision"],
                "evidence": score["evidence"],
                "merge_recommendation": score["merge_recommendation"],
                "mutation_performed": False,
                "execution_authority": False,
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
    if args.command == "release":
        if not args.json:
            parser.error("release commands are JSON-only in this read-only first implementation; pass --json")
        if args.release_command == "manifest":
            print(json.dumps(build_release_manifest(Path(args.root)), indent=2, sort_keys=True))
            return 0
        if args.release_command == "packaging-preflight":
            print(json.dumps(build_packaging_preflight(Path(args.root)).to_dict(), indent=2, sort_keys=True))
            return 0
        if args.release_command == "packaging-evidence-brief":
            print(json.dumps(build_packaging_signing_evidence_brief(Path(args.root)), indent=2, sort_keys=True))
            return 0
        if args.release_command == "artifact-evidence":
            print(json.dumps(build_release_artifact_evidence(Path(args.root)), indent=2, sort_keys=True))
            return 0
        if args.release_command == "security-review-plan":
            print(json.dumps(build_external_security_review_plan(Path(args.root)), indent=2, sort_keys=True))
            return 0
        if args.release_command == "security-evidence-brief":
            print(json.dumps(build_external_security_evidence_brief(Path(args.root)), indent=2, sort_keys=True))
            return 0
        if args.release_command == "evidence":
            if args.release_evidence_command == "add":
                artifact = Path(args.artifact) if args.artifact else None
                evidence = state.record_release_evidence(args.gate, args.summary, args.reviewer, artifact)
                print(json.dumps({"state_write_performed": True, "evidence": evidence.__dict__}, indent=2, sort_keys=True))
                return 0
            if args.release_evidence_command == "list":
                print(json.dumps({"release_evidence": state.release_evidence(), "execution_authority": False}, indent=2, sort_keys=True))
                return 0
        if args.release_command == "gate":
            if args.release_gate_command == "accept":
                acceptance = state.accept_release_gate(args.gate, args.evidence_id, args.summary, args.reviewer)
                print(
                    json.dumps(
                        {
                            "state_write_performed": True,
                            "execution_authority": False,
                            "evidence_closes_gates": False,
                            "acceptance": acceptance.__dict__,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
                return 0
            if args.release_gate_command == "list":
                print(
                    json.dumps(
                        {"release_gate_acceptances": state.release_gate_acceptances(), "execution_authority": False},
                        indent=2,
                        sort_keys=True,
                    )
                )
                return 0
            if args.release_gate_command == "acceptance-brief":
                print(
                    json.dumps(
                        build_release_gate_acceptance_brief(state.release_evidence(), state.release_gate_acceptances()),
                        indent=2,
                        sort_keys=True,
                    )
                )
                return 0
        if args.release_command == "gate-status":
            print(json.dumps(build_release_gate_status(state.release_evidence(), state.release_gate_acceptances()), indent=2, sort_keys=True))
            return 0
        if args.release_command == "readiness-checklist":
            print(
                json.dumps(
                    build_release_readiness_checklist(Path(args.root), state.release_evidence(), state.release_gate_acceptances()),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
    if args.command == "runtime":
        if args.runtime_command == "readiness":
            if not args.json:
                parser.error("runtime readiness is JSON-only; pass --json")
            print(json.dumps(build_runtime_readiness(), indent=2, sort_keys=True))
            return 0
        if args.runtime_command == "serve":
            if not args.allow_non_loopback and not _is_loopback_host(args.host):
                parser.error("runtime serve binds to loopback by default; pass --allow-non-loopback for private-network use")
            uvicorn.run(create_app(Path(args.state)), host=args.host, port=args.port, log_level="info")
            return 0
    if args.command == "mobile":
        if not args.json:
            parser.error("mobile commands are JSON-only in this read-only first implementation; pass --json")
        if args.mobile_command == "discover":
            print(json.dumps(discover_mobile_hosts(args.port, args.scheme).to_dict(), indent=2, sort_keys=True))
            return 0
        if args.mobile_command == "preflight":
            print(json.dumps(build_mobile_preflight(args.host, args.port, args.scheme).to_dict(), indent=2, sort_keys=True))
            return 0
        if args.mobile_command == "validation-plan":
            print(json.dumps(build_mobile_validation_plan(args.host, args.port, args.scheme).to_dict(), indent=2, sort_keys=True))
            return 0
        if args.mobile_command == "evidence-brief":
            print(json.dumps(build_mobile_evidence_brief(args.host, args.port, args.scheme).to_dict(), indent=2, sort_keys=True))
            return 0
    if args.command == "gemini":
        if not args.json:
            parser.error("gemini commands are JSON-only in this read-only first implementation; pass --json")
        if args.gemini_command == "feasibility":
            print(json.dumps(build_gemini_feasibility().to_dict(), indent=2, sort_keys=True))
            return 0
        if args.gemini_command == "validation-plan":
            print(json.dumps(build_gemini_live_validation_plan().to_dict(), indent=2, sort_keys=True))
            return 0
        if args.gemini_command == "evidence-brief":
            print(json.dumps(build_gemini_live_evidence_brief().to_dict(), indent=2, sort_keys=True))
            return 0
        if args.gemini_command == "nango-plan":
            print(json.dumps(build_nango_gemini_live_integration_plan().to_dict(), indent=2, sort_keys=True))
            return 0
    if args.command == "loop":
        if not args.json:
            parser.error("loop commands are JSON-only in this read-only first implementation; pass --json")
        if args.loop_command == "verify":
            result = validate_loop_readiness(Path(args.root))
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["status"] == "PASS" else 1
        if args.loop_command == "unattended-policy":
            result = build_unattended_loop_policy(Path(args.root))
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["status"] == "ready-for-human-policy-review" else 1
        if args.loop_command == "unattended-evidence-brief":
            result = build_unattended_loop_evidence_brief(Path(args.root))
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["status"] == "READY_FOR_OPERATOR_REVIEW" else 1
        if args.loop_command == "run-once":
            if not args.allow_validation:
                parser.error("loop run-once requires --allow-validation")
            result = run_autonomous_loop_once(Path(args.root), Path(args.state), allow_validation=True)
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
            return 0 if result.status == "PASS" else 1
        if args.loop_command == "schedule":
            if not args.allow_validation:
                parser.error("loop schedule requires --allow-validation")
            result = run_autonomous_loop_schedule(
                Path(args.root),
                Path(args.state),
                allow_validation=True,
                max_iterations=args.max_iterations,
                interval_seconds=args.interval_seconds,
            )
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
            return 0 if result.status == "PASS" else 1
    if args.command == "doctor":
        data = state.doctor()
        if args.governance:
            governance = validate_phase1_governance()
            data["codex_governance"] = governance.compact_summary()
            print(json.dumps(data, indent=2, sort_keys=True))
            return 0 if governance.failure_count == 0 else 1
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0
    return 2


def _is_loopback_host(host: str) -> bool:
    return host in {"127.0.0.1", "localhost", "::1"}


def _add_codex_voice_turn_args(command: argparse.ArgumentParser) -> None:
    command.add_argument("--session", help="Existing Codex app-server thread id to continue")
    command.add_argument("--cwd", default=".", help="Working directory for the Codex turn")
    command.add_argument(
        "--approval-policy",
        choices=["untrusted", "on-failure", "on-request", "never"],
        default="on-request",
        help="Codex app-server approval policy",
    )
    command.add_argument(
        "--sandbox",
        choices=["read-only", "workspace-write", "danger-full-access"],
        default="workspace-write",
        help="Codex app-server sandbox mode",
    )
    command.add_argument("--codex-model", dest="codex_model", help="Optional Codex model override")
    command.add_argument("--effort", help="Optional reasoning effort override")
    command.add_argument(
        "--approval-mode",
        choices=["inline", "deny"],
        default="inline",
        help="How Jarvis responds to app-server approval requests",
    )
    command.add_argument("--no-daemon-start", action="store_true", help="Use direct app-server stdio instead of trying the managed daemon first")
    command.add_argument("--json", action="store_true", help="Print JSONL backend events")


def _run_codex_voice_turn(args: argparse.Namespace, transcript: str) -> int:
    config = CodexAppServerConfig(
        cwd=Path(args.cwd),
        session=args.session,
        approval_policy=args.approval_policy,
        sandbox=args.sandbox,
        model=args.codex_model,
        effort=args.effort,
        start_daemon=not args.no_daemon_start,
    )

    def approval_callback(params: dict[str, object]) -> bool:
        if args.approval_mode == "deny":
            return False
        return inline_approval_prompt(params)

    try:
        for event in run_codex_turn(transcript, config=config, approval_callback=approval_callback):
            payload = {
                **event.to_dict(),
                "agent_mode": "full",
                "approval_mode": args.approval_mode,
                "execution_authority": True,
            }
            if args.json:
                print(json.dumps(payload, sort_keys=True))
            else:
                _print_codex_event(payload)
        return 0
    except (CodexAppServerError, subprocess.CalledProcessError) as exc:
        error = {
            "status": "failed",
            "error": str(exc),
            "agent_mode": "full",
            "approval_mode": args.approval_mode,
            "execution_authority": True,
        }
        if args.json:
            print(json.dumps(error, sort_keys=True))
        else:
            print(f"Codex app-server failed: {exc}")
        return 1


def _print_codex_event(event: dict[str, object]) -> None:
    event_type = event.get("event_type")
    if event_type in {"agent_message_delta", "plan_delta", "terminal_output"}:
        print(str(event.get("text", "")), end="", flush=True)
        return
    if event_type == "thread_started":
        print(f"Thread: {event.get('thread_id')}")
        return
    if event_type == "thread_resumed":
        print(f"Thread: {event.get('thread_id')}")
        return
    if event_type == "turn_completed":
        print("\nTurn completed.")
        return
    if event_type == "approval_requested":
        return
    if event_type == "approval_responded":
        print("\nApproval response sent.")


if __name__ == "__main__":
    raise SystemExit(main())

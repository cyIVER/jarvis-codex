from __future__ import annotations

import argparse
import json
from pathlib import Path

import uvicorn

from .gemini import build_gemini_feasibility, build_gemini_live_validation_plan
from .governance import validate_phase1_governance
from .hardware import inspect_hardware, recommend_backend
from .lanes import list_lanes, score_lane
from .loop_readiness import validate_loop_readiness
from .mobile import build_mobile_preflight, build_mobile_validation_plan, discover_mobile_hosts
from .packaging import build_packaging_preflight
from .release import build_release_manifest
from .runtime_app import build_runtime_readiness, create_app
from .safe_handoff import build_safe_handoff, render_safe_handoff_json, render_safe_handoff_markdown
from .state import JarvisState
from .voice import discover_local_stt_assets, ingest_audio_file, ingest_transcript_file, probe_audio_file


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
    gemini = sub.add_parser("gemini", help="Review Gemini Live feasibility without connecting to Gemini")
    gemini_sub = gemini.add_subparsers(dest="gemini_command", required=True)
    gemini_feasibility = gemini_sub.add_parser("feasibility", help="Print a read-only Gemini Live auth feasibility report")
    gemini_feasibility.add_argument("--json", action="store_true", help="Print Gemini feasibility as JSON")
    gemini_validation = gemini_sub.add_parser("validation-plan", help="Print a read-only Gemini Live connection validation plan")
    gemini_validation.add_argument("--json", action="store_true", help="Print Gemini validation plan as JSON")
    loop = sub.add_parser("loop", help="Review autonomous loop readiness without mutation")
    loop_sub = loop.add_subparsers(dest="loop_command", required=True)
    loop_verify = loop_sub.add_parser("verify", help="Print a read-only loop readiness report")
    loop_verify.add_argument("--root", default=".", help="Repository root to inspect")
    loop_verify.add_argument("--json", action="store_true", help="Print loop readiness as JSON")
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
        if not args.json:
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
    if args.command == "gemini":
        if not args.json:
            parser.error("gemini commands are JSON-only in this read-only first implementation; pass --json")
        if args.gemini_command == "feasibility":
            print(json.dumps(build_gemini_feasibility().to_dict(), indent=2, sort_keys=True))
            return 0
        if args.gemini_command == "validation-plan":
            print(json.dumps(build_gemini_live_validation_plan().to_dict(), indent=2, sort_keys=True))
            return 0
    if args.command == "loop":
        if not args.json:
            parser.error("loop commands are JSON-only in this read-only first implementation; pass --json")
        if args.loop_command == "verify":
            result = validate_loop_readiness(Path(args.root))
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["status"] == "PASS" else 1
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


if __name__ == "__main__":
    raise SystemExit(main())

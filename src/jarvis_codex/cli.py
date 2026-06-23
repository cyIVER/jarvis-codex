from __future__ import annotations

import argparse
import json
from pathlib import Path

from .governance import validate_phase1_governance
from .hardware import inspect_hardware, recommend_backend
from .lanes import list_lanes, score_lane
from .release import build_release_manifest
from .safe_handoff import build_safe_handoff, render_safe_handoff_json, render_safe_handoff_markdown
from .state import JarvisState


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


if __name__ == "__main__":
    raise SystemExit(main())

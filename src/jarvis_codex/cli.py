from __future__ import annotations

import argparse
import json
from pathlib import Path

from .hardware import inspect_hardware, recommend_backend
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

    hardware = sub.add_parser("hardware", help="Inspect local acceleration capabilities")
    hardware.add_argument(
        "--workload",
        choices=["general", "llm", "vision", "voice", "video", "background"],
        default="general",
        help="Workload to recommend a backend for",
    )

    sub.add_parser("doctor", help="Inspect state")

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
    if args.command == "doctor":
        print(json.dumps(state.doctor(), indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

# Jarvis Codex Overhaul Wrap-Up

## Overview
This document summarizes the architecture direction for transitioning `jarvis-codex` from a local-first read-only state viewer toward a governed continuity system capable of supporting approval-gated agent loops.

Some items below are implemented package logic, while others are held-out design work that requires separate review and approval before CLI wiring, runtime execution, or commit inclusion.

## 1. Architectural Contract
The proposed operational boundaries are drafted in `plans/jarvis-codex-swarm/jarvis-architecture-contract.yaml`.
- **Codex Reference:** Treat this YAML file as a planning artifact until it is separately reviewed and approved. It must not override committed governance policy, user approval gates, or current CLI behavior.

## 2. Lane Governance & Decision Scoring (`src/jarvis_codex/lanes.py`)
Worktrunk lane management is held out for a separate package review. Proposed commands include:
- `jarvis-codex lane list`
- `jarvis-codex lane refresh <name>`
- `jarvis-codex lane abandon <name>`

**Decision Scoring:**
The held-out lane design scores lanes into three labels (`ready`, `needs-review`, `blocked`) based on working tree status.
- **Codex Reference:** This is not current execution authority. Lane commands, lane mutation behavior, and `WorkerContract` logging require separate review and approval before use.

## 3. Hardware Preflight Gates (`src/jarvis_codex/hardware.py`)
Hardware preflight package logic exists in `src/jarvis_codex/hardware.py` to classify CUDA, Docker, and Windows NPU recommendations as approval-sensitive.
- The package logic can read an approval flag and append decisions to `state/logs/hardware_gate_checks.jsonl`.
- CLI wiring for `jarvis-codex hardware --workload <type> --preflight` is held out and not part of the clean governance commit.
- CLI behavior for `jarvis-codex approve hardware-flag --approve` is held out and not currently approved.
- A preflight decision or log entry is not permission to execute local ML, GPU, Docker, service, daemon, or runtime workflows. Execution requires explicit user approval.

## 4. State Continuity & Durable Queues (`src/jarvis_codex/plan_viewer.py`)
Plan-viewer continuity and durable queue behavior are held out for a separate package review.
- Proposed behavior includes a "State Continuity Card" and an approval endpoint for durable queue entries.
- **Codex Reference:** Do not rely on `state/next-steps/queue.json`, `/api/approve-queue`, or plan-viewer queue actions as execution authority until the plan-viewer package is separately reviewed and approved.

## 5. Voice Ingress Deduplication
Hook classification changes are held out with the notification package.
- **Codex Reference:** `jarvis_codex.notifications.get_pack_hints` is proposed as the shared routing helper, but hook integration requires separate review before operational use.

## Next Steps for Approval-Gated Operation
1. Review and validate the hardware preflight package without reintroducing held-out CLI wiring.
2. Review lane management, plan-viewer queue behavior, and notification routing as separate packages.
3. Keep autonomous operation planning-only until every runtime workflow, state write, Worktrunk mutation, local ML action, Docker action, and patching step has explicit user approval.

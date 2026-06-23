# Jarvis Codex Overhaul Wrap-Up

## Overview
This document summarizes the architecture direction for transitioning `jarvis-codex` from a local-first state viewer toward a governed continuity system capable of supporting approval-gated agent loops.

The packages below are now committed as local planning, review, and governance primitives. Runtime execution, Worktrunk mutation, local ML work, Docker work, service launch, and git mutation remain approval-gated.

## 1. Architectural Contract
The operational boundaries are drafted in `plans/jarvis-codex-swarm/jarvis-architecture-contract.yaml`.
- **Codex Reference:** Treat this YAML file as a planning artifact. It must not override committed governance policy, user approval gates, or current CLI behavior.

## 2. Lane Governance & Decision Scoring (`src/jarvis_codex/lanes.py`)
Read-only lane inventory and decision scoring package logic is committed in `src/jarvis_codex/lanes.py`.

**Decision Scoring:**
The lane design scores lanes into three labels (`ready`, `needs-review`, `blocked`) based on read-only working tree status.
- **Codex Reference:** This is not execution authority. Lane commands and lane mutation behavior require separate review and approval before use. `WorkerContract` records are planning records with `execution_authority: false`.

## 3. Hardware Preflight Gates (`src/jarvis_codex/hardware.py`)
Hardware preflight package logic exists in `src/jarvis_codex/hardware.py` to classify CUDA, Docker, and Windows NPU recommendations as approval-sensitive.
- The package logic can read an approval flag and append decisions to `state/logs/hardware_gate_checks.jsonl`.
- CLI wiring for `jarvis-codex hardware --workload <type> --preflight` is held out and not part of the clean governance commit.
- CLI behavior for `jarvis-codex approve hardware-flag --approve` is held out and not currently approved.
- A preflight decision or log entry is not permission to execute local ML, GPU, Docker, service, daemon, or runtime workflows. Execution requires explicit user approval.

## 4. State Continuity & Durable Queues (`src/jarvis_codex/plan_viewer.py`)
Plan-viewer continuity and planning queue behavior are committed in `src/jarvis_codex/plan_viewer.py`.
- Current behavior includes a state continuity card, next-step selection, and `/api/approve-queue` for writing local planning queue entries.
- **Codex Reference:** Do not rely on `state/next-steps/queue.json`, `/api/approve-queue`, or plan-viewer queue actions as execution authority. Queue entries are planning state only.

## 5. Voice Ingress Deduplication
Notification pack hint routing is committed in `jarvis_codex.notifications.get_pack_hints`.
- **Codex Reference:** This helper returns routing hints only. Hook integration and any action triggered from a notification require separate review before operational use.

## Next Steps for Approval-Gated Operation
1. Keep autonomous operation planning-only until every runtime workflow, state write, Worktrunk mutation, local ML action, Docker action, and patching step has explicit user approval.
2. Add CLI wiring for lane or hardware mutation only after exact command semantics, tests, and rollback expectations are approved.
3. Continue to use `jarvis-codex doctor --governance`, the Phase 1 validator, package tests, and architecture validation as readiness checks.

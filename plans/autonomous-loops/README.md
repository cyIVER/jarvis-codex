# Jarvis Codex Loop Planning Artifacts

This directory contains planning artifacts for future loop-based Jarvis Codex operation, inspired by the Two-Loop Architecture from the **AI-Research-SKILLs** repository.

These files are not execution authority. They do not approve installs, service launches, local ML runs, Docker runs, Worktrunk mutation, git mutation, code edits, documentation edits, or workflow execution. Each runtime action remains approval-gated by the user and by the relevant Jarvis governance checks.

## The Strategy

Traditional task-execution agents often fail in long-horizon tasks because they get stuck in an optimization loop without reflecting, or they reflect too much without making progress. The **Two-Loop Architecture** is useful as a planning model:

1. **Inner Loop (Optimization)**: Fast, constrained, and measurable. Designed to propose code, test, and lane work after explicit approval.
2. **Outer Loop (Synthesis)**: Periodic, reflective, and direction-setting. Designed to propose architecture-contract, documentation, and handoff updates after explicit approval.

## The Loops

- `01-engineering-inner-loop.yaml`: Planning model for task selection, lane proposals, test proposals, and WorkerContract records. It must not mutate code, git, Worktrunk lanes, or runtime state without explicit approval.
- `02-architecture-outer-loop.yaml`: Planning model for synthesis. It can propose reviews of `lane_decisions.jsonl`, architecture contract updates, docs updates, and handoffs, but does not authorize writing those artifacts.
- `03-hardware-optimization-loop.yaml`: Planning model for hardware backend evaluation. It requires explicit approval before workload execution, benchmark writes, patches, docs updates, or local runtime actions.

## Implementation Details for Codex
Codex can parse these YAML files as behavioral guidelines only. The `trigger` conditions identify when a planning proposal may be useful; they do not authorize execution.

Before any action derived from these files, produce an approval handoff that states:

- the exact command or file edit proposed
- expected writes and side effects
- validation commands
- rollback or inspection notes
- why the action is not covered by existing read-only governance

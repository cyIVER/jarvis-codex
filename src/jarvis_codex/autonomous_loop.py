from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .codeburn import read_codeburn_status
from .governance import validate_phase1_governance
from .loop_readiness import validate_loop_readiness
from .runtime_app import build_runtime_readiness


@dataclass(frozen=True)
class LoopRunResult:
    run_id: str
    created_at: int
    status: str
    root: str
    state_root: str
    level: str
    pattern: str
    checks_run: list[str]
    checks_passed: int
    failures: list[dict[str, Any]]
    warnings: list[str]
    writes_state: bool
    execution_authority: bool
    arbitrary_command_execution: bool
    service_launch_performed: bool
    network_probe_performed: bool
    git_mutation_performed: bool
    worktrunk_mutation_performed: bool
    record_path: str
    log_path: str
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_autonomous_loop_once(
    root: Path,
    state_root: Path,
    *,
    allow_validation: bool = False,
    pattern: str = "product-readiness-triage",
    level: str = "L1",
) -> LoopRunResult:
    """Run one bounded Jarvis loop iteration and record local evidence.

    This intentionally runs only fixed validation/readiness collectors plus the
    fixed no-shell Codeburn telemetry adapter. It does not accept user-supplied
    command strings or launch services.
    """
    if not allow_validation:
        raise ValueError("loop run-once requires allow_validation=True")

    resolved_root = root.resolve()
    resolved_state = state_root.resolve()
    run_id = f"loop_{uuid.uuid4().hex[:12]}"
    created_at = int(time.time())

    governance = validate_phase1_governance(resolved_root)
    loop_readiness = validate_loop_readiness(resolved_root)
    runtime_readiness = build_runtime_readiness(resolved_root)
    codeburn = read_codeburn_status().to_dict()

    failures: list[dict[str, Any]] = []
    warnings: list[str] = []
    if governance.failure_count:
        failures.append({"check": "governance", "status": governance.status, "failures": governance.failure_count})
    if loop_readiness.get("status") != "PASS":
        failures.append(
            {
                "check": "loop_readiness",
                "status": loop_readiness.get("status"),
                "failures": loop_readiness.get("failures", 0),
            }
        )
    if runtime_readiness.get("status") != "foundation-ready":
        warnings.append(f"runtime readiness status is {runtime_readiness.get('status') or 'unknown'}")
    if not codeburn.get("available"):
        warnings.append("codeburn status unavailable")

    status = "PASS" if not failures else "FAIL"
    record_dir = resolved_state / "loop-runs"
    log_path = resolved_state / "logs" / "loop-runs.jsonl"
    record_path = record_dir / f"{run_id}.json"

    result = LoopRunResult(
        run_id=run_id,
        created_at=created_at,
        status=status,
        root=str(resolved_root),
        state_root=str(resolved_state),
        level=level,
        pattern=pattern,
        checks_run=["governance", "loop_readiness", "runtime_readiness", "codeburn_status"],
        checks_passed=4 - len(failures),
        failures=failures,
        warnings=warnings,
        writes_state=True,
        execution_authority=False,
        arbitrary_command_execution=False,
        service_launch_performed=False,
        network_probe_performed=False,
        git_mutation_performed=False,
        worktrunk_mutation_performed=False,
        record_path=str(record_path),
        log_path=str(log_path),
        evidence={
            "governance": governance.compact_summary(),
            "loop_readiness": {
                "status": loop_readiness.get("status"),
                "checks_passed": loop_readiness.get("checks_passed"),
                "failures": loop_readiness.get("failures"),
                "execution_authority": loop_readiness.get("execution_authority"),
                "writes_files": loop_readiness.get("writes_files"),
            },
            "runtime_readiness": {
                "status": runtime_readiness.get("status"),
                "production_complete": runtime_readiness.get("production_complete"),
                "writes_state": runtime_readiness.get("writes_state"),
                "remaining_gaps": runtime_readiness.get("remaining_gaps"),
            },
            "codeburn": {
                "available": codeburn.get("available"),
                "today_cost": codeburn.get("today_cost"),
                "today_calls": codeburn.get("today_calls"),
                "month_cost": codeburn.get("month_cost"),
                "month_calls": codeburn.get("month_calls"),
                "writes_state": codeburn.get("writes_state"),
                "shell": codeburn.get("shell"),
            },
        },
    )

    _write_loop_record(record_path, log_path, result.to_dict())
    return result


def _write_loop_record(record_path: Path, log_path: Path, payload: dict[str, Any]) -> None:
    record_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")

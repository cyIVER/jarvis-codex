from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LoopCheck:
    name: str
    status: str
    path: str
    note: str


REQUIRED_FILES = {
    "state": "STATE.md",
    "loop": "LOOP.md",
    "budget": "loop-budget.md",
    "run_log": "loop-run-log.md",
    "safety": "docs/safety.md",
    "product_readiness": "docs/PRODUCT_READINESS.md",
    "ci": ".github/workflows/ci.yml",
}


FORBIDDEN_RUNTIME_MARKERS = [
    "jarvis_worker_fixer.toml",
    'sandbox_mode = "workspace-write"',
    "git push",
    "git reset",
    "git clean",
    "git rebase",
    "git merge",
    "npm run render",
    "npm run still",
]


def _check_file(root: Path, name: str, relative_path: str) -> LoopCheck:
    path = root / relative_path
    if path.exists():
        return LoopCheck(name=name, status="pass", path=relative_path, note="present")
    return LoopCheck(name=name, status="fail", path=relative_path, note="missing")


def _check_text_contains(root: Path, name: str, relative_path: str, marker: str) -> LoopCheck:
    path = root / relative_path
    if not path.exists():
        return LoopCheck(name=name, status="fail", path=relative_path, note="missing")
    text = path.read_text(encoding="utf-8", errors="replace")
    if marker in text:
        return LoopCheck(name=name, status="pass", path=relative_path, note=f"contains {marker!r}")
    return LoopCheck(name=name, status="fail", path=relative_path, note=f"missing {marker!r}")


def _check_forbidden_markers(root: Path) -> list[LoopCheck]:
    checks: list[LoopCheck] = []
    scanned_files = [root / ".github/workflows/ci.yml"]
    for marker in FORBIDDEN_RUNTIME_MARKERS:
        found = []
        for path in scanned_files:
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                if marker in line and "not" not in line.lower() and "no " not in line.lower():
                    found.append(str(path.relative_to(root)))
                    break
        checks.append(
            LoopCheck(
                name=f"forbidden marker: {marker}",
                status="fail" if found else "pass",
                path=", ".join(found) if found else "",
                note="unexpected executable authority marker found" if found else "not present outside negative guardrails",
            )
        )
    return checks


def validate_loop_readiness(root: Path) -> dict[str, Any]:
    """Validate the local autonomous-loop readiness surface without writing files."""
    root = root.resolve()
    checks = [_check_file(root, name, relative_path) for name, relative_path in REQUIRED_FILES.items()]
    checks.extend(
        [
            _check_text_contains(root, "loop status active", "STATE.md", "loop_status: active"),
            _check_text_contains(root, "loop level recorded", "STATE.md", "level: L1"),
            _check_text_contains(root, "ci runs pytest", ".github/workflows/ci.yml", "uv run pytest"),
            _check_text_contains(
                root,
                "ci validates governance",
                ".github/workflows/ci.yml",
                "python3 scripts/validate-jarvis-codex-phase1.py",
            ),
            _check_text_contains(root, "release manifest documented", "docs/RELEASE_ARTIFACTS.md", "release manifest --json"),
        ]
    )
    checks.extend(_check_forbidden_markers(root))

    failures = [check for check in checks if check.status == "fail"]
    return {
        "label": "Jarvis Codex loop readiness",
        "status": "PASS" if not failures else "FAIL",
        "root": str(root),
        "execution_authority": False,
        "writes_files": False,
        "checks_passed": len(checks) - len(failures),
        "failures": len(failures),
        "failure_details": [check.__dict__ for check in failures],
        "checks": [check.__dict__ for check in checks],
    }

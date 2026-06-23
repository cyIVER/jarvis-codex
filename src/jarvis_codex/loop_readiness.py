from __future__ import annotations

import re
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
SCAN_DIRS = [".github", ".codex", ".agents", ".hooks", "bin", "config", "lib", "packages", "scripts", "src", "tests"]
SCAN_FILES = [
    "STATE.md",
    "LOOP.md",
    "Makefile",
    "package.json",
    "docs/safety.md",
    "docs/PRODUCT_READINESS.md",
    "docs/jarvis-harness/production-readiness.md",
]
SCAN_SUFFIXES = {
    "",
    ".bash",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".yml",
    ".yaml",
    ".zsh",
}
SCAN_FILE_NAMES = {"package.json"}
SKIP_TOP_LEVEL_PARTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}
SECTION_GUARDRAIL_PHRASES = {
    "approval-gated actions",
    "approval gates",
    "deny list",
    "disallowed tools/actions",
    "forbidden",
    "must not perform",
    "must not run",
    "must not run or authorize",
    "never run",
    "safety gates",
    "without explicit approval",
}
TEST_EXECUTION_PHRASES = {"check_call", "check_output", "os.system", "popen", "subprocess."}
SPLIT_COMMAND_PATTERNS = {
    "git push": ("git\", \"push", "git', 'push", "git\" + \" push", "git' + ' push"),
    "git reset": ("git\", \"reset", "git', 'reset", "git\" + \" reset", "git' + ' reset"),
    "git clean": ("git\", \"clean", "git', 'clean", "git\" + \" clean", "git' + ' clean"),
    "git rebase": ("git\", \"rebase", "git', 'rebase", "git\" + \" rebase", "git' + ' rebase"),
    "git merge": ("git\", \"merge", "git', 'merge", "git\" + \" merge", "git' + ' merge"),
}
MARKER_REGEXES = {
    'sandbox_mode = "workspace-write"': re.compile(r"\bsandbox_mode\s*=\s*['\"]workspace-write['\"]", re.I),
    "git push": re.compile(r"\bgit\s+push\b", re.I),
    "git reset": re.compile(r"\bgit\s+reset\b", re.I),
    "git clean": re.compile(r"\bgit\s+clean\b", re.I),
    "git rebase": re.compile(r"\bgit\s+rebase\b", re.I),
    "git merge": re.compile(r"\bgit\s+merge\b", re.I),
    "npm run render": re.compile(r"\bnpm\s+run\s+render\b", re.I),
    "npm run still": re.compile(r"\bnpm\s+run\s+still\b", re.I),
}


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
    scanned_files = _iter_marker_scan_files(root)
    for marker in FORBIDDEN_RUNTIME_MARKERS:
        found = []
        for path in scanned_files:
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            for index, line in enumerate(lines):
                if _marker_in_line(marker, line) and not _line_is_negative_guardrail(path, lines, index, marker):
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


def _iter_marker_scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for relative in SCAN_FILES:
        path = root / relative
        if path.exists() and path.is_file():
            files.append(path)
    for relative in SCAN_DIRS:
        path = root / relative
        if not path.exists() or not path.is_dir():
            continue
        for candidate in path.rglob("*"):
            if _skip_scan_candidate(root, candidate):
                continue
            files.append(candidate)
    for candidate in root.rglob("*"):
        if not candidate.is_file() or candidate.name not in SCAN_FILE_NAMES:
            continue
        if _skip_scan_candidate(root, candidate):
            continue
        files.append(candidate)
    for candidate in root.iterdir():
        if candidate.is_file() and candidate.suffix in SCAN_SUFFIXES:
            files.append(candidate)
    return sorted(set(files))


def _skip_scan_candidate(root: Path, candidate: Path) -> bool:
    if not candidate.is_file() or candidate.suffix not in SCAN_SUFFIXES:
        return True
    relative_parts = candidate.relative_to(root).parts
    return any(part in SKIP_TOP_LEVEL_PARTS or part == "node_modules" for part in relative_parts)


def _marker_in_line(marker: str, line: str) -> bool:
    if MARKER_REGEXES.get(marker) and MARKER_REGEXES[marker].search(line):
        return True
    if marker in line:
        return True
    return any(pattern in line for pattern in SPLIT_COMMAND_PATTERNS.get(marker, ()))


def _line_is_negative_guardrail(path: Path, lines: list[str], index: int, marker: str) -> bool:
    line = lines[index].lower()
    if "tests" in path.parts:
        if path.name == "test_loop_readiness.py":
            return True
        return not _test_marker_has_nearby_execution(lines, index)

    if path.suffix == ".py":
        if _is_known_guardrail_definition(path, line, marker):
            return True
        start = max(0, index - 12)
        end = min(len(lines), index + 3)
        context = " ".join(lines[start:end]).lower()
        if path.name == "plan_viewer.py" and "command:" in line and "status: 'gated'" in context:
            return True
        return False

    if path.suffix in {".md", ".toml", ".yml", ".yaml"}:
        if ".github" in path.parts and path.suffix in {".yml", ".yaml"}:
            return False
        start = max(0, index - 12)
        context = " ".join(lines[start : index + 1]).lower()
        return any(phrase in context for phrase in SECTION_GUARDRAIL_PHRASES)

    return False


def _test_marker_has_nearby_execution(lines: list[str], index: int) -> bool:
    start = max(0, index - 2)
    end = min(len(lines), index + 4)
    text = "\n".join(lines[start:end]).lower()
    return any(phrase in text for phrase in TEST_EXECUTION_PHRASES)


def _is_known_guardrail_definition(path: Path, line: str, marker: str) -> bool:
    stripped = line.strip()
    quoted_marker_lines = {f'"{marker}",', f"'{marker}',"}
    if path.name == "loop_readiness.py":
        return (
            stripped in quoted_marker_lines
            or ": re.compile(" in stripped
            or any(pattern in stripped for pattern in SPLIT_COMMAND_PATTERNS.get(marker, ()))
            or "jarvis_worker_fixer.toml is absent" in stripped
        )
    if path.name == "governance.py":
        return (
            stripped in quoted_marker_lines
            or "worker_fixer_path=agent_dir" in stripped
            or 'pass_("jarvis_worker_fixer.toml is absent.")' in stripped
        )
    if path.name == "policy.py":
        return (
            "destructive git" in stripped
            or "hardline" in stripped
            or "git mutation" in stripped
            or "lowered[:2]" in stripped
        )
    return False


def validate_loop_readiness(root: Path) -> dict[str, Any]:
    """Validate the local autonomous-loop readiness surface without writing files."""
    root = root.resolve()
    checks = [_check_file(root, name, relative_path) for name, relative_path in REQUIRED_FILES.items()]
    checks.extend(
        [
            _check_text_contains(root, "loop status active", "STATE.md", "loop_status: active"),
            _check_text_contains(root, "loop level recorded", "STATE.md", "level: L1"),
            _check_text_contains(root, "loop budget records manual cadence", "loop-budget.md", "manual/operator-requested"),
            _check_text_contains(root, "loop budget records token cap", "loop-budget.md", "Suggested token cap per loop cycle"),
            _check_text_contains(root, "loop budget records kill switches", "loop-budget.md", "## Kill Switches"),
            _check_text_contains(root, "loop budget records escalation rules", "loop-budget.md", "## Escalation Rules"),
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


def build_unattended_loop_policy(root: Path) -> dict[str, Any]:
    """Summarize unattended-loop policy readiness without starting loops or writing state."""
    root = root.resolve()
    readiness = validate_loop_readiness(root)
    readiness_passed = readiness["status"] == "PASS"
    return {
        "label": "Jarvis Codex unattended loop policy",
        "status": "ready-for-human-policy-review" if readiness_passed else "needs-readiness-fixes",
        "root": str(root),
        "writes_files": False,
        "writes_state": False,
        "execution_authority": False,
        "arbitrary_command_execution": False,
        "service_launch_performed": False,
        "daemon_started": False,
        "scheduler_backgrounded": False,
        "network_probe_performed": False,
        "git_mutation_performed": False,
        "worktrunk_mutation_performed": False,
        "release_gate_closed": False,
        "human_acceptance_required": True,
        "approved_for_unattended_operation": False,
        "background_scheduler_implemented": False,
        "bounded_foreground_schedule_available": True,
        "bounded_foreground_schedule_command": (
            "jarvis-codex --state <state-dir> loop schedule "
            "--allow-validation --max-iterations <1-12> --interval-seconds <0-3600> --json"
        ),
        "read_only_verification_command": "jarvis-codex loop verify --json",
        "required_policy_evidence": [
            "accepted loop-budget manual/operator-requested cadence",
            "accepted token cap per loop cycle",
            "accepted kill switches",
            "accepted escalation rules",
            "human-visible run log location and review cadence",
            "explicit decision on whether unattended/background scheduling may be enabled",
        ],
        "operator_stop_controls": [
            "do not run as a daemon or background service",
            "keep foreground schedule capped to 12 iterations or fewer",
            "keep interval_seconds between 0 and 3600",
            "stop after any validation failure and inspect recorded evidence",
        ],
        "approval_required_before": [
            "starting any daemon or background scheduler",
            "expanding beyond fixed validators/readiness collectors",
            "running arbitrary commands",
            "launching services, agents, PTYs, Worktrunk, or Git mutation from loop policy",
            "treating loop evidence as release gate closure",
        ],
        "unsafe_actions_not_authorized": [
            "launch daemons",
            "run background schedulers",
            "execute arbitrary commands",
            "start services",
            "probe networks",
            "mutate Git",
            "mutate Worktrunk",
            "close release gates",
        ],
        "remaining_release_gates": ["unattended_loop_scheduling"],
        "readiness_summary": {
            "status": readiness["status"],
            "checks_passed": readiness["checks_passed"],
            "failures": readiness["failures"],
            "execution_authority": readiness["execution_authority"],
            "writes_files": readiness["writes_files"],
        },
        "notes": [
            "This policy report is read-only evidence.",
            "The existing loop schedule command is foreground and bounded.",
            "This report does not authorize unattended operation or close the unattended_loop_scheduling release gate.",
        ],
    }

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def discover_default_repo(start: Path | None = None) -> Path:
    """Find the project root for the checked-out Jarvis Codex repository."""
    current = (start or Path(__file__)).resolve()
    for candidate in (current.parent, *current.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / ".codex" / "config.toml").exists():
            return candidate
    return current.parents[2]


DEFAULT_REPO = discover_default_repo()

EXPECTED_AGENTS = {
    "jarvis_explorer.toml",
    "jarvis_reviewer.toml",
    "jarvis_docs_researcher.toml",
    "jarvis_worktrunk_planner.toml",
}

EXPECTED_SKILLS = {
    "jarvis-gate-stabilization",
    "worktrunk-lane-governance",
    "approval-handoff-briefing",
    "local-state-continuity",
    "ipc-orchestration-review",
    "safe-cli-handoff",
    "agent-skill-governance",
}

REQUIRED_AGENT_POLICY_TEXT = {
    "allowed skills": "Allowed skills:",
    "disallowed skills": "Disallowed skills:",
    "allowed MCP servers": "Allowed MCP servers:",
    "disallowed MCP servers": "Disallowed MCP servers:",
    "allowed tools/actions": "Allowed tools/actions:",
    "disallowed tools/actions": "Disallowed tools/actions:",
    "structured output expectations": "Return structured output",
}

REQUIRED_SKILL_SECTIONS = [
    "# Purpose",
    "# When to use",
    "# When not to use",
    "# Tool expectations",
    "# Workflow",
    "# Expected output",
    "# Guardrails",
    "# Validation",
]

CONFIG_FORBIDDEN_KEYS = {
    "model_provider",
    "model_providers",
    "provider",
    "providers",
    "auth",
    "api_key",
    "api_keys",
    "token",
    "tokens",
    "telemetry",
    "otel",
    "notify",
    "notifications",
    "mcp_servers",
}

CONFIG_FORBIDDEN_PATTERNS = [
    re.compile(r"\[\[skills\.config\]\]", re.IGNORECASE),
    re.compile(r"enabled\s*=\s*false", re.IGNORECASE),
    re.compile(r"\bapi[_-]?key\b", re.IGNORECASE),
    re.compile(r"\bsecret\b", re.IGNORECASE),
    re.compile(r"\btoken\b", re.IGNORECASE),
    re.compile(r"\btelemetry\b", re.IGNORECASE),
    re.compile(r"\botel\b", re.IGNORECASE),
    re.compile(r"\bnotify\b", re.IGNORECASE),
    re.compile(r"\[mcp_servers(?:\.|\])", re.IGNORECASE),
]

ACTIVATION_PATTERNS = [
    ".local/share/ai-env",
    "skills/extracted",
    "extracted skill catalogs",
    "temp plugin",
    "temporary plugin",
    "plugin-cache",
    "plugins/cache",
    "[[skills.config]]",
    "enabled = false",
    'sandbox_mode = "workspace-write"',
    "jarvis_worker_fixer",
]


@dataclass
class SectionResult:
    passed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def pass_(self, message: str) -> None:
        self.passed.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def fail(self, message: str) -> None:
        self.failures.append(message)


@dataclass
class GovernanceValidationResult:
    sections: dict[str, SectionResult]

    @property
    def checks_passed(self) -> int:
        return sum(len(section.passed) for section in self.sections.values())

    @property
    def warning_count(self) -> int:
        return sum(len(section.warnings) for section in self.sections.values())

    @property
    def failure_count(self) -> int:
        return sum(len(section.failures) for section in self.sections.values())

    @property
    def status(self) -> str:
        return "PASS" if self.failure_count == 0 else "FAIL"

    @property
    def failures(self) -> list[str]:
        return [item for section in self.sections.values() for item in section.failures]

    def compact_summary(self) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "label": "project-local Codex governance",
            "status": self.status,
            "checks_passed": self.checks_passed,
            "warnings": self.warning_count,
            "failures": self.failure_count,
            "writes_reports": False,
            "not_test_replacement": True,
        }
        if self.failures:
            summary["failure_details"] = self.failures[:10]
        return summary


@dataclass(frozen=True)
class GovernancePaths:
    repo: Path
    codex_dir: Path
    agent_dir: Path
    skill_dir: Path
    config_path: Path
    worker_fixer_path: Path

    @classmethod
    def from_repo(cls, repo: Path) -> "GovernancePaths":
        codex_dir = repo / ".codex"
        agent_dir = codex_dir / "agents"
        skill_dir = repo / ".agents" / "skills"
        return cls(
            repo=repo,
            codex_dir=codex_dir,
            agent_dir=agent_dir,
            skill_dir=skill_dir,
            config_path=codex_dir / "config.toml",
            worker_fixer_path=agent_dir / "jarvis_worker_fixer.toml",
        )


def validate_phase1_governance(repo: Path = DEFAULT_REPO) -> GovernanceValidationResult:
    paths = GovernancePaths.from_repo(repo)
    return GovernanceValidationResult(
        sections={
            "Config Checks": check_config(paths),
            "Agent Checks": check_agents(paths),
            "Skill Checks": check_skills(paths),
            "Activation Safety Checks": check_activation_safety(paths),
        }
    )


def load_toml(path: Path, result: SectionResult) -> dict[str, Any] | None:
    if not path.exists():
        result.fail(f"Missing TOML file: {path}")
        return None
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except Exception as exc:
        result.fail(f"TOML parse failed for {path}: {exc}")
        return None
    result.pass_(f"TOML syntax valid: {path}")
    return data


def flatten_keys(data: Any, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    if isinstance(data, dict):
        for key, value in data.items():
            full = f"{prefix}.{key}" if prefix else str(key)
            keys.add(full)
            keys.update(flatten_keys(value, full))
    return keys


def parse_frontmatter(text: str) -> tuple[dict[str, str], str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    raw = text[4:end]
    body = text[end + len("\n---\n") :]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        meta[key.strip()] = value.strip().strip("\"'")
    return meta, body


def includes_no_write_policy(text: str) -> bool:
    lowered = text.lower()
    write_terms = ["write", "edit", "delete", "move", "rename"]
    return any(
        phrase in lowered
        for phrase in [
            "create, edit, delete, move, or rename",
            "edits or writes",
            "writes",
            "editing files",
        ]
    ) or all(term in lowered for term in write_terms)


def includes_no_runtime_mutation_policy(text: str) -> bool:
    lowered = text.lower()
    return (
        ("install" in lowered or "package install" in lowered)
        and ("migrate" in lowered or "migration" in lowered or "package install" in lowered)
        and ("service launch" in lowered or "launch services" in lowered or "service-starting" in lowered)
    )


def check_config(paths: GovernancePaths) -> SectionResult:
    result = SectionResult()
    data = load_toml(paths.config_path, result)
    if data is None:
        return result

    text = paths.config_path.read_text(encoding="utf-8", errors="replace")
    if data.get("sandbox_mode") == "read-only":
        result.pass_("Config sandbox_mode is read-only.")
    else:
        result.fail("Config sandbox_mode must be read-only.")

    agents = data.get("agents")
    if isinstance(agents, dict) and agents.get("max_threads") == 5:
        result.pass_("Config [agents] max_threads is 5.")
    else:
        result.fail("Config [agents] max_threads must be 5.")

    if isinstance(agents, dict) and agents.get("max_depth") == 1:
        result.pass_("Config [agents] max_depth is 1.")
    else:
        result.fail("Config [agents] max_depth must be 1.")

    keys = flatten_keys(data)
    for forbidden in sorted(CONFIG_FORBIDDEN_KEYS):
        if forbidden in keys or any(key.endswith(f".{forbidden}") for key in keys):
            result.fail(f"Config contains forbidden key: {forbidden}")

    for pattern in CONFIG_FORBIDDEN_PATTERNS:
        if pattern.search(text):
            result.fail(f"Config contains forbidden pattern: {pattern.pattern}")

    result.pass_("Config contains no provider auth, telemetry, global MCP, notification, or skill-disabling entries detected.")
    return result


def check_agents(paths: GovernancePaths) -> SectionResult:
    result = SectionResult()
    if not paths.agent_dir.exists():
        result.fail(f"Missing agent directory: {paths.agent_dir}")
        return result

    actual = {path.name for path in paths.agent_dir.glob("*.toml")}
    missing = sorted(EXPECTED_AGENTS - actual)
    extra = sorted(actual - EXPECTED_AGENTS)
    for name in missing:
        result.fail(f"Missing expected agent TOML: {name}")
    for name in extra:
        result.warn(f"Unexpected project-local agent TOML present: {name}")
    if not missing:
        result.pass_("All expected project-local agent TOMLs are present.")

    if paths.worker_fixer_path.exists():
        result.fail(f"Disallowed worker/fixer agent exists: {paths.worker_fixer_path}")
    else:
        result.pass_("jarvis_worker_fixer.toml is absent.")

    for path in sorted(paths.agent_dir.glob("*.toml")):
        data = load_toml(path, result)
        if data is None:
            continue

        for key in ["name", "description", "developer_instructions"]:
            if data.get(key):
                result.pass_(f"{path.name} has {key}.")
            else:
                result.fail(f"{path.name} missing required field: {key}")

        sandbox_mode = data.get("sandbox_mode")
        if sandbox_mode == "read-only":
            result.pass_(f"{path.name} sandbox_mode is read-only.")
        else:
            result.fail(f"{path.name} sandbox_mode must be read-only, got: {sandbox_mode!r}")
        if sandbox_mode == "workspace-write":
            result.fail(f"{path.name} uses forbidden workspace-write sandbox.")

        for key in ["allowed_tools", "disallowed_tools"]:
            if key in data:
                result.fail(f"{path.name} contains unsupported TOML field: {key}")

        instructions = str(data.get("developer_instructions") or "")
        for label, marker in REQUIRED_AGENT_POLICY_TEXT.items():
            if marker in instructions:
                result.pass_(f"{path.name} includes policy text for {label}.")
            else:
                result.fail(f"{path.name} missing policy text for {label}.")

        if includes_no_write_policy(instructions):
            result.pass_(f"{path.name} includes no write/edit/delete/move/rename policy.")
        else:
            result.fail(f"{path.name} missing no write/edit/delete/move/rename policy.")

        if includes_no_runtime_mutation_policy(instructions):
            result.pass_(f"{path.name} includes no install/migration/service launch policy.")
        else:
            result.fail(f"{path.name} missing no install/migration/service launch policy.")

    return result


def check_skills(paths: GovernancePaths) -> SectionResult:
    result = SectionResult()
    if not paths.skill_dir.exists():
        result.fail(f"Missing skill directory: {paths.skill_dir}")
        return result

    actual = {path.name for path in paths.skill_dir.iterdir() if path.is_dir()}
    missing = sorted(EXPECTED_SKILLS - actual)
    extra = sorted(actual - EXPECTED_SKILLS)
    for name in missing:
        result.fail(f"Missing expected skill directory: {name}")
    for name in extra:
        result.warn(f"Unexpected repo-local skill directory present: {name}")
    if not missing:
        result.pass_("All expected repo-local skill directories are present.")

    for skill_path in sorted(path for path in paths.skill_dir.iterdir() if path.is_dir()):
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            result.fail(f"Missing SKILL.md for skill: {skill_path.name}")
            continue
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        parsed = parse_frontmatter(text)
        if parsed is None:
            result.fail(f"{skill_path.name} has invalid or missing YAML frontmatter block.")
            continue
        meta, body = parsed
        result.pass_(f"{skill_path.name} has YAML frontmatter block.")

        name = meta.get("name")
        description = meta.get("description")
        if name:
            result.pass_(f"{skill_path.name} frontmatter has name.")
        else:
            result.fail(f"{skill_path.name} frontmatter missing name.")
        if description:
            result.pass_(f"{skill_path.name} frontmatter has description.")
        else:
            result.fail(f"{skill_path.name} frontmatter missing description.")
        if name == skill_path.name:
            result.pass_(f"{skill_path.name} frontmatter name matches parent directory.")
        else:
            result.fail(f"{skill_path.name} frontmatter name does not match parent directory: {name!r}")
        if body.strip():
            result.pass_(f"{skill_path.name} body is non-empty.")
        else:
            result.fail(f"{skill_path.name} body is empty.")

        for section in REQUIRED_SKILL_SECTIONS:
            if section in body:
                result.pass_(f"{skill_path.name} includes section {section}.")
            else:
                result.fail(f"{skill_path.name} missing section {section}.")

    return result


def is_negative_activation_context(line: str) -> bool:
    lowered = line.lower()
    negative_markers = [
        "do not",
        "don't",
        "must not",
        "unless explicitly approved",
        "not activate",
        "without approval",
        "forbidden",
        "disallowed",
    ]
    return any(marker in lowered for marker in negative_markers)


def check_activation_safety(paths: GovernancePaths) -> SectionResult:
    result = SectionResult()
    files = sorted(paths.codex_dir.rglob("*")) + sorted(paths.skill_dir.rglob("*"))
    checked = 0
    for path in files:
        if not path.is_file():
            continue
        checked += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in ACTIVATION_PATTERNS:
                if pattern.lower() not in line.lower():
                    continue
                location = f"{path}:{lineno}"
                if is_negative_activation_context(line):
                    result.warn(f"Negative guardrail mention of {pattern!r} at {location}: {line.strip()}")
                else:
                    result.fail(f"Potential disallowed activation reference {pattern!r} at {location}: {line.strip()}")
    result.pass_(f"Activation safety scan inspected {checked} project-local governance files.")
    return result


def render_section(title: str, result: SectionResult) -> str:
    lines = [f"\n## {title}\n"]
    if result.failures:
        lines.append("Failures:")
        lines.extend(f"- {item}" for item in result.failures)
    else:
        lines.append("Failures: none")
    if result.warnings:
        lines.append("\nWarnings:")
        lines.extend(f"- {item}" for item in result.warnings)
    else:
        lines.append("\nWarnings: none")
    if result.passed:
        lines.append("\nPassed:")
        lines.extend(f"- {item}" for item in result.passed)
    return "\n".join(lines)


def render_validation_report(report: GovernanceValidationResult) -> str:
    lines = [
        "# Jarvis Phase 1 Project-local Validation",
        "\n## Summary\n",
        f"Status: {report.status}",
        f"Checks passed: {report.checks_passed}",
        f"Warnings: {report.warning_count}",
        f"Failures: {report.failure_count}",
    ]
    for title, result in report.sections.items():
        lines.append(render_section(title, result))
    lines.extend(["\n## Final Result\n"])
    if report.failure_count:
        lines.append("Validation failed. Fix failures before Phase 2 planning.")
    else:
        lines.append("Validation passed. Phase 1 project-local governance checks are clean.")
    return "\n".join(lines)


def main() -> int:
    report = validate_phase1_governance()
    print(render_validation_report(report))
    return 0 if report.failure_count == 0 else 1

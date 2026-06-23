from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from typing import Literal


PolicyProfile = Literal["observe", "dev-loop", "swarm", "high-risk-runtime"]
DecisionStatus = Literal["allow", "approval_required", "block"]


READ_ONLY_COMMANDS = {
    "cat",
    "date",
    "find",
    "git",
    "head",
    "ls",
    "pwd",
    "rg",
    "sed",
    "tail",
    "wc",
}

READ_ONLY_GIT_SUBCOMMANDS = {
    "branch",
    "diff",
    "log",
    "show",
    "status",
    "worktree",
}

SHELL_CONTROL_PATTERN = re.compile(r"(;|&&|\|\||\||<|>|`|\$\()")

HARDLINE_PATTERNS = (
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "destructive git reset"),
    (re.compile(r"\bgit\s+clean\b"), "destructive git clean"),
    (re.compile(r"\brm\s+(-[^\s]*r[^\s]*f|-[^\s]*f[^\s]*r)\b"), "recursive force delete"),
    (re.compile(r"\bsudo\s+rm\b"), "privileged delete"),
    (re.compile(r"\b(shred|sdelete)\b"), "destructive secure delete"),
)

APPROVAL_PATTERNS = (
    (re.compile(r"\bgit\s+(push|commit|merge|rebase|checkout|switch|worktree\s+(add|remove|prune))\b"), "git mutation"),
    (re.compile(r"\b(wt)\b"), "Worktrunk command"),
    (re.compile(r"\b(pip|pip3)\s+install\b"), "package install"),
    (re.compile(r"\buv\s+(add|sync|pip\s+install)\b"), "dependency operation"),
    (re.compile(r"\b(npm|pnpm|yarn)\s+(install|add|exec|run)\b"), "node package or script operation"),
    (re.compile(r"\bdocker\s+(run|compose|build|push|pull)\b"), "Docker runtime operation"),
    (re.compile(r"\b(systemctl|service)\b"), "service operation"),
    (re.compile(r"\b(ngrok|cloudflared\s+tunnel|tailscale\s+funnel)\b"), "public exposure"),
    (re.compile(r"\b(powercfg|reg\s+add|reg\s+delete)\b"), "host system configuration"),
    (re.compile(r"\b(curl|wget)\b.*\|\s*(sh|bash)\b"), "network script execution"),
)

APPROVAL_ROOTS = {
    "apt",
    "apt-get",
    "brew",
    "chmod",
    "chown",
    "choco",
    "cp",
    "dd",
    "mkfs",
    "mount",
    "mv",
    "podman",
    "rm",
    "scoop",
    "sudo",
    "umount",
    "wget",
    "winget",
}


@dataclass(frozen=True)
class PolicyDecision:
    status: DecisionStatus
    profile: PolicyProfile
    command: str
    risk: str
    reason: str
    execution_authority: bool

    @property
    def allowed(self) -> bool:
        return self.status == "allow"

    @property
    def approval_required(self) -> bool:
        return self.status == "approval_required"

    @property
    def blocked(self) -> bool:
        return self.status == "block"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "profile": self.profile,
            "command": self.command,
            "risk": self.risk,
            "reason": self.reason,
            "execution_authority": self.execution_authority,
        }


def classify_command(command: str, profile: PolicyProfile = "observe") -> PolicyDecision:
    normalized = " ".join(command.strip().split())
    if not normalized:
        return _decision("block", profile, command, "invalid", "empty command")

    try:
        tokens = shlex.split(normalized)
    except ValueError:
        return _decision("approval_required", profile, normalized, "high", "unparseable shell command")

    hardline_reason = _hardline_token_reason(tokens)
    if hardline_reason is not None:
        return _decision("block", profile, normalized, "hardline", hardline_reason)

    for pattern, reason in HARDLINE_PATTERNS:
        if pattern.search(normalized):
            return _decision("block", profile, normalized, "hardline", reason)

    if SHELL_CONTROL_PATTERN.search(normalized):
        return _decision("approval_required", profile, normalized, "high", "shell control operator")

    approval_reason = _approval_token_reason(tokens)
    if approval_reason is not None:
        return _decision("approval_required", profile, normalized, "high", approval_reason)

    for pattern, reason in APPROVAL_PATTERNS:
        if pattern.search(normalized):
            return _decision("approval_required", profile, normalized, "high", reason)

    if profile == "observe":
        if _is_read_only_command(normalized):
            return _decision("allow", profile, normalized, "low", "read-only inspection")
        return _decision("approval_required", profile, normalized, "medium", "observe profile only allows read-only commands")

    if profile == "dev-loop":
        if _looks_like_runtime_launch(normalized):
            return _decision("approval_required", profile, normalized, "high", "runtime launch")
        if not _is_known_dev_loop_command(normalized):
            return _decision("approval_required", profile, normalized, "medium", "unknown dev-loop command")
        return _decision("allow", profile, normalized, "medium", "allowed by dev-loop profile")

    if profile == "swarm":
        if _looks_like_runtime_launch(normalized):
            return _decision("approval_required", profile, normalized, "high", "runtime launch")
        if not _is_known_dev_loop_command(normalized):
            return _decision("approval_required", profile, normalized, "medium", "unknown swarm command")
        return _decision("allow", profile, normalized, "medium", "allowed by swarm profile")

    if profile == "high-risk-runtime":
        return _decision("approval_required", profile, normalized, "high", "high-risk runtime profile requires explicit approval")

    return _decision("block", profile, normalized, "invalid", "unknown profile")


def _decision(
    status: DecisionStatus,
    profile: PolicyProfile,
    command: str,
    risk: str,
    reason: str,
) -> PolicyDecision:
    return PolicyDecision(
        status=status,
        profile=profile,
        command=command,
        risk=risk,
        reason=reason,
        execution_authority=status == "allow",
    )


def _is_read_only_command(command: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    if not parts:
        return False
    root = parts[0]
    if root not in READ_ONLY_COMMANDS:
        return False
    if root == "git":
        return len(parts) >= 2 and parts[1] in READ_ONLY_GIT_SUBCOMMANDS and not _is_mutating_git_command(parts)
    if root == "find":
        return not _is_mutating_find_command(parts)
    if root == "sed":
        return not _is_mutating_sed_command(parts)
    return True


def _is_known_dev_loop_command(command: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    if not parts:
        return False
    if _is_read_only_command(command):
        return True
    if parts[0] == "pytest":
        return True
    return len(parts) >= 3 and parts[0] == "uv" and parts[1] == "run" and parts[2] == "pytest"


def _is_mutating_git_command(parts: list[str]) -> bool:
    if len(parts) >= 3 and parts[1] == "worktree":
        return parts[2] not in {"list"}
    if len(parts) >= 3 and parts[1] == "branch":
        return not _is_read_only_git_branch(parts[2:])
    return False


def _is_read_only_git_branch(args: list[str]) -> bool:
    if not args:
        return True
    safe_exact = {
        "--all",
        "--contains",
        "--list",
        "--merged",
        "--no-merged",
        "--remotes",
        "--show-current",
        "--verbose",
        "-a",
        "-r",
        "-v",
        "-vv",
    }
    safe_value_prefixes = ("--format=", "--sort=")
    return all(arg in safe_exact or arg.startswith(safe_value_prefixes) for arg in args)


def _is_mutating_find_command(parts: list[str]) -> bool:
    mutating = {"-delete", "-exec", "-execdir", "-ok", "-okdir"}
    return any(part in mutating for part in parts[1:])


def _is_mutating_sed_command(parts: list[str]) -> bool:
    return any(part == "--in-place" or part.startswith("-i") for part in parts[1:])


def _looks_like_runtime_launch(command: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        return True
    if not parts:
        return True
    runtime_terms = {"serve", "server", "start", "dev", "watch"}
    if parts[0] in {"python", "python3", "node", "npm", "pnpm"}:
        return any(token in runtime_terms for token in parts[1:])
    if parts[0] == "uv":
        return any(token in runtime_terms for token in parts[1:]) or _uv_run_starts_runtime(parts)
    return parts[0] in {"flask", "fastapi", "uvicorn", "gunicorn"}


def _uv_run_starts_runtime(parts: list[str]) -> bool:
    if len(parts) < 3 or parts[1] != "run":
        return False
    if parts[2].startswith("pytest"):
        return False
    if parts[2] in {"python", "python3"}:
        return any(token in {"http.server", "uvicorn", "flask"} for token in parts[3:]) or any(
            token in {"serve", "server", "start", "dev", "watch"} for token in parts[3:]
        )
    return True


def _hardline_token_reason(tokens: list[str]) -> str | None:
    lowered = [_strip_shell_escape(token).lower() for token in tokens]
    for index, token in enumerate(lowered):
        if token == "git" and lowered[index + 1 : index + 3] == ["reset", "--hard"]:
            return "destructive git reset"
        if token == "git" and index + 1 < len(lowered) and lowered[index + 1] == "clean":
            return "destructive git clean"
        if token == "sudo" and index + 1 < len(lowered) and lowered[index + 1] == "rm":
            return "privileged delete"
        if token == "rm" and _rm_is_recursive_force(lowered[index + 1 :]):
            return "recursive force delete"
    return None


def _approval_token_reason(tokens: list[str]) -> str | None:
    lowered = [_strip_shell_escape(token).lower() for token in tokens]
    if any(token in APPROVAL_ROOTS for token in lowered):
        return "host mutation or privileged command"
    if lowered[:2] in (["git", "push"], ["git", "commit"], ["git", "merge"], ["git", "rebase"], ["git", "checkout"], ["git", "switch"]):
        return "git mutation"
    if len(lowered) >= 3 and lowered[:2] == ["git", "worktree"] and lowered[2] != "list":
        return "git mutation"
    return None


def _rm_is_recursive_force(tokens: list[str]) -> bool:
    recursive = False
    force = False
    for token in tokens:
        if not token.startswith("-"):
            continue
        if token in {"--recursive", "-r", "-R"}:
            recursive = True
        if token in {"--force", "-f"}:
            force = True
        letters = token.lstrip("-")
        if "r" in letters or "R" in letters:
            recursive = True
        if "f" in letters:
            force = True
    return recursive and force


def _strip_shell_escape(token: str) -> str:
    return token.replace("\\", "")

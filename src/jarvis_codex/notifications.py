from __future__ import annotations

import re
from typing import Any


PROMPT_CATEGORIES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("worktrunk", re.compile(r"\b(worktrunk|worktree|wt\s+|lane refresh|branch lane)\b", re.I), "Worktree operation queued."),
    ("swarm", re.compile(r"\b(swarm|multi-agent|subagent|delegate|worker lane|agent lane)\b", re.I), "Swarm coordination started."),
    ("ui-browser", re.compile(r"\b(ui|ux|frontend|browser|playwright|screenshot|interface|visual)\b", re.I), "Reviewing the interface."),
    ("github", re.compile(r"\b(github|pull request|pr\b|ci\b|actions|issue|merge queue)\b", re.I), "Checking the GitHub workflow."),
    ("hardware", re.compile(r"\b(gpu|npu|cuda|docker|hardware|acceleration|ml|model|video|voice)\b", re.I), "Checking local acceleration."),
    ("planning", re.compile(r"\b(plan|planning|architecture|design doc|roadmap|gate|reconcile)\b", re.I), "Planning pass started."),
    ("coding", re.compile(r"\b(code|implement|fix|test|pytest|build|refactor|bug)\b", re.I), "Code change pass started."),
)

ACTION_NEEDED_PATTERN = re.compile(
    r"\b(approval|approve|blocked|need(?:s)? input|need(?:s)? attention|action needed|user action|waiting for|permission|required)\b",
    re.I,
)


def classify_prompt(prompt: str) -> tuple[str, str]:
    for category, pattern, phrase in PROMPT_CATEGORIES:
        if pattern.search(prompt):
            return category, phrase
    return "general", "I'm on it."


def payload_success(payload: dict[str, Any]) -> bool | None:
    value = payload.get("success")
    if isinstance(value, bool):
        return value
    status = str(payload.get("status") or payload.get("result") or "").lower()
    if status in {"success", "succeeded", "ok", "complete", "completed"}:
        return True
    if status in {"failed", "failure", "error", "cancelled", "canceled"}:
        return False
    return None


def classify_completion(payload: dict[str, Any]) -> tuple[str, str, bool]:
    text = " ".join(str(payload.get(key) or "") for key in ("status", "result", "type", "event", "reason", "error", "message", "summary", "last-assistant-message"))
    lowered = text.lower()
    success = payload_success(payload)

    if success is False or re.search(r"\b(error|failed|failure|cancelled|canceled|exception)\b", lowered):
        return "error", "The task needs attention.", True
    if re.search(r"\b(approval|approve|permission|required)\b", lowered):
        return "approval-needed", "Approval is needed.", True
    if re.search(r"\b(blocked|stuck|cannot proceed|impasse)\b", lowered):
        return "blocked", "I'm blocked and need input.", True
    if ACTION_NEEDED_PATTERN.search(text):
        return "user-action-needed", "Input is needed.", True
    return "success", "", False


PACK_HINTS: dict[str, re.Pattern[str]] = {
    "agent-engineering": re.compile(r"\b(agent|harness|eval|memory|context|orchestrat|tool design)\b", re.I),
    "design-frontend": re.compile(r"\b(frontend|ui|ux|design|responsive|landing|screen)\b", re.I),
    "obsidian-knowledge": re.compile(r"\b(obsidian|vault|wikilink|canvas|base|pkm|note)\b", re.I),
    "browser-testing": re.compile(r"\b(browser|playwright|screenshot|console|network|scrap|visual qa)\b", re.I),
    "native-tools": re.compile(r"\b(graphify|native tool|plugin|skill creator|notebooklm)\b", re.I),
    "dfir-cyber": re.compile(r"\b(dfir|incident|sentinel|kql|volatility|forensic|evidence|ioc|sift)\b", re.I),
}


def get_pack_hints(prompt: str) -> list[str]:
    return [name for name, pattern in PACK_HINTS.items() if pattern.search(prompt)]

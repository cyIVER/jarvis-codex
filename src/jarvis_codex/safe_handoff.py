from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .plan_viewer import load_approved_queue, next_steps_queue_path


@dataclass(frozen=True)
class SafeHandoff:
    source: str
    selected_steps: list[str]
    brief: str
    execution_authority: bool
    status: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "selected_steps": self.selected_steps,
            "brief": self.brief,
            "execution_authority": self.execution_authority,
            "status": self.status,
            "message": self.message,
        }


def build_safe_handoff(state_dir: Path) -> SafeHandoff:
    queue_path = next_steps_queue_path(state_dir)
    queue = load_approved_queue(state_dir)
    if queue is None:
        return SafeHandoff(
            source=str(queue_path),
            selected_steps=[],
            brief="",
            execution_authority=False,
            status="empty",
            message="No readable planning queue is available. Re-select next steps before requesting execution approval.",
        )

    selected = queue.get("selected", [])
    safe_selected = [item for item in selected if isinstance(item, str)]
    brief = queue.get("brief", "")
    return SafeHandoff(
        source=str(queue_path),
        selected_steps=safe_selected,
        brief=brief if isinstance(brief, str) else "",
        execution_authority=False,
        status="ready",
        message="Planning queue is ready for human review. It is not execution authority.",
    )


def render_safe_handoff_markdown(handoff: SafeHandoff) -> str:
    selected = "\n".join(f"- `{item}`" for item in handoff.selected_steps) or "- None"
    brief = handoff.brief.strip() or "No proceed brief captured."
    return "\n".join(
        [
            "# Safe CLI Handoff",
            "",
            f"Source: `{handoff.source}`",
            f"Status: `{handoff.status}`",
            f"Execution authority: `{str(handoff.execution_authority).lower()}`",
            "",
            "## Selected Steps",
            "",
            selected,
            "",
            "## Proceed Brief",
            "",
            brief,
            "",
            "## Proposed Commands",
            "",
            "- None executed.",
            "- Any command derived from this handoff requires explicit approval for that exact command.",
            "",
            "## Preconditions",
            "",
            "- Confirm the selected steps are still relevant.",
            "- Confirm expected writes, runtime side effects, and rollback or inspection steps before execution.",
            "",
            "## Expected Side Effects",
            "",
            "- This handoff generation has no repo, git, Worktrunk, service, Docker, local ML, install, or migration side effects.",
            "",
            "## Approval Required",
            "",
            "- Required before running any displayed or derived command.",
            "- Required before writing files, mutating git or worktrees, launching services, running local ML, running Docker, installing packages, or applying migrations.",
            "",
            "## Verification",
            "",
            "- Re-run the relevant validator, tests, or inspection command after any separately approved action.",
            "",
            "## Rollback Or Inspection",
            "",
            "- Inspect generated output before execution.",
            "- Use exact-path review and targeted validation before committing any future changes.",
            "",
            f"Message: {handoff.message}",
            "",
        ]
    )


def render_safe_handoff_json(handoff: SafeHandoff) -> str:
    return json.dumps(handoff.to_dict(), indent=2, sort_keys=True) + "\n"

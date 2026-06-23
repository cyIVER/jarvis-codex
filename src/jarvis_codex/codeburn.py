from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


CODEBURN_CLI = Path("/home/iveri/.local/share/ai-env/native-tools/codeburn/dist/cli.js")
STATUS_PATTERN = re.compile(
    r"Today\s+\$(?P<today_cost>[0-9]+(?:\.[0-9]+)?)\s+"
    r"(?P<today_calls>[0-9]+)\s+calls\s+"
    r"Month\s+\$(?P<month_cost>[0-9]+(?:\.[0-9]+)?)\s+"
    r"(?P<month_calls>[0-9]+)\s+calls",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CodeburnStatus:
    available: bool
    today_cost: float | None
    today_calls: int | None
    month_cost: float | None
    month_calls: int | None
    raw: str
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "available": self.available,
            "today_cost": self.today_cost,
            "today_calls": self.today_calls,
            "month_cost": self.month_cost,
            "month_calls": self.month_calls,
            "raw": self.raw,
            "error": self.error,
            "writes_state": False,
            "shell": False,
        }


def parse_codeburn_status(output: str) -> CodeburnStatus:
    match = STATUS_PATTERN.search(output)
    if match is None:
        return CodeburnStatus(
            available=False,
            today_cost=None,
            today_calls=None,
            month_cost=None,
            month_calls=None,
            raw=output.strip(),
            error="unrecognized_status_output",
        )
    return CodeburnStatus(
        available=True,
        today_cost=float(match.group("today_cost")),
        today_calls=int(match.group("today_calls")),
        month_cost=float(match.group("month_cost")),
        month_calls=int(match.group("month_calls")),
        raw=output.strip(),
    )


def read_codeburn_status(command: Sequence[str] | None = None, timeout_seconds: float = 10) -> CodeburnStatus:
    argv = tuple(command) if command is not None else ("node", str(CODEBURN_CLI), "status")
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
    except FileNotFoundError as exc:
        return _failed_status("command_not_found", str(exc))
    except subprocess.TimeoutExpired:
        return _failed_status("timeout", "Codeburn status command timed out")

    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
    if completed.returncode != 0:
        return _failed_status("command_failed", output)
    return parse_codeburn_status(output)


def _failed_status(error: str, raw: str) -> CodeburnStatus:
    return CodeburnStatus(
        available=False,
        today_cost=None,
        today_calls=None,
        month_cost=None,
        month_calls=None,
        raw=raw.strip(),
        error=error,
    )

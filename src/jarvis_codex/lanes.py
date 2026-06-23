from __future__ import annotations

import json
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .state import JarvisState


@dataclass(frozen=True)
class WorkerContract:
    schema_version: int = 1
    artifact: str = "worker_contract"
    mutation_performed: bool = False
    execution_authority: bool = False
    action: str = ""
    lane: str = ""
    base_commit: str = ""
    timestamp: int = 0
    decision: str = "needs-review"  # ready, needs-review, blocked
    evidence: str = ""
    merge_recommendation: str = ""


def score_lane(repo_dir: Path, branch: str) -> dict[str, str]:
    """Score a lane using read-only git status output."""
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    status_output = result.stdout.strip()
    
    if not status_output:
        return {"decision": "ready", "evidence": "clean working tree", "merge_recommendation": "ready to merge or refresh"}
    elif "??" in status_output:
        return {"decision": "needs-review", "evidence": "untracked files present", "merge_recommendation": "review untracked files before merge"}
    else:
        return {"decision": "blocked", "evidence": "uncommitted changes", "merge_recommendation": "commit or stash changes before proceeding"}


def list_lanes(repo_dir: Path) -> list[dict[str, str]]:
    result = subprocess.run(
        ["git", "worktree", "list"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []

    lanes = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        path = parts[0]
        branch = parts[-1] if len(parts) > 1 else ""
        if branch.startswith("[") and branch.endswith("]"):
            branch = branch[1:-1]
            
        score = score_lane(Path(path), branch)
        
        lanes.append({
            "path": path, 
            "branch": branch,
            "decision": score["decision"],
            "evidence": score["evidence"],
            "merge_recommendation": score["merge_recommendation"]
        })
    return lanes


def log_lane_decision(state: JarvisState, action: str, lane_branch: str, repo_dir: Path) -> WorkerContract:
    """Append a local planning decision; this does not mutate git/worktrees."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    base_commit = result.stdout.strip() if result.returncode == 0 else ""
    
    score = score_lane(repo_dir, lane_branch)

    contract = WorkerContract(
        action=action,
        lane=lane_branch,
        base_commit=base_commit,
        timestamp=int(time.time()),
        decision=score["decision"],
        evidence=score["evidence"],
        merge_recommendation=score["merge_recommendation"],
    )
    
    log_path = state.logs / "lane_decisions.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(contract), sort_keys=True) + "\n")
        
    return contract

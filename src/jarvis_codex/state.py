from __future__ import annotations

import json
import hashlib
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Episode:
    id: str
    created_at: int
    text: str
    source: str
    status: str = "captured"


@dataclass(frozen=True)
class Memory:
    id: str
    created_at: int
    key: str
    value: str
    source: str = "user"


@dataclass(frozen=True)
class ApprovalRequest:
    id: str
    created_at: int
    summary: str
    status: str = "pending"


@dataclass(frozen=True)
class ReleaseEvidence:
    id: str
    created_at: int
    gate: str
    summary: str
    reviewer: str
    artifact_path: str | None
    artifact_size_bytes: int | None
    artifact_sha256: str | None
    status: str = "submitted"
    execution_authority: bool = False
    release_gate_closed: bool = False


@dataclass(frozen=True)
class ReleaseGateAcceptance:
    id: str
    created_at: int
    gate: str
    evidence_id: str
    summary: str
    reviewer: str
    status: str = "accepted"
    execution_authority: bool = False
    publication_ready: bool = False
    release_gate_closed: bool = True


RELEASE_EVIDENCE_GATES = {
    "actual_mobile_device_validation",
    "electron_packaging_and_signing",
    "external_security_review",
    "networked_gemini_live_validation",
    "release_packaging_and_signing",
    "unattended_loop_scheduling",
}


class JarvisState:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.inbox = root / "inbox"
        self.memory = root / "memory"
        self.approvals = root / "approvals"
        self.handoffs = root / "handoffs"
        self.logs = root / "logs"
        self.release = root / "release"

    def init(self) -> None:
        for path in (self.inbox, self.memory, self.approvals, self.handoffs, self.logs, self.release):
            path.mkdir(parents=True, exist_ok=True)
            gitkeep = path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.write_text("", encoding="utf-8")

    def capture_episode(self, text: str, source: str = "text") -> Episode:
        self.init()
        episode = Episode(id=_new_id("ep"), created_at=_now(), text=text.strip(), source=source)
        if not episode.text:
            raise ValueError("episode text cannot be empty")
        self._write_json(self.inbox / f"{episode.id}.json", asdict(episode))
        self._append_jsonl(self.logs / "episodes.jsonl", asdict(episode))
        return episode

    def add_memory(self, key: str, value: str, source: str = "user") -> Memory:
        self.init()
        memory = Memory(id=_new_id("mem"), created_at=_now(), key=key.strip(), value=value.strip(), source=source)
        if not memory.key or not memory.value:
            raise ValueError("memory key and value are required")
        self._append_jsonl(self.memory / "memory.jsonl", asdict(memory))
        return memory

    def request_approval(self, summary: str) -> ApprovalRequest:
        self.init()
        request = ApprovalRequest(id=_new_id("approval"), created_at=_now(), summary=summary.strip())
        if not request.summary:
            raise ValueError("approval summary cannot be empty")
        self._append_jsonl(self.approvals / "approvals.jsonl", asdict(request))
        return request

    def recent_episodes(self, limit: int = 5) -> list[dict[str, Any]]:
        return sorted(self._read_json_files(self.inbox), key=lambda item: item.get("created_at", 0), reverse=True)[:limit]

    def memories(self) -> list[dict[str, Any]]:
        return self._read_jsonl(self.memory / "memory.jsonl")

    def approval_requests(self) -> list[dict[str, Any]]:
        return self._read_jsonl(self.approvals / "approvals.jsonl")

    def release_evidence(self) -> list[dict[str, Any]]:
        return self._read_jsonl(self.release / "evidence.jsonl")

    def release_gate_acceptances(self) -> list[dict[str, Any]]:
        return self._read_jsonl(self.release / "gate-acceptance.jsonl")

    def record_release_evidence(
        self,
        gate: str,
        summary: str,
        reviewer: str = "operator",
        artifact: Path | None = None,
    ) -> ReleaseEvidence:
        self.init()
        normalized_gate = gate.strip()
        if normalized_gate not in RELEASE_EVIDENCE_GATES:
            raise ValueError(f"gate must be one of: {', '.join(sorted(RELEASE_EVIDENCE_GATES))}")
        normalized_summary = summary.strip()
        if not normalized_summary:
            raise ValueError("release evidence summary cannot be empty")
        normalized_reviewer = reviewer.strip() or "operator"
        artifact_path: str | None = None
        artifact_size_bytes: int | None = None
        artifact_sha256: str | None = None
        if artifact is not None:
            resolved_artifact = artifact.resolve()
            resolved_release_root = self.release.resolve()
            if resolved_release_root not in (resolved_artifact, *resolved_artifact.parents):
                raise ValueError("artifact must be under the selected state release directory before hashing")
            artifact_path = str(resolved_artifact)
            if not resolved_artifact.is_file():
                raise ValueError("artifact must be an existing file")
            artifact_size_bytes = resolved_artifact.stat().st_size
            artifact_sha256 = _sha256(resolved_artifact)
        evidence = ReleaseEvidence(
            id=_new_id("evidence"),
            created_at=_now(),
            gate=normalized_gate,
            summary=normalized_summary,
            reviewer=normalized_reviewer,
            artifact_path=artifact_path,
            artifact_size_bytes=artifact_size_bytes,
            artifact_sha256=artifact_sha256,
        )
        self._append_jsonl(self.release / "evidence.jsonl", asdict(evidence))
        return evidence

    def accept_release_gate(
        self,
        gate: str,
        evidence_id: str,
        summary: str,
        reviewer: str = "operator",
    ) -> ReleaseGateAcceptance:
        self.init()
        normalized_gate = gate.strip()
        if normalized_gate not in RELEASE_EVIDENCE_GATES:
            raise ValueError(f"gate must be one of: {', '.join(sorted(RELEASE_EVIDENCE_GATES))}")
        normalized_evidence_id = evidence_id.strip()
        if not normalized_evidence_id:
            raise ValueError("release gate acceptance requires an evidence id")
        matching_evidence = [
            item
            for item in self.release_evidence()
            if item.get("id") == normalized_evidence_id and item.get("gate") == normalized_gate
        ]
        if not matching_evidence:
            raise ValueError("release gate acceptance requires an existing evidence record for the same gate")
        normalized_summary = summary.strip()
        if not normalized_summary:
            raise ValueError("release gate acceptance summary cannot be empty")
        normalized_reviewer = reviewer.strip() or "operator"
        acceptance = ReleaseGateAcceptance(
            id=_new_id("gate_acceptance"),
            created_at=_now(),
            gate=normalized_gate,
            evidence_id=normalized_evidence_id,
            summary=normalized_summary,
            reviewer=normalized_reviewer,
        )
        self._append_jsonl(self.release / "gate-acceptance.jsonl", asdict(acceptance))
        return acceptance


    def recent_handoffs(self, limit: int = 1) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for file in sorted(self.handoffs.glob("*.md"), reverse=True)[:limit]:
            try:
                text = file.read_text(encoding="utf-8")
            except OSError:
                continue
            items.append({"id": file.name, "text": text})
        return items

    def write_handoff(self, objective: str = "Continue Jarvis Codex work") -> Path:
        self.init()
        now = _now()
        path = self.handoffs / f"handoff-{now}.md"
        path.write_text(render_handoff(objective, self.recent_episodes(), self.memories(), self.approval_requests()), encoding="utf-8")
        return path

    def doctor(self) -> dict[str, Any]:
        return {
            "state_root": str(self.root),
            "episodes": len(list(self.inbox.glob("*.json"))),
            "memories": len(self.memories()),
            "approvals": len(self.approval_requests()),
            "handoffs": len(list(self.handoffs.glob("*.md"))),
            "release_evidence": self._count_jsonl_records(self.release / "evidence.jsonl"),
        }

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _append_jsonl(self, path: Path, data: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(data, sort_keys=True) + "\n")

    def _read_json_files(self, path: Path) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for file in path.glob("*.json"):
            try:
                value = json.loads(file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(value, dict):
                items.append(value)
        return items

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        items: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                items.append(value)
        return items

    def _count_jsonl_records(self, path: Path) -> int:
        if not path.exists():
            return 0
        count = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                count += 1
        return count


def render_handoff(
    objective: str,
    episodes: list[dict[str, Any]],
    memories: list[dict[str, Any]],
    approvals: list[dict[str, Any]],
) -> str:
    lines = [
        "# Codex Handoff",
        "",
        f"Objective: {objective}",
        "",
        "## Recent Episodes",
    ]
    if episodes:
        for episode in episodes:
            lines.append(f"- `{episode.get('id')}`: {episode.get('text')}")
    else:
        lines.append("- None captured yet.")
    lines.extend(["", "## Relevant Memory"])
    if memories:
        for memory in memories[-10:]:
            lines.append(f"- {memory.get('key')}: {memory.get('value')}")
    else:
        lines.append("- No memory records yet.")
    lines.extend(["", "## Approval Boundary"])
    pending = [item for item in approvals if item.get("status") == "pending"]
    if pending:
        for item in pending:
            lines.append(f"- Pending `{item.get('id')}`: {item.get('summary')}")
    else:
        lines.append("- No pending approvals. Ask before tool execution, repository mutation, commits, pushes, PRs, purchases, deployments, or credential changes.")
    lines.extend(["", "## Next Action", "", "Use this handoff as context, inspect the project state, and propose the smallest next implementation step."])
    return "\n".join(lines) + "\n"


def _now() -> int:
    return int(time.time())


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

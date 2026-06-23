from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Literal

from .event_store import JarvisEventStore, StoredEvent

ApprovalStatus = Literal["pending", "approved", "rejected"]


@dataclass(frozen=True)
class ApprovalResult:
    approval: dict[str, Any]
    event: StoredEvent


class ApprovalError(ValueError):
    pass


class ApprovalService:
    def __init__(self, store: JarvisEventStore) -> None:
        self.store = store

    def request(
        self,
        *,
        session_id: str,
        summary: str,
        operation: str,
        risk: str = "medium",
        scope: dict[str, Any] | None = None,
        actor_id: str = "runtime",
        source_client: str = "rpc",
    ) -> ApprovalResult:
        if not summary.strip():
            raise ApprovalError("approval summary is required")
        if not operation.strip():
            raise ApprovalError("approval operation is required")
        approval_id = f"appr_{uuid.uuid4().hex[:16]}"
        event = self.store.append_event(
            session_id=session_id,
            actor_id=actor_id,
            source_client=source_client,
            event_type="approval.requested",
            payload={
                "approval_id": approval_id,
                "summary": summary,
                "operation": operation,
                "risk": risk,
                "scope": scope or {},
            },
        )
        approval = self.store.approval(approval_id)
        if approval is None:
            raise ApprovalError("approval projection was not created")
        return ApprovalResult(approval=approval, event=event)

    def respond(
        self,
        *,
        approval_id: str,
        status: Literal["approved", "rejected"],
        actor_id: str = "runtime",
        source_client: str = "rpc",
        reason: str = "",
    ) -> ApprovalResult:
        approval = self.store.approval(approval_id)
        if approval is None:
            raise ApprovalError("approval does not exist")
        if approval["status"] != "pending":
            raise ApprovalError("approval is already decided")
        event = self.store.append_event(
            session_id=str(approval["session_id"]),
            actor_id=actor_id,
            source_client=source_client,
            event_type="approval.responded",
            payload={
                "approval_id": approval_id,
                "status": status,
                "reason": reason,
            },
        )
        updated = self.store.approval(approval_id)
        if updated is None:
            raise ApprovalError("approval projection was not updated")
        return ApprovalResult(approval=updated, event=event)

    def list(self, status: ApprovalStatus | None = None) -> list[dict[str, Any]]:
        return self.store.approvals(status=status)

from concurrent.futures import ThreadPoolExecutor

import pytest

from jarvis_codex.approval import ApprovalError, ApprovalService
from jarvis_codex.event_store import JarvisEventStore


def test_approval_service_creates_pending_request(tmp_path):
    service = ApprovalService(JarvisEventStore(tmp_path / "jarvis.db"))

    result = service.request(
        session_id="session-1",
        summary="Run targeted tests",
        operation="uv run pytest tests/test_approval.py",
        risk="medium",
        scope={"command": "uv run pytest tests/test_approval.py"},
        actor_id="codex",
        source_client="pytest",
    )

    assert result.approval["id"].startswith("appr_")
    assert result.approval["status"] == "pending"
    assert result.event.event_type == "approval.requested"


def test_approval_service_responds_once(tmp_path):
    service = ApprovalService(JarvisEventStore(tmp_path / "jarvis.db"))
    request = service.request(
        session_id="session-1",
        summary="Run targeted tests",
        operation="uv run pytest",
    )

    response = service.respond(approval_id=request.approval["id"], status="approved", reason="targeted")

    assert response.approval["status"] == "approved"
    assert response.event.event_type == "approval.responded"
    with pytest.raises(ApprovalError):
        service.respond(approval_id=request.approval["id"], status="rejected")


def test_approval_service_consumes_approved_request_once(tmp_path):
    service = ApprovalService(JarvisEventStore(tmp_path / "jarvis.db"))
    request = service.request(
        session_id="session-1",
        summary="Run targeted tests",
        operation="uv run pytest",
    )
    approved = service.respond(approval_id=request.approval["id"], status="approved")

    consumed = service.consume(approval_id=approved.approval["id"], reason="used for pty.create")

    assert consumed.approval["status"] == "used"
    assert consumed.event.event_type == "approval.consumed"
    with pytest.raises(ApprovalError):
        service.consume(approval_id=approved.approval["id"])


def test_approval_service_consumes_approved_request_once_under_concurrency(tmp_path):
    store = JarvisEventStore(tmp_path / "jarvis.db")
    service = ApprovalService(store)
    request = service.request(
        session_id="session-1",
        summary="Run targeted tests",
        operation="uv run pytest",
    )
    approved = service.respond(approval_id=request.approval["id"], status="approved")

    def consume_once() -> str:
        try:
            service.consume(approval_id=approved.approval["id"], reason="concurrent use")
            return "used"
        except ApprovalError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda _: consume_once(), range(10)))

    consumed_events = [event for event in store.events() if event.event_type == "approval.consumed"]
    assert results.count("used") == 1
    assert results.count("rejected") == 9
    assert len(consumed_events) == 1
    assert store.approval(approved.approval["id"])["status"] == "used"


def test_approval_service_rejects_invalid_requests(tmp_path):
    service = ApprovalService(JarvisEventStore(tmp_path / "jarvis.db"))

    with pytest.raises(ApprovalError):
        service.request(session_id="session-1", summary="", operation="uv run pytest")
    with pytest.raises(ApprovalError):
        service.respond(approval_id="missing", status="approved")

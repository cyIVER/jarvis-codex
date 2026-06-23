import time
import base64
import hashlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import jarvis_codex.runtime_app as runtime_app
from jarvis_codex.codeburn import CodeburnStatus
from jarvis_codex.state import JarvisState
from jarvis_codex.protocol import make_request
from jarvis_codex.runtime_app import create_app


def _runtime_token(client: TestClient) -> str:
    return str(client.app.state.runtime_token)


def test_runtime_health_does_not_initialize_state(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["writes_state"] is False
    assert not (tmp_path / "state").exists()


def test_runtime_serves_pwa_assets_without_initializing_state(tmp_path):
    state = tmp_path / "state"
    app = create_app(state)
    client = TestClient(app)

    manifest = client.get("/manifest.webmanifest")
    icon = client.get("/assets/icon.svg")
    service_worker = client.get("/service-worker.js")

    assert manifest.status_code == 200
    assert manifest.headers["content-type"].startswith("application/manifest+json")
    assert manifest.json()["display"] == "standalone"
    assert icon.status_code == 200
    assert icon.headers["content-type"].startswith("image/svg+xml")
    assert "<svg" in icon.text
    assert service_worker.status_code == 200
    assert service_worker.headers["service-worker-allowed"] == "/"
    assert "CACHE_NAME" in service_worker.text
    assert 'url.pathname === "/rpc"' in service_worker.text
    assert not state.exists()


def test_runtime_initialize_rpc_reports_capabilities(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post("/rpc", json=make_request("initialize", request_id="req_1"))

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "response"
    assert data["result"]["runtime"] == "jarvis"
    assert "agent.provider_status" in data["result"]["capabilities"]
    assert "session.create" in data["result"]["capabilities"]
    assert "session.archive" in data["result"]["capabilities"]
    assert "session.get" in data["result"]["capabilities"]
    assert "session.list" in data["result"]["capabilities"]
    assert "telemetry.codeburn_status" in data["result"]["capabilities"]
    assert "runtime.readiness" in data["result"]["capabilities"]
    assert "release.gate_status" in data["result"]["capabilities"]
    assert "profile.list" in data["result"]["capabilities"]
    assert "message.list" in data["result"]["capabilities"]
    assert "swarm.plan" in data["result"]["capabilities"]
    assert "swarm.launch" in data["result"]["capabilities"]
    assert "command.propose" in data["result"]["capabilities"]
    assert "approval.request" in data["result"]["capabilities"]
    assert "event.subscribe" in data["result"]["capabilities"]
    assert "voice.submit" in data["result"]["capabilities"]
    assert "voice.synthesize_audio" in data["result"]["capabilities"]


def test_runtime_session_create_writes_event_store(tmp_path):
    state = tmp_path / "state"
    app = create_app(state)
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request(
            "session.create",
            {
                "session_id": "session-1",
                "title": "Jarvis memory",
                "profile_id": "dev-loop",
                "source_client": "pytest",
            },
            request_id="req_1",
        ),
    )

    assert response.status_code == 200
    assert response.json()["result"]["session_id"] == "session-1"
    assert (state / "runtime" / "jarvis.db").exists()
    session = app.state.event_store.session("session-1")
    assert session["title"] == "Jarvis memory"


def test_runtime_session_list_and_get_return_session_projection(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post(
        "/rpc",
        json=make_request(
            "session.create",
            {
                "session_id": "session-1",
                "title": "Jarvis memory",
                "profile_id": "dev-loop",
                "model_route": {"agent": "codex"},
                "source_client": "pytest",
            },
            request_id="req_1",
        ),
    )

    list_response = client.post(
        "/rpc",
        json=make_request("session.list", {"status": "active", "limit": 10}, request_id="req_2"),
    )
    get_response = client.post(
        "/rpc",
        json=make_request("session.get", {"session_id": "session-1"}, request_id="req_3"),
    )

    listed = list_response.json()["result"]["sessions"][0]
    fetched = get_response.json()["result"]["session"]
    assert listed["id"] == "session-1"
    assert listed["model_route"] == {"agent": "codex"}
    assert fetched["title"] == "Jarvis memory"
    assert fetched["profile_id"] == "dev-loop"


def test_runtime_session_get_reports_unknown_session(tmp_path):
    state = tmp_path / "state"
    app = create_app(state)
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request("session.get", {"session_id": "missing"}, request_id="req_1"),
    )

    assert response.json()["error"]["code"] == "unknown_session"
    assert (state / "runtime" / "jarvis.db").exists()


def test_runtime_session_resume_returns_session_and_recent_history_without_writing(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post(
        "/rpc",
        json=make_request("session.create", {"session_id": "session-resume"}, request_id="req_1"),
    )
    client.post(
        "/rpc",
        json=make_request(
            "prompt.send",
            {"session_id": "session-resume", "text": "resume me"},
            request_id="req_2",
        ),
    )

    response = client.post(
        "/rpc",
        json=make_request("session.resume", {"session_id": "session-resume"}, request_id="req_3"),
    )

    result = response.json()["result"]
    assert result["resumed_session_id"] == "session-resume"
    assert result["session"]["id"] == "session-resume"
    assert [message["event_type"] for message in result["messages"]] == ["session.created", "prompt.sent"]
    assert result["writes_state"] is False
    assert result["execution_authority"] is False


def test_runtime_session_resume_absent_store_does_not_write_state(tmp_path):
    state = tmp_path / "state"
    app = create_app(state)
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request("session.resume", {"session_id": "missing"}, request_id="req_1"),
    )

    assert response.json()["error"]["code"] == "unknown_session"
    assert response.json()["error"]["details"]["writes_state"] is False
    assert not state.exists()


def test_runtime_session_resume_validates_session_id(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post("/rpc", json=make_request("session.resume", request_id="req_1"))

    assert response.json()["error"]["code"] == "missing_session_id"


def test_runtime_session_archive_updates_projection_and_history(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post(
        "/rpc",
        json=make_request(
            "session.create",
            {"session_id": "session-archive", "title": "Archive me", "source_client": "pytest"},
            request_id="req_1",
        ),
    )

    archive_response = client.post(
        "/rpc",
        json=make_request(
            "session.archive",
            {"session_id": "session-archive", "reason": "test cleanup", "source_client": "pytest"},
            request_id="req_2",
        ),
    )
    active_response = client.post(
        "/rpc",
        json=make_request("session.list", {"status": "active"}, request_id="req_3"),
    )
    archived_response = client.post(
        "/rpc",
        json=make_request("session.list", {"status": "archived"}, request_id="req_4"),
    )
    history_response = client.post(
        "/rpc",
        json=make_request("message.list", {"session_id": "session-archive"}, request_id="req_5"),
    )

    archived = archive_response.json()["result"]
    assert archived["archived_session_id"] == "session-archive"
    assert archived["writes_state"] is True
    assert archived["session"]["status"] == "archived"
    assert active_response.json()["result"]["sessions"] == []
    assert archived_response.json()["result"]["sessions"][0]["id"] == "session-archive"
    assert [event["event_type"] for event in history_response.json()["result"]["messages"]] == [
        "session.created",
        "session.archived",
    ]


def test_runtime_session_archive_is_idempotent_for_archived_session(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post(
        "/rpc",
        json=make_request("session.create", {"session_id": "session-archive"}, request_id="req_1"),
    )
    first = client.post(
        "/rpc",
        json=make_request("session.archive", {"session_id": "session-archive"}, request_id="req_2"),
    )
    second = client.post(
        "/rpc",
        json=make_request("session.archive", {"session_id": "session-archive"}, request_id="req_3"),
    )

    assert first.json()["result"]["writes_state"] is True
    assert second.json()["result"]["already_archived"] is True
    assert second.json()["result"]["writes_state"] is False
    assert app.state.event_store.current_sequence() == 2


def test_runtime_session_archive_validates_session_id(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    missing_response = client.post("/rpc", json=make_request("session.archive", request_id="req_1"))
    unknown_response = client.post(
        "/rpc",
        json=make_request("session.archive", {"session_id": "missing"}, request_id="req_2"),
    )

    assert missing_response.json()["error"]["code"] == "missing_session_id"
    assert unknown_response.json()["error"]["code"] == "unknown_session"


def test_runtime_session_fork_creates_child_session_without_execution_authority(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post(
        "/rpc",
        json=make_request(
            "session.create",
            {
                "session_id": "session-parent",
                "title": "Parent",
                "profile_id": "dev-loop",
                "model_route": {"agent": "codex"},
            },
            request_id="req_1",
        ),
    )

    response = client.post(
        "/rpc",
        json=make_request(
            "session.fork",
            {"session_id": "session-parent", "child_session_id": "session-child"},
            request_id="req_2",
        ),
    )
    child_response = client.post(
        "/rpc",
        json=make_request("session.get", {"session_id": "session-child"}, request_id="req_3"),
    )

    result = response.json()["result"]
    child = child_response.json()["result"]["session"]
    assert result["child_session_id"] == "session-child"
    assert result["parent_session_id"] == "session-parent"
    assert result["writes_state"] is True
    assert result["execution_authority"] is False
    assert child["parent_session_id"] == "session-parent"
    assert child["profile_id"] == "dev-loop"
    assert child["model_route"] == {"agent": "codex"}


def test_runtime_session_fork_validates_inputs(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post(
        "/rpc",
        json=make_request("session.create", {"session_id": "session-parent"}, request_id="req_1"),
    )

    missing_response = client.post("/rpc", json=make_request("session.fork", request_id="req_2"))
    unknown_response = client.post(
        "/rpc",
        json=make_request("session.fork", {"session_id": "missing"}, request_id="req_3"),
    )
    invalid_profile_response = client.post(
        "/rpc",
        json=make_request(
            "session.fork",
            {"session_id": "session-parent", "profile_id": "unbounded"},
            request_id="req_4",
        ),
    )

    assert missing_response.json()["error"]["code"] == "missing_session_id"
    assert unknown_response.json()["error"]["code"] == "unknown_session"
    assert invalid_profile_response.json()["error"]["code"] == "invalid_profile"


def test_runtime_prompt_send_records_semantic_prompt_without_execution_authority(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post(
        "/rpc",
        json=make_request("session.create", {"session_id": "session-prompt"}, request_id="req_1"),
    )

    response = client.post(
        "/rpc",
        json=make_request(
            "prompt.send",
            {"session_id": "session-prompt", "text": "Plan the next UI slice", "source_client": "hud"},
            request_id="req_2",
        ),
    )
    history_response = client.post(
        "/rpc",
        json=make_request("message.list", {"session_id": "session-prompt"}, request_id="req_3"),
    )

    result = response.json()["result"]
    messages = history_response.json()["result"]["messages"]
    assert result["writes_state"] is True
    assert result["execution_authority"] is False
    assert messages[-1]["event_type"] == "prompt.sent"
    assert messages[-1]["payload"]["text"] == "Plan the next UI slice"
    assert messages[-1]["payload"]["execution_authority"] is False


def test_runtime_prompt_send_validates_session_and_text(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post(
        "/rpc",
        json=make_request("session.create", {"session_id": "session-prompt"}, request_id="req_1"),
    )

    missing_session = client.post(
        "/rpc",
        json=make_request("prompt.send", {"text": "hello"}, request_id="req_2"),
    )
    missing_prompt = client.post(
        "/rpc",
        json=make_request("prompt.send", {"session_id": "session-prompt", "text": "   "}, request_id="req_3"),
    )
    unknown_session = client.post(
        "/rpc",
        json=make_request("prompt.send", {"session_id": "missing", "text": "hello"}, request_id="req_4"),
    )

    assert missing_session.json()["error"]["code"] == "missing_session_id"
    assert missing_prompt.json()["error"]["code"] == "missing_prompt"
    assert unknown_session.json()["error"]["code"] == "unknown_session"


def test_runtime_message_list_reports_empty_history_without_writing_state(tmp_path):
    state = tmp_path / "state"
    app = create_app(state)
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request("message.list", {"session_id": "missing"}, request_id="req_1"),
    )

    data = response.json()["result"]
    assert data["messages"] == []
    assert data["current_sequence"] == 0
    assert data["writes_state"] is False
    assert not state.exists()


def test_runtime_message_list_returns_session_events(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post(
        "/rpc",
        json=make_request(
            "session.create",
            {"session_id": "session-1", "title": "History", "source_client": "pytest"},
            request_id="req_1",
        ),
    )
    client.post(
        "/rpc",
        json=make_request(
            "voice.submit",
            {"session_id": "session-1", "transcript": "summarize current readiness"},
            request_id="req_2",
        ),
    )

    response = client.post(
        "/rpc",
        json=make_request("message.list", {"session_id": "session-1", "limit": 20}, request_id="req_3"),
    )

    data = response.json()["result"]
    event_types = [message["event_type"] for message in data["messages"]]
    assert event_types == ["session.created", "voice.transcript_final"]
    assert data["messages"][1]["payload"]["text"] == "summarize current readiness"
    assert data["current_sequence"] == 2
    assert data["writes_state"] is False


def test_runtime_message_search_returns_matching_events_without_writing(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-search"}, request_id="req_1"))
    client.post(
        "/rpc",
        json=make_request(
            "prompt.send",
            {"session_id": "session-search", "text": "Find the blue reactor plan"},
            request_id="req_2",
        ),
    )

    response = client.post(
        "/rpc",
        json=make_request("message.search", {"query": "blue reactor"}, request_id="req_3"),
    )

    data = response.json()["result"]
    assert data["writes_state"] is False
    assert data["query"] == "blue reactor"
    assert data["results"][0]["event_type"] == "prompt.sent"
    assert data["results"][0]["payload"]["text"] == "Find the blue reactor plan"


def test_runtime_message_search_can_filter_by_session(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    for session_id in ("session-a", "session-b"):
        client.post("/rpc", json=make_request("session.create", {"session_id": session_id}, request_id=session_id))
        client.post(
            "/rpc",
            json=make_request(
                "prompt.send",
                {"session_id": session_id, "text": "shared reactor keyword"},
                request_id=f"prompt-{session_id}",
            ),
        )

    response = client.post(
        "/rpc",
        json=make_request(
            "message.search",
            {"query": "reactor", "session_id": "session-b"},
            request_id="req_1",
        ),
    )

    assert {result["session_id"] for result in response.json()["result"]["results"]} == {"session-b"}


def test_runtime_message_search_absent_store_and_blank_query_do_not_write_state(tmp_path):
    state = tmp_path / "state"
    app = create_app(state)
    client = TestClient(app)

    blank_response = client.post("/rpc", json=make_request("message.search", {"query": "   "}, request_id="req_1"))
    missing_response = client.post("/rpc", json=make_request("message.search", {"query": "anything"}, request_id="req_2"))

    assert blank_response.json()["result"]["results"] == []
    assert missing_response.json()["result"]["results"] == []
    assert blank_response.json()["result"]["writes_state"] is False
    assert missing_response.json()["result"]["writes_state"] is False
    assert not state.exists()


def test_runtime_message_search_validates_session_filter_type(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request("message.search", {"query": "x", "session_id": 42}, request_id="req_1"),
    )

    assert response.json()["error"]["code"] == "invalid_session_id"


def test_runtime_swarm_plan_records_planning_event_without_execution_authority(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-swarm"}, request_id="req_1"))

    response = client.post(
        "/rpc",
        json=make_request(
            "swarm.plan",
            {
                "session_id": "session-swarm",
                "objective": "Plan UI and runtime lanes",
                "lanes": [
                    {"lane_id": "docs", "task": "Review docs", "agent": "jarvis_docs_researcher"},
                    "Review runtime tests",
                ],
            },
            request_id="req_2",
        ),
    )
    history_response = client.post(
        "/rpc",
        json=make_request("message.list", {"session_id": "session-swarm"}, request_id="req_3"),
    )

    result = response.json()["result"]
    messages = history_response.json()["result"]["messages"]
    swarm_event = messages[-1]
    assert result["writes_state"] is True
    assert result["execution_authority"] is False
    assert result["agent_launch"] is False
    assert result["worktrunk_mutation"] is False
    assert result["lane_count"] == 2
    assert swarm_event["event_type"] == "swarm.planned"
    assert swarm_event["payload"]["objective"] == "Plan UI and runtime lanes"
    assert swarm_event["payload"]["lanes"][0]["status"] == "planned"
    assert swarm_event["payload"]["lanes"][1]["agent"] == "unassigned"
    assert swarm_event["payload"]["command_execution"] is False


def test_runtime_swarm_plan_validates_session_objective_and_lanes(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-swarm"}, request_id="req_1"))

    missing_session = client.post(
        "/rpc",
        json=make_request("swarm.plan", {"objective": "Plan lanes"}, request_id="req_2"),
    )
    missing_objective = client.post(
        "/rpc",
        json=make_request("swarm.plan", {"session_id": "session-swarm", "objective": "   "}, request_id="req_3"),
    )
    unknown_session = client.post(
        "/rpc",
        json=make_request("swarm.plan", {"session_id": "missing", "objective": "Plan lanes"}, request_id="req_4"),
    )
    invalid_lanes = client.post(
        "/rpc",
        json=make_request(
            "swarm.plan",
            {"session_id": "session-swarm", "objective": "Plan lanes", "lanes": "not-a-list"},
            request_id="req_5",
        ),
    )

    assert missing_session.json()["error"]["code"] == "missing_session_id"
    assert missing_objective.json()["error"]["code"] == "missing_objective"
    assert unknown_session.json()["error"]["code"] == "unknown_session"
    assert invalid_lanes.json()["error"]["code"] == "invalid_lanes"


def test_runtime_swarm_start_records_approved_lifecycle_without_launching_agents(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    token = app.state.runtime_token
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-swarm"}, request_id="req_1"))
    plan_response = client.post(
        "/rpc",
        json=make_request(
            "swarm.plan",
            {"session_id": "session-swarm", "objective": "Plan review lanes", "lanes": ["Review runtime"]},
            request_id="req_2",
        ),
    )
    plan_event_id = plan_response.json()["result"]["swarm_plan_event_id"]
    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-swarm",
                "summary": "Record swarm start",
                "operation": "swarm.start",
                "risk": "medium",
                "scope": {"source": "swarm.start", "session_id": "session-swarm", "plan_event_id": plan_event_id},
            },
            request_id="approval_req",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": token,
            },
            request_id="approval_resp",
        ),
    )

    response = client.post(
        "/rpc",
        json=make_request(
            "swarm.start",
            {
                "session_id": "session-swarm",
                "plan_event_id": plan_event_id,
                "approval_id": approval["id"],
                "runtime_token": token,
            },
            request_id="req_3",
        ),
    )

    result = response.json()["result"]
    event = list(app.state.event_store.iter_events(session_id="session-swarm"))[-1]
    assert result["lifecycle_state"] == "started"
    assert result["writes_state"] is True
    assert result["approval_consumed"] is True
    assert result["execution_authority"] is False
    assert result["agent_launch"] is False
    assert result["worktrunk_mutation"] is False
    assert result["pty_launch"] is False
    assert result["command_execution"] is False
    assert result["runtime_workflow_execution"] is False
    assert event.event_type == "swarm.started"
    assert event.parent_event_id == plan_event_id
    assert app.state.event_store.approval(approval["id"])["status"] == "used"


def test_runtime_swarm_lifecycle_requires_matching_approval_and_runtime_token(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    token = app.state.runtime_token
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-swarm"}, request_id="req_1"))
    plan_response = client.post(
        "/rpc",
        json=make_request(
            "swarm.plan",
            {"session_id": "session-swarm", "objective": "Plan review lanes"},
            request_id="req_2",
        ),
    )
    plan_event_id = plan_response.json()["result"]["swarm_plan_event_id"]
    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-swarm",
                "summary": "Record swarm start",
                "operation": "swarm.start",
                "risk": "medium",
                "scope": {"source": "swarm.start", "session_id": "session-swarm", "plan_event_id": plan_event_id},
            },
            request_id="approval_req",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": token,
            },
            request_id="approval_resp",
        ),
    )

    missing_token = client.post(
        "/rpc",
        json=make_request(
            "swarm.start",
            {"session_id": "session-swarm", "plan_event_id": plan_event_id, "approval_id": approval["id"]},
            request_id="req_3",
        ),
    )
    mismatch = client.post(
        "/rpc",
        json=make_request(
            "swarm.start",
            {
                "session_id": "session-swarm",
                "plan_event_id": "evt_other",
                "approval_id": approval["id"],
                "runtime_token": token,
            },
            request_id="req_4",
        ),
    )

    assert missing_token.json()["error"]["code"] == "unauthorized"
    assert mismatch.json()["error"]["code"] == "approval_required"
    assert app.state.event_store.approval(approval["id"])["status"] == "approved"


def test_runtime_swarm_stop_records_approved_lifecycle_without_execution(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    token = app.state.runtime_token
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-swarm"}, request_id="req_1"))
    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-swarm",
                "summary": "Record swarm stop",
                "operation": "swarm.stop",
                "risk": "medium",
                "scope": {"source": "swarm.stop", "session_id": "session-swarm", "swarm_event_id": "evt_started"},
            },
            request_id="approval_req",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": token,
            },
            request_id="approval_resp",
        ),
    )

    response = client.post(
        "/rpc",
        json=make_request(
            "swarm.stop",
            {
                "session_id": "session-swarm",
                "swarm_event_id": "evt_started",
                "approval_id": approval["id"],
                "runtime_token": token,
            },
            request_id="req_2",
        ),
    )

    result = response.json()["result"]
    event = list(app.state.event_store.iter_events(session_id="session-swarm"))[-1]
    assert result["lifecycle_state"] == "stopped"
    assert result["execution_authority"] is False
    assert result["agent_launch"] is False
    assert result["worktrunk_mutation"] is False
    assert result["runtime_workflow_execution"] is False
    assert event.event_type == "swarm.stopped"
    assert event.parent_event_id == "evt_started"
    assert app.state.event_store.approval(approval["id"])["status"] == "used"


def test_runtime_swarm_launch_starts_approved_role_labeled_pty_panes(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    token = app.state.runtime_token
    command = "python3 -c \"print('codex role')\""
    roles = [{"role_id": "codex-executor", "label": "Codex Executor", "command": command, "profile": "swarm"}]
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-swarm"}, request_id="req_1"))
    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-swarm",
                "summary": "Launch swarm role panes",
                "operation": "swarm.launch",
                "risk": "high",
                "scope": {
                    "source": "swarm.launch",
                    "session_id": "session-swarm",
                    "swarm_event_id": "evt_started",
                    "roles": roles,
                },
            },
            request_id="approval_req",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": token,
            },
            request_id="approval_resp",
        ),
    )

    response = client.post(
        "/rpc",
        json=make_request(
            "swarm.launch",
            {
                "session_id": "session-swarm",
                "swarm_event_id": "evt_started",
                "roles": roles,
                "approval_id": approval["id"],
                "runtime_token": token,
            },
            request_id="req_2",
        ),
    )

    try:
        result = response.json()["result"]
        channel_id = result["roles"][0]["channel_id"]
        app.state.pty_supervisor.get(channel_id).wait(timeout=2)
        deadline = time.time() + 2
        text = ""
        while time.time() < deadline and "codex role" not in text:
            text += "".join(chunk.chunk for chunk in app.state.pty_supervisor.drain_output(channel_id))
            time.sleep(0.02)
    finally:
        app.state.pty_supervisor.close_all()

    event = list(app.state.event_store.iter_events(session_id="session-swarm"))[-1]
    assert result["role_count"] == 1
    assert result["execution_authority"] is True
    assert result["agent_launch"] is True
    assert result["pty_launch"] is True
    assert result["command_execution"] is True
    assert result["worktrunk_mutation"] is False
    assert result["git_mutation"] is False
    assert result["runtime_workflow_execution"] is False
    assert result["roles"][0]["role_id"] == "codex-executor"
    assert result["roles"][0]["approval_id"] == approval["id"]
    assert "codex role" in text
    assert event.event_type == "swarm.launched"
    assert event.parent_event_id == "evt_started"
    assert app.state.event_store.approval(approval["id"])["status"] == "used"


def test_runtime_swarm_launch_requires_matching_approval_and_runtime_token(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    token = app.state.runtime_token
    command = "python3 -c \"print('codex role')\""
    roles = [{"role_id": "codex-executor", "command": command, "profile": "swarm"}]
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-swarm"}, request_id="req_1"))
    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-swarm",
                "summary": "Launch swarm role panes",
                "operation": "swarm.launch",
                "risk": "high",
                "scope": {
                    "source": "swarm.launch",
                    "session_id": "session-swarm",
                    "swarm_event_id": "evt_started",
                    "roles": roles,
                },
            },
            request_id="approval_req",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": token,
            },
            request_id="approval_resp",
        ),
    )

    missing_token = client.post(
        "/rpc",
        json=make_request(
            "swarm.launch",
            {
                "session_id": "session-swarm",
                "swarm_event_id": "evt_started",
                "roles": roles,
                "approval_id": approval["id"],
            },
            request_id="req_2",
        ),
    )
    mismatched_command = client.post(
        "/rpc",
        json=make_request(
            "swarm.launch",
            {
                "session_id": "session-swarm",
                "swarm_event_id": "evt_started",
                "roles": [{"role_id": "codex-executor", "command": "pwd", "profile": "swarm"}],
                "approval_id": approval["id"],
                "runtime_token": token,
            },
            request_id="req_3",
        ),
    )
    mismatched_cwd = client.post(
        "/rpc",
        json=make_request(
            "swarm.launch",
            {
                "session_id": "session-swarm",
                "swarm_event_id": "evt_started",
                "roles": [{"role_id": "codex-executor", "command": command, "profile": "swarm", "cwd": str(tmp_path)}],
                "approval_id": approval["id"],
                "runtime_token": token,
            },
            request_id="req_4",
        ),
    )

    assert missing_token.json()["error"]["code"] == "unauthorized"
    assert mismatched_command.json()["error"]["code"] == "approval_required"
    assert mismatched_cwd.json()["error"]["code"] == "approval_required"
    assert app.state.event_store.approval(approval["id"])["status"] == "approved"


def test_runtime_swarm_launch_validates_role_shape_and_limit(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-swarm"}, request_id="req_1"))

    invalid_profile = client.post(
        "/rpc",
        json=make_request(
            "swarm.launch",
            {
                "session_id": "session-swarm",
                "swarm_event_id": "evt_started",
                "roles": [{"role_id": "bad", "command": "pwd", "profile": "unknown"}],
            },
            request_id="req_2",
        ),
    )
    too_many_roles = client.post(
        "/rpc",
        json=make_request(
            "swarm.launch",
            {
                "session_id": "session-swarm",
                "swarm_event_id": "evt_started",
                "roles": [{"role_id": f"role-{index}", "command": "pwd"} for index in range(5)],
            },
            request_id="req_3",
        ),
    )

    assert invalid_profile.json()["error"]["code"] == "invalid_roles"
    assert too_many_roles.json()["error"]["code"] == "invalid_roles"


def test_runtime_swarm_launch_preserves_hardline_policy_blocks(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    token = app.state.runtime_token
    roles = [{"role_id": "danger", "command": "git reset --hard HEAD", "profile": "swarm"}]
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-swarm"}, request_id="req_1"))
    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-swarm",
                "summary": "Launch dangerous swarm role",
                "operation": "swarm.launch",
                "risk": "high",
                "scope": {
                    "source": "swarm.launch",
                    "session_id": "session-swarm",
                    "swarm_event_id": "evt_started",
                    "roles": roles,
                },
            },
            request_id="approval_req",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": token,
            },
            request_id="approval_resp",
        ),
    )

    response = client.post(
        "/rpc",
        json=make_request(
            "swarm.launch",
            {
                "session_id": "session-swarm",
                "swarm_event_id": "evt_started",
                "roles": roles,
                "approval_id": approval["id"],
                "runtime_token": token,
            },
            request_id="req_2",
        ),
    )

    assert response.json()["error"]["code"] == "policy_blocked"
    assert response.json()["error"]["policy_blocked"] is True
    assert app.state.event_store.approval(approval["id"])["status"] == "approved"


def test_runtime_loop_start_records_approved_lifecycle_without_execution(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    token = app.state.runtime_token
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-loop"}, request_id="req_1"))
    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-loop",
                "summary": "Record loop start",
                "operation": "loop.start",
                "risk": "medium",
                "scope": {"source": "loop.start", "session_id": "session-loop"},
            },
            request_id="approval_req",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": token,
            },
            request_id="approval_resp",
        ),
    )

    response = client.post(
        "/rpc",
        json=make_request(
            "loop.start",
            {
                "session_id": "session-loop",
                "objective": "Continue verified implementation loop",
                "approval_id": approval["id"],
                "runtime_token": token,
            },
            request_id="req_2",
        ),
    )

    result = response.json()["result"]
    event = list(app.state.event_store.iter_events(session_id="session-loop"))[-1]
    assert result["lifecycle_state"] == "started"
    assert result["writes_state"] is True
    assert result["approval_consumed"] is True
    assert result["execution_authority"] is False
    assert result["agent_launch"] is False
    assert result["worktrunk_mutation"] is False
    assert result["pty_launch"] is False
    assert result["command_execution"] is False
    assert result["runtime_workflow_execution"] is False
    assert event.event_type == "loop.started"
    assert event.payload["objective"] == "Continue verified implementation loop"
    assert app.state.event_store.approval(approval["id"])["status"] == "used"


def test_runtime_loop_lifecycle_requires_matching_approval_and_runtime_token(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    token = app.state.runtime_token
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-loop"}, request_id="req_1"))
    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-loop",
                "summary": "Record loop pause",
                "operation": "loop.pause",
                "risk": "medium",
                "scope": {"source": "loop.pause", "session_id": "session-loop"},
            },
            request_id="approval_req",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": token,
            },
            request_id="approval_resp",
        ),
    )

    missing_token = client.post(
        "/rpc",
        json=make_request(
            "loop.pause",
            {"session_id": "session-loop", "approval_id": approval["id"]},
            request_id="req_2",
        ),
    )
    mismatch = client.post(
        "/rpc",
        json=make_request(
            "loop.stop",
            {"session_id": "session-loop", "approval_id": approval["id"], "runtime_token": token},
            request_id="req_3",
        ),
    )

    assert missing_token.json()["error"]["code"] == "unauthorized"
    assert mismatch.json()["error"]["code"] == "approval_required"
    assert app.state.event_store.approval(approval["id"])["status"] == "approved"


def test_runtime_loop_stop_records_parent_lifecycle_reference_without_stopping_processes(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    token = app.state.runtime_token
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-loop"}, request_id="req_1"))
    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-loop",
                "summary": "Record loop stop",
                "operation": "loop.stop",
                "risk": "medium",
                "scope": {"source": "loop.stop", "session_id": "session-loop"},
            },
            request_id="approval_req",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": token,
            },
            request_id="approval_resp",
        ),
    )

    response = client.post(
        "/rpc",
        json=make_request(
            "loop.stop",
            {
                "session_id": "session-loop",
                "loop_event_id": "evt_loop_started",
                "approval_id": approval["id"],
                "runtime_token": token,
            },
            request_id="req_2",
        ),
    )

    result = response.json()["result"]
    event = list(app.state.event_store.iter_events(session_id="session-loop"))[-1]
    assert result["lifecycle_state"] == "stopped"
    assert result["execution_authority"] is False
    assert result["runtime_workflow_execution"] is False
    assert event.event_type == "loop.stopped"
    assert event.parent_event_id == "evt_loop_started"
    assert event.payload["loop_event_id"] == "evt_loop_started"
    assert app.state.event_store.approval(approval["id"])["status"] == "used"


def test_runtime_codeburn_status_returns_compact_telemetry(tmp_path, monkeypatch):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    monkeypatch.setattr(
        runtime_app,
        "read_codeburn_status",
        lambda: CodeburnStatus(
            available=True,
            today_cost=0.0,
            today_calls=0,
            month_cost=527.99,
            month_calls=5787,
            raw="Today  $0.00  0 calls    Month  $527.99  5787 calls",
        ),
    )

    response = client.post(
        "/rpc",
        json=make_request("telemetry.codeburn_status", request_id="req_1"),
    )

    data = response.json()["result"]["codeburn"]
    assert data["available"] is True
    assert data["month_cost"] == 527.99
    assert data["month_calls"] == 5787
    assert data["writes_state"] is False
    assert data["shell"] is False


def test_runtime_agent_provider_status_is_read_only(tmp_path):
    state = tmp_path / "state"
    app = create_app(state)
    client = TestClient(app)

    response = client.post("/rpc", json=make_request("agent.provider_status", request_id="req_1"))

    result = response.json()["result"]
    providers = {provider["id"]: provider for provider in result["providers"]}
    assert result["status"] == "ready"
    assert result["writes_state"] is False
    assert result["launch_performed"] is False
    assert result["execution_authority"] is False
    assert providers["codex"]["launch_performed"] is False
    assert providers["antigravity"]["launch_performed"] is False
    assert providers["codeburn"]["execution_boundary"] == "fixed no-shell telemetry adapter"
    assert not state.exists()


def test_runtime_readiness_reports_foundation_without_writing_state(tmp_path):
    state = tmp_path / "state"
    app = create_app(state)
    client = TestClient(app)

    response = client.post("/rpc", json=make_request("runtime.readiness", request_id="req_1"))

    data = response.json()["result"]
    assert data["status"] == "foundation-ready"
    assert data["production_complete"] is False
    assert data["writes_state"] is False
    assert data["checks"]["approval_replay_protection"] is True
    assert data["checks"]["approval_runtime_token"] is True
    assert data["checks"]["websocket_origin_validation"] is True
    assert data["checks"]["stt_runtime_path_constraints"] is True
    assert data["checks"]["voice_execution_authority"] is False
    assert data["checks"]["agent_provider_status"] is True
    assert data["checks"]["swarm_role_launch"] is True
    assert data["checks"]["electron_hud_scaffold"] is True
    assert data["checks"]["electron_lockfile"] is True
    assert data["checks"]["mobile_preflight"] is True
    assert data["checks"]["mobile_validation_plan"] is True
    assert data["checks"]["gemini_feasibility"] is True
    assert data["checks"]["gemini_validation_plan"] is True
    assert data["checks"]["loop_lifecycle_records"] is True
    assert data["checks"]["bounded_loop_run_once"] is True
    assert data["checks"]["packaging_preflight"] is True
    assert data["checks"]["local_stt_discovery"] is True
    assert data["checks"]["mobile_host_discovery"] is True
    assert data["mobile_access"]["writes_state"] is False
    assert data["mobile_access"]["network_probe_performed"] is False
    assert data["mobile_access"]["service_launch_performed"] is False
    assert data["mobile_access"]["browser_opened"] is False
    assert data["mobile_access"]["execution_authority"] is False
    assert isinstance(data["mobile_access"]["candidate_count"], int)
    if data["mobile_access"]["recommended_candidate"]:
        assert data["mobile_access"]["recommended_candidate"]["iphone_reachable_candidate"] is True
        assert data["mobile_access"]["recommended_candidate"]["runtime_command"].startswith(
            "jarvis-codex runtime serve"
        )
    assert "electron_installer_artifact" in data["checks"]
    assert "electron_icon" in data["checks"]
    if data["checks"]["electron_package_artifact"]:
        assert "electron_sign_and_distribution_flow" in data["remaining_gaps"]
        assert "electron_package_sign_flow" not in data["remaining_gaps"]
    else:
        assert "electron_package_sign_flow" in data["remaining_gaps"]
    assert "approved_gemini_live_network_test" in data["remaining_gaps"]
    assert "actual_loop_execution" not in data["remaining_gaps"]
    assert not state.exists()


def test_runtime_release_gate_status_reads_state_without_writing(tmp_path):
    state = tmp_path / "state"
    JarvisState(state).record_release_evidence(
        "external_security_review",
        "External reviewer artifact submitted, not accepted yet.",
    )
    app = create_app(state)
    client = TestClient(app)

    response = client.post("/rpc", json=make_request("release.gate_status", request_id="req_1"))

    data = response.json()["result"]
    external = next(item for item in data["gates"] if item["gate"] == "external_security_review")
    assert data["status"] == "open-gates"
    assert data["writes_state"] is False
    assert data["execution_authority"] is False
    assert data["evidence_closes_gates"] is False
    assert external["evidence_count"] == 1
    assert external["release_gate_closed"] is False


def test_runtime_profile_list_reports_policy_catalog_without_writing_state(tmp_path):
    state = tmp_path / "state"
    app = create_app(state)
    client = TestClient(app)

    response = client.post("/rpc", json=make_request("profile.list", request_id="req_1"))

    data = response.json()["result"]
    profile_ids = {profile["id"] for profile in data["profiles"]}
    assert data["default_profile"] == "observe"
    assert data["writes_state"] is False
    assert profile_ids == {"observe", "dev-loop", "swarm", "high-risk-runtime"}
    assert all(profile["description"] for profile in data["profiles"])
    assert not state.exists()


def test_runtime_profile_set_updates_session_profile_and_history(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post(
        "/rpc",
        json=make_request("session.create", {"session_id": "session-profile"}, request_id="req_1"),
    )

    response = client.post(
        "/rpc",
        json=make_request(
            "profile.set",
            {"session_id": "session-profile", "profile_id": "dev-loop", "reason": "test"},
            request_id="req_2",
        ),
    )
    get_response = client.post(
        "/rpc",
        json=make_request("session.get", {"session_id": "session-profile"}, request_id="req_3"),
    )
    history_response = client.post(
        "/rpc",
        json=make_request("message.list", {"session_id": "session-profile"}, request_id="req_4"),
    )

    result = response.json()["result"]
    assert result["profile_id"] == "dev-loop"
    assert result["writes_state"] is True
    assert get_response.json()["result"]["session"]["profile_id"] == "dev-loop"
    assert [event["event_type"] for event in history_response.json()["result"]["messages"]] == [
        "session.created",
        "session.profile_set",
    ]


def test_runtime_profile_set_is_idempotent_for_current_profile(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post(
        "/rpc",
        json=make_request(
            "session.create",
            {"session_id": "session-profile", "profile_id": "dev-loop"},
            request_id="req_1",
        ),
    )

    response = client.post(
        "/rpc",
        json=make_request(
            "profile.set",
            {"session_id": "session-profile", "profile_id": "dev-loop"},
            request_id="req_2",
        ),
    )

    result = response.json()["result"]
    assert result["already_set"] is True
    assert result["writes_state"] is False
    assert app.state.event_store.current_sequence() == 1


def test_runtime_profile_set_validates_session_and_profile(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    missing_response = client.post("/rpc", json=make_request("profile.set", request_id="req_1"))
    invalid_profile_response = client.post(
        "/rpc",
        json=make_request(
            "profile.set",
            {"session_id": "session-profile", "profile_id": "unbounded"},
            request_id="req_2",
        ),
    )
    unknown_response = client.post(
        "/rpc",
        json=make_request(
            "profile.set",
            {"session_id": "missing", "profile_id": "observe"},
            request_id="req_3",
        ),
    )

    assert missing_response.json()["error"]["code"] == "missing_session_id"
    assert invalid_profile_response.json()["error"]["code"] == "invalid_profile"
    assert unknown_response.json()["error"]["code"] == "unknown_session"


def test_runtime_session_create_rejects_unknown_profile(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request(
            "session.create",
            {"session_id": "session-1", "profile_id": "unbounded"},
            request_id="req_1",
        ),
    )

    assert response.status_code == 200
    assert response.json()["error"]["code"] == "invalid_profile"
    assert not (tmp_path / "state").exists()


def test_runtime_command_classify_uses_policy(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request(
            "command.classify",
            {"command": "git reset --hard HEAD", "profile": "dev-loop"},
            request_id="req_1",
        ),
    )

    assert response.status_code == 200
    assert response.json()["result"]["status"] == "block"


def test_runtime_command_propose_records_policy_review_without_execution_or_approval(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-command"}, request_id="req_1"))

    response = client.post(
        "/rpc",
        json=make_request(
            "command.propose",
            {"session_id": "session-command", "command": "git status --short", "profile": "observe"},
            request_id="req_2",
        ),
    )
    history_response = client.post(
        "/rpc",
        json=make_request("message.list", {"session_id": "session-command"}, request_id="req_3"),
    )
    approvals_response = client.post(
        "/rpc",
        json=make_request("approval.list", {"status": "pending"}, request_id="req_4"),
    )

    result = response.json()["result"]
    event = history_response.json()["result"]["messages"][-1]
    assert result["writes_state"] is True
    assert result["policy"]["status"] == "allow"
    assert result["policy"]["execution_authority"] is True
    assert result["approval_required"] is True
    assert result["approval_created"] is False
    assert result["execution_authority"] is False
    assert result["routed_as_command"] is False
    assert result["pty_launch"] is False
    assert result["worktrunk_mutation"] is False
    assert approvals_response.json()["result"]["approvals"] == []
    assert event["event_type"] == "command.proposed"
    assert event["payload"]["command"] == "git status --short"
    assert event["payload"]["approval_created"] is False
    assert event["payload"]["execution_authority"] is False


def test_runtime_command_propose_validates_inputs(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    client.post("/rpc", json=make_request("session.create", {"session_id": "session-command"}, request_id="req_1"))

    missing_session = client.post(
        "/rpc",
        json=make_request("command.propose", {"command": "git status"}, request_id="req_2"),
    )
    missing_command = client.post(
        "/rpc",
        json=make_request("command.propose", {"session_id": "session-command", "command": "  "}, request_id="req_3"),
    )
    invalid_profile = client.post(
        "/rpc",
        json=make_request(
            "command.propose",
            {"session_id": "session-command", "command": "git status", "profile": "invalid"},
            request_id="req_4",
        ),
    )
    unknown_session = client.post(
        "/rpc",
        json=make_request(
            "command.propose",
            {"session_id": "missing", "command": "git status"},
            request_id="req_5",
        ),
    )

    assert missing_session.json()["error"]["code"] == "missing_session_id"
    assert missing_command.json()["error"]["code"] == "missing_command"
    assert invalid_profile.json()["error"]["code"] == "invalid_profile"
    assert unknown_session.json()["error"]["code"] == "unknown_session"


def test_runtime_planned_methods_are_explicitly_not_implemented(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    for index, method in enumerate(("pty.restart", "session.cancel", "prompt.cancel")):
        response = client.post("/rpc", json=make_request(method, request_id=f"req_{index}"))

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "response"
        assert data["error"]["code"] == "not_implemented"
        assert "planned but not implemented" in data["error"]["message"]


def test_runtime_pty_create_returns_channel_for_allowed_command(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request(
            "pty.create",
            {"command": "pwd", "profile": "dev-loop"},
            request_id="req_1",
        ),
    )

    try:
        assert response.status_code == 200
        data = response.json()
        channel_id = data["result"]["channel_id"]
        app.state.pty_supervisor.get(channel_id).wait(timeout=2)
        deadline = time.time() + 2
        text = ""
        while time.time() < deadline and "/" not in text:
            text += "".join(chunk.chunk for chunk in app.state.pty_supervisor.drain_output(channel_id))
            time.sleep(0.02)
    finally:
        app.state.pty_supervisor.close_all()

    assert data["type"] == "response"
    assert data["result"]["policy"]["status"] == "allow"
    assert "/" in text


def test_runtime_pty_create_surfaces_policy_blocks(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request(
            "pty.create",
            {"command": "git reset --hard HEAD", "profile": "dev-loop"},
            request_id="req_1",
        ),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == "policy_blocked"
    assert data["error"]["policy_blocked"] is True


def test_runtime_pty_create_surfaces_approval_requirements(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request(
            "pty.create",
            {"command": "python3 -c \"print('runtime pty')\"", "profile": "observe"},
            request_id="req_1",
        ),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == "approval_required"
    assert data["error"]["approval_required"] is True


def test_runtime_pty_create_uses_matching_approved_approval_record(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    command = "python3 -c \"print('approved pty')\""

    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-1",
                "summary": "Launch approved PTY",
                "operation": command,
                "risk": "medium",
                "scope": {"command": command},
            },
            request_id="req_1",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": _runtime_token(client),
            },
            request_id="req_2",
        ),
    )
    create_response = client.post(
        "/rpc",
        json=make_request(
            "pty.create",
            {
                "command": command,
                "profile": "observe",
                "approval_id": approval["id"],
                "runtime_token": _runtime_token(client),
            },
            request_id="req_3",
        ),
    )
    replay_response = client.post(
        "/rpc",
        json=make_request(
            "pty.create",
            {
                "command": command,
                "profile": "observe",
                "approval_id": approval["id"],
                "runtime_token": _runtime_token(client),
            },
            request_id="req_4",
        ),
    )

    try:
        data = create_response.json()["result"]
        channel_id = data["channel_id"]
        app.state.pty_supervisor.get(channel_id).wait(timeout=2)
        deadline = time.time() + 2
        text = ""
        while time.time() < deadline and "approved pty" not in text:
            text += "".join(chunk.chunk for chunk in app.state.pty_supervisor.drain_output(channel_id))
            time.sleep(0.02)
    finally:
        app.state.pty_supervisor.close_all()

    assert data["approval_granted"] is True
    assert data["approval_id"] == approval["id"]
    assert data["policy"]["status"] == "approval_required"
    assert "approved pty" in text
    assert app.state.event_store.approval(approval["id"])["status"] == "used"
    assert replay_response.json()["error"]["code"] == "approval_required"


def test_runtime_pty_create_rejects_mismatched_or_blocked_approval(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    approved_command = "python3 -c \"print('approved')\""

    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-1",
                "summary": "Launch approved PTY",
                "operation": approved_command,
                "risk": "medium",
                "scope": {"command": approved_command},
            },
            request_id="req_1",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": _runtime_token(client),
            },
            request_id="req_2",
        ),
    )

    mismatch = client.post(
        "/rpc",
        json=make_request(
            "pty.create",
            {
                "command": "python3 -c \"print('different')\"",
                "profile": "observe",
                "approval_id": approval["id"],
                "runtime_token": _runtime_token(client),
            },
            request_id="req_3",
        ),
    )
    blocked = client.post(
        "/rpc",
        json=make_request(
            "pty.create",
            {
                "command": "git reset --hard HEAD",
                "profile": "dev-loop",
                "approval_id": approval["id"],
                "runtime_token": _runtime_token(client),
            },
            request_id="req_4",
        ),
    )

    assert mismatch.json()["error"]["code"] == "approval_required"
    assert blocked.json()["error"]["code"] == "policy_blocked"


def test_runtime_pty_create_requires_runtime_token_to_consume_approval(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    command = "python3 -c \"print('approved')\""

    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-1",
                "summary": "Launch approved PTY",
                "operation": command,
                "risk": "medium",
                "scope": {"command": command},
            },
            request_id="req_1",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": _runtime_token(client),
            },
            request_id="req_2",
        ),
    )

    response = client.post(
        "/rpc",
        json=make_request(
            "pty.create",
            {"command": command, "profile": "observe", "approval_id": approval["id"]},
            request_id="req_3",
        ),
    )

    assert response.json()["error"]["code"] == "unauthorized"
    assert app.state.event_store.approval(approval["id"])["status"] == "approved"


def test_runtime_pty_input_resize_and_kill(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    create_response = client.post(
        "/rpc",
        json=make_request("pty.create", {"command": "cat", "profile": "observe"}, request_id="req_1"),
    )
    channel_id = create_response.json()["result"]["channel_id"]

    try:
        input_response = client.post(
            "/rpc",
            json=make_request(
                "pty.input",
                {"channel_id": channel_id, "text": "hello runtime\n"},
                request_id="req_2",
            ),
        )
        resize_response = client.post(
            "/rpc",
            json=make_request(
                "pty.resize",
                {"channel_id": channel_id, "rows": 24, "cols": 80},
                request_id="req_3",
            ),
        )
        kill_response = client.post(
            "/rpc",
            json=make_request("pty.kill", {"channel_id": channel_id}, request_id="req_4"),
        )
    finally:
        app.state.pty_supervisor.close_all()

    assert input_response.json()["result"]["accepted"] is True
    assert resize_response.json()["result"]["rows"] == 24
    assert isinstance(kill_response.json()["result"]["returncode"], int)


def test_runtime_approval_lifecycle_and_event_subscription(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-1",
                "summary": "Run targeted tests",
                "operation": "uv run pytest tests/test_runtime_app.py",
                "risk": "medium",
                "scope": {"command": "uv run pytest tests/test_runtime_app.py"},
            },
            request_id="req_1",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    list_response = client.post(
        "/rpc",
        json=make_request("approval.list", {"status": "pending"}, request_id="req_2"),
    )
    unauthorized_response = client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {"approval_id": approval["id"], "status": "approved", "reason": "targeted"},
            request_id="req_3",
        ),
    )
    respond_response = client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "targeted",
                "runtime_token": _runtime_token(client),
            },
            request_id="req_4",
        ),
    )
    subscribe_response = client.post(
        "/rpc",
        json=make_request(
            "event.subscribe",
            {"session_id": "session-1", "since_sequence": 0, "limit": 10},
            request_id="req_5",
        ),
    )

    assert approval["status"] == "pending"
    assert list_response.json()["result"]["approvals"][0]["id"] == approval["id"]
    assert unauthorized_response.json()["error"]["code"] == "unauthorized"
    assert respond_response.json()["result"]["approval"]["status"] == "approved"
    replay_types = [event["event_type"] for event in subscribe_response.json()["result"]["replay"]]
    assert replay_types == ["approval.requested", "approval.responded"]


def test_runtime_approval_errors_are_structured(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request("approval.request", {"session_id": "session-1", "summary": ""}, request_id="req_1"),
    )

    assert response.status_code == 200
    assert response.json()["error"]["code"] == "invalid_approval"


def test_runtime_voice_provider_status_and_transcript_submit(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    status_response = client.post(
        "/rpc",
        json=make_request("voice.provider_status", request_id="req_1"),
    )
    start_response = client.post(
        "/rpc",
        json=make_request(
            "voice.start",
            {"session_id": "session-voice", "provider": "browser-web-speech"},
            request_id="req_2",
        ),
    )
    submit_response = client.post(
        "/rpc",
        json=make_request(
            "voice.submit",
            {
                "session_id": "session-voice",
                "provider": "browser-web-speech",
                "transcript": "Draft the Jarvis mobile plan.",
            },
            request_id="req_3",
        ),
    )
    stop_response = client.post(
        "/rpc",
        json=make_request(
            "voice.stop",
            {"session_id": "session-voice", "provider": "browser-web-speech"},
            request_id="req_4",
        ),
    )

    assert status_response.json()["result"]["providers"]["browser_web_speech"]["status"] == "client-managed"
    assert start_response.json()["result"]["event"]["event_type"] == "voice.start_requested"
    submit = submit_response.json()["result"]
    assert submit["characters"] == len("Draft the Jarvis mobile plan.")
    assert submit["execution_authority"] is False
    assert submit["routed_as_command"] is False
    assert submit["event"]["event_type"] == "voice.transcript_final"
    assert stop_response.json()["result"]["event"]["event_type"] == "voice.stopped"


def test_runtime_voice_intent_propose_classifies_without_execution_authority(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.intent_propose",
            {"session_id": "session-voice", "transcript": "run git status --short", "profile": "observe"},
            request_id="req_1",
        ),
    )

    data = response.json()["result"]
    proposal = data["proposal"]
    assert response.status_code == 200
    assert proposal["intent_type"] == "command_proposal"
    assert proposal["command"] == "git status --short"
    assert proposal["policy"]["status"] == "allow"
    assert proposal["policy"]["execution_authority"] is True
    assert proposal["approval_required"] is True
    assert proposal["execution_authority"] is False
    assert proposal["routed_as_command"] is False
    assert data["execution_authority"] is False
    assert data["routed_as_command"] is False
    assert data["event"]["event_type"] == "voice.intent_classified"


def test_runtime_voice_intent_propose_surfaces_invalid_inputs(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    empty = client.post(
        "/rpc",
        json=make_request("voice.intent_propose", {"session_id": "session-voice", "transcript": " "}, request_id="req_1"),
    )
    bad_profile = client.post(
        "/rpc",
        json=make_request(
            "voice.intent_propose",
            {"session_id": "session-voice", "transcript": "run git status", "profile": "invalid"},
            request_id="req_2",
        ),
    )

    assert empty.json()["error"]["code"] == "invalid_transcript"
    assert bad_profile.json()["error"]["code"] == "invalid_profile"


def test_runtime_voice_submit_rejects_empty_transcript(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request("voice.submit", {"session_id": "session-voice", "transcript": "  "}, request_id="req_1"),
    )

    assert response.status_code == 200
    assert response.json()["error"]["code"] == "invalid_transcript"


def test_runtime_voice_audio_chunk_writes_local_audio_and_event(tmp_path):
    state = tmp_path / "state"
    app = create_app(state)
    client = TestClient(app)
    chunk = base64.b64encode(b"webm-bytes").decode("ascii")

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.audio_chunk",
            {
                "session_id": "session-voice",
                "utterance_id": "utt-1",
                "sequence": 0,
                "mime_type": "audio/webm",
                "chunk_b64": chunk,
                "final": True,
            },
            request_id="req_1",
        ),
    )

    data = response.json()["result"]
    audio_path = Path(data["audio"]["path"])
    assert response.status_code == 200
    assert data["audio"]["audio_processed"] is False
    assert data["event"]["event_type"] == "voice.audio_utterance_received"
    assert data["event"]["payload"]["execution_authority"] is False
    assert data["event"]["payload"]["audio_processed"] is False
    assert str(audio_path).startswith(str(state))
    assert audio_path.read_bytes() == b"webm-bytes"
    assert data["audio"]["bytes_written"] == len(b"webm-bytes")


def test_runtime_voice_audio_chunk_rejects_bad_base64(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request("voice.audio_chunk", {"session_id": "session-voice", "chunk_b64": "bad!"}, request_id="req_1"),
    )

    assert response.status_code == 200
    assert response.json()["error"]["code"] == "invalid_audio_chunk"


def _approve_voice_transcription(client: TestClient, audio: Path, model: Path, model_id: str | None = None) -> str:
    scope = {
        "source": "voice.transcribe_audio",
        "audio_file": str(audio),
    }
    if model_id:
        scope["model_id"] = model_id
    else:
        scope["model_path"] = str(model)
    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-voice",
                "summary": "Transcribe local audio",
                "operation": "voice.transcribe_audio",
                "risk": "medium",
                "scope": scope,
            },
            request_id="approval_req",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": _runtime_token(client),
            },
            request_id="approval_resp",
        ),
    )
    return str(approval["id"])


def _approve_voice_synthesis(client: TestClient, text: str) -> str:
    text_sha256 = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
    request_response = client.post(
        "/rpc",
        json=make_request(
            "approval.request",
            {
                "session_id": "session-voice",
                "summary": "Synthesize local speech",
                "operation": "voice.synthesize_audio",
                "risk": "medium",
                "scope": {
                    "source": "voice.synthesize_audio",
                    "text_sha256": text_sha256,
                },
            },
            request_id="tts_approval_req",
        ),
    )
    approval = request_response.json()["result"]["approval"]
    client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {
                "approval_id": approval["id"],
                "status": "approved",
                "reason": "operator approved",
                "runtime_token": _runtime_token(client),
            },
            request_id="tts_approval_resp",
        ),
    )
    return str(approval["id"])


def test_runtime_voice_transcribe_audio_requires_explicit_approval(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.transcribe_audio",
            {"session_id": "session-voice", "audio_file": "/tmp/audio.webm"},
            request_id="req_1",
        ),
    )

    data = response.json()
    assert response.status_code == 200
    assert data["error"]["code"] == "approval_required"
    assert data["error"]["approval_required"] is True


def test_runtime_voice_transcribe_audio_writes_transcript_event(tmp_path, monkeypatch):
    state = tmp_path / "state"
    audio = state / "runtime" / "audio" / "session-voice" / "sample.webm"
    model = state / "runtime" / "models" / "model.bin"
    adapter = tmp_path / "fake_stt.py"
    audio.parent.mkdir(parents=True)
    model.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    model.write_bytes(b"model")
    adapter.write_text(
        "import argparse\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--audio-file')\n"
        "parser.add_argument('--model')\n"
        "args = parser.parse_args()\n"
        "print('open the diagnostics panel')\n",
        encoding="utf-8",
    )
    app = create_app(state)
    client = TestClient(app)
    approval_id = _approve_voice_transcription(client, audio, model)
    monkeypatch.setenv("JARVIS_LOCAL_STT_COMMAND", f"{sys.executable} {adapter}")

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.transcribe_audio",
            {
                "session_id": "session-voice",
                "audio_file": str(audio),
                "model_path": str(model),
                "stt_command": "python3 /tmp/malicious_client_supplied_stt.py",
                "approval_id": approval_id,
                "runtime_token": _runtime_token(client),
                "timeout_seconds": 5,
            },
            request_id="req_1",
        ),
    )

    data = response.json()["result"]
    payload = data["event"]["payload"]
    assert response.status_code == 200
    assert data["characters"] == len("open the diagnostics panel")
    assert data["audio_processed"] is True
    assert data["external_services"] is False
    assert data["execution_authority"] is False
    assert data["routed_as_command"] is False
    assert payload["text"] == "open the diagnostics panel"
    assert payload["provider"] == "local-stt-adapter"
    assert payload["audio_processed"] is True
    assert payload["external_services"] is False
    assert payload["execution_authority"] is False
    assert app.state.event_store.approval(approval_id)["status"] == "used"


def test_runtime_voice_transcribe_audio_resolves_server_model_id(tmp_path, monkeypatch):
    state = tmp_path / "state"
    audio = state / "runtime" / "audio" / "session-voice" / "sample.wav"
    model_root = tmp_path / "stt-models"
    model = model_root / "ggml-tiny.en.bin"
    adapter = tmp_path / "fake_stt.py"
    audio.parent.mkdir(parents=True)
    model_root.mkdir()
    audio.write_bytes(b"audio")
    model.write_bytes(b"model")
    adapter.write_text(
        "import argparse\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--audio-file')\n"
        "parser.add_argument('--model')\n"
        "args = parser.parse_args()\n"
        "assert args.model.endswith('ggml-tiny.en.bin')\n"
        "print('transcribed from server model id')\n",
        encoding="utf-8",
    )
    app = create_app(state)
    client = TestClient(app)
    approval_id = _approve_voice_transcription(client, audio, model, model_id="tiny.en")
    monkeypatch.setenv("JARVIS_LOCAL_STT_MODELS_DIR", str(model_root))
    monkeypatch.setenv("JARVIS_LOCAL_STT_COMMAND", f"{sys.executable} {adapter}")

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.transcribe_audio",
            {
                "session_id": "session-voice",
                "audio_file": str(audio),
                "model_id": "tiny.en",
                "approval_id": approval_id,
                "runtime_token": _runtime_token(client),
                "timeout_seconds": 5,
            },
            request_id="req_1",
        ),
    )

    data = response.json()["result"]
    payload = data["event"]["payload"]
    assert response.status_code == 200
    assert payload["text"] == "transcribed from server model id"
    assert payload["model_id"] == "tiny.en"
    assert payload["model_path"] == str(model.resolve())
    assert data["transcription"]["model_path"] == str(model.resolve())
    assert app.state.event_store.approval(approval_id)["status"] == "used"


def test_runtime_voice_transcribe_audio_rejects_unsafe_model_id_before_adapter(tmp_path, monkeypatch):
    state = tmp_path / "state"
    audio = state / "runtime" / "audio" / "session-voice" / "sample.wav"
    model_root = tmp_path / "stt-models"
    adapter_marker = tmp_path / "adapter-ran"
    adapter = tmp_path / "fake_stt.py"
    audio.parent.mkdir(parents=True)
    model_root.mkdir()
    audio.write_bytes(b"audio")
    adapter.write_text(
        f"from pathlib import Path\nPath({str(adapter_marker)!r}).write_text('ran', encoding='utf-8')\nprint('bad')\n",
        encoding="utf-8",
    )
    app = create_app(state)
    client = TestClient(app)
    monkeypatch.setenv("JARVIS_LOCAL_STT_MODELS_DIR", str(model_root))
    monkeypatch.setenv("JARVIS_LOCAL_STT_COMMAND", f"{sys.executable} {adapter}")

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.transcribe_audio",
            {
                "session_id": "session-voice",
                "audio_file": str(audio),
                "model_id": "../secret;touch-pwned",
                "approval_id": "approval_missing",
                "runtime_token": _runtime_token(client),
                "timeout_seconds": 5,
            },
            request_id="req_1",
        ),
    )

    assert response.json()["error"]["code"] == "invalid_model_path"
    assert not adapter_marker.exists()


def test_runtime_voice_transcribe_audio_rejects_direct_cache_path_without_model_id(tmp_path, monkeypatch):
    state = tmp_path / "state"
    audio = state / "runtime" / "audio" / "session-voice" / "sample.wav"
    model_root = tmp_path / "stt-models"
    model = model_root / "ggml-tiny.en.bin"
    audio.parent.mkdir(parents=True)
    model_root.mkdir()
    audio.write_bytes(b"audio")
    model.write_bytes(b"model")
    app = create_app(state)
    client = TestClient(app)
    approval_id = _approve_voice_transcription(client, audio, model)
    monkeypatch.setenv("JARVIS_LOCAL_STT_MODELS_DIR", str(model_root))

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.transcribe_audio",
            {
                "session_id": "session-voice",
                "audio_file": str(audio),
                "model_path": str(model),
                "approval_id": approval_id,
                "runtime_token": _runtime_token(client),
                "timeout_seconds": 5,
            },
            request_id="req_1",
        ),
    )

    assert response.json()["error"]["code"] == "invalid_model_path"
    assert app.state.event_store.approval(approval_id)["status"] == "approved"


def test_runtime_voice_transcribe_audio_requires_server_configured_adapter(tmp_path, monkeypatch):
    state = tmp_path / "state"
    audio = state / "runtime" / "audio" / "session-voice" / "sample.webm"
    model = state / "runtime" / "models" / "model.bin"
    audio.parent.mkdir(parents=True)
    model.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    model.write_bytes(b"model")
    app = create_app(state)
    client = TestClient(app)
    approval_id = _approve_voice_transcription(client, audio, model)
    monkeypatch.delenv("JARVIS_LOCAL_STT_COMMAND", raising=False)

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.transcribe_audio",
            {
                "session_id": "session-voice",
                "audio_file": str(audio),
                "model_path": str(model),
                "approval_id": approval_id,
                "runtime_token": _runtime_token(client),
                "timeout_seconds": 5,
            },
            request_id="req_1",
        ),
    )

    assert response.json()["error"]["code"] == "invalid_audio_chunk"
    assert "JARVIS_LOCAL_STT_COMMAND" in response.json()["error"]["message"]
    assert app.state.event_store.approval(approval_id)["status"] == "approved"


def test_runtime_voice_transcribe_audio_requires_runtime_token(tmp_path):
    state = tmp_path / "state"
    audio = state / "runtime" / "audio" / "session-voice" / "sample.webm"
    model = state / "runtime" / "models" / "model.bin"
    audio.parent.mkdir(parents=True)
    model.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    model.write_bytes(b"model")
    app = create_app(state)
    client = TestClient(app)
    approval_id = _approve_voice_transcription(client, audio, model)

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.transcribe_audio",
            {
                "session_id": "session-voice",
                "audio_file": str(audio),
                "model_path": str(model),
                "approval_id": approval_id,
                "timeout_seconds": 5,
            },
            request_id="req_1",
        ),
    )

    assert response.json()["error"]["code"] == "unauthorized"
    assert app.state.event_store.approval(approval_id)["status"] == "approved"


def test_runtime_voice_transcribe_audio_surfaces_adapter_errors(tmp_path, monkeypatch):
    state = tmp_path / "state"
    audio = state / "runtime" / "audio" / "session-voice" / "sample.webm"
    model = state / "runtime" / "models" / "model.bin"
    adapter = tmp_path / "empty_stt.py"
    audio.parent.mkdir(parents=True)
    model.parent.mkdir(parents=True)
    audio.write_bytes(b"audio")
    model.write_bytes(b"model")
    adapter.write_text("print('')\n", encoding="utf-8")
    app = create_app(state)
    client = TestClient(app)
    approval_id = _approve_voice_transcription(client, audio, model)
    monkeypatch.setenv("JARVIS_LOCAL_STT_COMMAND", f"{sys.executable} {adapter}")

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.transcribe_audio",
            {
                "session_id": "session-voice",
                "audio_file": str(audio),
                "model_path": str(model),
                "approval_id": approval_id,
                "runtime_token": _runtime_token(client),
                "timeout_seconds": 5,
            },
            request_id="req_1",
        ),
    )

    assert response.status_code == 200
    assert response.json()["error"]["code"] == "invalid_audio_chunk"
    assert "empty transcript" in response.json()["error"]["message"]


def test_runtime_voice_transcribe_audio_rejects_paths_outside_runtime_roots(tmp_path):
    state = tmp_path / "state"
    external_audio = tmp_path / "outside.webm"
    model = state / "runtime" / "models" / "model.bin"
    external_audio.write_bytes(b"audio")
    model.parent.mkdir(parents=True)
    model.write_bytes(b"model")
    app = create_app(state)
    client = TestClient(app)
    approval_id = _approve_voice_transcription(client, external_audio, model)

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.transcribe_audio",
            {
                "session_id": "session-voice",
                "audio_file": str(external_audio),
                "model_path": str(model),
                "approval_id": approval_id,
                "runtime_token": _runtime_token(client),
                "timeout_seconds": 5,
            },
            request_id="req_1",
        ),
    )

    assert response.status_code == 200
    assert response.json()["error"]["code"] == "invalid_audio_path"
    assert app.state.event_store.approval(approval_id)["status"] == "approved"


def test_runtime_voice_synthesize_audio_requires_explicit_approval(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.synthesize_audio",
            {"session_id": "session-voice", "text": "Systems online."},
            request_id="req_1",
        ),
    )

    data = response.json()
    assert response.status_code == 200
    assert data["error"]["code"] == "approval_required"
    assert data["error"]["approval_required"] is True
    assert data["error"]["details"]["required_approval_scope"] == "voice.synthesize_audio"


def test_runtime_voice_synthesize_audio_writes_audio_event(tmp_path, monkeypatch):
    state = tmp_path / "state"
    adapter = tmp_path / "fake_tts.py"
    text = "Systems are online."
    adapter.write_text(
        "import argparse, pathlib, sys\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--output-file')\n"
        "args = parser.parse_args()\n"
        "pathlib.Path(args.output_file).write_bytes(('audio:' + sys.stdin.read()).encode())\n",
        encoding="utf-8",
    )
    app = create_app(state)
    client = TestClient(app)
    approval_id = _approve_voice_synthesis(client, text)
    monkeypatch.setenv("JARVIS_LOCAL_TTS_COMMAND", f"{sys.executable} {adapter}")

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.synthesize_audio",
            {
                "session_id": "session-voice",
                "text": text,
                "tts_command": "python3 /tmp/malicious_client_supplied_tts.py",
                "approval_id": approval_id,
                "runtime_token": _runtime_token(client),
                "timeout_seconds": 5,
            },
            request_id="req_1",
        ),
    )

    data = response.json()["result"]
    payload = data["event"]["payload"]
    audio_path = Path(data["synthesis"]["audio_file"])
    assert response.status_code == 200
    assert data["characters"] == len(text)
    assert data["audio_processed"] is True
    assert data["external_services"] is False
    assert data["execution_authority"] is False
    assert data["routed_as_command"] is False
    assert audio_path.is_file()
    assert audio_path.read_bytes() == b"audio:Systems are online."
    assert str(audio_path).startswith(str((state / "runtime" / "audio").resolve()))
    assert payload["text_sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert payload["provider"] == "local-tts-adapter"
    assert payload["audio_processed"] is True
    assert payload["external_services"] is False
    assert payload["execution_authority"] is False
    assert app.state.event_store.approval(approval_id)["status"] == "used"


def test_runtime_voice_synthesize_audio_requires_server_configured_adapter(tmp_path, monkeypatch):
    text = "Systems are online."
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    approval_id = _approve_voice_synthesis(client, text)
    monkeypatch.delenv("JARVIS_LOCAL_TTS_COMMAND", raising=False)

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.synthesize_audio",
            {
                "session_id": "session-voice",
                "text": text,
                "approval_id": approval_id,
                "runtime_token": _runtime_token(client),
                "timeout_seconds": 5,
            },
            request_id="req_1",
        ),
    )

    assert response.json()["error"]["code"] == "invalid_audio_chunk"
    assert "JARVIS_LOCAL_TTS_COMMAND" in response.json()["error"]["message"]
    assert app.state.event_store.approval(approval_id)["status"] == "approved"


def test_runtime_voice_synthesize_audio_requires_runtime_token(tmp_path, monkeypatch):
    adapter = tmp_path / "fake_tts.py"
    text = "Systems are online."
    adapter.write_text("pass\n", encoding="utf-8")
    app = create_app(tmp_path / "state")
    client = TestClient(app)
    approval_id = _approve_voice_synthesis(client, text)
    monkeypatch.setenv("JARVIS_LOCAL_TTS_COMMAND", f"{sys.executable} {adapter}")

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.synthesize_audio",
            {
                "session_id": "session-voice",
                "text": text,
                "approval_id": approval_id,
                "timeout_seconds": 5,
            },
            request_id="req_1",
        ),
    )

    assert response.json()["error"]["code"] == "unauthorized"
    assert app.state.event_store.approval(approval_id)["status"] == "approved"


def test_runtime_voice_synthesize_audio_rejects_blank_text(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.synthesize_audio",
            {"session_id": "session-voice", "text": " "},
            request_id="req_1",
        ),
    )

    assert response.json()["error"]["code"] == "invalid_tts_text"


def test_runtime_internal_errors_return_structured_error(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    def fail_append_event(**_kwargs):
        raise RuntimeError("database unavailable")

    app.state.event_store.append_event = fail_append_event

    response = client.post(
        "/rpc",
        json=make_request("session.create", {"session_id": "session-1"}, request_id="req_1"),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "response"
    assert data["id"] == "req_1"
    assert data["error"]["code"] == "internal_error"
    assert data["error"]["details"]["exception"] == "RuntimeError"


def test_runtime_websocket_accepts_json_rpc_requests(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(make_request("runtime.health", request_id="req_1"))
        response = websocket.receive_json()

    assert response["type"] == "response"
    assert response["result"]["status"] == "ok"


def test_runtime_websocket_rejects_cross_origin_browser_clients(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws", headers={"origin": "https://malicious.example"}):
            pass


def test_runtime_websocket_streams_pty_output(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(
            make_request(
                "pty.create",
                {"command": "pwd", "profile": "dev-loop"},
                request_id="req_1",
            )
        )
        frames = [websocket.receive_json(), websocket.receive_json()]

    app.state.pty_supervisor.close_all()
    frame_types = {frame["type"] for frame in frames}
    stream_frames = [frame for frame in frames if frame["type"] == "stream"]

    assert "response" in frame_types
    assert "stream" in frame_types
    assert "/" in "".join(frame["chunk"] for frame in stream_frames)


def test_runtime_websocket_pushes_semantic_events(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(
            make_request(
                "approval.request",
                {
                    "session_id": "session-1",
                    "summary": "Run targeted tests",
                    "operation": "uv run pytest tests/test_runtime_app.py",
                    "risk": "medium",
                },
                request_id="req_1",
            )
        )
        frames = [websocket.receive_json(), websocket.receive_json()]

    frame_types = {frame["type"] for frame in frames}
    event_frames = [frame for frame in frames if frame["type"] == "event"]
    response_frames = [frame for frame in frames if frame["type"] == "response"]

    assert frame_types == {"response", "event"}
    assert response_frames[0]["result"]["approval"]["status"] == "pending"
    assert event_frames[0]["event_type"] == "approval.requested"
    assert event_frames[0]["session_id"] == "session-1"
    assert event_frames[0]["payload"]["event"]["event_type"] == "approval.requested"


def test_runtime_websocket_returns_structured_errors(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    def fail_append_event(**_kwargs):
        raise RuntimeError("database unavailable")

    app.state.event_store.append_event = fail_append_event

    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(make_request("session.create", {"session_id": "session-1"}, request_id="req_1"))
        response = websocket.receive_json()

    assert response["type"] == "response"
    assert response["id"] == "req_1"
    assert response["error"]["code"] == "internal_error"


def test_runtime_rejects_non_request_frames(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post("/rpc", json={"type": "event", "event_type": "x", "session_id": "s"})

    assert response.status_code == 200
    assert response.json()["error"]["code"] == "unsupported_frame"

import time

from fastapi.testclient import TestClient

from jarvis_codex.protocol import make_request
from jarvis_codex.runtime_app import create_app


def test_runtime_health_does_not_initialize_state(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["writes_state"] is False
    assert not (tmp_path / "state").exists()


def test_runtime_initialize_rpc_reports_capabilities(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post("/rpc", json=make_request("initialize", request_id="req_1"))

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "response"
    assert data["result"]["runtime"] == "jarvis"
    assert "session.create" in data["result"]["capabilities"]
    assert "approval.request" in data["result"]["capabilities"]
    assert "event.subscribe" in data["result"]["capabilities"]


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


def test_runtime_planned_methods_are_explicitly_not_implemented(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post("/rpc", json=make_request("pty.restart", request_id="req_1"))

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
            {"command": "python3 -c \"print('runtime pty')\"", "profile": "dev-loop"},
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
        while time.time() < deadline and "runtime pty" not in text:
            text += "".join(chunk.chunk for chunk in app.state.pty_supervisor.drain_output(channel_id))
            time.sleep(0.02)
    finally:
        app.state.pty_supervisor.close_all()

    assert data["type"] == "response"
    assert data["result"]["policy"]["status"] == "allow"
    assert "runtime pty" in text


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
    respond_response = client.post(
        "/rpc",
        json=make_request(
            "approval.respond",
            {"approval_id": approval["id"], "status": "approved", "reason": "targeted"},
            request_id="req_3",
        ),
    )
    subscribe_response = client.post(
        "/rpc",
        json=make_request(
            "event.subscribe",
            {"session_id": "session-1", "since_sequence": 0, "limit": 10},
            request_id="req_4",
        ),
    )

    assert approval["status"] == "pending"
    assert list_response.json()["result"]["approvals"][0]["id"] == approval["id"]
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

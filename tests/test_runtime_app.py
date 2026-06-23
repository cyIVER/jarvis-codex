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

    response = client.post("/rpc", json=make_request("pty.create", request_id="req_1"))

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "response"
    assert data["error"]["code"] == "not_implemented"
    assert "planned but not implemented" in data["error"]["message"]


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

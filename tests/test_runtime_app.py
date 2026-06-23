import time
import base64
import sys
from pathlib import Path

from fastapi.testclient import TestClient

import jarvis_codex.runtime_app as runtime_app
from jarvis_codex.codeburn import CodeburnStatus
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
    assert "session.get" in data["result"]["capabilities"]
    assert "session.list" in data["result"]["capabilities"]
    assert "telemetry.codeburn_status" in data["result"]["capabilities"]
    assert "approval.request" in data["result"]["capabilities"]
    assert "event.subscribe" in data["result"]["capabilities"]
    assert "voice.submit" in data["result"]["capabilities"]


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
            {"approval_id": approval["id"], "status": "approved", "reason": "operator approved"},
            request_id="req_2",
        ),
    )
    create_response = client.post(
        "/rpc",
        json=make_request(
            "pty.create",
            {"command": command, "profile": "observe", "approval_id": approval["id"]},
            request_id="req_3",
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
            {"approval_id": approval["id"], "status": "approved", "reason": "operator approved"},
            request_id="req_2",
        ),
    )

    mismatch = client.post(
        "/rpc",
        json=make_request(
            "pty.create",
            {"command": "python3 -c \"print('different')\"", "profile": "observe", "approval_id": approval["id"]},
            request_id="req_3",
        ),
    )
    blocked = client.post(
        "/rpc",
        json=make_request(
            "pty.create",
            {"command": "git reset --hard HEAD", "profile": "dev-loop", "approval_id": approval["id"]},
            request_id="req_4",
        ),
    )

    assert mismatch.json()["error"]["code"] == "approval_required"
    assert blocked.json()["error"]["code"] == "policy_blocked"


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


def test_runtime_voice_transcribe_audio_writes_transcript_event(tmp_path):
    state = tmp_path / "state"
    audio = tmp_path / "sample.webm"
    model = tmp_path / "model.bin"
    adapter = tmp_path / "fake_stt.py"
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

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.transcribe_audio",
            {
                "session_id": "session-voice",
                "audio_file": str(audio),
                "model_path": str(model),
                "stt_command": f"{sys.executable} {adapter}",
                "allow_audio_processing": True,
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


def test_runtime_voice_transcribe_audio_surfaces_adapter_errors(tmp_path):
    audio = tmp_path / "sample.webm"
    model = tmp_path / "model.bin"
    adapter = tmp_path / "empty_stt.py"
    audio.write_bytes(b"audio")
    model.write_bytes(b"model")
    adapter.write_text("print('')\n", encoding="utf-8")
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    response = client.post(
        "/rpc",
        json=make_request(
            "voice.transcribe_audio",
            {
                "session_id": "session-voice",
                "audio_file": str(audio),
                "model_path": str(model),
                "stt_command": f"{sys.executable} {adapter}",
                "allow_audio_processing": True,
                "timeout_seconds": 5,
            },
            request_id="req_1",
        ),
    )

    assert response.status_code == 200
    assert response.json()["error"]["code"] == "invalid_audio_chunk"
    assert "empty transcript" in response.json()["error"]["message"]


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


def test_runtime_websocket_streams_pty_output(tmp_path):
    app = create_app(tmp_path / "state")
    client = TestClient(app)

    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(
            make_request(
                "pty.create",
                {"command": "python3 -c \"print('streamed pty')\"", "profile": "dev-loop"},
                request_id="req_1",
            )
        )
        frames = [websocket.receive_json(), websocket.receive_json()]

    app.state.pty_supervisor.close_all()
    frame_types = {frame["type"] for frame in frames}
    stream_frames = [frame for frame in frames if frame["type"] == "stream"]

    assert "response" in frame_types
    assert "stream" in frame_types
    assert "streamed pty" in "".join(frame["chunk"] for frame in stream_frames)


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

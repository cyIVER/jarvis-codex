import json

import pytest

from jarvis_codex.protocol import (
    ProtocolError,
    encode_frame,
    make_error_response,
    make_event,
    make_request,
    make_response,
    make_stream,
    parse_frame,
)


def test_request_frame_round_trips():
    frame = make_request("session.create", {"title": "Jarvis"}, request_id="req_1")

    encoded = encode_frame(frame)
    parsed = parse_frame(encoded)

    assert parsed.frame_type == "request"
    assert json.loads(encoded)["method"] == "session.create"


def test_response_frame_requires_result_or_error():
    frame = make_response("req_1", {"ok": True})

    assert parse_frame(frame).payload["result"] == {"ok": True}
    with pytest.raises(ProtocolError, match="result or error"):
        parse_frame({"type": "response", "id": "req_1"})


def test_error_response_contains_policy_flags():
    frame = make_error_response(
        "req_1",
        code="policy_blocked",
        message="approval required",
        policy_blocked=True,
        approval_required=True,
        details={"risk": "git-push"},
    )

    parsed = parse_frame(frame)

    assert parsed.payload["error"]["policy_blocked"] is True
    assert parsed.payload["error"]["approval_required"] is True


def test_event_frame_requires_session_id():
    assert make_event("approval.requested", "session-1", {"summary": "Push"}).get("session_id") == "session-1"
    with pytest.raises(ProtocolError, match="session id"):
        make_event("approval.requested", "")


def test_stream_frame_keeps_pty_chunks_separate_from_events():
    frame = make_stream("pty-1", "pty.stdout", "hello", sequence=3, session_id="session-1")
    parsed = parse_frame(frame)

    assert parsed.frame_type == "stream"
    assert parsed.payload["stream_type"] == "pty.stdout"
    assert "event_type" not in parsed.payload


def test_rejects_invalid_json_and_unknown_types():
    with pytest.raises(ProtocolError, match="invalid JSON"):
        parse_frame("{")
    with pytest.raises(ProtocolError, match="frame type"):
        parse_frame({"type": "command", "command": "git push"})


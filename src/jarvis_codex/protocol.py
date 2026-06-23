from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Literal


FrameType = Literal["request", "response", "event", "stream"]


class ProtocolError(ValueError):
    def __init__(self, message: str, *, code: str = "invalid_frame") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ProtocolFrame:
    frame_type: FrameType
    payload: dict[str, Any]


def make_request(method: str, params: dict[str, Any] | None = None, request_id: str | None = None) -> dict[str, Any]:
    if not method.strip():
        raise ProtocolError("request method is required", code="missing_method")
    return {
        "type": "request",
        "id": request_id or _new_id("req"),
        "method": method,
        "params": params or {},
    }


def make_response(request_id: str, result: dict[str, Any] | None = None) -> dict[str, Any]:
    if not request_id.strip():
        raise ProtocolError("response request id is required", code="missing_id")
    return {
        "type": "response",
        "id": request_id,
        "result": result or {},
    }


def make_error_response(
    request_id: str | None,
    *,
    code: str,
    message: str,
    retryable: bool = False,
    policy_blocked: bool = False,
    approval_required: bool = False,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "type": "response",
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "policy_blocked": policy_blocked,
            "approval_required": approval_required,
            "details": details or {},
        },
    }


def make_event(event_type: str, session_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if not event_type.strip():
        raise ProtocolError("event type is required", code="missing_event_type")
    if not session_id.strip():
        raise ProtocolError("event session id is required", code="missing_session_id")
    return {
        "type": "event",
        "event_type": event_type,
        "session_id": session_id,
        "payload": payload or {},
    }


def make_stream(
    channel_id: str,
    stream_type: str,
    chunk: str,
    *,
    sequence: int,
    session_id: str | None = None,
) -> dict[str, Any]:
    if not channel_id.strip():
        raise ProtocolError("stream channel id is required", code="missing_channel_id")
    if not stream_type.strip():
        raise ProtocolError("stream type is required", code="missing_stream_type")
    if sequence < 0:
        raise ProtocolError("stream sequence must be non-negative", code="invalid_sequence")
    frame: dict[str, Any] = {
        "type": "stream",
        "channel_id": channel_id,
        "stream_type": stream_type,
        "chunk": chunk,
        "sequence": sequence,
    }
    if session_id is not None:
        frame["session_id"] = session_id
    return frame


def parse_frame(raw: str | bytes | dict[str, Any]) -> ProtocolFrame:
    data = _load_frame(raw)
    frame_type = data.get("type")
    if frame_type not in {"request", "response", "event", "stream"}:
        raise ProtocolError("frame type must be request, response, event, or stream", code="invalid_type")
    _validate_frame(data, frame_type)
    return ProtocolFrame(frame_type=frame_type, payload=data)


def encode_frame(frame: dict[str, Any]) -> str:
    parse_frame(frame)
    return json.dumps(frame, sort_keys=True, separators=(",", ":"))


def _load_frame(raw: str | bytes | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"invalid JSON frame: {exc.msg}", code="invalid_json") from exc
    if not isinstance(value, dict):
        raise ProtocolError("frame must be a JSON object", code="invalid_shape")
    return value


def _validate_frame(data: dict[str, Any], frame_type: str) -> None:
    if frame_type == "request":
        if not isinstance(data.get("id"), str) or not data["id"].strip():
            raise ProtocolError("request id is required", code="missing_id")
        if not isinstance(data.get("method"), str) or not data["method"].strip():
            raise ProtocolError("request method is required", code="missing_method")
        if "params" in data and not isinstance(data["params"], dict):
            raise ProtocolError("request params must be an object", code="invalid_params")
        return

    if frame_type == "response":
        if "result" in data and "error" in data:
            raise ProtocolError("response cannot contain both result and error", code="invalid_response")
        if "result" not in data and "error" not in data:
            raise ProtocolError("response must contain result or error", code="invalid_response")
        if "error" in data:
            _validate_error(data["error"])
        return

    if frame_type == "event":
        if not isinstance(data.get("event_type"), str) or not data["event_type"].strip():
            raise ProtocolError("event type is required", code="missing_event_type")
        if not isinstance(data.get("session_id"), str) or not data["session_id"].strip():
            raise ProtocolError("event session id is required", code="missing_session_id")
        if "payload" in data and not isinstance(data["payload"], dict):
            raise ProtocolError("event payload must be an object", code="invalid_payload")
        return

    if frame_type == "stream":
        if not isinstance(data.get("channel_id"), str) or not data["channel_id"].strip():
            raise ProtocolError("stream channel id is required", code="missing_channel_id")
        if not isinstance(data.get("stream_type"), str) or not data["stream_type"].strip():
            raise ProtocolError("stream type is required", code="missing_stream_type")
        if not isinstance(data.get("sequence"), int) or data["sequence"] < 0:
            raise ProtocolError("stream sequence must be non-negative", code="invalid_sequence")
        if not isinstance(data.get("chunk"), str):
            raise ProtocolError("stream chunk must be text", code="invalid_chunk")


def _validate_error(error: Any) -> None:
    if not isinstance(error, dict):
        raise ProtocolError("response error must be an object", code="invalid_error")
    if not isinstance(error.get("code"), str) or not error["code"].strip():
        raise ProtocolError("response error code is required", code="missing_error_code")
    if not isinstance(error.get("message"), str) or not error["message"].strip():
        raise ProtocolError("response error message is required", code="missing_error_message")
    for key in ("retryable", "policy_blocked", "approval_required"):
        if key in error and not isinstance(error[key], bool):
            raise ProtocolError(f"response error {key} must be boolean", code="invalid_error_flag")
    if "details" in error and not isinstance(error["details"], dict):
        raise ProtocolError("response error details must be an object", code="invalid_error_details")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


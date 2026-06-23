from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .event_store import JarvisEventStore
from .policy import classify_command
from .protocol import (
    ProtocolError,
    make_error_response,
    make_response,
    parse_frame,
)

POLICY_PROFILES = {"observe", "dev-loop", "swarm", "high-risk-runtime"}
PLANNED_METHODS = {
    "approval.list",
    "approval.request",
    "approval.respond",
    "event.subscribe",
    "pty.create",
    "pty.input",
    "pty.kill",
    "pty.resize",
    "pty.restart",
}


def create_app(state_dir: Path) -> FastAPI:
    app = FastAPI(title="Jarvis Runtime", version="0.1.0")
    store = JarvisEventStore(state_dir / "runtime" / "jarvis.db")
    app.state.event_store = store

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "runtime": "jarvis",
            "writes_state": False,
        }

    @app.post("/rpc")
    def rpc(frame: dict[str, Any]) -> dict[str, Any]:
        return _handle_frame(store, frame)

    @app.websocket("/ws")
    async def websocket_rpc(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                raw = await websocket.receive_text()
                response = await asyncio.to_thread(_handle_frame, store, raw)
                await websocket.send_json(response)
        except WebSocketDisconnect:
            return

    return app


def _handle_frame(store: JarvisEventStore, raw: str | bytes | dict[str, Any]) -> dict[str, Any]:
    try:
        frame = parse_frame(raw)
    except ProtocolError as exc:
        return make_error_response(
            None,
            code=exc.code,
            message=str(exc),
            retryable=False,
            details={},
        )

    if frame.frame_type != "request":
        return make_error_response(
            frame.payload.get("id") if isinstance(frame.payload.get("id"), str) else None,
            code="unsupported_frame",
            message="runtime RPC accepts request frames only",
            retryable=False,
        )

    request_id = str(frame.payload["id"])
    method = str(frame.payload["method"])
    params = frame.payload.get("params", {})
    if not isinstance(params, dict):
        return make_error_response(request_id, code="invalid_params", message="params must be an object")

    try:
        return _dispatch_request(store, request_id, method, params)
    except Exception as exc:
        return make_error_response(
            request_id,
            code="internal_error",
            message="runtime request failed",
            retryable=False,
            details={"exception": type(exc).__name__},
        )


def _dispatch_request(
    store: JarvisEventStore,
    request_id: str,
    method: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    if method == "initialize":
        return make_response(
            request_id,
            {
                "runtime": "jarvis",
                "protocol": "acp-style-json-rpc",
                "capabilities": [
                    "initialize",
                    "session.create",
                    "runtime.health",
                    "command.classify",
                ],
                "writes_reports": False,
            },
        )

    if method == "runtime.health":
        return make_response(
            request_id,
            {
                "status": "ok",
                "current_sequence": store.current_sequence(),
            },
        )

    if method == "session.create":
        session_id = str(params.get("session_id") or f"session_{uuid.uuid4().hex[:12]}")
        title = str(params.get("title") or "Untitled session")
        profile_id = str(params.get("profile_id") or "observe")
        if profile_id not in POLICY_PROFILES:
            return make_error_response(request_id, code="invalid_profile", message="unknown policy profile")
        event = store.append_event(
            session_id=session_id,
            actor_id=str(params.get("actor_id") or "runtime"),
            source_client=str(params.get("source_client") or "rpc"),
            event_type="session.created",
            payload={
                "title": title,
                "profile_id": profile_id,
                "model_route": params.get("model_route") or {},
                "parent_session_id": params.get("parent_session_id"),
            },
        )
        return make_response(
            request_id,
            {
                "session_id": session_id,
                "event_id": event.id,
                "sequence": event.sequence,
            },
        )

    if method == "command.classify":
        command = str(params.get("command") or "")
        profile = str(params.get("profile") or "observe")
        if profile not in POLICY_PROFILES:
            return make_error_response(request_id, code="invalid_profile", message="unknown policy profile")
        decision = classify_command(command, profile)  # type: ignore[arg-type]
        return make_response(request_id, decision.to_dict())

    if method in PLANNED_METHODS:
        return make_error_response(
            request_id,
            code="not_implemented",
            message=f"runtime method is planned but not implemented: {method}",
            retryable=False,
        )

    return make_error_response(
        request_id,
        code="unknown_method",
        message=f"unknown runtime method: {method}",
        retryable=False,
    )

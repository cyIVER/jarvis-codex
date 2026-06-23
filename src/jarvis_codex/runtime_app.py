from __future__ import annotations

import asyncio
import os
import queue
import secrets
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response

from .approval import ApprovalError, ApprovalService
from .codeburn import read_codeburn_status
from .event_store import JarvisEventStore, StoredEvent
from .event_stream import RuntimeEventBroadcaster
from .hud import HUD_CSP, HUD_HTML, HUD_ICON_SVG, HUD_JS, HUD_MANIFEST, HUD_SERVICE_WORKER
from .policy import classify_command
from .protocol import (
    ProtocolError,
    make_event,
    make_error_response,
    make_response,
    make_stream,
    parse_frame,
)
from .pty_supervisor import PtyNotFoundError, PtyPolicyError, PtySupervisor
from .voice_audio import VoiceAudioBuffer, VoiceAudioError, transcribe_with_local_adapter
from .voice_intent import propose_voice_intent

POLICY_PROFILE_DETAILS = {
    "observe": {
        "label": "Observe",
        "description": "Read-only inspection, search, status checks, and non-mutating diagnostics.",
        "execution": "read-only",
    },
    "dev-loop": {
        "label": "Dev Loop",
        "description": "Targeted development-loop commands such as direct pytest runs after policy classification.",
        "execution": "bounded-local",
    },
    "swarm": {
        "label": "Swarm",
        "description": "High-coordination planning mode for future multi-agent fanout. Execution remains approval-gated.",
        "execution": "approval-gated",
    },
    "high-risk-runtime": {
        "label": "High-risk Runtime",
        "description": "Runtime, network, service, git mutation, and destructive operations. Human approval is required.",
        "execution": "approval-required",
    },
}
POLICY_PROFILES = set(POLICY_PROFILE_DETAILS)
LOCAL_STT_COMMAND_ENV = "JARVIS_LOCAL_STT_COMMAND"
PLANNED_METHODS = {
    "loop.pause",
    "loop.resume",
    "loop.start",
    "loop.stop",
    "prompt.cancel",
    "pty.restart",
    "session.cancel",
    "swarm.plan",
    "swarm.start",
    "swarm.stop",
}


def create_app(state_dir: Path) -> FastAPI:
    app = FastAPI(title="Jarvis Runtime", version="0.1.0")
    store = JarvisEventStore(state_dir / "runtime" / "jarvis.db")
    pty_supervisor = PtySupervisor()
    event_broadcaster = RuntimeEventBroadcaster()
    approval_service = ApprovalService(store)
    voice_audio = VoiceAudioBuffer(state_dir)
    runtime_token = secrets.token_urlsafe(32)
    app.state.event_store = store
    app.state.pty_supervisor = pty_supervisor
    app.state.event_broadcaster = event_broadcaster
    app.state.approval_service = approval_service
    app.state.voice_audio = voice_audio
    app.state.runtime_token = runtime_token
    app.router.add_event_handler("shutdown", pty_supervisor.close_all)

    @app.get("/", response_class=HTMLResponse)
    def hud() -> HTMLResponse:
        return HTMLResponse(
            HUD_HTML.replace("__JARVIS_RUNTIME_TOKEN__", runtime_token),
            headers={"Content-Security-Policy": HUD_CSP},
        )

    @app.get("/assets/hud.js")
    def hud_js() -> Response:
        return Response(HUD_JS, media_type="application/javascript")

    @app.get("/manifest.webmanifest")
    def hud_manifest() -> Response:
        return Response(HUD_MANIFEST, media_type="application/manifest+json")

    @app.get("/assets/icon.svg")
    def hud_icon() -> Response:
        return Response(HUD_ICON_SVG, media_type="image/svg+xml")

    @app.get("/service-worker.js")
    def service_worker() -> Response:
        return Response(
            HUD_SERVICE_WORKER,
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/"},
        )

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "runtime": "jarvis",
            "writes_state": False,
        }

    @app.post("/rpc")
    def rpc(frame: dict[str, Any]) -> dict[str, Any]:
        return _handle_frame(
            store,
            pty_supervisor,
            event_broadcaster,
            approval_service,
            voice_audio,
            frame,
            runtime_token=runtime_token,
        )

    @app.websocket("/ws")
    async def websocket_rpc(websocket: WebSocket) -> None:
        if not _websocket_origin_allowed(
            origin=websocket.headers.get("origin"),
            host=websocket.headers.get("host"),
        ):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        send_lock = asyncio.Lock()
        stop_streaming = asyncio.Event()
        stream_task = asyncio.create_task(_send_pty_streams(websocket, pty_supervisor, send_lock, stop_streaming))
        event_task = asyncio.create_task(_send_runtime_events(websocket, event_broadcaster, send_lock, stop_streaming))
        try:
            while True:
                raw = await websocket.receive_text()
                response = await asyncio.to_thread(
                    _handle_frame,
                    store,
                    pty_supervisor,
                    event_broadcaster,
                    approval_service,
                    voice_audio,
                    raw,
                    runtime_token=runtime_token,
                )
                async with send_lock:
                    await websocket.send_json(response)
        except WebSocketDisconnect:
            return
        finally:
            stop_streaming.set()
            stream_task.cancel()
            event_task.cancel()

    return app


async def _send_pty_streams(
    websocket: WebSocket,
    pty_supervisor: PtySupervisor,
    send_lock: asyncio.Lock,
    stop_streaming: asyncio.Event,
) -> None:
    while not stop_streaming.is_set():
        chunk = await asyncio.to_thread(pty_supervisor.next_output, 0.1)
        if chunk is None:
            continue
        frame = make_stream(
            channel_id=chunk.channel_id,
            stream_type=chunk.stream_type,
            chunk=chunk.chunk,
            sequence=chunk.sequence,
        )
        async with send_lock:
            await websocket.send_json(frame)


async def _send_runtime_events(
    websocket: WebSocket,
    event_broadcaster: RuntimeEventBroadcaster,
    send_lock: asyncio.Lock,
    stop_streaming: asyncio.Event,
) -> None:
    subscriber = event_broadcaster.subscribe()
    try:
        while not stop_streaming.is_set():
            event = await asyncio.to_thread(_next_runtime_event, subscriber, 0.1)
            if event is None:
                continue
            frame = make_event(
                event.event_type,
                event.session_id,
                {"event": _stored_event_to_dict(event)},
            )
            async with send_lock:
                await websocket.send_json(frame)
    finally:
        event_broadcaster.unsubscribe(subscriber)


def _next_runtime_event(subscriber, timeout: float) -> StoredEvent | None:
    try:
        return subscriber.get(timeout=timeout)
    except queue.Empty:
        return None


def _handle_frame(
    store: JarvisEventStore,
    pty_supervisor: PtySupervisor,
    event_broadcaster: RuntimeEventBroadcaster,
    approval_service: ApprovalService,
    voice_audio: VoiceAudioBuffer,
    raw: str | bytes | dict[str, Any],
    runtime_token: str | None = None,
) -> dict[str, Any]:
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
        return _dispatch_request(
            store,
            pty_supervisor,
            event_broadcaster,
            approval_service,
            voice_audio,
            request_id,
            method,
            params,
            runtime_token,
        )
    except PtyPolicyError as exc:
        decision = exc.decision
        return make_error_response(
            request_id,
            code="policy_blocked" if decision.blocked else "approval_required",
            message=decision.reason,
            retryable=False,
            policy_blocked=decision.blocked,
            approval_required=decision.approval_required,
            details={"policy": decision.to_dict()},
        )
    except PtyNotFoundError:
        return make_error_response(
            request_id,
            code="unknown_channel",
            message="PTY channel does not exist",
            retryable=False,
        )
    except ApprovalError as exc:
        return make_error_response(
            request_id,
            code="invalid_approval",
            message=str(exc),
            retryable=False,
        )
    except VoiceAudioError as exc:
        return make_error_response(
            request_id,
            code="invalid_audio_chunk",
            message=str(exc),
            retryable=False,
        )
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
    pty_supervisor: PtySupervisor,
    event_broadcaster: RuntimeEventBroadcaster,
    approval_service: ApprovalService,
    voice_audio: VoiceAudioBuffer,
    request_id: str,
    method: str,
    params: dict[str, Any],
    runtime_token: str | None,
) -> dict[str, Any]:
    if method == "initialize":
        return make_response(
            request_id,
            {
                "runtime": "jarvis",
                "protocol": "acp-style-json-rpc",
                "capabilities": [
                    "initialize",
                    "approval.list",
                    "approval.request",
                    "approval.respond",
                    "event.subscribe",
                    "message.list",
                    "session.archive",
                    "session.create",
                    "session.fork",
                    "session.get",
                    "session.list",
                    "session.resume",
                    "telemetry.codeburn_status",
                    "runtime.health",
                    "runtime.readiness",
                    "profile.list",
                    "profile.set",
                    "prompt.send",
                    "command.classify",
                    "pty.create",
                    "pty.input",
                    "pty.resize",
                    "pty.kill",
                    "voice.provider_status",
                    "voice.audio_chunk",
                    "voice.transcribe_audio",
                    "voice.intent_propose",
                    "voice.start",
                    "voice.stop",
                    "voice.submit",
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

    if method == "runtime.readiness":
        return make_response(
            request_id,
            {
                "status": "foundation-ready",
                "production_complete": False,
                "writes_state": False,
                "checks": {
                    "policy_profiles": sorted(POLICY_PROFILES),
                    "pwa_assets": True,
                    "approval_replay_protection": True,
                    "approval_runtime_token": True,
                    "websocket_origin_validation": True,
                    "stt_runtime_path_constraints": True,
                    "voice_execution_authority": False,
                    "codeburn_shell": False,
                },
                "remaining_gaps": [
                    "electron_packaging",
                    "iphone_private_network_validation",
                    "gemini_oauth_feasibility",
                    "local_tts_adapter",
                    "swarm_command_surfaces",
                    "release_packaging",
                ],
            },
        )

    if method == "telemetry.codeburn_status":
        return make_response(request_id, {"codeburn": read_codeburn_status().to_dict()})

    if method == "profile.list":
        profiles = [
            {"id": profile_id, **POLICY_PROFILE_DETAILS[profile_id]}
            for profile_id in sorted(POLICY_PROFILE_DETAILS)
        ]
        return make_response(
            request_id,
            {
                "profiles": profiles,
                "default_profile": "observe",
                "writes_state": False,
            },
        )

    if method == "profile.set":
        session_id = str(params.get("session_id") or "")
        profile_id = str(params.get("profile_id") or "")
        if not session_id:
            return make_error_response(request_id, code="missing_session_id", message="session_id is required")
        if profile_id not in POLICY_PROFILES:
            return make_error_response(request_id, code="invalid_profile", message="unknown policy profile")
        session = store.session(session_id)
        if session is None:
            return make_error_response(request_id, code="unknown_session", message="session does not exist")
        if session.get("profile_id") == profile_id:
            return make_response(
                request_id,
                {
                    "session_id": session_id,
                    "profile_id": profile_id,
                    "already_set": True,
                    "writes_state": False,
                    "session": session,
                },
            )
        event = _append_and_publish(
            store,
            event_broadcaster,
            session_id=session_id,
            actor_id=str(params.get("actor_id") or "runtime"),
            source_client=str(params.get("source_client") or "rpc"),
            event_type="session.profile_set",
            payload={
                "profile_id": profile_id,
                "previous_profile_id": session.get("profile_id"),
                "reason": str(params.get("reason") or "profile set"),
            },
        )
        updated = store.session(session_id)
        return make_response(
            request_id,
            {
                "session_id": session_id,
                "profile_id": profile_id,
                "event_id": event.id,
                "sequence": event.sequence,
                "writes_state": True,
                "session": updated or session,
            },
        )

    if method == "session.create":
        session_id = str(params.get("session_id") or f"session_{uuid.uuid4().hex[:12]}")
        title = str(params.get("title") or "Untitled session")
        profile_id = str(params.get("profile_id") or "observe")
        if profile_id not in POLICY_PROFILES:
            return make_error_response(request_id, code="invalid_profile", message="unknown policy profile")
        event = _append_and_publish(
            store,
            event_broadcaster,
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

    if method == "session.list":
        status = params.get("status")
        if status is not None and status not in {"active", "archived"}:
            return make_error_response(request_id, code="invalid_status", message="unknown session status")
        limit = int(params.get("limit") or 50)
        return make_response(
            request_id,
            {"sessions": store.sessions(status=status if isinstance(status, str) else None, limit=limit)},
        )

    if method == "session.get":
        session_id = str(params.get("session_id") or "")
        if not session_id:
            return make_error_response(request_id, code="missing_session_id", message="session_id is required")
        session = store.session(session_id)
        if session is None:
            return make_error_response(request_id, code="unknown_session", message="session does not exist")
        return make_response(request_id, {"session": session})

    if method == "session.resume":
        session_id = str(params.get("session_id") or "")
        if not session_id:
            return make_error_response(request_id, code="missing_session_id", message="session_id is required")
        if not store.db_path.exists():
            return make_error_response(
                request_id,
                code="unknown_session",
                message="session does not exist",
                details={"writes_state": False},
            )
        session = store.session(session_id)
        if session is None:
            return make_error_response(request_id, code="unknown_session", message="session does not exist")
        limit = max(1, min(int(params.get("limit") or 25), 100))
        messages = [_stored_event_to_dict(event) for event in store.iter_events(session_id=session_id)][-limit:]
        return make_response(
            request_id,
            {
                "resumed_session_id": session_id,
                "session": session,
                "messages": messages,
                "current_sequence": store.current_sequence(),
                "writes_state": False,
                "execution_authority": False,
            },
        )

    if method == "session.archive":
        session_id = str(params.get("session_id") or "")
        if not session_id:
            return make_error_response(request_id, code="missing_session_id", message="session_id is required")
        session = store.session(session_id)
        if session is None:
            return make_error_response(request_id, code="unknown_session", message="session does not exist")
        if session.get("status") == "archived":
            return make_response(
                request_id,
                {
                    "archived_session_id": session_id,
                    "already_archived": True,
                    "writes_state": False,
                    "session": session,
                },
            )
        event = _append_and_publish(
            store,
            event_broadcaster,
            session_id=session_id,
            actor_id=str(params.get("actor_id") or "runtime"),
            source_client=str(params.get("source_client") or "rpc"),
            event_type="session.archived",
            payload={"reason": str(params.get("reason") or "session archived")},
        )
        archived = store.session(session_id)
        return make_response(
            request_id,
            {
                "archived_session_id": session_id,
                "event_id": event.id,
                "sequence": event.sequence,
                "writes_state": True,
                "session": archived or session,
            },
        )

    if method == "session.fork":
        parent_session_id = str(params.get("session_id") or "")
        if not parent_session_id:
            return make_error_response(request_id, code="missing_session_id", message="session_id is required")
        parent = store.session(parent_session_id)
        if parent is None:
            return make_error_response(request_id, code="unknown_session", message="session does not exist")
        child_session_id = str(params.get("child_session_id") or f"session_{uuid.uuid4().hex[:12]}")
        profile_id = str(params.get("profile_id") or parent.get("profile_id") or "observe")
        if profile_id not in POLICY_PROFILES:
            return make_error_response(request_id, code="invalid_profile", message="unknown policy profile")
        event = _append_and_publish(
            store,
            event_broadcaster,
            session_id=child_session_id,
            actor_id=str(params.get("actor_id") or "runtime"),
            source_client=str(params.get("source_client") or "rpc"),
            event_type="session.created",
            payload={
                "title": str(params.get("title") or f"Fork of {parent.get('title') or parent_session_id}"),
                "profile_id": profile_id,
                "model_route": params.get("model_route") or parent.get("model_route") or {},
                "parent_session_id": parent_session_id,
            },
        )
        return make_response(
            request_id,
            {
                "child_session_id": child_session_id,
                "parent_session_id": parent_session_id,
                "event_id": event.id,
                "sequence": event.sequence,
                "writes_state": True,
                "execution_authority": False,
                "session": store.session(child_session_id),
            },
        )

    if method == "prompt.send":
        session_id = str(params.get("session_id") or "")
        text = str(params.get("text") or "").strip()
        if not session_id:
            return make_error_response(request_id, code="missing_session_id", message="session_id is required")
        if not text:
            return make_error_response(request_id, code="missing_prompt", message="prompt text is required")
        if store.session(session_id) is None:
            return make_error_response(request_id, code="unknown_session", message="session does not exist")
        event = _append_and_publish(
            store,
            event_broadcaster,
            session_id=session_id,
            actor_id=str(params.get("actor_id") or "user"),
            source_client=str(params.get("source_client") or "rpc"),
            event_type="prompt.sent",
            payload={
                "text": text,
                "target": str(params.get("target") or "planning"),
                "execution_authority": False,
            },
        )
        return make_response(
            request_id,
            {
                "prompt_event_id": event.id,
                "session_id": session_id,
                "sequence": event.sequence,
                "writes_state": True,
                "execution_authority": False,
            },
        )

    if method == "message.list":
        session_id = params.get("session_id")
        if session_id is not None and not isinstance(session_id, str):
            return make_error_response(request_id, code="invalid_session_id", message="session_id must be a string")
        since_sequence = max(0, int(params.get("since_sequence") or 0))
        limit = max(1, min(int(params.get("limit") or 50), 200))
        if not store.db_path.exists():
            return make_response(
                request_id,
                {
                    "messages": [],
                    "current_sequence": 0,
                    "writes_state": False,
                },
            )
        events = [
            _stored_event_to_dict(event)
            for event in store.iter_events(session_id=session_id)
            if event.sequence > since_sequence
        ][:limit]
        return make_response(
            request_id,
            {
                "messages": events,
                "current_sequence": store.current_sequence(),
                "writes_state": False,
            },
        )

    if method == "command.classify":
        command = str(params.get("command") or "")
        profile = str(params.get("profile") or "observe")
        if profile not in POLICY_PROFILES:
            return make_error_response(request_id, code="invalid_profile", message="unknown policy profile")
        decision = classify_command(command, profile)  # type: ignore[arg-type]
        return make_response(request_id, decision.to_dict())

    if method == "pty.create":
        command = str(params.get("command") or "")
        profile = str(params.get("profile") or "observe")
        if profile not in POLICY_PROFILES:
            return make_error_response(request_id, code="invalid_profile", message="unknown policy profile")
        approval_id = str(params.get("approval_id") or "")
        try:
            result = pty_supervisor.spawn(command, profile=profile)  # type: ignore[arg-type]
        except PtyPolicyError as exc:
            if not _approval_allows_command(store, approval_id, command):
                raise
            if not _valid_runtime_token(params, runtime_token):
                return make_error_response(
                    request_id,
                    code="unauthorized",
                    message="approved PTY launches require the HUD runtime token",
                    retryable=False,
                )
            consumed = approval_service.consume(
                approval_id=approval_id,
                actor_id=str(params.get("actor_id") or "runtime"),
                source_client=str(params.get("source_client") or "rpc"),
                reason="pty.create launched approved command",
            )
            event_broadcaster.publish(consumed.event)
            result = pty_supervisor.spawn(command, profile=profile, approval_granted=True)  # type: ignore[arg-type]
        data = result.to_dict()
        if result.approval_granted:
            data["approval_id"] = approval_id
        return make_response(request_id, data)

    if method == "pty.input":
        channel_id = str(params.get("channel_id") or "")
        text = str(params.get("text") or "")
        pty_supervisor.write(channel_id, text)
        return make_response(request_id, {"channel_id": channel_id, "accepted": True})

    if method == "pty.resize":
        channel_id = str(params.get("channel_id") or "")
        rows = int(params.get("rows") or 0)
        cols = int(params.get("cols") or 0)
        pty_supervisor.resize(channel_id, rows=rows, cols=cols)
        return make_response(request_id, {"channel_id": channel_id, "rows": rows, "cols": cols})

    if method == "pty.kill":
        channel_id = str(params.get("channel_id") or "")
        returncode = pty_supervisor.kill(channel_id)
        return make_response(request_id, {"channel_id": channel_id, "returncode": returncode})

    if method == "approval.request":
        result = approval_service.request(
            session_id=str(params.get("session_id") or "runtime"),
            summary=str(params.get("summary") or ""),
            operation=str(params.get("operation") or ""),
            risk=str(params.get("risk") or "medium"),
            scope=params.get("scope") if isinstance(params.get("scope"), dict) else {},
            actor_id=str(params.get("actor_id") or "runtime"),
            source_client=str(params.get("source_client") or "rpc"),
        )
        event_broadcaster.publish(result.event)
        return make_response(
            request_id,
            {
                "approval": result.approval,
                "event": _stored_event_to_dict(result.event),
            },
        )

    if method == "approval.list":
        status = params.get("status")
        if status is not None and status not in {"pending", "approved", "rejected", "used"}:
            return make_error_response(request_id, code="invalid_status", message="unknown approval status")
        return make_response(request_id, {"approvals": approval_service.list(status=status)})  # type: ignore[arg-type]

    if method == "approval.respond":
        if not _valid_runtime_token(params, runtime_token):
            return make_error_response(
                request_id,
                code="unauthorized",
                message="approval responses require the HUD runtime token",
                retryable=False,
            )
        status = str(params.get("status") or "")
        if status not in {"approved", "rejected"}:
            return make_error_response(request_id, code="invalid_status", message="status must be approved or rejected")
        result = approval_service.respond(
            approval_id=str(params.get("approval_id") or ""),
            status=status,  # type: ignore[arg-type]
            actor_id=str(params.get("actor_id") or "runtime"),
            source_client=str(params.get("source_client") or "rpc"),
            reason=str(params.get("reason") or ""),
        )
        event_broadcaster.publish(result.event)
        return make_response(
            request_id,
            {
                "approval": result.approval,
                "event": _stored_event_to_dict(result.event),
            },
        )

    if method == "event.subscribe":
        session_id = params.get("session_id")
        since_sequence = int(params.get("since_sequence") or 0)
        limit = max(0, min(int(params.get("limit") or 100), 500))
        events = [
            _stored_event_to_dict(event)
            for event in store.iter_events(session_id=session_id if isinstance(session_id, str) else None)
            if event.sequence > since_sequence
        ][:limit]
        return make_response(
            request_id,
            {
                "subscribed": True,
                "replay": events,
                "current_sequence": store.current_sequence(),
            },
        )

    if method == "voice.provider_status":
        return make_response(
            request_id,
            {
                "providers": {
                    "browser_web_speech": {
                        "status": "client-managed",
                        "privacy": "browser-dependent",
                        "note": "Used only after microphone click and browser permission.",
                    },
                    "local_audio_file": {
                        "status": "available",
                        "privacy": "local",
                        "note": "CLI/local adapter path remains approval-gated for audio processing.",
                    },
                    "server_audio_stream": {
                        "status": "available",
                        "privacy": "local",
                        "note": "MediaRecorder chunks can be stored locally; transcription remains separate and approval-gated.",
                    },
                    "local_stt_adapter": {
                        "status": "approval-gated",
                        "privacy": "local",
                        "note": "Saved audio may be transcribed only with a matching approval id and server-configured local STT command.",
                    },
                    "gemini_realtime": {
                        "status": "not_configured",
                        "privacy": "cloud",
                        "note": "Requires explicit OAuth feasibility check and visible cloud indicator.",
                    },
                },
                "execution_authority": False,
            },
        )

    if method == "voice.start":
        event = _append_and_publish(
            store,
            event_broadcaster,
            session_id=str(params.get("session_id") or "hud"),
            actor_id=str(params.get("actor_id") or "user"),
            source_client=str(params.get("source_client") or "hud"),
            event_type="voice.start_requested",
            payload={
                "provider": str(params.get("provider") or "browser-web-speech"),
                "execution_authority": False,
            },
        )
        return make_response(request_id, {"event": _stored_event_to_dict(event), "execution_authority": False})

    if method == "voice.stop":
        event = _append_and_publish(
            store,
            event_broadcaster,
            session_id=str(params.get("session_id") or "hud"),
            actor_id=str(params.get("actor_id") or "user"),
            source_client=str(params.get("source_client") or "hud"),
            event_type="voice.stopped",
            payload={
                "provider": str(params.get("provider") or "browser-web-speech"),
                "execution_authority": False,
            },
        )
        return make_response(request_id, {"event": _stored_event_to_dict(event), "execution_authority": False})

    if method == "voice.submit":
        transcript = str(params.get("transcript") or "").strip()
        if not transcript:
            return make_error_response(request_id, code="invalid_transcript", message="voice transcript is required")
        event = _append_and_publish(
            store,
            event_broadcaster,
            session_id=str(params.get("session_id") or "hud"),
            actor_id=str(params.get("actor_id") or "user"),
            source_client=str(params.get("source_client") or "hud"),
            event_type="voice.transcript_final",
            payload={
                "text": transcript,
                "provider": str(params.get("provider") or "browser-web-speech"),
                "execution_authority": False,
                "routed_as_command": False,
            },
        )
        return make_response(
            request_id,
            {
                "event": _stored_event_to_dict(event),
                "characters": len(transcript),
                "execution_authority": False,
                "routed_as_command": False,
            },
        )

    if method == "voice.intent_propose":
        transcript = str(params.get("transcript") or "").strip()
        if not transcript:
            return make_error_response(request_id, code="invalid_transcript", message="voice transcript is required")
        profile = str(params.get("profile") or "observe")
        if profile not in POLICY_PROFILES:
            return make_error_response(request_id, code="invalid_profile", message="unknown policy profile")
        proposal = propose_voice_intent(transcript, profile=profile)  # type: ignore[arg-type]
        event = _append_and_publish(
            store,
            event_broadcaster,
            session_id=str(params.get("session_id") or "hud"),
            actor_id=str(params.get("actor_id") or "user"),
            source_client=str(params.get("source_client") or "hud"),
            event_type="voice.intent_classified",
            payload=proposal.to_dict(),
        )
        return make_response(
            request_id,
            {
                "proposal": proposal.to_dict(),
                "event": _stored_event_to_dict(event),
                "execution_authority": False,
                "routed_as_command": False,
            },
        )

    if method == "voice.audio_chunk":
        session_id = str(params.get("session_id") or "hud")
        result = voice_audio.append_chunk(
            session_id=session_id,
            utterance_id=str(params.get("utterance_id")) if params.get("utterance_id") else None,
            sequence=int(params.get("sequence") or 0),
            mime_type=str(params.get("mime_type") or "audio/webm"),
            chunk_b64=str(params.get("chunk_b64") or ""),
            final=bool(params.get("final") or False),
        )
        event = _append_and_publish(
            store,
            event_broadcaster,
            session_id=session_id,
            actor_id=str(params.get("actor_id") or "user"),
            source_client=str(params.get("source_client") or "hud"),
            event_type="voice.audio_chunk" if not result.final else "voice.audio_utterance_received",
            payload={
                "utterance_id": result.utterance_id,
                "sequence": result.sequence,
                "mime_type": result.mime_type,
                "path": str(result.path),
                "bytes_written": result.bytes_written,
                "final": result.final,
                "execution_authority": False,
                "audio_processed": False,
            },
        )
        return make_response(
            request_id,
            {
                "audio": result.to_dict(),
                "event": _stored_event_to_dict(event),
            },
        )

    if method == "voice.transcribe_audio":
        audio_file = Path(str(params.get("audio_file") or ""))
        model_path = Path(str(params.get("model_path") or ""))
        approval_id = str(params.get("approval_id") or "")
        if not _approval_allows_audio_transcription(store, approval_id, audio_file, model_path):
            return make_error_response(
                request_id,
                code="approval_required",
                message="local audio transcription requires a matching approved audio processing approval",
                retryable=False,
                approval_required=True,
                details={"required_approval_scope": "voice.transcribe_audio"},
            )
        if not _valid_runtime_token(params, runtime_token):
            return make_error_response(
                request_id,
                code="unauthorized",
                message="approved audio transcription requires the HUD runtime token",
                retryable=False,
            )
        if not _path_within(voice_audio.root, audio_file):
            return make_error_response(
                request_id,
                code="invalid_audio_path",
                message="local audio transcription is restricted to runtime audio files",
                retryable=False,
            )
        if not _path_within(voice_audio.model_root, model_path):
            return make_error_response(
                request_id,
                code="invalid_model_path",
                message="local audio transcription models must be under the runtime model directory",
                retryable=False,
            )
        stt_command = _local_stt_command()
        consumed = approval_service.consume(
            approval_id=approval_id,
            actor_id=str(params.get("actor_id") or "runtime"),
            source_client=str(params.get("source_client") or "rpc"),
            reason="voice.transcribe_audio processed approved audio",
        )
        event_broadcaster.publish(consumed.event)
        transcript = transcribe_with_local_adapter(
            audio_file=audio_file,
            model_path=model_path,
            stt_command=stt_command,
            timeout_seconds=int(params.get("timeout_seconds") or 120),
        )
        session_id = str(params.get("session_id") or "hud")
        event = _append_and_publish(
            store,
            event_broadcaster,
            session_id=session_id,
            actor_id=str(params.get("actor_id") or "user"),
            source_client=str(params.get("source_client") or "rpc"),
            event_type="voice.transcript_final",
            payload={
                "text": transcript.transcript,
                "provider": str(params.get("provider") or "local-stt-adapter"),
                "audio_file": str(transcript.audio_file),
                "model_path": str(transcript.model_path),
                "execution_authority": False,
                "routed_as_command": False,
                "audio_processed": True,
                "external_services": False,
            },
        )
        return make_response(
            request_id,
            {
                "event": _stored_event_to_dict(event),
                "characters": len(transcript.transcript),
                "transcription": transcript.to_dict(),
                "execution_authority": False,
                "routed_as_command": False,
                "audio_processed": True,
                "external_services": False,
            },
        )

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


def _stored_event_to_dict(event) -> dict[str, Any]:
    return {
        "sequence": event.sequence,
        "id": event.id,
        "session_id": event.session_id,
        "actor_id": event.actor_id,
        "source_client": event.source_client,
        "event_type": event.event_type,
        "payload": event.payload,
        "correlation_id": event.correlation_id,
        "parent_event_id": event.parent_event_id,
        "created_at": event.created_at,
    }


def _append_and_publish(
    store: JarvisEventStore,
    event_broadcaster: RuntimeEventBroadcaster,
    **kwargs: Any,
) -> StoredEvent:
    event = store.append_event(**kwargs)
    event_broadcaster.publish(event)
    return event


def _approval_allows_command(store: JarvisEventStore, approval_id: str, command: str) -> bool:
    if not approval_id.strip():
        return False
    approval = store.approval(approval_id)
    if approval is None or approval.get("status") != "approved":
        return False
    expected = _normalize_command(command)
    operation = _normalize_command(str(approval.get("operation") or ""))
    scope = approval.get("scope") if isinstance(approval.get("scope"), dict) else {}
    scoped_command = _normalize_command(str(scope.get("command") or ""))
    return expected in {operation, scoped_command}


def _approval_allows_audio_transcription(
    store: JarvisEventStore,
    approval_id: str,
    audio_file: Path,
    model_path: Path,
) -> bool:
    if not approval_id.strip():
        return False
    approval = store.approval(approval_id)
    if approval is None or approval.get("status") != "approved":
        return False
    if str(approval.get("operation") or "") != "voice.transcribe_audio":
        return False
    scope = approval.get("scope") if isinstance(approval.get("scope"), dict) else {}
    return (
        scope.get("source") == "voice.transcribe_audio"
        and _normalize_path(str(scope.get("audio_file") or "")) == _normalize_path(str(audio_file))
        and _normalize_path(str(scope.get("model_path") or "")) == _normalize_path(str(model_path))
    )


def _normalize_command(command: str) -> str:
    return " ".join(command.strip().split())


def _normalize_path(path: str) -> str:
    if not path.strip():
        return ""
    return str(Path(path).expanduser().resolve())


def _path_within(root: Path, path: Path) -> bool:
    try:
        path.expanduser().resolve().relative_to(root.expanduser().resolve())
    except (OSError, ValueError):
        return False
    return True


def _local_stt_command() -> str:
    command = os.environ.get(LOCAL_STT_COMMAND_ENV, "").strip()
    if not command:
        raise VoiceAudioError(f"{LOCAL_STT_COMMAND_ENV} is not configured")
    return command


def _valid_runtime_token(params: dict[str, Any], runtime_token: str | None) -> bool:
    candidate = params.get("runtime_token")
    return isinstance(candidate, str) and bool(runtime_token) and secrets.compare_digest(candidate, runtime_token)


def _websocket_origin_allowed(origin: str | None, host: str | None) -> bool:
    if not origin:
        return True
    if not host:
        return False
    parsed = urlparse(origin)
    if parsed.scheme not in {"http", "https"}:
        return False
    return parsed.netloc == host

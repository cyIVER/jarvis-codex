from __future__ import annotations

import asyncio
import queue
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response

from .approval import ApprovalError, ApprovalService
from .event_store import JarvisEventStore, StoredEvent
from .event_stream import RuntimeEventBroadcaster
from .hud import HUD_CSP, HUD_HTML, HUD_JS
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

POLICY_PROFILES = {"observe", "dev-loop", "swarm", "high-risk-runtime"}
PLANNED_METHODS = {
    "pty.restart",
}


def create_app(state_dir: Path) -> FastAPI:
    app = FastAPI(title="Jarvis Runtime", version="0.1.0")
    store = JarvisEventStore(state_dir / "runtime" / "jarvis.db")
    pty_supervisor = PtySupervisor()
    event_broadcaster = RuntimeEventBroadcaster()
    approval_service = ApprovalService(store)
    voice_audio = VoiceAudioBuffer(state_dir)
    app.state.event_store = store
    app.state.pty_supervisor = pty_supervisor
    app.state.event_broadcaster = event_broadcaster
    app.state.approval_service = approval_service
    app.state.voice_audio = voice_audio
    app.router.add_event_handler("shutdown", pty_supervisor.close_all)

    @app.get("/", response_class=HTMLResponse)
    def hud() -> HTMLResponse:
        return HTMLResponse(HUD_HTML, headers={"Content-Security-Policy": HUD_CSP})

    @app.get("/assets/hud.js")
    def hud_js() -> Response:
        return Response(HUD_JS, media_type="application/javascript")

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "runtime": "jarvis",
            "writes_state": False,
        }

    @app.post("/rpc")
    def rpc(frame: dict[str, Any]) -> dict[str, Any]:
        return _handle_frame(store, pty_supervisor, event_broadcaster, approval_service, voice_audio, frame)

    @app.websocket("/ws")
    async def websocket_rpc(websocket: WebSocket) -> None:
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
                    "session.create",
                    "session.get",
                    "session.list",
                    "runtime.health",
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
        if status is not None and status not in {"pending", "approved", "rejected"}:
            return make_error_response(request_id, code="invalid_status", message="unknown approval status")
        return make_response(request_id, {"approvals": approval_service.list(status=status)})  # type: ignore[arg-type]

    if method == "approval.respond":
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
                        "note": "Saved audio may be transcribed only when allow_audio_processing is true.",
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
        if not bool(params.get("allow_audio_processing") or False):
            return make_error_response(
                request_id,
                code="approval_required",
                message="local audio transcription requires explicit audio processing approval",
                retryable=False,
                approval_required=True,
                details={"required_param": "allow_audio_processing"},
            )
        transcript = transcribe_with_local_adapter(
            audio_file=Path(str(params.get("audio_file") or "")),
            model_path=Path(str(params.get("model_path") or "")),
            stt_command=str(params.get("stt_command") or ""),
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


def _normalize_command(command: str) -> str:
    return " ".join(command.strip().split())

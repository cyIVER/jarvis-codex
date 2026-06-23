from __future__ import annotations

import base64
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, TextIO


ApprovalCallback = Callable[[dict[str, object]], bool]


class CodexAppServerError(RuntimeError):
    pass


@dataclass(frozen=True)
class CodexAppServerConfig:
    cwd: Path
    session: str | None = None
    approval_policy: str = "on-request"
    sandbox: str = "workspace-write"
    model: str | None = None
    effort: str | None = None
    start_daemon: bool = True


@dataclass(frozen=True)
class CodexEvent:
    event_type: str
    thread_id: str | None = None
    turn_id: str | None = None
    text: str | None = None
    payload: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {"event_type": self.event_type}
        if self.thread_id is not None:
            data["thread_id"] = self.thread_id
        if self.turn_id is not None:
            data["turn_id"] = self.turn_id
        if self.text is not None:
            data["text"] = self.text
        if self.payload is not None:
            data["payload"] = self.payload
        return data


class CodexJsonRpcTransport:
    def start(self) -> None:
        raise NotImplementedError

    def request(self, method: str, params: dict[str, object]) -> dict[str, object]:
        raise NotImplementedError

    def respond(self, request_id: object, result: dict[str, object]) -> None:
        raise NotImplementedError

    def read_message(self) -> dict[str, object] | None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class CodexProxyTransport(CodexJsonRpcTransport):
    """Raw JSON-RPC transport through Codex app-server stdio."""

    def __init__(self, *, start_daemon: bool = True) -> None:
        self.start_daemon = start_daemon
        self._process: subprocess.Popen[str] | None = None
        self._next_id = 1

    def start(self) -> None:
        if self.start_daemon:
            try:
                subprocess.run(["codex", "app-server", "daemon", "start"], check=True, capture_output=True, text=True)
                self._start_process(["codex", "app-server", "proxy"])
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        self._start_process(["codex", "app-server", "--listen", "stdio://"])

    def _start_process(self, command: list[str]) -> None:
        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def request(self, method: str, params: dict[str, object]) -> dict[str, object]:
        request_id = self._next_id
        self._next_id += 1
        self._write({"id": request_id, "method": method, "params": params})
        if method == "initialize":
            self._write({"method": "initialized", "params": {}})
        while True:
            message = self.read_message()
            if message is None:
                raise CodexAppServerError("codex app-server closed before responding")
            if message.get("id") == request_id:
                if "error" in message:
                    raise CodexAppServerError(json.dumps(message["error"], sort_keys=True))
                result = message.get("result")
                return result if isinstance(result, dict) else {"result": result}

    def respond(self, request_id: object, result: dict[str, object]) -> None:
        self._write({"id": request_id, "result": result})

    def read_message(self) -> dict[str, object] | None:
        if self._process is None or self._process.stdout is None:
            raise CodexAppServerError("codex app-server transport is not started")
        line = self._process.stdout.readline()
        if line == "":
            return None
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CodexAppServerError(f"invalid app-server JSON-RPC frame: {line.strip()}") from exc
        return message if isinstance(message, dict) else {"payload": message}

    def close(self) -> None:
        if self._process is None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=3)

    def _write(self, message: dict[str, object]) -> None:
        if self._process is None or self._process.stdin is None:
            raise CodexAppServerError("codex app-server transport is not started")
        self._process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self._process.stdin.flush()


def run_codex_turn(
    transcript: str,
    *,
    config: CodexAppServerConfig,
    approval_callback: ApprovalCallback | None = None,
    transport: CodexJsonRpcTransport | None = None,
) -> Iterable[CodexEvent]:
    text = transcript.strip()
    if not text:
        raise CodexAppServerError("transcript is required")
    owned_transport = transport is None
    rpc = transport or CodexProxyTransport(start_daemon=config.start_daemon)
    rpc.start()
    try:
        initialize = rpc.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "jarvis-codex-cli",
                    "title": "Jarvis Codex CLI",
                    "version": "0.1.0",
                },
                "capabilities": {},
            },
        )
        yield CodexEvent("app_server_initialized", payload=initialize)

        thread_id = config.session
        if thread_id is None:
            thread_params: dict[str, object] = {
                "cwd": str(config.cwd.resolve()),
                "approvalPolicy": config.approval_policy,
                "sandbox": config.sandbox,
                "threadSource": "other",
                "sessionStartSource": "startup",
            }
            if config.model:
                thread_params["model"] = config.model
            thread_response = rpc.request("thread/start", thread_params)
            thread = thread_response.get("thread")
            if not isinstance(thread, dict) or not isinstance(thread.get("id"), str):
                raise CodexAppServerError("thread/start response did not include thread.id")
            thread_id = thread["id"]
            yield CodexEvent("thread_started", thread_id=thread_id, payload=thread_response)
        else:
            yield CodexEvent("thread_resumed", thread_id=thread_id, payload={"thread_id": thread_id})

        turn_params: dict[str, object] = {
            "threadId": thread_id,
            "cwd": str(config.cwd.resolve()),
            "approvalPolicy": config.approval_policy,
            "input": [{"type": "text", "text": text}],
        }
        if config.model:
            turn_params["model"] = config.model
        if config.effort:
            turn_params["effort"] = config.effort
        turn_response = rpc.request("turn/start", turn_params)
        turn = turn_response.get("turn")
        turn_id = turn.get("id") if isinstance(turn, dict) else None
        yield CodexEvent("turn_started", thread_id=thread_id, turn_id=turn_id if isinstance(turn_id, str) else None, payload=turn_response)

        yield from _drain_turn_events(rpc, thread_id=thread_id, approval_callback=approval_callback)
    finally:
        if owned_transport:
            rpc.close()


def _drain_turn_events(
    rpc: CodexJsonRpcTransport,
    *,
    thread_id: str,
    approval_callback: ApprovalCallback | None,
) -> Iterable[CodexEvent]:
    while True:
        message = rpc.read_message()
        if message is None:
            yield CodexEvent("app_server_closed", thread_id=thread_id)
            return
        if "id" in message and "method" in message:
            approval_event, response = _approval_response_for(message, approval_callback)
            if approval_event is not None:
                yield approval_event
                rpc.respond(message["id"], response)
                yield CodexEvent(
                    "approval_responded",
                    thread_id=_str_or_none(approval_event.payload, "threadId") or thread_id,
                    turn_id=_str_or_none(approval_event.payload, "turnId"),
                    payload={"request_id": message["id"], "response": response},
                )
            continue
        method = message.get("method")
        params = message.get("params") if isinstance(message.get("params"), dict) else {}
        if method == "item/agentMessage/delta":
            yield CodexEvent(
                "agent_message_delta",
                thread_id=_str_or_none(params, "threadId") or thread_id,
                turn_id=_str_or_none(params, "turnId"),
                text=str(params.get("delta", "")),
                payload=params,
            )
        elif method == "item/plan/delta":
            yield CodexEvent(
                "plan_delta",
                thread_id=_str_or_none(params, "threadId") or thread_id,
                turn_id=_str_or_none(params, "turnId"),
                text=str(params.get("delta", "")),
                payload=params,
            )
        elif method in {"command/exec/outputDelta", "item/commandExecution/outputDelta"}:
            yield CodexEvent("terminal_output", thread_id=thread_id, text=_decode_output(params), payload=params)
        elif method == "turn/completed":
            turn = params.get("turn")
            completed_turn_id = turn.get("id") if isinstance(turn, dict) else None
            yield CodexEvent(
                "turn_completed",
                thread_id=_str_or_none(params, "threadId") or thread_id,
                turn_id=completed_turn_id if isinstance(completed_turn_id, str) else None,
                payload=params,
            )
            return
        elif isinstance(method, str):
            yield CodexEvent("app_server_event", thread_id=thread_id, payload={"method": method, "params": params})


def _approval_response_for(
    message: dict[str, object],
    approval_callback: ApprovalCallback | None,
) -> tuple[CodexEvent | None, dict[str, object]]:
    method = str(message.get("method", ""))
    params = message.get("params") if isinstance(message.get("params"), dict) else {}
    if method not in {
        "item/commandExecution/requestApproval",
        "item/fileChange/requestApproval",
        "item/permissions/requestApproval",
        "execCommandApproval",
        "applyPatchApproval",
    }:
        return None, {}
    callback_payload = {"method": method, **params}
    approved = approval_callback(callback_payload) if approval_callback is not None else False
    event = CodexEvent(
        "approval_requested",
        thread_id=_str_or_none(params, "threadId") or _str_or_none(params, "conversationId"),
        turn_id=_str_or_none(params, "turnId"),
        payload=callback_payload,
    )
    if method == "item/commandExecution/requestApproval":
        return event, {"decision": "accept" if approved else "decline"}
    if method == "item/fileChange/requestApproval":
        return event, {"decision": "accept" if approved else "decline"}
    if method == "item/permissions/requestApproval":
        permissions = params.get("permissions") if approved and isinstance(params.get("permissions"), dict) else {}
        return event, {"permissions": permissions, "scope": "turn", "strictAutoReview": True}
    if method == "execCommandApproval":
        return event, {"decision": "approved" if approved else "denied"}
    return event, {"decision": "approved" if approved else "denied"}


def _str_or_none(data: object, key: str) -> str | None:
    if not isinstance(data, dict):
        return None
    value = data.get(key)
    return value if isinstance(value, str) else None


def _decode_output(params: dict[str, object]) -> str:
    value = params.get("deltaBase64")
    if isinstance(value, str):
        try:
            return base64.b64decode(value).decode("utf-8", errors="replace")
        except ValueError:
            return ""
    value = params.get("delta")
    return value if isinstance(value, str) else ""


def inline_approval_prompt(params: dict[str, object], *, stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> bool:
    method = params.get("method", "approval")
    command = params.get("command")
    cwd = params.get("cwd")
    reason = params.get("reason")
    print("\nApproval requested by Codex app-server", file=stdout)
    print(f"Method: {method}", file=stdout)
    if command:
        print(f"Command: {command}", file=stdout)
    if cwd:
        print(f"CWD: {cwd}", file=stdout)
    if reason:
        print(f"Reason: {reason}", file=stdout)
    print("Approve? Type 'yes' to approve: ", end="", file=stdout)
    stdout.flush()
    return stdin.readline().strip().lower() == "yes"

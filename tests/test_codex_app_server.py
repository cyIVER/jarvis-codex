from __future__ import annotations

from pathlib import Path

from jarvis_codex.codex_app_server import CodexAppServerConfig, run_codex_turn


class FakeTransport:
    def __init__(self, messages):
        self.messages = list(messages)
        self.requests = []
        self.responses = []
        self.started = False

    def start(self):
        self.started = True

    def request(self, method, params):
        self.requests.append((method, params))
        if method == "initialize":
            return {"userAgent": "fake"}
        if method == "thread/start":
            return {"thread": {"id": "thread-1", "status": "idle"}}
        if method == "turn/start":
            return {"turn": {"id": "turn-1", "status": "inProgress", "items": []}}
        raise AssertionError(method)

    def respond(self, request_id, result):
        self.responses.append((request_id, result))

    def read_message(self):
        if not self.messages:
            return None
        return self.messages.pop(0)

    def close(self):
        pass


def test_run_codex_turn_starts_thread_and_streams_agent_delta():
    transport = FakeTransport(
        [
            {
                "method": "item/agentMessage/delta",
                "params": {"threadId": "thread-1", "turnId": "turn-1", "itemId": "item-1", "delta": "Planning..."},
            },
            {
                "method": "turn/completed",
                "params": {"threadId": "thread-1", "turn": {"id": "turn-1", "status": "completed", "items": []}},
            },
        ]
    )

    events = list(run_codex_turn("plan this feature", config=CodexAppServerConfig(cwd=Path(".")), transport=transport))

    assert transport.started is True
    assert transport.requests[1] == (
        "thread/start",
        {
            "cwd": str(Path(".").resolve()),
            "approvalPolicy": "on-request",
            "sandbox": "workspace-write",
            "threadSource": "other",
            "sessionStartSource": "startup",
        },
    )
    assert transport.requests[2][0] == "turn/start"
    assert transport.requests[2][1]["input"] == [{"type": "text", "text": "plan this feature"}]
    assert [event.event_type for event in events] == [
        "app_server_initialized",
        "thread_started",
        "turn_started",
        "agent_message_delta",
        "turn_completed",
    ]
    assert events[3].text == "Planning..."


def test_run_codex_turn_declines_command_approval_by_default():
    transport = FakeTransport(
        [
            {
                "id": "approval-1",
                "method": "item/commandExecution/requestApproval",
                "params": {
                    "threadId": "thread-1",
                    "turnId": "turn-1",
                    "itemId": "item-1",
                    "startedAtMs": 1,
                    "command": "git status",
                },
            },
            {
                "method": "turn/completed",
                "params": {"threadId": "thread-1", "turn": {"id": "turn-1", "status": "completed", "items": []}},
            },
        ]
    )

    events = list(run_codex_turn("run git status", config=CodexAppServerConfig(cwd=Path(".")), transport=transport))

    assert [event.event_type for event in events][-3:] == ["approval_requested", "approval_responded", "turn_completed"]
    assert transport.responses == [("approval-1", {"decision": "decline"})]


def test_run_codex_turn_reuses_explicit_session():
    transport = FakeTransport(
        [
            {
                "method": "turn/completed",
                "params": {"threadId": "thread-existing", "turn": {"id": "turn-1", "status": "completed", "items": []}},
            }
        ]
    )

    events = list(
        run_codex_turn(
            "continue",
            config=CodexAppServerConfig(cwd=Path("."), session="thread-existing"),
            transport=transport,
        )
    )

    methods = [method for method, _ in transport.requests]
    assert methods == ["initialize", "turn/start"]
    assert events[1].event_type == "thread_resumed"
    assert events[1].thread_id == "thread-existing"

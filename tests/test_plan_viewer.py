import json
from io import BytesIO

from jarvis_codex.state import JarvisState
from jarvis_codex.plan_viewer import (
    INDEX_HTML,
    PlanViewerHandler,
    approve_next_steps_queue,
    build_current_state,
    document_sources,
    harness_route_path,
    load_harness_route,
    load_approved_queue,
    load_next_steps_selection,
    next_steps_queue_path,
    next_steps_state_path,
    save_harness_route,
    save_next_steps_selection,
)


def test_next_steps_selection_round_trip(tmp_path):
    state = tmp_path / "state"
    saved = save_next_steps_selection(
        state,
        ["push-gate-2", "bad id", "../escape", "hardware-runtime-gate"],
        "# Proceed Brief",
    )

    assert saved["selected"] == ["push-gate-2", "hardware-runtime-gate"]
    assert saved["brief"] == "# Proceed Brief"
    assert isinstance(saved["updated_at"], int)
    assert load_next_steps_selection(state) == saved


def test_next_steps_selection_defaults_when_missing_or_invalid(tmp_path):
    state = tmp_path / "state"

    assert load_next_steps_selection(state) == {"selected": [], "brief": "", "updated_at": None}

    path = next_steps_state_path(state)
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")

    assert load_next_steps_selection(state) == {"selected": [], "brief": "", "updated_at": None}


def test_next_steps_selection_file_shape(tmp_path):
    state = tmp_path / "state"
    save_next_steps_selection(state, ["voice-notification-hardening"], "brief")

    data = json.loads(next_steps_state_path(state).read_text(encoding="utf-8"))
    assert data["selected"] == ["voice-notification-hardening"]
    assert data["brief"] == "brief"


class FakeApproveQueueRequest:
    path = "/api/approve-queue"

    def __init__(self, state_dir):
        self.state_dir = state_dir
        self.sent = []

    def _send(self, status, body, content_type):
        self.sent.append((status, body, content_type))


class FakeJsonPostRequest:
    def __init__(self, state_dir, path, payload):
        body = json.dumps(payload).encode("utf-8")
        self.state_dir = state_dir
        self.path = path
        self.rfile = BytesIO(body)
        self.headers = {"Content-Length": str(len(body))}
        self.sent = []

    def _send(self, status, body, content_type):
        self.sent.append((status, body, content_type))


class FakeGetRequest:
    def __init__(self, repo_dir, plan_dir, state_dir, path):
        self.repo_dir = repo_dir
        self.plan_dir = plan_dir
        self.state_dir = state_dir
        self.path = path
        self.sent = []

    def _send(self, status, body, content_type):
        self.sent.append((status, body, content_type))


def test_next_steps_post_writes_selection_file(tmp_path):
    state = tmp_path / "state"
    request = FakeJsonPostRequest(
        state,
        "/api/next-steps",
        {"selected": ["hardware-runtime-gate", "../escape"], "brief": "# Brief"},
    )

    PlanViewerHandler.do_POST(request)

    assert request.sent[0][0] == 200
    data = json.loads(request.sent[0][1].decode("utf-8"))
    assert data["selected"] == ["hardware-runtime-gate"]
    assert data["brief"] == "# Brief"
    assert load_next_steps_selection(state) == data


def test_next_steps_post_rejects_bad_payload(tmp_path):
    request = FakeJsonPostRequest(tmp_path / "state", "/api/next-steps", {"selected": "hardware-runtime-gate"})

    PlanViewerHandler.do_POST(request)

    assert request.sent == [(400, b"selected must be a list", "text/plain")]
    assert not next_steps_state_path(tmp_path / "state").exists()


def test_approve_queue_post_writes_queue_file(tmp_path):
    state = tmp_path / "state"
    save_next_steps_selection(state, ["hardware-runtime-gate"], "# Brief")

    request = FakeApproveQueueRequest(state)
    PlanViewerHandler.do_POST(request)

    assert request.sent[0][0] == 200
    queue = json.loads(next_steps_queue_path(state).read_text(encoding="utf-8"))
    assert queue["selected"] == ["hardware-runtime-gate"]
    assert queue["brief"] == "# Brief"
    assert queue["source"] == "plan_viewer"
    assert queue["purpose"] == "planning"
    assert queue["execution_authority"] is False


def test_approve_queue_post_returns_400_without_selection(tmp_path):
    request = FakeApproveQueueRequest(tmp_path / "state")

    PlanViewerHandler.do_POST(request)

    assert request.sent == [(400, b"nothing selected", "text/plain")]
    assert not next_steps_queue_path(tmp_path / "state").exists()


def test_approve_queue_helper_and_current_state_read_consistently(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    state = tmp_path / "state"
    save_next_steps_selection(state, ["hardware-runtime-gate"], "# Brief")

    monkeypatch.setattr("jarvis_codex.plan_viewer.run_git", lambda args, cwd: "")
    approved = approve_next_steps_queue(state)
    current = build_current_state(repo, state)

    assert load_approved_queue(state) == approved
    assert current["continuity"]["queued_state"] == approved
    assert current["continuity"]["queued_state"]["execution_authority"] is False


def test_invalid_queue_json_does_not_break_current_state(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    state = tmp_path / "state"
    queue_path = next_steps_queue_path(state)
    queue_path.parent.mkdir(parents=True)
    queue_path.write_text("{not json", encoding="utf-8")

    monkeypatch.setattr("jarvis_codex.plan_viewer.run_git", lambda args, cwd: "")
    current = build_current_state(repo, state)

    assert load_approved_queue(state) is None
    assert current["continuity"]["queued_state"] is None


def test_harness_route_round_trip_is_planning_only(tmp_path):
    state = tmp_path / "state"

    saved = save_harness_route(
        state,
        "antigravity",
        "Review the harness route boundaries",
        "Use read-only analysis.",
        microphone_required=True,
    )
    loaded = load_harness_route(state)

    assert loaded == saved
    assert loaded["target"] == "antigravity"
    assert loaded["source"] == "plan_viewer"
    assert loaded["purpose"] == "harness-routing"
    assert loaded["execution_authority"] is False
    assert loaded["agent_invoked"] is False
    assert loaded["runtime_started"] is False
    assert loaded["microphone_required"] is True


def test_harness_route_rejects_invalid_target_and_missing_objective(tmp_path):
    state = tmp_path / "state"

    try:
        save_harness_route(state, "shell", "Do work")
    except ValueError as exc:
        assert "target" in str(exc)
    else:
        raise AssertionError("invalid harness target should fail")

    try:
        save_harness_route(state, "codex", " ")
    except ValueError as exc:
        assert "objective" in str(exc)
    else:
        raise AssertionError("missing harness objective should fail")

    assert not harness_route_path(state).exists()


def test_invalid_harness_route_json_does_not_break_current_state(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    state = tmp_path / "state"
    route_path = harness_route_path(state)
    route_path.parent.mkdir(parents=True)
    route_path.write_text("{not json", encoding="utf-8")

    monkeypatch.setattr("jarvis_codex.plan_viewer.run_git", lambda args, cwd: "")
    current = build_current_state(repo, state)

    assert load_harness_route(state) is None
    assert current["continuity"]["harness_route"] is None


def test_get_files_and_file_endpoint_use_allowlisted_sources(tmp_path):
    repo = tmp_path / "repo"
    plan = repo / "plans" / "jarvis-codex-swarm"
    docs = repo / "docs"
    plan.mkdir(parents=True)
    docs.mkdir()
    (plan / "plan.mdx").write_text("# Plan", encoding="utf-8")
    (docs / "JARVIS_WHITE_PAPER.md").write_text("# White Paper", encoding="utf-8")

    files_request = FakeGetRequest(repo, plan, tmp_path / "state", "/api/files")
    PlanViewerHandler.do_GET(files_request)
    files = json.loads(files_request.sent[0][1].decode("utf-8"))

    file_request = FakeGetRequest(repo, plan, tmp_path / "state", "/api/file/plan.mdx")
    PlanViewerHandler.do_GET(file_request)

    assert files_request.sent[0][0] == 200
    assert [item["id"] for item in files] == ["plan.mdx", "jarvis-white-paper"]
    assert file_request.sent == [(200, b"# Plan", "text/markdown")]


def test_get_file_endpoint_rejects_traversal_and_unknown_files(tmp_path):
    repo = tmp_path / "repo"
    plan = repo / "plans" / "jarvis-codex-swarm"
    plan.mkdir(parents=True)
    (plan / "plan.mdx").write_text("# Plan", encoding="utf-8")

    traversal = FakeGetRequest(repo, plan, tmp_path / "state", "/api/file/..%2Fsecret.md")
    unknown = FakeGetRequest(repo, plan, tmp_path / "state", "/api/file/missing.mdx")

    PlanViewerHandler.do_GET(traversal)
    PlanViewerHandler.do_GET(unknown)

    assert traversal.sent == [(400, b"invalid file name", "text/plain")]
    assert unknown.sent == [(404, b"not found", "text/plain")]


def test_get_current_state_endpoint_returns_queue_and_harness_state(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    state = tmp_path / "state"
    save_next_steps_selection(state, ["hardware-runtime-gate"], "# Brief")
    approve_next_steps_queue(state)
    save_harness_route(state, "codex", "Review route", "Context")
    monkeypatch.setattr("jarvis_codex.plan_viewer.run_git", lambda args, cwd: "")

    request = FakeGetRequest(repo, repo / "plans", state, "/api/current-state")
    PlanViewerHandler.do_GET(request)
    data = json.loads(request.sent[0][1].decode("utf-8"))

    assert request.sent[0][0] == 200
    assert data["continuity"]["queued_state"]["execution_authority"] is False
    assert data["continuity"]["harness_route"]["target"] == "codex"
    assert data["continuity"]["harness_route"]["execution_authority"] is False


def test_harness_route_post_writes_route_file(tmp_path):
    state = tmp_path / "state"
    request = FakeJsonPostRequest(
        state,
        "/api/harness-route",
        {
            "target": "codex",
            "objective": "Implement the next approved slice",
            "context": "Bounded by tests.",
            "microphone_required": True,
        },
    )

    PlanViewerHandler.do_POST(request)

    assert request.sent[0][0] == 200
    route = json.loads(harness_route_path(state).read_text(encoding="utf-8"))
    assert route["target"] == "codex"
    assert route["objective"] == "Implement the next approved slice"
    assert route["context"] == "Bounded by tests."
    assert route["source"] == "plan_viewer"
    assert route["execution_authority"] is False
    assert route["agent_invoked"] is False
    assert route["runtime_started"] is False
    assert route["microphone_required"] is True


def test_harness_route_post_returns_400_for_invalid_route(tmp_path):
    state = tmp_path / "state"
    request = FakeJsonPostRequest(
        state,
        "/api/harness-route",
        {"target": "antigravity", "objective": ""},
    )

    PlanViewerHandler.do_POST(request)

    assert request.sent[0][0] == 400
    assert not harness_route_path(state).exists()


def test_recent_handoffs_reads_temp_state_and_handles_absent_directory(tmp_path):
    state = JarvisState(tmp_path / "state")
    assert state.recent_handoffs() == []

    state.handoffs.mkdir(parents=True)
    (state.handoffs / "handoff-2.md").write_text("second", encoding="utf-8")
    (state.handoffs / "handoff-1.md").write_text("first", encoding="utf-8")

    assert state.recent_handoffs(limit=1) == [{"id": "handoff-2.md", "text": "second"}]


def test_displayed_commands_are_not_execution_paths():
    assert "git push origin main" in INDEX_HTML
    assert "Display-only check or proposal" in INDEX_HTML
    assert "does not authorize command execution" in INDEX_HTML
    assert "Enable Microphone" in INDEX_HTML
    assert "navigator.mediaDevices.getUserMedia" in INDEX_HTML
    assert "stream.getTracks()" in INDEX_HTML
    assert "no upload" in INDEX_HTML
    assert "no transcription" in INDEX_HTML
    assert "no state write" in INDEX_HTML
    assert "Claude Code Feature Parity Map" in INDEX_HTML
    assert "Antigravity" in INDEX_HTML
    assert "Codex" in INDEX_HTML
    assert "/api/harness-route" in INDEX_HTML
    assert "eval(" not in INDEX_HTML
    assert "exec(" not in INDEX_HTML
    assert "subprocess" not in INDEX_HTML


def test_build_current_state_uses_repo_and_docs(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    docs = repo / "docs"
    docs.mkdir()
    for name in (
        "VOICE_NOTIFICATIONS.md",
        "RUNTIME_GATES.md",
        "REMOTION_REVIEW.md",
        "WORKTRUNK_LANES.md",
    ):
        (docs / name).write_text("", encoding="utf-8")
    package = repo / "src" / "jarvis_codex"
    package.mkdir(parents=True)
    (package / "notifications.py").write_text("", encoding="utf-8")
    state = tmp_path / "state"
    save_next_steps_selection(state, ["voice-notification-hardening", "hardware-runtime-gate"], "brief")

    def fake_run_git(args, cwd):
        assert cwd == repo
        if args == ["status", "--short", "--branch"]:
            return "## main...origin/main"
        if args == ["worktree", "list"]:
            return "/repo main\n/repo.lane lane/voice"
        if args == ["ls-files", "state"]:
            return "state/approvals/.gitkeep\nstate/memory/.gitkeep"
        return ""

    monkeypatch.setattr("jarvis_codex.plan_viewer.run_git", fake_run_git)
    current = build_current_state(repo, state)

    assert current["branch"] == "## main...origin/main"
    assert current["dirty"] is False
    assert current["worktree_count"] == 2
    assert current["tracked_state_files"] == 2
    assert current["selected_count"] == 2
    assert current["docs_ready"] is True
    assert current["notification_policy_module"] is True


def test_document_sources_include_plan_files_and_white_paper(tmp_path):
    repo = tmp_path / "repo"
    plan = repo / "plans" / "jarvis-codex-swarm"
    docs = repo / "docs"
    plan.mkdir(parents=True)
    docs.mkdir()
    (plan / "plan.mdx").write_text("# Plan", encoding="utf-8")
    (plan / "canvas.mdx").write_text("# Canvas", encoding="utf-8")
    (docs / "JARVIS_WHITE_PAPER.md").write_text("# White Paper", encoding="utf-8")

    sources = document_sources(repo, plan)

    assert [item["label"] for item in sources] == ["canvas.mdx", "plan.mdx", "Jarvis White Paper"]
    assert sources[-1]["id"] == "jarvis-white-paper"

import json

from jarvis_codex.plan_viewer import (
    build_current_state,
    document_sources,
    load_next_steps_selection,
    next_steps_state_path,
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

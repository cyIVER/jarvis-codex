import json
import subprocess

from jarvis_codex.lanes import list_lanes, log_lane_decision, score_lane
from jarvis_codex.state import JarvisState


def completed(stdout="", returncode=0):
    return subprocess.CompletedProcess(args=["git"], returncode=returncode, stdout=stdout, stderr="")


def test_score_lane_read_only_clean_tree(monkeypatch, tmp_path):
    calls = []

    def fake_run(args, cwd, capture_output, text, check):
        calls.append((args, cwd, check))
        return completed("")

    monkeypatch.setattr("jarvis_codex.lanes.subprocess.run", fake_run)

    result = score_lane(tmp_path, "main")

    assert result["decision"] == "ready"
    assert calls == [(["git", "status", "--short"], tmp_path, False)]


def test_score_lane_marks_untracked_for_review(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "jarvis_codex.lanes.subprocess.run",
        lambda args, cwd, capture_output, text, check: completed("?? new.txt\n"),
    )

    result = score_lane(tmp_path, "main")

    assert result["decision"] == "needs-review"
    assert "untracked" in result["evidence"]


def test_list_lanes_uses_worktree_list_and_scores_paths(monkeypatch, tmp_path):
    calls = []

    def fake_run(args, cwd, capture_output, text, check):
        calls.append((args, cwd))
        if args == ["git", "worktree", "list"]:
            return completed(f"{tmp_path} abc123 [main]\n{tmp_path / 'lane'} def456 [lane/test]\n")
        if args == ["git", "status", "--short"]:
            return completed("")
        raise AssertionError(args)

    monkeypatch.setattr("jarvis_codex.lanes.subprocess.run", fake_run)

    lanes = list_lanes(tmp_path)

    assert [lane["branch"] for lane in lanes] == ["main", "lane/test"]
    assert all(lane["decision"] == "ready" for lane in lanes)
    assert calls[0] == (["git", "worktree", "list"], tmp_path)


def test_log_lane_decision_writes_planning_record(monkeypatch, tmp_path):
    state = JarvisState(tmp_path / "state")
    repo = tmp_path / "repo"
    repo.mkdir()

    def fake_run(args, cwd, capture_output, text, check):
        if args == ["git", "rev-parse", "HEAD"]:
            return completed("abc123\n")
        if args == ["git", "status", "--short"]:
            return completed("")
        raise AssertionError(args)

    monkeypatch.setattr("jarvis_codex.lanes.subprocess.run", fake_run)

    contract = log_lane_decision(state, "hold", "lane/test", repo)

    assert contract.base_commit == "abc123"
    assert contract.mutation_performed is False
    assert contract.execution_authority is False
    log_path = state.logs / "lane_decisions.jsonl"
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["lane"] == "lane/test"
    assert rows[0]["mutation_performed"] is False
    assert rows[0]["execution_authority"] is False

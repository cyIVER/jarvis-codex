from pathlib import Path


DOC = Path("docs/WORKTRUNK_LANE_CLI_PRD.md")


def test_worktrunk_lane_cli_prd_exists_and_is_read_only_first():
    text = DOC.read_text(encoding="utf-8")

    assert "The first implementation must be read-only by default" in text
    assert "execution_authority: false" in text
    assert "mutation_performed: false" in text
    assert "Future mutation commands" in text
    assert "need a separate PRD" in text


def test_worktrunk_lane_cli_prd_denies_mutating_commands():
    text = DOC.read_text(encoding="utf-8")

    denied = [
        "wt",
        "git worktree add",
        "git worktree remove",
        "git checkout",
        "git merge",
        "git rebase",
        "git reset",
        "git clean",
        "git push",
    ]
    for command in denied:
        assert command in text

    first_slice = text.split("## First Implementation Slice Recommendation", maxsplit=1)[1]
    assert "lane list --json" in first_slice
    assert "lane score" in first_slice
    assert "Defer `lane decision`" in first_slice
    assert "mutation verbs" in first_slice

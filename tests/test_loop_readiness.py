from __future__ import annotations

from pathlib import Path

from jarvis_codex.loop_readiness import validate_loop_readiness


def write(path: Path, text: str = "ok") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_minimal_loop_repo(root: Path) -> None:
    write(root / "STATE.md", "loop_status: active\nlevel: L1\n")
    write(root / "LOOP.md")
    write(root / "loop-budget.md")
    write(root / "loop-run-log.md")
    write(root / "docs/safety.md")
    write(root / "docs/PRODUCT_READINESS.md")
    write(root / "docs/RELEASE_ARTIFACTS.md", "jarvis-codex release manifest --json\n")
    write(
        root / ".github/workflows/ci.yml",
        "permissions:\n  contents: read\nsteps:\n  - run: uv run pytest\n  - run: python3 scripts/validate-jarvis-codex-phase1.py\n",
    )


def test_loop_readiness_passes_for_minimal_governed_repo(tmp_path):
    write_minimal_loop_repo(tmp_path)

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "PASS"
    assert result["execution_authority"] is False
    assert result["writes_files"] is False
    assert result["failures"] == 0


def test_loop_readiness_fails_when_required_surfaces_are_missing(tmp_path):
    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "FAIL"
    assert result["failures"] > 0
    assert any(item["path"] == "STATE.md" for item in result["failure_details"])


def test_loop_readiness_flags_runtime_authority_markers(tmp_path):
    write_minimal_loop_repo(tmp_path)
    write(
        tmp_path / ".github/workflows/ci.yml",
        "steps:\n  - run: uv run pytest\n  - run: python3 scripts/validate-jarvis-codex-phase1.py\n  - run: git push origin main\n",
    )

    result = validate_loop_readiness(tmp_path)

    assert result["status"] == "FAIL"
    assert any("git push" in item["name"] for item in result["failure_details"])

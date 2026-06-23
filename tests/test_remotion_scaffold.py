import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REMOTION = ROOT / "video" / "remotion"


def test_remotion_package_is_local_private_and_pinned():
    package = json.loads((REMOTION / "package.json").read_text(encoding="utf-8"))

    assert package["private"] is True
    assert package["dependencies"]["remotion"] == "4.0.481"
    assert package["dependencies"]["@remotion/cli"] == "4.0.481"
    assert package["scripts"]["render"].startswith("remotion render")
    assert "out/jarvis-codex-plan.mp4" in package["scripts"]["render"]


def test_remotion_docker_build_uses_lockfile_install():
    dockerfile = (REMOTION / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY package.json package-lock.json*" in dockerfile
    assert "RUN npm ci" in dockerfile
    assert "RUN npm install" not in dockerfile


def test_remotion_outputs_are_ignored_except_placeholder():
    ignore = (REMOTION / ".gitignore").read_text(encoding="utf-8")

    assert "out/*" in ignore
    assert "!out/.gitkeep" in ignore
    assert (REMOTION / "out" / ".gitkeep").exists()


def test_remotion_readme_marks_runtime_commands_approval_gated():
    readme = (REMOTION / "README.md").read_text(encoding="utf-8")

    assert "not runtime authority" in readme
    assert "without explicit approval" in readme
    assert "write files under `out/`" in readme
    assert "not permission to mutate git" in readme
    assert "hosted publishing workflow" in readme


def test_remotion_scene_uses_current_planning_lane_language():
    scene = (REMOTION / "src" / "scenes" / "JarvisCodexPlan.tsx").read_text(encoding="utf-8")

    assert "Planning lanes" in scene
    assert "main integration" in scene
    assert "governance review" in scene
    assert "lane/codex-bridge" not in scene
    assert "voice ingress" not in scene

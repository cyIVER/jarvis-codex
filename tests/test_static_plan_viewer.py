from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def load_static_viewer_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "serve-plan-viewer.py"
    spec = importlib.util.spec_from_file_location("serve_plan_viewer", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeStaticRequest:
    def __init__(self, module, plans_dir):
        self.module = module
        self.plans_dir = plans_dir
        self.static_dir = module.STATIC_DIR
        self.responses = []
        self.headers = []
        self.body = bytearray()

    def send_response(self, status):
        self.responses.append(status)

    def send_header(self, name, value):
        self.headers.append((name, value))

    def end_headers(self):
        pass

    @property
    def wfile(self):
        return self

    def write(self, data):
        self.body.extend(data)

    def _send_json(self, payload, status=200):
        return self.module.PlanViewerHandler._send_json(self, payload, status)

    def _is_inside(self, path, parent):
        return self.module.PlanViewerHandler._is_inside(path, parent)


def test_static_viewer_path_containment(tmp_path):
    module = load_static_viewer_module()
    parent = tmp_path / "served"
    parent.mkdir()

    assert module.PlanViewerHandler._is_inside(parent / "plan.md", parent)
    assert not module.PlanViewerHandler._is_inside(tmp_path / "outside.md", parent)


def test_static_viewer_plan_index_lists_only_markdown_files(tmp_path):
    module = load_static_viewer_module()
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "plan.md").write_text("# Plan", encoding="utf-8")
    (plans / "deck.mdx").write_text("# Deck", encoding="utf-8")
    (plans / "secret.txt").write_text("no", encoding="utf-8")
    request = FakeStaticRequest(module, plans)

    module.PlanViewerHandler._send_plan_index(request)

    payload = json.loads(bytes(request.body).decode("utf-8"))
    assert request.responses == [200]
    assert [item["name"] for item in payload["plans"]] == ["deck.mdx", "plan.md"]


def test_static_viewer_serves_plan_by_basename_only(tmp_path):
    module = load_static_viewer_module()
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "plan.md").write_text("# Plan", encoding="utf-8")
    request = FakeStaticRequest(module, plans)

    module.PlanViewerHandler._send_plan_file(request, "../plan.md")

    payload = json.loads(bytes(request.body).decode("utf-8"))
    assert request.responses == [200]
    assert payload["name"] == "plan.md"
    assert payload["content"] == "# Plan"


def test_static_viewer_assets_exist():
    module = load_static_viewer_module()

    assert (module.STATIC_DIR / "index.html").is_file()
    assert (module.STATIC_DIR / "app.js").is_file()
    assert (module.STATIC_DIR / "styles.css").is_file()

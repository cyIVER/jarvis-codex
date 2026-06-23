from __future__ import annotations

import importlib.util
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright


def load_static_viewer_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "serve-plan-viewer.py"
    spec = importlib.util.spec_from_file_location("serve_plan_viewer_browser", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_static_plan_viewer_renders_plan_in_headless_browser(tmp_path):
    module = load_static_viewer_module()
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "gate-review.mdx").write_text(
        "\n".join(
            [
                "# Gate Review",
                "",
                "Use this plan for display-only checks.",
                "",
                "## Approval Boundary",
                "",
                "- Do not execute displayed commands.",
                "- Keep Worktrunk mutation approval-gated.",
                "",
                "```bash",
                "git push origin main",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    module.PlanViewerHandler.static_dir = module.STATIC_DIR.resolve()
    module.PlanViewerHandler.plans_dir = plans.resolve()
    server = ThreadingHTTPServer(("127.0.0.1", 0), module.PlanViewerHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    console_errors: list[str] = []
    page_errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            page.goto(f"http://127.0.0.1:{server.server_port}/", wait_until="networkidle")
            page.wait_for_selector("#document h1")

            assert page.title() == "Jarvis Codex Plan Viewer"
            assert page.locator("#active-title").inner_text() == "gate-review.mdx"
            assert page.locator("#document h1").inner_text() == "Gate Review"
            assert page.locator("#document h2").inner_text() == "Approval Boundary"
            assert page.locator("#heading-count").inner_text() == "2"
            assert page.locator("#code-count").inner_text() == "1"
            assert "git push origin main" in page.locator("#document pre").inner_text()
            assert page.locator("#outline-list li").count() == 2

            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert console_errors == []
    assert page_errors == []

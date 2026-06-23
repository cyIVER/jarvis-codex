from __future__ import annotations

import socket
import threading
import time
from pathlib import Path

import httpx
import uvicorn
from playwright.sync_api import expect, sync_playwright

from jarvis_codex.runtime_app import create_app


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_runtime(state_dir: Path) -> tuple[uvicorn.Server, threading.Thread, str]:
    port = _free_port()
    app = create_app(state_dir)
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            if httpx.get(f"{base_url}/health", timeout=0.5).status_code == 200:
                return server, thread, base_url
        except httpx.HTTPError:
            time.sleep(0.05)
    server.should_exit = True
    thread.join(timeout=5)
    raise RuntimeError("runtime server did not start")


def test_hud_browser_connects_and_records_command_proposal(tmp_path):
    server, thread, base_url = _start_runtime(tmp_path / "state")
    console_errors: list[str] = []
    page_errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1200})
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            page.goto(base_url, wait_until="domcontentloaded")
            expect(page.locator("#socket-status")).to_have_text("online", timeout=5000)
            expect(page.locator("#pwa-status")).to_have_text("ready", timeout=5000)
            expect(page.locator("#readiness-status")).to_have_text("foundation-ready", timeout=5000)
            expect(page.locator("#release-gate-status")).to_contain_text("open", timeout=5000)
            expect(page.locator("#release-checklist-status")).to_contain_text("blocked", timeout=5000)
            expect(page.locator("[data-page-target='overview']")).to_have_attribute("aria-selected", "true")
            expect(page.locator("[data-page-target='voice']")).to_be_visible()
            expect(page.locator("[data-page-target='session']")).to_be_visible()
            expect(page.locator("[data-page-target='swarm']")).to_be_visible()
            expect(page.locator("[data-page-target='loop']")).to_be_visible()
            expect(page.locator("[data-page-target='release']")).to_be_visible()

            page.locator("[data-page-target='release']").click()
            expect(page.locator("#release-checklist-panel")).to_contain_text("Display-only command", timeout=5000)

            page.locator("#release-evidence-gate").select_option("external_security_review")
            page.locator("#release-evidence-reviewer").fill("browser-smoke")
            page.locator("#release-evidence-summary").fill("Browser smoke evidence metadata; not review acceptance.")
            page.locator("#record-release-evidence").click()
            expect(page.locator("#release-evidence-status")).to_contain_text("Gate closed: no", timeout=5000)
            expect(page.locator("#release-gate-panel")).to_contain_text("Evidence records: 1", timeout=5000)
            expect(page.locator("#release-checklist-panel")).to_contain_text("Evidence records: 1", timeout=5000)

            page.locator("[data-page-target='session']").click()
            page.locator("#create-session").click()
            expect(page.locator("#active-session")).to_contain_text("Active session:", timeout=5000)

            page.locator("[data-page-target='loop']").click()
            page.locator("#loop-objective").fill("Continue governed overnight loop")
            page.locator("#request-loop-start-approval").click()
            expect(page.locator("#loop-lifecycle-status")).to_contain_text("loop.start approval requested", timeout=5000)
            page.locator("[data-page-target='voice']").click()
            loop_approval_id = page.locator("#approvals-list [data-approval-id]").first.get_attribute("data-approval-id")
            assert loop_approval_id
            page.locator("#approvals-list [data-approval-action='approved']").first.click()
            expect(page.locator("#console")).to_contain_text("Approval approved requested", timeout=5000)
            page.locator("[data-page-target='loop']").click()
            page.locator("#loop-lifecycle-approval-id").fill(loop_approval_id)
            page.locator("#record-loop-start").click()
            expect(page.locator("#loop-lifecycle-status")).to_contain_text("Loop lifecycle started recorded", timeout=5000)

            page.locator("#command-proposal").fill("git status --short")
            page.locator("#record-command-proposal").click()
            expect(page.locator("#command-proposal-status")).to_contain_text("No approval created", timeout=5000)
            expect(page.locator("#console")).to_contain_text("Command proposal recorded", timeout=5000)

            page.locator("[data-page-target='swarm']").click()
            page.locator("#swarm-objective").fill("Coordinate docs and runtime review lanes")
            page.locator("#record-swarm-plan").click()
            expect(page.locator("#swarm-plan-status")).to_contain_text("Plan event:", timeout=5000)
            page.locator("#request-swarm-start-approval").click()
            expect(page.locator("#swarm-plan-status")).to_contain_text("Swarm start approval requested", timeout=5000)
            page.locator("[data-page-target='voice']").click()
            approval_id = page.locator("#approvals-list [data-approval-id]").first.get_attribute("data-approval-id")
            assert approval_id
            page.locator("#approvals-list [data-approval-action='approved']").first.click()
            expect(page.locator("#console")).to_contain_text("Approval approved requested", timeout=5000)
            page.locator("[data-page-target='swarm']").click()
            page.locator("#swarm-lifecycle-approval-id").fill(approval_id)
            page.locator("#record-swarm-start").click()
            expect(page.locator("#swarm-plan-status")).to_contain_text("Swarm lifecycle started recorded", timeout=5000)

            page.locator("#swarm-launch-command").fill("pwd")
            page.locator("#request-swarm-launch-approval").click()
            expect(page.locator("#swarm-launch-status")).to_contain_text("swarm.launch approval requested", timeout=5000)
            page.locator("[data-page-target='voice']").click()
            launch_approval_id = page.locator("#approvals-list [data-approval-id]").first.get_attribute("data-approval-id")
            assert launch_approval_id
            page.locator("#approvals-list [data-approval-action='approved']").first.click()
            expect(page.locator("#console")).to_contain_text("Approval approved requested", timeout=5000)
            page.locator("[data-page-target='swarm']").click()
            page.locator("#swarm-launch-approval-id").fill(launch_approval_id)
            page.locator("#launch-approved-swarm").click()
            expect(page.locator("#swarm-launch-status")).to_contain_text("Swarm launched", timeout=5000)

            page.locator("[data-page-target='session']").click()
            page.locator("#refresh-session-history").click()
            expect(page.locator("#session-history")).to_contain_text("command.proposed", timeout=5000)
            expect(page.locator("#session-history")).to_contain_text("loop.started", timeout=5000)
            expect(page.locator("#session-history")).to_contain_text("swarm.started", timeout=5000)
            expect(page.locator("#session-history")).to_contain_text("swarm.launched", timeout=5000)
            expect(page.locator("#session-history")).to_contain_text('"approval_created": false', timeout=5000)
            expect(page.locator("#session-history")).to_contain_text('"execution_authority": false', timeout=5000)

            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=5)

    assert console_errors == []
    assert page_errors == []

from fastapi.testclient import TestClient

from jarvis_codex.runtime_app import create_app


def test_hud_root_serves_jarvis_shell(tmp_path):
    client = TestClient(create_app(tmp_path / "state"))

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert "Jarvis Harness" in response.text
    assert 'id="mic-toggle"' in response.text
    assert 'id="proposal-preview"' in response.text
    assert 'id="request-proposal-approval"' in response.text
    assert 'id="approvals-list"' in response.text
    assert 'id="approved-launches"' in response.text
    assert 'id="active-session"' in response.text
    assert 'id="create-session"' in response.text
    assert 'id="sessions-list"' in response.text
    assert 'id="codeburn-status"' in response.text
    assert 'id="refresh-codeburn"' in response.text
    assert 'id="pwa-status"' in response.text
    assert 'id="readiness-status"' in response.text
    assert 'id="readiness-gaps"' in response.text
    assert 'id="refresh-readiness"' in response.text
    assert 'rel="manifest" href="/manifest.webmanifest"' in response.text
    assert 'rel="icon" href="/assets/icon.svg"' in response.text
    assert 'name="jarvis-runtime-token"' in response.text
    assert "__JARVIS_RUNTIME_TOKEN__" not in response.text
    assert "Codex" in response.text
    assert "Antigravity" in response.text
    assert "Codeburn" in response.text
    assert "/assets/hud.js" in response.text


def test_hud_javascript_connects_runtime_and_requests_microphone(tmp_path):
    client = TestClient(create_app(tmp_path / "state"))

    response = client.get("/assets/hud.js")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/javascript")
    assert "new WebSocket" in response.text
    assert "getUserMedia({ audio: true })" in response.text
    assert "SpeechRecognition" in response.text
    assert "MediaRecorder" in response.text
    assert 'request("voice.audio_chunk"' in response.text
    assert 'request("voice.submit"' in response.text
    assert 'request("voice.intent_propose"' in response.text
    assert 'request("voice.provider_status")' in response.text
    assert 'request("initialize")' in response.text
    assert 'request("session.list", { status: "active", limit: 25 })' in response.text
    assert 'request("session.create"' in response.text
    assert 'request("telemetry.codeburn_status")' in response.text
    assert 'request("runtime.readiness")' in response.text
    assert "/native-tools/codeburn/dist/cli.js status" not in response.text
    assert 'request("approval.list", { status: "pending" })' in response.text
    assert 'request("approval.list", { status: "approved" })' in response.text
    assert "Voice intent proposal" in response.text
    assert "No execution authority" in response.text
    assert "lastVoiceProposal" in response.text
    assert "Review voice proposal" in response.text
    assert "No command was executed" in response.text
    assert 'source: "voice.intent_propose"' in response.text
    assert "renderVoiceProposal(proposal)" in response.text
    assert "PANE_LAUNCHES" in response.text
    assert 'source: "hud.pane.prepare"' in response.text
    assert "pane launch approval requested. No PTY was started." in response.text
    assert "renderApprovals(frame.result.approvals)" in response.text
    assert 'data-approval-action="approved"' in response.text
    assert 'data-approval-action="rejected"' in response.text
    assert 'request("approval.respond"' in response.text
    assert "privilegedParams" in response.text
    assert "runtime_token: runtimeToken" in response.text
    assert "<pre>Scope:" in response.text
    assert 'request("pty.create"' in response.text
    assert "renderApprovedLaunches(frame.result.approvals)" in response.text
    assert "approvedLaunchCommand" in response.text
    assert "Launch Approved PTY" in response.text
    assert "Runtime policy gate still applies" in response.text
    assert "renderSessions(frame.result.sessions)" in response.text
    assert "renderCodeburnStatus(frame.result.codeburn)" in response.text
    assert "Codeburn month usage" in response.text
    assert "renderReadiness(frame.result)" in response.text
    assert "Remaining release gaps" in response.text
    assert "Runtime readiness refresh requested" in response.text
    assert 'navigator.serviceWorker.register("/service-worker.js")' in response.text
    assert "PWA service worker registered" in response.text
    assert "currentSessionId()" in response.text
    assert "Use Session" in response.text
    assert "escapeHtml" in response.text
    assert "Event: ${frame.event_type}" in response.text
    assert 'frame.event_type.startsWith("approval.")' in response.text
    assert 'frame.event_type.startsWith("session.")' in response.text

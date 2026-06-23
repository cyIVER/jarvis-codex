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
    assert 'request("approval.list", { status: "pending" })' in response.text
    assert "Voice intent proposal" in response.text
    assert "No execution authority" in response.text
    assert "lastVoiceProposal" in response.text
    assert "Review voice proposal" in response.text
    assert "No command was executed" in response.text
    assert 'source: "voice.intent_propose"' in response.text
    assert "renderVoiceProposal(proposal)" in response.text
    assert "Event: ${frame.event_type}" in response.text
    assert 'frame.event_type.startsWith("approval.")' in response.text
    assert "Execution requires an explicit runtime command and policy decision" in response.text

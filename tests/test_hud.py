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
    assert 'id="speak-status"' in response.text
    assert 'id="proposal-preview"' in response.text
    assert 'id="request-proposal-approval"' in response.text
    assert 'id="approvals-list"' in response.text
    assert 'id="approved-launches"' in response.text
    assert 'id="active-session"' in response.text
    assert 'id="session-profile"' in response.text
    assert 'id="set-session-profile"' in response.text
    assert 'id="create-session"' in response.text
    assert 'id="sessions-list"' in response.text
    assert 'id="prompt-text"' in response.text
    assert 'id="send-prompt"' in response.text
    assert "This does not execute Codex" in response.text
    assert 'id="swarm-objective"' in response.text
    assert 'id="record-swarm-plan"' in response.text
    assert 'id="request-swarm-start-approval"' in response.text
    assert 'id="swarm-lifecycle-approval-id"' in response.text
    assert 'id="record-swarm-start"' in response.text
    assert 'id="request-swarm-stop-approval"' in response.text
    assert 'id="record-swarm-stop"' in response.text
    assert 'id="swarm-plan-status"' in response.text
    assert "This does not launch agents" in response.text
    assert "Swarm planning is semantic state only" in response.text
    assert 'id="loop-objective"' in response.text
    assert 'id="request-loop-start-approval"' in response.text
    assert 'id="loop-lifecycle-approval-id"' in response.text
    assert 'id="record-loop-start"' in response.text
    assert 'id="request-loop-pause-approval"' in response.text
    assert 'id="record-loop-pause"' in response.text
    assert 'id="request-loop-resume-approval"' in response.text
    assert 'id="record-loop-resume"' in response.text
    assert 'id="request-loop-stop-approval"' in response.text
    assert 'id="record-loop-stop"' in response.text
    assert 'id="loop-lifecycle-status"' in response.text
    assert "They do not start autonomous execution" in response.text
    assert 'id="command-proposal"' in response.text
    assert 'id="record-command-proposal"' in response.text
    assert 'id="command-proposal-status"' in response.text
    assert "it does not request approval or execute" in response.text
    assert 'id="history-search"' in response.text
    assert 'id="search-history"' in response.text
    assert 'id="history-search-results"' in response.text
    assert "Search is read-only" in response.text
    assert 'id="refresh-session-history"' in response.text
    assert 'id="session-history"' in response.text
    assert "This is not an execution queue" in response.text
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
    assert "speechSynthesis" in response.text
    assert "SpeechSynthesisUtterance" in response.text
    assert "speakRuntimeStatus" in response.text
    assert "No local TTS command was run" in response.text
    assert "MediaRecorder" in response.text
    assert 'request("voice.audio_chunk"' in response.text
    assert 'request("voice.submit"' in response.text
    assert 'request("voice.intent_propose"' in response.text
    assert 'request("voice.provider_status")' in response.text
    assert 'request("initialize")' in response.text
    assert 'request("session.list", { status: "active", limit: 25 })' in response.text
    assert 'request("profile.list")' in response.text
    assert 'request("profile.set"' in response.text
    assert "renderProfiles(frame.result.profiles" in response.text
    assert "Profile selection changes session metadata only" in response.text
    assert "Session profile update requested" in response.text
    assert 'request("session.create"' in response.text
    assert 'request("session.resume"' in response.text
    assert "Session resume requested" in response.text
    assert "Resumed session" in response.text
    assert 'request("prompt.send"' in response.text
    assert "Prompt recorded" in response.text
    assert "No execution authority granted" in response.text
    assert "This does not execute a command or agent" in response.text
    assert 'request("swarm.plan"' in response.text
    assert 'request("swarm.start"' in response.text
    assert 'request("swarm.stop"' in response.text
    assert 'requestLoopApproval("loop.start")' in response.text
    assert 'recordLoopLifecycle("loop.start")' in response.text
    assert 'requestLoopApproval("loop.pause")' in response.text
    assert 'recordLoopLifecycle("loop.pause")' in response.text
    assert 'requestLoopApproval("loop.resume")' in response.text
    assert 'recordLoopLifecycle("loop.resume")' in response.text
    assert 'requestLoopApproval("loop.stop")' in response.text
    assert 'recordLoopLifecycle("loop.stop")' in response.text
    assert "Swarm plan record requested" in response.text
    assert "Swarm plan recorded" in response.text
    assert "Swarm start approval requested" in response.text
    assert "Approved swarm start record requested" in response.text
    assert "Swarm stop approval requested" in response.text
    assert "Approved swarm stop record requested" in response.text
    assert "lastSwarmPlanEventId" in response.text
    assert "lastSwarmLifecycleEventId" in response.text
    assert "No agents launched" in response.text
    assert "no Worktrunk mutation occurred" in response.text
    assert "No agents, PTYs, Worktrunk, commands, or workflows executed" in response.text
    assert "Approval does not launch agents or commands" in response.text
    assert "No agents, PTYs, Worktrunk, shell, or workflows launched" in response.text
    assert "Loop lifecycle" in response.text
    assert "lastLoopLifecycleEventId" in response.text
    assert "Approval does not launch agents, PTYs, Worktrunk, shell, or workflows" in response.text
    assert 'request("command.propose"' in response.text
    assert "Command proposal record requested" in response.text
    assert "No approval was created and nothing executed" in response.text
    assert "does not request approval, launch a PTY, or execute" in response.text
    assert 'request("message.search"' in response.text
    assert "renderSearchResults(frame.result.results" in response.text
    assert "History search requested" in response.text
    assert 'request("message.list", { session_id: currentSessionId(), limit: 25 })' in response.text
    assert "renderSessionHistory(frame.result.messages" in response.text
    assert "Session history refresh requested" in response.text
    assert 'request("session.archive"' in response.text
    assert 'request("session.fork"' in response.text
    assert "Fork Session" in response.text
    assert "Session fork requested" in response.text
    assert "Forked session" in response.text
    assert "Archive Session" in response.text
    assert "Session archive requested" in response.text
    assert "Archived session" in response.text
    assert "No semantic history" in response.text
    assert "semantic history" in response.text
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

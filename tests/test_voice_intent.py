import pytest

from jarvis_codex.voice_intent import propose_voice_intent


def test_voice_intent_command_proposal_never_has_execution_authority():
    proposal = propose_voice_intent("run git status --short", profile="observe")

    data = proposal.to_dict()
    assert data["intent_type"] == "command_proposal"
    assert data["target"] == "operator"
    assert data["command"] == "git status --short"
    assert data["approval_required"] is True
    assert data["execution_authority"] is False
    assert data["routed_as_command"] is False
    assert data["policy"]["status"] == "allow"
    assert data["policy"]["execution_authority"] is True


def test_voice_intent_dangerous_command_remains_blocked_policy_proposal():
    proposal = propose_voice_intent("execute command git reset --hard HEAD", profile="dev-loop")

    data = proposal.to_dict()
    assert data["intent_type"] == "command_proposal"
    assert data["execution_authority"] is False
    assert data["policy"]["status"] == "block"
    assert data["policy"]["reason"] == "destructive git reset"


def test_voice_intent_routes_codex_and_antigravity_handoffs():
    codex = propose_voice_intent("ask Codex to review the test failures")
    ag = propose_voice_intent("send AG to challenge the architecture plan")

    assert codex.intent_type == "agent_handoff"
    assert codex.target == "codex"
    assert codex.approval_required is True
    assert codex.execution_authority is False
    assert ag.intent_type == "agent_handoff"
    assert ag.target == "antigravity"
    assert ag.approval_required is True
    assert ag.execution_authority is False


def test_voice_intent_note_and_unknown_are_planning_context_only():
    note = propose_voice_intent("remember the mobile PWA needs private network mode")
    unknown = propose_voice_intent("what is the current runtime status")

    assert note.intent_type == "note"
    assert note.approval_required is False
    assert note.execution_authority is False
    assert unknown.intent_type == "unknown"
    assert unknown.target == "none"
    assert unknown.approval_required is False
    assert unknown.execution_authority is False


def test_voice_intent_rejects_empty_transcript():
    with pytest.raises(ValueError, match="voice transcript is required"):
        propose_voice_intent("  ")
